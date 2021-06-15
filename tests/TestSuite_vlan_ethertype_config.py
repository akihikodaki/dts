# BSD LICENSE
#
# Copyright(c) 2010-2015 Intel Corporation. All rights reserved.
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

Test the support of VLAN Offload Features by Poll Mode Drivers.

"""

import dts
import time
import utils

from test_case import TestCase
from pmd_output import PmdOutput
from scapy.utils import struct, socket, wrpcap, rdpcap
from scapy.layers.inet import Ether, IP, TCP, UDP, ICMP
from scapy.layers.l2 import Dot1Q, ARP, GRE
from settings import DPDK_RXMODE_SETTING
from settings import load_global_setting

import random
MAX_VLAN = 4095


class TestVlanEthertypeConfig(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.


        Vlan Prerequisites
        """
        global dutRxPortId
        global dutTxPortId

        # Based on h/w type, choose how many ports to use
        ports = self.dut.get_ports()

        # Verify that enough ports are available
        self.verify(len(ports) >= 2, "Insufficient ports")

        valports = [_ for _ in ports if self.tester.get_local_port(_) != -1]
        dutRxPortId = valports[0]
        dutTxPortId = valports[1]
        port = self.tester.get_local_port(dutTxPortId)
        self.rxItf = self.tester.get_interface(port)

        self.portmask = utils.create_mask(valports[:2])

    def set_up(self):
        """
        Run before each test case.
        """
        self.pmdout = PmdOutput(self.dut)
        self.pmdout.start_testpmd("Default", "--portmask=%s" % self.portmask)
        if self.kdriver == "i40e":
            self.dut.send_expect("set promisc all off", "testpmd> ")

    def start_tcpdump(self, rxItf):

        self.tester.alt_session.send_expect(
            "rm -rf /tmp/getPkgByTcpdump_%s.cap" % rxItf, "#")
        self.tester.alt_session.send_expect(
            "tcpdump -i %s -w /tmp/getPkgByTcpdump_%s.cap" % (rxItf, rxItf), "listening on")

    def get_tcpdump_packet(self, rxItf):
        recv_pattern = self.tester.alt_session.send_expect("^C", "#")
        fmt = '1/1 "%02x"'
        out = self.tester.send_expect(
            "hexdump -ve '%s' '/tmp/getPkgByTcpdump_%s.cap'" % (fmt, rxItf), "# ")
        return out

    def vlan_send_packet(self, outer_vid, outer_tpid=0x8100, inner_vid=-1, inner_tpid=-1):
        """
        if vid is -1, it means send pakcage not include vlan id.
        """

        self.tpid_ori_file = "/tmp/tpid_ori.pcap"
        self.tpid_new_file = "/tmp/tpid_new.pcap"
        self.tester.send_expect("rm -rf /tmp/tpid_ori.pcap", "# ")
        self.tester.send_expect("rm -rf /tmp/tpid_new.pcap", "# ")
        # The package stream : testTxPort->dutRxPort->dutTxport->testRxPort
        port = self.tester.get_local_port(dutRxPortId)
        self.txItf = self.tester.get_interface(port)
        self.smac = self.tester.get_mac(port)

        port = self.tester.get_local_port(dutTxPortId)
        self.rxItf = self.tester.get_interface(port)

        # the package dect mac must is dut tx port id when the port promisc is
        # off
        self.dmac = self.dut.get_mac_address(dutRxPortId)

        pkt = []
        if outer_vid < 0 or outer_tpid <= 0:
            pkt = [
                Ether(dst="%s" % self.dmac, src="%s" % self.smac) / IP(len=46)]
            wrpcap(self.tpid_new_file, pkt)
        else:
            pkt = [Ether(dst="%s" % self.dmac, src="%s" %
                         self.smac) / Dot1Q(vlan=1) / Dot1Q(vlan=2) / IP(len=46)]
            wrpcap(self.tpid_ori_file, pkt)
            fmt = '1/1 "%02x"'
            out = self.tester.send_expect(
                "hexdump -ve '%s' '%s'" % (fmt, self.tpid_ori_file), "# ")
            if(inner_vid < 0 or inner_tpid <= 0):
                replace = str("%04x" % outer_tpid) + str("%04x" % outer_vid)
            else:
                replace = str("%04x" % outer_tpid) + str("%04x" % outer_vid) + str(
                    "%04x" % inner_tpid) + str("%04x" % inner_vid)
            fmt = '1/1 "%02x"'
            out = self.tester.send_expect("hexdump -ve '%s' '%s' |sed 's/8100000181000002/%s/' |xxd -r -p > '%s'" % (
                fmt, self.tpid_ori_file, replace, self.tpid_new_file), "# ")

        self.tester.scapy_foreground()
        self.tester.scapy_append("pkt=rdpcap('%s')" % self.tpid_new_file)
        self.tester.scapy_append("sendp(pkt, iface='%s', count=4)" % self.txItf)
        self.tester.scapy_execute()

    def check_vlan_packets(self, vlan, tpid, rxItf, result=True):

        self.start_tcpdump(rxItf)
        self.vlan_send_packet(vlan, tpid)
        out = self.get_tcpdump_packet(self.rxItf)
        tpid_vlan = str("%04x" % tpid) + str("%04x" % vlan)
        print(("tpid_vlan: %s" % tpid_vlan))
        if(result):
            self.verify(tpid_vlan in out, "Wrong vlan:" + str(out))
        else:
            self.verify(tpid_vlan not in out, "Wrong vlan:" + str(out))

    def test_vlan_change_tpid(self):
        """
        Test Case 1: change VLAN TPID
        """
        random_vlan = random.randint(1, MAX_VLAN - 1)
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect(
            "vlan set filter off %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect(
            "vlan set strip on %s" % dutRxPortId, "testpmd> ", 20)
        rx_vlans = [1, random_vlan, MAX_VLAN]
        tpids = [0x8100, 0xA100]
        for tpid in tpids:
            self.dut.send_expect("vlan set outer tpid 0x%x %s" %
                                 (tpid, dutRxPortId), "testpmd> ")
            for rx_vlan in rx_vlans:
                self.vlan_send_packet(rx_vlan, tpid)
                out = self.dut.get_session_output()
                self.verify(
                    "PKT_RX_VLAN" in out, "Vlan recognized error:" + str(out))

    def test_vlan_filter_on_off(self):
        """
        Disable receipt of VLAN packets
        """
        random_vlan = random.randint(1, MAX_VLAN - 1)
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("vlan set strip off %s" %
                             dutRxPortId, "testpmd> ", 20)
        rx_vlans = [1, random_vlan, MAX_VLAN]
        # caium_a063 card support only default '0x8100' tpid in rx mode
        if (self.nic in ["cavium_a063", "cavium_a064"]):
            tpids = [0x8100]
        else:
            tpids = [0x8100, 0xA100]
        for tpid in tpids:
            self.dut.send_expect("vlan set outer tpid 0x%x %s" %
                                 (tpid, dutRxPortId), "testpmd> ")
            for rx_vlan in rx_vlans:
                # test vlan filter on
                self.dut.send_expect(
                    "vlan set filter on  %s" % dutRxPortId, "testpmd> ")
                self.dut.send_expect("start", "testpmd> ")
                self.check_vlan_packets(rx_vlan, tpid, self.rxItf, False)
                # test vlan filter off
                self.dut.send_expect(
                    "vlan set filter off  %s" % dutRxPortId, "testpmd> ")
                self.check_vlan_packets(rx_vlan, tpid, self.rxItf)

    def test_vlan_add_vlan_tag(self):
        """
        test adding VLAN Tag Identifier with changing VLAN TPID
        """
        random_vlan = random.randint(1, MAX_VLAN - 1)
        rx_vlans = [1, random_vlan, MAX_VLAN]
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect(
            "vlan set filter on  %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("vlan set strip off %s" %
                             dutRxPortId, "testpmd> ", 20)
        self.dut.send_expect("start", "testpmd> ")

        # caium_a063 card support only default '0x8100' tpid in rx mode
        if (self.nic in ["cavium_a063", "cavium_a064"]):
            tpids = [0x8100]
        else:
            tpids = [0x8100, 0xA100]
        for tpid in tpids:
            self.dut.send_expect("vlan set outer tpid 0x%x %s" %
                                 (tpid, dutRxPortId), "testpmd> ")
            for rx_vlan in rx_vlans:
                self.dut.send_expect(
                    "rx_vlan add 0x%x %s" % (rx_vlan, dutRxPortId), "testpmd> ")
                self.check_vlan_packets(rx_vlan, tpid, self.rxItf)

                self.dut.send_expect("rx_vlan rm 0x%x %d" %
                                     (rx_vlan, dutRxPortId), "testpmd> ", 30)
                self.check_vlan_packets(rx_vlan, tpid, self.rxItf, False)

        self.dut.send_expect("stop", "testpmd> ", 30)

    def test_vlan_strip(self):
        """
        Test Case 4: test VLAN header striping with changing VLAN TPID
        """
        random_vlan = random.randint(1, MAX_VLAN - 1)
        rx_vlans = [1, random_vlan, MAX_VLAN]
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect(
            "vlan set filter off %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect(
            "vlan set strip on %s" % dutRxPortId, "testpmd> ", 20)
        self.dut.send_expect("start", "testpmd> ", 20)

        # caium_a063 card support only default '0x8100' tpid in rx mode
        if (self.nic in ["cavium_a063", "cavium_a064"]):
            tpids = [0x8100]
        else:
            tpids = [0x8100, 0xA100]
        for tpid in tpids:
            self.dut.send_expect("vlan set outer tpid 0x%x %s" %
                                 (tpid, dutRxPortId), "testpmd> ")
            for rx_vlan in rx_vlans:
                self.dut.send_expect(
                    "vlan set strip on %s" % dutRxPortId, "testpmd> ", 20)
                self.check_vlan_packets(rx_vlan, tpid, self.rxItf, False)
                self.dut.send_expect(
                    "vlan set strip off %s" % dutRxPortId, "testpmd> ", 20)
                self.check_vlan_packets(rx_vlan, tpid, self.rxItf)

    def test_vlan_enable_vlan_insertion(self):
        """
        Test Case 5: test VLAN header inserting with changing VLAN TPID
        """
        random_vlan = random.randint(1, MAX_VLAN - 1)
        tx_vlans = [2, random_vlan, MAX_VLAN]
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect(
            "vlan set filter off %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("vlan set strip off %s" %
                             dutRxPortId, "testpmd> ", 20)
        self.dut.send_expect("start", "testpmd> ")

        # caium_a063 card support only default '0x8100' tpid in rx mode
        if (self.nic in ["cavium_a063", "cavium_a064", "foxville"]):
            tpids = [0x8100]
        else:
            tpids = [0x8100, 0xA100]
        for tpid in tpids:
            self.dut.send_expect("vlan set outer tpid 0x%x %s" %
                                 (tpid, dutTxPortId), "testpmd> ")
            for tx_vlan in tx_vlans:
                self.dut.send_expect("stop", "testpmd>")
                self.dut.send_expect("port stop all", "testpmd> ")
                self.dut.send_expect(
                    "tx_vlan set %s 0x%x" % (dutTxPortId, tx_vlan), "testpmd> ")
                self.dut.send_expect("port start all", "testpmd> ")
                self.dut.send_expect("start", "testpmd>")
                self.start_tcpdump(self.rxItf)
                self.vlan_send_packet(-1)
                out = self.get_tcpdump_packet(self.rxItf)
                vlan_string = str("%04x" % tpid) + str("%04x" % tx_vlan)
                self.verify(vlan_string in out, "Wrong vlan:" + str(out))
                self.verify(str("%x" % tpid) in out, "Wrong vlan:" + str(out))
                self.verify(
                    str("%x" % tx_vlan) in out, "Vlan not found:" + str(out))
                self.dut.send_expect("stop", "testpmd>")
                self.dut.send_expect("port stop all", "testpmd> ")
                self.dut.send_expect(
                    "tx_vlan reset %s" % dutTxPortId, "testpmd> ", 30)
                self.dut.send_expect("port start all", "testpmd> ")
                self.dut.send_expect("start", "testpmd>")
                self.start_tcpdump(self.rxItf)
                self.vlan_send_packet(-1)
                out = self.get_tcpdump_packet(self.rxItf)
                vlan_string = str("%04x" % tpid) + str("%04x" % tx_vlan)
                self.verify(vlan_string not in out, "Wrong vlan:" + str(out))

    def test_vlan_qinq_tpid(self):
        """
        Test Case 6: Change S-Tag and C-Tag within QinQ
        It need be tested in nonvector mode.
        """
        self.verify(
            self.nic in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "carlsville"], "%s NIC not support QinQ " % self.nic)
        rx_mode = load_global_setting(DPDK_RXMODE_SETTING)
        self.verify(rx_mode == 'novector',
                    "The case must by tested in novector mode")

        random_vlan = random.randint(1, MAX_VLAN - 1)
        rx_vlans = [1, random_vlan, MAX_VLAN]
        self.dut.send_expect(
            "vlan set extend on %d" % dutRxPortId, "testpmd> ", 20)
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect(
            "vlan set filter off  %s" % dutRxPortId, "testpmd> ")
        tpids = [0x8100, 0xA100, 0x88A8, 0x9100]
        for outer_tpid in tpids:
            for inner_tpid in tpids:
                self.dut.send_expect("vlan set outer tpid 0x%x %s" %
                                     (outer_tpid, dutRxPortId), "testpmd> ")
                self.dut.send_expect("vlan set inner tpid 0x%x %s" %
                                     (inner_tpid, dutRxPortId), "testpmd> ")
            for outer_vlan in rx_vlans:
                for inner_vlan in rx_vlans:
                    self.vlan_send_packet(
                        outer_vlan, outer_tpid, inner_vlan, inner_tpid)
                    out = self.dut.get_session_output()
                    self.verify("QinQ VLAN" in out, "Wrong QinQ:" + str(out))

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("stop", "testpmd> ", 30)
        self.dut.send_expect("quit", "# ", 30)
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
