#
# BSD LICENSE
#
# Copyright(c) 2010-2020 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""
DPDK Test suite.
This test vhost/virtio-user pvp multi-queues with split virtqueue
and packed virtqueue different rx/tx paths, includes split virtqueue in-order
mergeable, in-order non-mergeable, mergeable, non-mergeable, vector_rx path test,
and packed virtqueue in-order mergeable, in-order non-mergeable, mergeable,
non-mergeable path, also cover port restart test with each path.
"""
import time
import re
from test_case import TestCase
from packet import Packet
from pktgen import PacketGeneratorHelper


class TestPVPVirtioUserMultiQueuesPortRestart(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.frame_sizes = [64]
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        # get core mask
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list('all', socket=self.ports_socket)
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.out_path = '/tmp'
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.pci_info = self.dut.ports_info[0]['pci']
        self.vhost = self.dut.new_session(suite="vhost-user")
        self.tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.queue_number = 2
        self.dut.kill_all()

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.dut.send_expect("rm -rf ./vhost.out", "#")
        # Prepare the result table
        self.table_header = ["FrameSize(B)", "Mode",
                             "Throughput(Mpps)", "% linerate", "Cycle"]
        self.result_table_create(self.table_header)

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        testcmd = self.dut.target + "/app/testpmd "
        vdev = 'net_vhost0,iface=vhost-net,queues=2,client=0'
        eal_params = self.dut.create_eal_parameters(cores=self.core_list[2:5], prefix='vhost', ports=[self.pci_info],
                                                    vdevs=[vdev])
        para = " -- -i --nb-cores=2 --rxq=%s --txq=%s --rss-ip" % (self.queue_number, self.queue_number)
        command_line_vhost = testcmd + eal_params + para
        self.vhost.send_expect(command_line_vhost, "testpmd> ", 120)
        self.vhost.send_expect("set fwd mac", "testpmd> ", 120)
        self.vhost.send_expect("start", "testpmd> ", 120)

    def start_virtio_user_testpmd(self, flag):
        """
        start testpmd in vm depend on different path
        """
        testcmd = self.dut.target + "/app/testpmd "
        vdev = 'net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2'
        if 'packed_ring' in flag:
            vdev += ',packed_vq=1'
        if 'nonmergeable' in flag or 'vector' in flag:
            vdev += ',mrg_rxbuf=0'
        if 'inorder' not in flag:
            vdev += ',in_order=0'
        eal_params = self.dut.create_eal_parameters(cores=self.core_list[5:8], prefix='virtio', no_pci=True,
                                                    vdevs=[vdev])
        if 'vector' not in flag:
            para = " -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=2 --rxq=%s --txq=%s --rss-ip" % (
            self.queue_number, self.queue_number)
        else:
            para = " -- -i --tx-offloads=0x0 --rss-ip --nb-cores=2 --rxq=%s --txq=%s --rss-ip" % (
            self.queue_number, self.queue_number)
        command_line_user = testcmd + eal_params + para
        self.dut.send_expect(command_line_user, "testpmd> ", 30)
        self.dut.send_expect("set fwd mac", "testpmd> ", 30)
        self.dut.send_expect("start", "testpmd> ", 30)

    def check_port_link_status_after_port_restart(self):
        """
        check the link status after port restart
        """
        loop = 1
        port_status = 'down'
        while (loop <= 5):
            out = self.vhost.send_expect("show port info 0", "testpmd> ", 120)
            port_status = re.findall("Link\s*status:\s*([a-z]*)", out)
            if ("down" not in port_status):
                break
            time.sleep(2)
            loop = loop + 1
        self.verify("down" not in port_status, "port can not up after restart")

    def port_restart(self, restart_times=1):
        for i in range(restart_times):
            self.vhost.send_expect("stop", "testpmd> ", 120)
            self.vhost.send_expect("port stop 0", "testpmd> ", 120)
            self.vhost.send_expect("clear port stats 0", "testpmd> ", 120)
            self.vhost.send_expect("port start 0", "testpmd> ", 120)
            self.check_port_link_status_after_port_restart()
            self.vhost.send_expect("start", "testpmd> ", 120)

    def update_table_info(self, case_info, frame_size, Mpps, throughtput, Cycle):
        results_row = [frame_size]
        results_row.append(case_info)
        results_row.append(Mpps)
        results_row.append(throughtput)
        results_row.append(Cycle)
        self.result_table_add(results_row)

    def calculate_avg_throughput(self, frame_size):
        """
        start to send packet and get the throughput
        """
        pkt = Packet(pkt_type='IP_RAW', pkt_len=frame_size)
        pkt.config_layer('ether', {'dst': '%s' % self.dst_mac})
        pkt.save_pcapfile(self.tester, "%s/pvp_multipath.pcap" % (self.out_path))

        tgenInput = []
        port = self.tester.get_local_port(self.dut_ports[0])
        tgenInput.append((port, port, "%s/pvp_multipath.pcap" % self.out_path))
        self.tester.pktgen.clear_streams()
        fields_config = {'ip': {'dst': {'action': 'random'}}}
        streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, fields_config, self.tester.pktgen)
        # set traffic option
        traffic_opt = {'delay': 5}
        _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)
        Mpps = pps / 1000000.0
        self.verify(Mpps > 0, "can not receive packets of frame size %d" % (frame_size))
        throughput = Mpps * 100 / \
                    float(self.wirespeed(self.nic, frame_size, 1))
        return Mpps, throughput

    def send_and_verify(self, case_info):
        """
        start to send packets and verify it
        """
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (self.running_case, frame_size)
            self.logger.info(info)
            Mpps, throughput = self.calculate_avg_throughput(frame_size)
            self.update_table_info(case_info, frame_size, Mpps, throughput, "Before Restart")
            self.check_packets_of_each_queue(frame_size)
            restart_times = 100 if case_info == 'packed_ring_mergeable' else 1
            self.port_restart(restart_times=restart_times)
            Mpps, throughput = self.calculate_avg_throughput(frame_size)
            self.update_table_info(case_info, frame_size, Mpps, throughput, "After Restart")
            self.check_packets_of_each_queue(frame_size)

    def check_packets_of_each_queue(self, frame_size):
        """
        check each queue has receive packets
        """
        out = self.dut.send_expect("stop", "testpmd> ", 60)
        p = re.compile("RX Port= 0/Queue= (\d+) -> TX Port= 0/Queue= \d+.*\n.*RX-packets:\s?(\d+).*TX-packets:\s?(\d+)")
        res = p.findall(out)
        self.res_queues = sorted([int(i[0]) for i in res])
        self.res_rx_pkts = [int(i[1]) for i in res]
        self.res_tx_pkts = [int(i[2]) for i in res]
        self.verify(self.res_queues == list(range(self.queue_number)),
                    "frame_size: %s, expect %s queues to handle packets, result %s queues" % (frame_size, list(range(self.queue_number)), self.res_queues))
        self.verify(all(self.res_rx_pkts), "each queue should has rx packets, result: %s" % self.res_rx_pkts)
        self.verify(all(self.res_tx_pkts), "each queue should has tx packets, result: %s" % self.res_tx_pkts)
        self.dut.send_expect("start", "testpmd> ", 60)

    def close_all_testpmd(self):
        """
        close testpmd about vhost-user and vm_testpmd
        """
        self.vhost.send_expect("quit", "#", 60)
        self.dut.send_expect("quit", "#", 60)

    def test_perf_pvp_2queues_test_with_packed_ring_mergeable_path(self):
        self.start_vhost_testpmd()
        self.start_virtio_user_testpmd(flag="packed_ring_mergeable")
        self.send_and_verify("packed_ring_mergeable")
        self.close_all_testpmd()
        self.result_table_print()

    def test_perf_pvp_2queues_test_with_packed_ring_nonmergeable_path(self):
        self.start_vhost_testpmd()
        self.start_virtio_user_testpmd(flag="packed_ring_nonmergeable")
        self.send_and_verify("packed_ring_nonmergeable")
        self.close_all_testpmd()
        self.result_table_print()

    def test_perf_pvp_2queues_test_with_split_ring_inorder_mergeable_path(self):
        self.start_vhost_testpmd()
        self.start_virtio_user_testpmd(flag="split_ring_inorder_mergeable")
        self.send_and_verify("split_ring_inorder_mergeable")
        self.close_all_testpmd()
        self.result_table_print()

    def test_perf_pvp_2queues_test_with_split_ring_inorder_nonmergeable_path(self):
        self.start_vhost_testpmd()
        self.start_virtio_user_testpmd(flag="split_ring_inorder_nonmergeable")
        self.send_and_verify("split_ring_inorder_nonmergeable")
        self.close_all_testpmd()
        self.result_table_print()

    def test_perf_pvp_2queues_test_with_split_ring_mergeable_path(self):
        self.start_vhost_testpmd()
        self.start_virtio_user_testpmd(flag="split_ring_mergeable")
        self.send_and_verify("split_ring_mergeable")
        self.close_all_testpmd()
        self.result_table_print()

    def test_perf_pvp_2queues_test_with_split_ring_nonmergeable_path(self):
        self.start_vhost_testpmd()
        self.start_virtio_user_testpmd(flag="split_ring_nonmergeable")
        self.send_and_verify("split_ring_nonmergeable")
        self.close_all_testpmd()
        self.result_table_print()

    def test_perf_pvp_2queues_test_with_split_ring_vector_rx_path(self):
        self.start_vhost_testpmd()
        self.start_virtio_user_testpmd(flag="split_ring_vector_rx")
        self.send_and_verify("split_ring_vector_rx")
        self.close_all_testpmd()
        self.result_table_print()

    def test_perf_pvp_2queues_test_with_packed_ring_inorder_mergeable_path(self):
        self.start_vhost_testpmd()
        self.start_virtio_user_testpmd(flag="packed_ring_inorder_mergeable")
        self.send_and_verify("packed_ring_inorder_mergeable")
        self.close_all_testpmd()
        self.result_table_print()

    def test_perf_pvp_2queues_test_with_packed_ring_inorder_nonmergeable_path(self):
        self.start_vhost_testpmd()
        self.start_virtio_user_testpmd(flag="packed_ring_inorder_nonmergeable")
        self.send_and_verify("packed_ring_inorder_nonmergeable")
        self.close_all_testpmd()
        self.result_table_print()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost)
