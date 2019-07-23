# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation. All rights reserved.
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

Test VXLAN-GPE behaviour in DPDK.

"""

import utils
import os
import re
from pmd_output import PmdOutput
from scapy.utils import wrpcap, rdpcap
from scapy.layers.inet import Ether, IP, UDP
from scapy.layers.l2 import Dot1Q
from vxlan import VXLAN
from scapy.config import conf
from test_case import TestCase
from settings import FOLDERS

#
#
# Test class.
#

VXLAN_GPE_PORT = 4790


class VxlanGpeTestConfig(object):

    """
    Module for config/create/transmit vxlan packet
    """

    def __init__(self, test_case, **kwargs):
        self.test_case = test_case
        self.init()
        for name in kwargs:
            setattr(self, name, kwargs[name])

    def init(self):
        self.packets_config()

    def packets_config(self):
        """
        Default vxlan packet format
        """
        self.pcap_file = '/root/vxlan_gpe.pcap'
        self.outer_mac_dst = '11:22:33:44:55:66'
        self.outer_ip_dst = '192.168.1.2'
        self.outer_udp_dst = VXLAN_GPE_PORT
        self.vni = 1
        self.inner_mac_dst = '00:00:20:00:00:01'
        self.inner_vlan = 'N/A'
        self.inner_ip_dst = '192.168.2.2'
        self.payload_size = 18

    def create_pcap(self):
        """
        Create pcap file and copy it to tester
        """
        self.inner_payload = ("X" * self.payload_size)

        if self.inner_vlan != 'N/A':
            inner = Ether() / Dot1Q() / IP() / UDP() / self.inner_payload
            inner[Dot1Q].vlan = self.inner_vlan
        else:
            inner = Ether() / IP() / UDP() / self.inner_payload

        inner[IP().name].dst = self.inner_ip_dst

        inner[Ether].dst = self.inner_mac_dst

        outer = Ether() / IP() / UDP()

        outer[Ether].dst = self.outer_mac_dst

        outer[IP().name].dst = self.outer_ip_dst

        outer[UDP].dport = self.outer_udp_dst

        if self.outer_udp_dst == VXLAN_GPE_PORT:
            self.pkt = outer / VXLAN(vni=self.vni) / inner
        else:
            self.pkt = outer / ("X" * self.payload_size)

        wrpcap(self.pcap_file, self.pkt)

    def send_pcap(self, iface=""):
        """
        Send vxlan pcap file by iface
        """
        # load vxlan module to scapy
        cwd = os.getcwd()
        dir_vxlan_module = cwd + r'/' + FOLDERS['Depends']
        self.test_case.tester.scapy_append("sys.path.append('%s')" % dir_vxlan_module)
        self.test_case.tester.scapy_append("from vxlan import VXLAN")
        self.test_case.tester.scapy_append(
            'pcap = rdpcap("%s")' % self.pcap_file)
        self.test_case.tester.scapy_append(
            'sendp(pcap, iface="%s")' % iface)
        self.test_case.tester.scapy_execute()


class TestVxlanGpeSupportInI40e(TestCase):

    def set_up_all(self):
        """
        vxlan Prerequisites
        """
        # this feature only enable in FVL now
        if self.nic not in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortville_25g"]:
            self.verify(False, "%s not support this vxlan-gpe" % self.nic)
        # Based on h/w type, choose how many ports to use
        ports = self.dut.get_ports()

        # Verify that enough ports are available
        self.verify(len(ports) >= 2, "Insufficient ports for testing")
        global valports
        valports = [_ for _ in ports if self.tester.get_local_port(_) != -1]

        self.portMask = utils.create_mask(valports[:2])

        # Verify that enough threads are available
        netdev = self.dut.ports_info[ports[0]]['port']
        self.ports_socket = netdev.socket
        cores = self.dut.get_core_list("all", socket=self.ports_socket)
        self.verify(cores is not None, "Insufficient cores for speed testing")
        self.coremask = utils.create_mask(cores)

        # start testpmd
        self.pmdout = PmdOutput(self.dut)

        # init port config
        self.dut_port = valports[0]
        self.dut_port_mac = self.dut.get_mac_address(self.dut_port)
        tester_port = self.tester.get_local_port(self.dut_port)
        self.tester_iface = self.tester.get_interface(tester_port)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def filter_and_check(self, filter_type="imac-ivlan", queue_id=3,
                         vlan=False, remove=False):
        """
        send vxlan packet and check whether receive packet in assigned queue
        """
        if vlan is not False:
            config = VxlanGpeTestConfig(self, inner_vlan=vlan)
            vlan_id = vlan
        else:
            config = VxlanGpeTestConfig(self)
            vlan_id = 1

        # now cloud filter will default enable L2 mac filter, so dst mac must
        # be same
        config.outer_mac_dst = self.dut_port_mac

        args = [self.dut_port, config.outer_mac_dst, config.inner_mac_dst,
                config.inner_ip_dst, vlan_id, filter_type, config.vni,
                queue_id]

        self.tunnel_filter_add(*args)

        # invalid case request to remove tunnel filter
        if remove is True:
            queue_id = 0
            args = [self.dut_port, config.outer_mac_dst, config.inner_mac_dst,
                    config.inner_ip_dst, vlan_id, filter_type, config.vni,
                    queue_id]
            self.tunnel_filter_del(*args)

        # send vxlan packet
        config.create_pcap()
        self.dut.send_expect("start", "testpmd>", 10)
        config.send_pcap(self.tester_iface)
        out = self.dut.get_session_output(timeout=2)

        queue = -1
        pattern = re.compile("- Receive queue=0x(\d)")
        m = pattern.search(out)
        if m is not None:
            queue = m.group(1)

        # verify received in expected queue
        self.verify(queue_id == int(queue), "invalid receive queue")

        self.dut.send_expect("stop", "testpmd>", 10)

    def test_vxlan_gpe_ipv4_detect(self):
        self.pmdout.start_testpmd('all')
        self.pmdout.execute_cmd('set fwd io')
        self.pmdout.execute_cmd('set verbose 1')
        # add VXLAN-GPE packet type
        self.pmdout.execute_cmd('port config 0 udp_tunnel_port add vxlan-gpe %s' % VXLAN_GPE_PORT)
        self.pmdout.execute_cmd('start')
        mac = self.pmdout.get_port_mac(0)
        # send one VXLAN-GPE type packet
        packet = 'sendp([Ether(dst="%s")/IP(src="18.0.0.1")/UDP(dport=%d, sport=43)/' % (mac, VXLAN_GPE_PORT) + \
                 'VXLAN(flags=12)/IP(src="10.0.0.1")], iface="%s", count=1)' % self.tester_iface
        cwd = os.getcwd()
        dir_vxlan_module = cwd + r'/' + FOLDERS['Depends']
        self.tester.scapy_append("sys.path.append('%s')" % dir_vxlan_module)
        self.tester.scapy_append("from vxlan import VXLAN")
        self.tester.scapy_append(packet)
        self.tester.scapy_execute()
        out = self.dut.get_session_output(timeout=5)
        print out
        self.verify('L3_IPV4_EXT_UNKNOWN' in out and '%s' % VXLAN_GPE_PORT in out, 'no detect vxlan-gpe packet')

        # delete the VXLAN-GPE packet type, testpmd should treat the packet as a normal UDP packet
        self.pmdout.execute_cmd('port config 0 udp_tunnel_port rm vxlan-gpe %s' % VXLAN_GPE_PORT)
        self.tester.scapy_append("sys.path.append('%s')" % dir_vxlan_module)
        self.tester.scapy_append("from vxlan import VXLAN")
        self.tester.scapy_append(packet)
        self.tester.scapy_execute()
        out = self.dut.get_session_output(timeout=5)
        print out
        self.pmdout.execute_cmd('quit', '#')
        self.verify('L3_IPV4_EXT_UNKNOWN' in out and '%s' % VXLAN_GPE_PORT not in out, 'no detect vxlan-gpe packet')

    def test_tunnel_filter_vxlan_gpe(self):
        """
        verify tunnel filter feature
        """
        pmd_temp = "./%(TARGET)s/app/testpmd -c %(COREMASK)s -n " + \
            "%(CHANNEL)d -- -i --disable-rss --rxq=4 --txq=4" + \
            " --nb-cores=4 --portmask=%(PORT)s"
        pmd_cmd = pmd_temp % {'TARGET': self.target,
                              'COREMASK': self.coremask,
                              'CHANNEL': self.dut.get_memory_channels(),
                              'PORT': self.portMask}
        self.dut.send_expect(pmd_cmd, "testpmd>", 30)

        self.dut.send_expect("set fwd rxonly", "testpmd>", 10)
        self.dut.send_expect("set verbose 1", "testpmd>", 10)
        self.enable_vxlan(self.dut_port)

        # check inner mac + inner vlan filter can work
        self.filter_and_check(filter_type="imac-ivlan", vlan=1)
        # check inner mac + inner vlan + tunnel id filter can work
        self.filter_and_check(filter_type="imac-ivlan-tenid", vlan=1)
        # check inner mac + tunnel id filter can work
        self.filter_and_check(filter_type="imac-tenid")
        # check inner mac filter can work
        self.filter_and_check(filter_type="imac")
        # check outer mac + inner mac + tunnel id filter can work
        self.filter_and_check(filter_type="omac-imac-tenid")
        # iip not supported by now
        self.filter_and_check(filter_type="iip")

        self.dut.send_expect("quit", "#", 10)

    def enable_vxlan(self, port):
        self.dut.send_expect("rx_vxlan_port add %d %d"
                             % (VXLAN_GPE_PORT, port),
                             "testpmd>", 10)

    def tunnel_filter_add(self, *args):
        # tunnel_filter add port_id outer_mac inner_mac ip inner_vlan
        # tunnel_type(vxlan)
        # filter_type
        # (imac-ivlan|imac-ivlan-tenid|imac-tenid|imac|omac-imac-tenid|iip)
        # tenant_id queue_num
        out = self.dut.send_expect("tunnel_filter add %d " % args[0] +
                                   "%s %s %s " % (args[1], args[2], args[3]) +
                                   "%d vxlan-gpe %s " % (args[4], args[5]) +
                                   "%d %d" % (args[6], args[7]),
                                   "testpmd>", 10)
        self.verify("Bad arguments" not in out, "Failed to add tunnel filter")
        self.verify("error" not in out, "Failed to add tunnel filter")

    def tunnel_filter_del(self, *args):
        out = self.dut.send_expect("tunnel_filter rm %d " % args[0] +
                                   "%s %s %s " % (args[1], args[2], args[3]) +
                                   "%d vxlan-gpe %s " % (args[4], args[5]) +
                                   "%d %d" % (args[6], args[7]),
                                   "testpmd>", 10)
        self.verify("Bad arguments" not in out,
                    "Failed to remove tunnel filter")
        self.verify("error" not in out, "Failed to remove tunnel filter")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
