# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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
Test vhost/virtio-user loopback multi-queues on 8 tx/rx path.
Includes Mergeable, Normal, Vector_RX, Inorder mergeable,
Inorder no-mergeable, Virtio 1.1 mergeable, Virtio 1.1 no-mergeable Path,
Virtio 1.1 inorder no-mergeable Path.
"""

import utils
import time
import re
from settings import HEADER_SIZE
from test_case import TestCase
from pktgen import PacketGeneratorHelper


class TestPVPVirtioMultiQueues(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.tester.extend_external_packet_generator(TestPVPVirtioMultiQueues, self)
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.core_config = "1S/6C/1T"
        self.queue_number = 2
        self.port_number = 2
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n['socket'])
                          == self.ports_socket])
        self.verify(self.cores_num >= 6,
                    "There has not enought cores to test this case")
        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip'] + \
            HEADER_SIZE['udp']
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket)
        self.core_list_user = self.core_list[0:3]
        self.core_list_host = self.core_list[3:6]
        self.core_mask_user = utils.create_mask(self.core_list_user)
        self.core_mask_host = utils.create_mask(self.core_list_host)
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])

        self.logger.info("you can config packet_size in file %s.cfg," % self.suite_name + \
                        "in region 'suite' like packet_sizes=[64, 128, 256]")
        # get the frame_sizes from cfg file
        if 'packet_sizes' in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()['packet_sizes']

        self.out_path = '/tmp'
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        Run before each test case.
        """
        # Prepare the result table
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.table_header = ["Frame", "Mode", "Throughput(Mpps)", "% linerate"]
        self.result_table_create(self.table_header)

        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        command_line_client = self.dut.target + "/app/testpmd -n %d -c %s --socket-mem 1024,1024" + \
                              " --legacy-mem --file-prefix=vhost --vdev " + \
                              "'net_vhost0,iface=vhost-net,queues=2,client=0' -- -i --nb-cores=2 " + \
                              "--rxq=2 --txq=2 --rss-ip"
        command_line_client = command_line_client % (
            self.dut.get_memory_channels(), self.core_mask_host)
        self.vhost_user.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def start_virtio_testpmd(self, args):
        """
        start testpmd on virtio
        """
        command_line_user = self.dut.target + "/app/testpmd -n %d -c %s " + \
                            " --socket-mem 1024,1024 --legacy-mem --no-pci --file-prefix=virtio " + \
                            "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,%s " + \
                            "-- -i %s --rss-ip --nb-cores=2 --rxq=2 --txq=2"
        command_line_user = command_line_user % (
            self.dut.get_memory_channels(), self.core_mask_user,
            args["version"], args["path"])
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.virtio_user.send_expect("start", "testpmd> ", 120)

    def update_result_table(self, frame_size, case_info, Mpps, throughput):
        results_row = [frame_size]
        results_row.append(case_info)
        results_row.append(Mpps)
        results_row.append(throughput)
        self.result_table_add(results_row)

    def check_packets_of_each_queue(self, frame_size):
        """
        check each queue has receive packets
        """
        out = self.vhost_user.send_expect("stop", "testpmd> ", 60)
        for port_index in range(0, self.port_number):
            for queue_index in range(0, self.queue_number):
                queue_info = re.findall("RX\s*Port=\s*%d/Queue=\s*%d" %
                                (port_index, queue_index),  out)
                queue = queue_info[0]
                index = out.find(queue)
                rx = re.search("RX-packets:\s*(\d*)", out[index:])
                tx = re.search("TX-packets:\s*(\d*)", out[index:])
                rx_packets = int(rx.group(1))
                tx_packets = int(tx.group(1))
                self.verify(rx_packets > 0 and tx_packets > 0,
                      "The queue %d rx-packets or tx-packets is 0 about " %
                      queue_index + \
                      "frame_size:%d, rx-packets:%d, tx-packets:%d" %
                      (frame_size, rx_packets, tx_packets))

        self.vhost_user.send_expect("start", "testpmd> ", 60)

    def set_fields(self):
        """
        set ip protocol field behavior
        """
        fields_config = {'ip':  {'dst': {'action': 'random'}, }, }
        return fields_config

    def send_and_verify(self, case_info):
        """
        start to send packets and calculate avg throughput
        """
        for frame_size in self.frame_sizes:
            payload_size = frame_size - self.headers_size
            tgen_input = []
            port = self.tester.get_local_port(self.dut_ports[0])
            self.tester.scapy_append('a=[Ether(dst="%s")/IP(src="0.240.74.101",proto=255)/UDP()/("X"*%d)]' % (self.dst_mac, payload_size))
            self.tester.scapy_append('wrpcap("%s/multiqueue.pcap" , a)' % self.out_path)
            self.tester.scapy_execute()

            tgen_input.append((port, port, "%s/multiqueue.pcap" % self.out_path))

            vm_config = self.set_fields()
            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100, vm_config, self.tester.pktgen)
            # set traffic option
            traffic_opt = {'delay': 5, 'duration': 20}
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)
            Mpps = pps / 1000000.0
            self.verify(Mpps > 0, "can not receive packets of frame size %d" % (frame_size))
            throughput = Mpps * 100 / \
                        float(self.wirespeed(self.nic, frame_size, 1))

            self.update_result_table(frame_size, case_info, Mpps, throughput)
            self.check_packets_of_each_queue(frame_size)
        self.result_table_print()

    def close_all_testpmd(self):
        """
        close all testpmd of vhost and virtio
        """
        self.vhost_user.send_expect("quit", "#", 60)
        self.virtio_user.send_expect("quit", "#", 60)

    def close_all_session(self):
        """
        close all session of vhost and vhost-user
        """
        self.dut.close_session(self.virtio_user)
        self.dut.close_session(self.vhost_user)

    def test_perf_pvp_viritouser_multi_queue_virtio11_mergeable(self):
        """
        performance for Vhost PVP virtio 1.1 Mergeable Path.
        """
        virtio_pmd_arg = {"version": "in_order=0,packed_vq=1,mrg_rxbuf=1",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virtio_1.1 mergeable on")
        self.close_all_testpmd()

    def test_perf_pvp_viritouser_multi_queue_virtio11_normal(self):
        """
        performance for Vhost PVP virtio1.1 Normal Path.
        """
        virtio_pmd_arg = {"version": "in_order=0,packed_vq=1,mrg_rxbuf=0",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virtio_1.1 mergeable off")
        self.close_all_testpmd()

    def test_perf_pvp_viritouser_multi_queue_virtio11_inorder(self):
        """
        performance for Vhost PVP virtio1.1 inorder Path.
        """
        virtio_pmd_arg = {"version": "in_order=1,packed_vq=1,mrg_rxbuf=0",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virtio_1.1 inorder")
        self.close_all_testpmd()

    def test_perf_pvp_viritouser_multi_queue_inorder_mergeable(self):
        """
        performance for Vhost PVP In_order mergeable Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=1,mrg_rxbuf=1",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("inoder mergeable on")
        self.close_all_testpmd()

    def test_perf_pvp_viritouser_multi_queue_inorder_no_mergeable(self):
        """
        performance for Vhost PVP In_order no_mergeable Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=1,mrg_rxbuf=0",
                        "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("inoder mergeable off")
        self.close_all_testpmd()

    def test_perf_pvp_viritouser_mulit_queue_mergeable(self):
        """
        performance for Vhost PVP Mergeable Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=1",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virito mergeable")
        self.close_all_testpmd()

    def test_perf_pvp_viritouser_multi_queue_normal(self):
        """
        performance for Vhost PVP Normal Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=0",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virtio normal")
        self.close_all_testpmd()

    def test_perf_pvp_viritouser_multi_queue_vector_rx(self):
        """
        performance for Vhost PVP Vector_RX Path
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=0",
                            "path": "--tx-offloads=0x0"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.send_and_verify("virito vector rx")
        self.close_all_testpmd()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.close_all_session()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
