# BSD LICENSE
#
# Copyright(c) 2010-2017 Intel Corporation. All rights reserved.
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

vhost pmd xstats test suite.
"""
import re
import time
import utils
import datetime
import copy
from test_case import TestCase
from settings import HEADER_SIZE
from qemu_kvm import QEMUKvm
from packet import Packet
ETHER_JUMBO_FRAME_MTU = 9000
DEFAULT_JUMBO_FRAME_MTU = 1500

class TestVhostPmdXstats(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.unbind_ports = copy.deepcopy(self.dut_ports)
        self.unbind_ports.remove(0)
        self.dut.unbind_interfaces_linux(self.unbind_ports)
        txport = self.tester.get_local_port(self.dut_ports[0])
        self.txItf = self.tester.get_interface(txport)
        self.scapy_num = 0
        self.dmac = self.dut.get_mac_address(self.dut_ports[0])
        self.virtio1_mac = "52:54:00:00:00:01"
        self.core_config = "1S/6C/1T"
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n['socket'])
                              == self.ports_socket])
        self.verify(self.cores_num >= 6,
                    "There has not enough cores to test this case")
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket)
        self.core_list_user = self.core_list[0:3]
        self.core_list_host = self.core_list[3:6]
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.app_testpmd_path = self.dut.apps_name['test-pmd']

    def set_up(self):
        """ 
        Run before each test case.
        Launch vhost sample using default params
        """
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")

    @property
    def check_2M_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if out == '2048' else False

    def scapy_send_packet(self, pktsize, dmac, num=1):
        """
        Send a packet to port
        """
        self.scapy_num += 1
        pkt = Packet(pkt_type='TCP', pkt_len=pktsize)
        pkt.config_layer('ether', {'dst': dmac})
        pkt.send_pkt(self.tester, tx_port=self.txItf, count=num)

    def send_verify(self, scope, mun):
        """
        according the scope to check results
        """
        out = self.vhost_user.send_expect(
            "show port xstats 1", "testpmd>", 60)
        packet_rx = re.search("rx_%s_packets:\s*(\d*)" % scope, out)
        sum_packet_rx = packet_rx.group(1)
        packet_tx = re.search("tx_%s_packets:\s*(\d*)" % scope, out)
        sum_packet_tx = packet_tx.group(1)
        self.verify(int(sum_packet_rx) >= mun,
                    "Insufficient the received packets from nic")
        self.verify(int(sum_packet_tx) >= mun,
                    "Insufficient the received packets from virtio")

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        eal_param = self.dut.create_eal_parameters(socket=self.ports_socket, cores=self.core_list_host, prefix='vhost',
                                                   vdevs=['net_vhost0,iface=vhost-net,queues=2,client=0'])
        command_line_client = "./%s " % self.app_testpmd_path + eal_param + ' -- -i --nb-cores=2 --rxq=2 --txq=2 --rss-ip'
        self.vhost_user.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost_user.send_expect("set fwd io", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def start_virtio_testpmd(self, args):
        """
        start testpmd on virtio
        """
        eal_param = self.dut.create_eal_parameters(socket=self.ports_socket, cores=self.core_list_user, prefix='virtio',
                                                   no_pci=True, vdevs=[
                'net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=2,%s' % args["version"]])
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        command_line_user = "./%s " % self.app_testpmd_path + eal_param + " -- -i %s --rss-ip --nb-cores=2 --rxq=2 --txq=2" % \
                            args["path"]
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd io", "testpmd> ", 120)
        self.virtio_user.send_expect("start", "testpmd> ", 120)

    def xstats_number_and_type_verify(self):
        """
        Verify receiving and transmitting packets correctly in the Vhost PMD xstats
        """
        out = self.vhost_user.send_expect(
            "show port xstats 1", "testpmd>", 60)
        p = re.compile(r'rx_size_[0-9]+_[to_\w+]*packets')
        categories = p.findall(out)
        categories = categories[:-1]
        self.verify(len(categories) > 0, 'Unable to find the categories of RX packet size!')
        for cat in categories:
            scope = re.search(r'(?<=rx_)\w+(?=_packets)', cat).group(0)
            pktsize = int(re.search(r'(?<=rx_size_)\d+', cat).group(0))
            if pktsize > 1518:
                self.tester.send_expect('ifconfig %s mtu %d' % (self.txItf, ETHER_JUMBO_FRAME_MTU), '# ')
            types = ['ff:ff:ff:ff:ff:ff', '01:00:00:33:00:01']
            for p in types:
                if p == 'ff:ff:ff:ff:ff:ff':
                    scope = 'broadcast'
                    self.dmac = 'ff:ff:ff:ff:ff:ff'
                elif p == '01:00:00:33:00:01':
                    scope = 'multicast'
                    self.dmac = '01:00:00:33:00:01'
                self.scapy_send_packet(int(pktsize + 4), self.dmac, 10000)
                self.send_verify(scope, 10000)
                self.clear_port_xstats(scope)
            self.tester.send_expect('ifconfig %s mtu %d' % (self.txItf, DEFAULT_JUMBO_FRAME_MTU), '# ')

    def test_vhost_xstats_virtio11_mergeable(self):
        """
        performance for Vhost PVP virtio1.1 Mergeable Path.
        """
        self.scapy_num = 0
        virtio_pmd_arg = {"version": "in_order=0,packed_vq=1,mrg_rxbuf=1",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        # stability test with basic packets number check
        self.scapy_num = 0
        date_old = datetime.datetime.now()
        date_new = date_old + datetime.timedelta(minutes=2)
        while (1):
            date_now = datetime.datetime.now()
            scope = 'multicast'
            self.dmac = '01:00:00:33:00:01'
            self.scapy_send_packet(64, self.dmac, 1)
            if date_now >= date_new:
                break
        self.send_verify(scope, self.scapy_num)
        self.close_all_testpmd()

    def test_vhost_xstats_virtio11_no_mergeable(self):
        """
        performance for Vhost PVP virtio1.1 no_mergeable Path.
        """
        virtio_pmd_arg = {"version": "in_order=0,packed_vq=1,mrg_rxbuf=0",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_virtio11_inorder_mergeable(self):
        """
        performance for Vhost PVP virtio1.1 inorder Mergeable Path.
        """
        virtio_pmd_arg = {"version": "in_order=1,packed_vq=1,mrg_rxbuf=1",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_virtio11_inorder_no_mergeable(self):
        """
        performance for Vhost PVP virtio1.1 inorder no_mergeable Path.
        """
        virtio_pmd_arg = {"version": "in_order=1,packed_vq=1,mrg_rxbuf=0,vectorized=1",
                            "path": "--rx-offloads=0x10 --enable-hw-vlan-strip --rss-ip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_virtio11_vector(self):
        """
        performance for Vhost PVP virtio1.1 inorder no_mergeable Path.
        """
        virtio_pmd_arg = {"version": "in_order=1,packed_vq=1,mrg_rxbuf=0,vectorized=1",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        # stability test with basic packets number check
        self.scapy_num = 0
        date_old = datetime.datetime.now()
        date_new = date_old + datetime.timedelta(minutes=2)
        while (1):
            date_now = datetime.datetime.now()
            scope = 'broadcast'
            self.dmac = 'ff:ff:ff:ff:ff:ff'
            self.scapy_send_packet(64, self.dmac, 1)
            if date_now >= date_new:
                break
        self.send_verify(scope, self.scapy_num)
        self.close_all_testpmd()

    def test_vhost_xstats_virtio11_vector_ringsize_not_powerof_2(self):
        """
        performance for Vhost PVP virtio1.1 inorder no_mergeable Path.
        """
        virtio_pmd_arg = {"version": "in_order=1,packed_vq=1,mrg_rxbuf=0,vectorized=1,queue_size=1221",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --rxd=1221 --txd=1221"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        # stability test with basic packets number check
        self.scapy_num = 0
        date_old = datetime.datetime.now()
        date_new = date_old + datetime.timedelta(minutes=2)
        while (1):
            date_now = datetime.datetime.now()
            scope = 'broadcast'
            self.dmac = 'ff:ff:ff:ff:ff:ff'
            self.scapy_send_packet(64, self.dmac, 1)
            if date_now >= date_new:
                break
        self.send_verify(scope, self.scapy_num)
        self.close_all_testpmd()

    def test_vhost_xstats_inorder_mergeable(self):
        """
        performance for Vhost PVP In_order mergeable Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=1,mrg_rxbuf=1",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_inorder_no_mergeable(self):
        """
        performance for Vhost PVP In_order no_mergeable Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=1,mrg_rxbuf=0",
                        "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_mergeable(self):
        """
        performance for Vhost PVP Mergeable Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=1",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_no_mergeable(self):
        """
        performance for Vhost PVP no_mergeable Path.
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=0,vectorized=1",
                            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_vector_rx(self):
        """
        performance for Vhost PVP Vector_RX Path
        """
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=0,vectorized=1",
                            "path": "--tx-offloads=0x0"}
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def close_all_testpmd(self):
        """
        close all testpmd of vhost and virtio
        """
        self.vhost_user.send_expect("quit", "#", 60)
        self.virtio_user.send_expect("quit", "#", 60)

    def clear_port_xstats(self, scope):

        self.vhost_user.send_expect("clear port xstats 1", "testpmd>", 60)
        out = self.vhost_user.send_expect(
            "show port xstats 1", "testpmd>", 60)
        packet = re.search("rx_%s_packets:\s*(\d*)" % scope, out)
        sum_packet = packet.group(1)
        self.verify(int(sum_packet) == 0, "Insufficient the received package")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT testpmd", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass