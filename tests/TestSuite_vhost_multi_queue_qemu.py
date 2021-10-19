# BSD LICENSE
#
# Copyright(c) 2010-2018 Intel Corporation. All rights reserved.
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

Vhost PVP performance using Qemu test suite.
"""
import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase
from framework.virt_common import VM


class TestVhostMultiQueueQemu(TestCase):

    def set_up_all(self):
        # Get and verify the ports
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        # Get the port's socket
        self.pf = self.dut_ports[0]
        netdev = self.dut.ports_info[self.pf]['port']
        self.socket = netdev.get_nic_socket()
        self.cores = self.dut.get_core_list("1S/3C/1T", socket=self.socket)
        self.verify(len(self.cores) >= 3, "Insufficient cores for speed testing")
        self.pci_info = self.dut.ports_info[0]['pci']
        self.frame_sizes = [64, 128, 256, 512, 1024, 1500]
        self.queue_number = 2
        # Using file to save the vhost sample output since in jumboframe case,
        # there will be lots of output

        self.virtio1 = "eth1"
        self.virtio1_mac = "52:54:00:00:00:01"
        self.vm_dut = None

        self.number_of_ports = 1
        self.header_row = ["FrameSize(B)", "Throughput(Mpps)", "LineRate(%)", "Cycle"]
        self.memory_channel = self.dut.get_memory_channels()
        self.pmd_out = PmdOutput(self.dut)

        self.out_path = '/tmp'
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.base_dir = self.dut.base_dir.replace('~', '/root')
        self.app_path = self.dut.apps_name['test-pmd']
        self.app_name = self.app_path[self.app_path.rfind('/')+1:]

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf ./vhost.out", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT %s" % self.app_name, "#")
        self.vm_testpmd_vector = self.app_path + "-c %s -n 3" + \
                                 " -- -i --tx-offloads=0x0 " + \
                                 " --rxq=%d --txq=%d --rss-ip --nb-cores=2" % (self.queue_number, self.queue_number)

    def launch_testpmd(self):
        """
        Launch the vhost sample with different parameters
        """
        vdev = [r"'net_vhost0,iface=%s/vhost-net,queues=%d'" % (self.base_dir, self.queue_number)]
        eal_params = self.dut.create_eal_parameters(cores=self.cores, ports=[self.pci_info], vdevs=vdev)
        para = " -- -i --rxq=%d --txq=%d --nb-cores=2" % (self.queue_number, self.queue_number)
        testcmd_start = self.app_path + eal_params + para
        self.dut.send_expect(testcmd_start, "testpmd> ", 120)
        self.dut.send_expect("set fwd mac", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)

    def start_onevm(self):
        """
        Start One VM with one virtio device
        """
        self.vm = VM(self.dut, 'vm0', 'vhost_sample')
        vm_params = {}
        vm_params['driver'] = 'vhost-user'
        vm_params['opt_path'] = self.base_dir + '/vhost-net'
        vm_params['opt_mac'] = self.virtio1_mac
        vm_params['opt_queue'] = self.queue_number
        vm_params['opt_settings'] = 'mrg_rxbuf=on,mq=on,vectors=%d' % (2*self.queue_number + 2)

        self.vm.set_vm_device(**vm_params)

        try:
            self.vm_dut = self.vm.start()
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

        return True

    def get_vm_coremask(self):
        """
        Get the vm coremask
        """
        cores = self.vm_dut.get_core_list("1S/3C/1T")
        self.verify(len(cores) >= 3, "Insufficient cores for speed testing, add the cpu number in cfg file.")
        self.vm_coremask = utils.create_mask(cores)

    @property
    def check_value(self):
        check_dict = dict.fromkeys(self.frame_sizes)
        linerate = {64: 0.09, 128: 0.15, 256: 0.25, 512: 0.40, 1024: 0.50, 1280: 0.55, 1500: 0.60}
        for size in self.frame_sizes:
            speed = self.wirespeed(self.nic, size, self.number_of_ports)
            check_dict[size] = round(speed * linerate[size], 2)
        return check_dict

    def vhost_performance(self):
        """
        Verify the testpmd can receive and forward the data
        """
        self.result_table_create(self.header_row)
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (self.running_case, frame_size)
            self.logger.info(info)
            payload_size = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip']
            tgenInput = []

            pkt1 = Packet()
            pkt1.assign_layers(['ether', 'ipv4', 'raw'])
            pkt1.config_layers([('ether', {'dst': '%s' % self.virtio1_mac}), ('ipv4', {'dst': '1.1.1.1'}),
                               ('raw', {'payload': ['01'] * int('%d' % payload_size)})])

            pkt1.save_pcapfile(self.tester, "%s/multiqueue.pcap" % self.out_path)

            port = self.tester.get_local_port(self.pf)
            tgenInput.append((port, port, "%s/multiqueue.pcap" % self.out_path))

            fields_config = {'ip':  {'dst': {'action': 'random'}, }, }
            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, fields_config, self.tester.pktgen)
            traffic_opt = {'delay': 5}
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)
            Mpps = pps / 1000000.0
            pct = Mpps * 100 / float(self.wirespeed(self.nic, frame_size,
                                     self.number_of_ports))
            data_row = [frame_size, str(Mpps), str(pct), "Mergeable Multiqueue Performance"]
            self.result_table_add(data_row)
            self.verify(Mpps > self.check_value[frame_size],
                        "%s of frame size %d speed verify failed, expect %s, result %s" % (
                            self.running_case, frame_size, self.check_value[frame_size], Mpps))
        self.result_table_print()

    def send_and_verify(self, verify_type):
        """
        Verify the virtio-pmd can receive the data before/after change queue size
        While verify_type is "vhost queue = virtio queue", the vhost should forward all set of data
        While verify_type is "vhost queue < virtio queue", the vhost should forward all set of data
        While verify_type is "vhost queue > virtio queue", the vhost should forward at least one set of data
        """
        local_port = self.tester.get_local_port(self.dut_ports[0])
        self.tx_interface = self.tester.get_interface(local_port)
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (self.running_case, frame_size)
            self.logger.info(info)
            self.dut.send_expect("clear port stats all", "testpmd> ", 120)
            payload_size = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']
            pkts = Packet()
            pkt1 = Packet()
            pkt1.assign_layers(['ether', 'ipv4', 'udp', 'raw'])
            pkt1.config_layers([('ether', {'dst': '%s' % self.virtio1_mac}), ('ipv4', {'dst': '1.1.1.1'}),
                               ('udp', {'src': 4789, 'dst': 4789}), ('raw', {'payload': ['01'] * int('%d' % payload_size)})])
            pkt2 = Packet()
            pkt2.assign_layers(['ether', 'ipv4', 'udp', 'raw'])
            pkt2.config_layers([('ether', {'dst': '%s' % self.virtio1_mac}), ('ipv4', {'dst': '1.1.1.20'}),
                              ('udp', {'src': 4789, 'dst': 4789}), ('raw', {'payload': ['01'] * int('%d' % payload_size)})])
            pkt3 = Packet()
            pkt3.assign_layers(['ether', 'ipv4', 'udp', 'raw'])
            pkt3.config_layers([('ether', {'dst': '%s' % self.virtio1_mac}), ('ipv4', {'dst': '1.1.1.7'}),
                               ('udp', {'src': 4789, 'dst': 4789}), ('raw', {'payload': ['01'] * int('%d' % payload_size)})])
            pkt4 = Packet()
            pkt4.assign_layers(['ether', 'ipv4', 'udp', 'raw'])
            pkt4.config_layers([('ether', {'dst': '%s' % self.virtio1_mac}), ('ipv4', {'dst': '1.1.1.8'}),
                               ('udp', {'src': 4789, 'dst': 4789}), ('raw', {'payload': ['01'] * int('%d' % payload_size)})])

            pkt = [pkt1, pkt2, pkt3, pkt4]
            for i in pkt:
                pkts.pktgen.pkts.append(i.pktgen.pkt)
            pkts.send_pkt(self.tester, tx_port=self.tx_interface, count=10)

            out = self.dut.send_expect("show port stats 0", "testpmd> ", 120)
            print(out)
            rx_packet = re.search("RX-packets:\s*(\d*)", out)
            rx_num = int(rx_packet.group(1))
            tx_packet = re.search("TX-packets:\s*(\d*)", out)
            tx_num = int(tx_packet.group(1))
            if verify_type == "vhost queue = virtio queue" or verify_type == "vhost queue < virtio queue":
                verify_rx_num = 40
                verify_tx_num = 40
            elif verify_type == "vhost queue > virtio queue":
                verify_rx_num = 40
                verify_tx_num = 10

            self.verify(rx_num >= verify_rx_num and tx_num >= verify_tx_num,
                        "The rx or tx lost some packets of frame-size:%d" % frame_size)

    def test_perf_pvp_multiqemu_mergeable_pmd(self):
        """
        Test the performance for mergeable path
        """
        self.launch_testpmd()
        self.start_onevm()
        self.get_vm_coremask()

        self.vm_dut.send_expect(self.vm_testpmd_vector % self.vm_coremask, "testpmd>", 20)
        self.vm_dut.send_expect("set fwd mac", "testpmd>", 20)
        self.vm_dut.send_expect("start", "testpmd>")

        self.dut.send_expect("stop", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(5)
        self.vhost_performance()
        self.vm_dut.kill_all()

    def test_dynamic_change_virtio_queue_size(self):
        """
        Test the performance for change virtio queue size
        """
        self.launch_testpmd()
        self.start_onevm()
        self.vm_testpmd_queue_1 = self.app_path + "-c %s -n 3" + \
                                  " -- -i --tx-offloads=0x0 " + \
                                  " --rxq=1 --txq=1 --rss-ip --nb-cores=1"
        self.get_vm_coremask()
        self.vm_dut.send_expect(self.vm_testpmd_queue_1 % self.vm_coremask, "testpmd>", 20)
        self.vm_dut.send_expect("set fwd mac", "testpmd>", 20)
        self.vm_dut.send_expect("start", "testpmd>")

        self.dut.send_expect("clear port stats all", "testpmd> ", 120)
        res = self.pmd_out.wait_link_status_up('all', timeout = 15)
        self.verify(res is True, 'There has port link is down')
        self.send_and_verify("vhost queue > virtio queue")

        self.vm_dut.send_expect("stop", "testpmd>", 20)
        self.vm_dut.send_expect("port stop all", "testpmd>")
        self.vm_dut.send_expect("port config all rxq 2", "testpmd>", 20)
        self.vm_dut.send_expect("port config all txq 2", "testpmd>")
        self.vm_dut.send_expect("port start all", "testpmd>", 20)
        self.vm_dut.send_expect("start", "testpmd>")

        self.dut.send_expect("stop", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        res = self.pmd_out.wait_link_status_up('all', timeout = 15)
        self.verify(res is True, 'There has port link is down')


        self.dut.send_expect("clear port stats all", "testpmd> ", 120)
        self.send_and_verify("vhost queue = virtio queue")

        self.vm_dut.kill_all()
        self.dut.send_expect("quit", "# ", 120)

    def test_dynamic_change_vhost_queue_size(self):
        """
        Test the performance for change vhost queue size
        """
        self.queue_number = 2
        vdev = [r"'net_vhost0,iface=%s/vhost-net,queues=2'" % self.base_dir]
        eal_params = self.dut.create_eal_parameters(cores=self.cores, ports=[self.pci_info], vdevs=vdev)
        para = " -- -i --rxq=1 --txq=1 --nb-cores=1"
        testcmd_start = self.app_path + eal_params + para
        self.dut.send_expect(testcmd_start, "testpmd> ", 120)
        self.dut.send_expect("set fwd mac", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)

        self.start_onevm()

        self.get_vm_coremask()
        self.vm_dut.send_expect(self.vm_testpmd_vector % self.vm_coremask, "testpmd>", 20)
        self.vm_dut.send_expect("set fwd mac", "testpmd>", 20)
        self.vm_dut.send_expect("start", "testpmd>")
        self.dut.send_expect("clear port stats all", "testpmd> ", 120)
        res = self.pmd_out.wait_link_status_up('all', timeout = 15)
        self.verify(res is True, 'There has port link is down')

        self.send_and_verify("vhost queue < virtio queue")

        self.dut.send_expect("stop", "testpmd>", 20)
        self.dut.send_expect("port stop all", "testpmd>")
        self.dut.send_expect("port config all rxq 2", "testpmd>", 20)
        self.dut.send_expect("port config all txq 2", "testpmd>")
        self.dut.send_expect("port start all", "testpmd>", 20)
        self.dut.send_expect("start", "testpmd>")
        self.dut.send_expect("clear port stats all", "testpmd>")
        res = self.pmd_out.wait_link_status_up('all', timeout = 15)
        self.verify(res is True, 'There has port link is down')

        self.send_and_verify("vhost queue = virtio queue")

        self.vm_dut.kill_all()
        self.dut.send_expect("quit", "# ", 120)

    def tear_down(self):
        """
        Run after each test case.
        Clear vhost-switch and qemu to avoid blocking the following TCs
        """
        if hasattr(self, "vm"):
            self.vm.stop()
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
