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
import utils
from test_case import TestCase
from settings import HEADER_SIZE
from virt_common import VM
from packet import Packet, send_packets, save_packets


class TestVhostUserOneCopyOneVm(TestCase):

    def set_up_all(self):
        # Get and verify the ports
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        local_port = self.tester.get_local_port(self.dut_ports[0])
        self.tx_interface = self.tester.get_interface(local_port)
        # Get the port's socket
        self.pf = self.dut_ports[0]
        netdev = self.dut.ports_info[self.pf]['port']
        self.socket = netdev.get_nic_socket()
        self.cores = self.dut.get_core_list("1S/3C/1T", socket=self.socket)
        self.verify(len(self.cores) >= 3, "Insufficient cores for speed testing")

        self.queue_number = 2
        # Using file to save the vhost sample output since in jumboframe case,
        # there will be lots of output

        self.virtio1 = "eth1"
        self.virtio1_mac = "52:54:00:00:00:01"
        self.vm_dut = None

        self.number_of_ports = 1
        self.header_row = ["FrameSize(B)", "Throughput(Mpps)", "LineRate(%)", "Cycle"]
        self.memory_channel = self.dut.get_memory_channels()

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf ./vhost.out", "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT vhost-switch", "#")

        self.frame_sizes = [64, 128, 256, 512, 1024, 1500]
        self.vm_testpmd_vector = self.target + "/app/testpmd -c %s -n 3" + \
                                 " -- -i --tx-offloads=0x0 " + \
                                 " --rxq=%d --txq=%d --rss-ip --nb-cores=2" % (self.queue_number, self.queue_number)

    def launch_testpmd(self):
        """
        Launch the vhost sample with different parameters
        """
        testcmd = self.target + "/app/testpmd -c %s -n %d --socket-mem 1024,1024" + \
                       " --vdev 'net_vhost0,iface=vhost-net,queues=%d' -- -i --rxq=%d --txq=%d --nb-cores=2"
        self.coremask = utils.create_mask(self.cores)
        testcmd_start = testcmd % (self.coremask, self.memory_channel, self.queue_number, self.queue_number, self.queue_number)

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
        vm_params['opt_path'] = './vhost-net'
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

    def vhost_performance(self):
        """
        Verify the testpmd can receive and forward the data
        """
        self.result_table_create(self.header_row)
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (self.running_case, frame_size)
            self.logger.info(info)
            payload_size = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']
            tgenInput = []

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
            save_packets(pkt, "/root/multiqueue_2.pcap")

            port = self.tester.get_local_port(self.pf)
            tgenInput.append((port, port, "multiqueue_2.pcap"))

            _, pps = self.tester.traffic_generator_throughput(tgenInput, delay=30)
            Mpps = pps / 1000000.0
            pct = Mpps * 100 / float(self.wirespeed(self.nic, frame_size,
                                     self.number_of_ports))
            data_row = [frame_size, str(Mpps), str(pct), "Mergeable Multiqueue Performance"]
            self.result_table_add(data_row)
            self.verify(Mpps != 0, "The receive data of frame-size: %d is 0" % frame_size)
        self.result_table_print()

    def send_and_verify(self, verify_type):
        """
        Verify the virtio-pmd can receive the data before/after change queue size
        While verify_type is "vhost queue = virtio queue", the vhost should forward all set of data
        While verify_type is "vhost queue < virtio queue", the vhost should forward all set of data
        While verify_type is "vhost queue > virtio queue", the vhost should forward at least one set of data
        """
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (self.running_case, frame_size)
            self.logger.info(info)
            self.dut.send_expect("clear port stats all", "testpmd> ", 120)
            payload_size = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']

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

            pkt = [pkt1, pkt2, pkt3, pkt4] * 10
            send_packets(self.tx_interface, pkt)

            out = self.dut.send_expect("show port stats 0", "testpmd> ", 120)
            print out
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
        self.vm_testpmd_queue_1 = self.target + "/app/testpmd -c %s -n 3" + \
                                  " -- -i --tx-offloads=0x0 " + \
                                  " --rxq=1 --txq=1 --rss-ip --nb-cores=1"
        self.get_vm_coremask()
        self.vm_dut.send_expect(self.vm_testpmd_queue_1 % self.vm_coremask, "testpmd>", 20)
        self.vm_dut.send_expect("set fwd mac", "testpmd>", 20)
        self.vm_dut.send_expect("start", "testpmd>")

        self.dut.send_expect("clear port stats all", "testpmd> ", 120)
        self.send_and_verify("vhost queue > virtio queue")

        self.vm_dut.send_expect("stop", "testpmd>", 20)
        self.vm_dut.send_expect("port stop all", "testpmd>")
        self.vm_dut.send_expect("port config all rxq 2", "testpmd>", 20)
        self.vm_dut.send_expect("port config all txq 2", "testpmd>")
        self.vm_dut.send_expect("port start all", "testpmd>", 20)
        self.vm_dut.send_expect("start", "testpmd>")

        self.dut.send_expect("stop", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)

        self.dut.send_expect("clear port stats all", "testpmd> ", 120)
        self.send_and_verify("vhost queue = virtio queue")

        self.vm_dut.kill_all()
        self.dut.send_expect("quit", "# ", 120)

    def test_dynamic_change_vhost_queue_size(self):
        """
        Test the performance for change vhost queue size
        """
        self.queue_number = 2
        testcmd = self.target + "/app/testpmd -c %s -n %d --socket-mem 1024,1024" + \
                       " --vdev 'net_vhost0,iface=vhost-net,queues=2' -- -i --rxq=1 --txq=1 --nb-cores=1"
        self.coremask = utils.create_mask(self.cores)
        testcmd_start = testcmd % (self.coremask, self.memory_channel)

        self.dut.send_expect(testcmd_start, "testpmd> ", 120)
        self.dut.send_expect("set fwd mac", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)

        self.start_onevm()

        self.get_vm_coremask()
        self.vm_dut.send_expect(self.vm_testpmd_vector % self.vm_coremask, "testpmd>", 20)
        self.vm_dut.send_expect("set fwd mac", "testpmd>", 20)
        self.vm_dut.send_expect("start", "testpmd>")
        self.dut.send_expect("clear port stats all", "testpmd> ", 120)

        self.send_and_verify("vhost queue < virtio queue")

        self.dut.send_expect("stop", "testpmd>", 20)
        self.dut.send_expect("port stop all", "testpmd>")
        self.dut.send_expect("port config all rxq 2", "testpmd>", 20)
        self.dut.send_expect("port config all txq 2", "testpmd>")
        self.dut.send_expect("port start all", "testpmd>", 20)
        self.dut.send_expect("start", "testpmd>")
        self.dut.send_expect("clear port stats all", "testpmd>")

        self.send_and_verify("vhost queue = virtio queue")

        self.vm_dut.kill_all()
        self.dut.send_expect("quit", "# ", 120)

    def tear_down(self):
        """
        Run after each test case.
        Clear vhost-switch and qemu to avoid blocking the following TCs
        """
        self.vm.stop()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
