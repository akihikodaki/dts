# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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

import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.settings import DRIVERS, HEADER_SIZE
from framework.test_case import TestCase


class TestGeneric_filter(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.


        Generic filter Prerequisites
        """

        # Based on h/w type, choose how many ports to use
        ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(ports) >= 2, "Insufficient ports")

        self.cores = "1S/5C/1T"

        # Based on h/w type, choose how many ports to use
        global valports
        valports = [_ for _ in ports if self.tester.get_local_port(_) != -1]
        global portMask
        portMask = utils.create_mask(valports[:2])
        self.pmdout = PmdOutput(self.dut)
        self.ethertype_filter = "off"

    def request_mbufs(self, queue_num):
        """
        default txq/rxq descriptor is 64
        """
        return 1024 * queue_num + 512

    def port_config(self):
        """
         set port queue mapping, fortville not support this function
        """
        if self.nic not in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortville_25g", "fortpark_TLV","fortpark_BASE-T", "carlsville", "columbiaville_25g", "columbiaville_100g"]:
            self.dut.send_expect(
                "set stat_qmap rx %s 0 0" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "set stat_qmap rx %s 0 0" % valports[1], "testpmd> ")
            self.dut.send_expect(
                "set stat_qmap rx %s 1 1" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "set stat_qmap rx %s 1 1" % valports[1], "testpmd> ")
            self.dut.send_expect(
                "set stat_qmap rx %s 2 2" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "set stat_qmap rx %s 2 2" % valports[1], "testpmd> ")
            self.dut.send_expect(
                "set stat_qmap rx %s 3 3" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "set stat_qmap rx %s 3 3" % valports[1], "testpmd> ")
            self.dut.send_expect(
                "vlan set strip off %s" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "vlan set strip off %s" % valports[1], "testpmd> ")
            #reson dpdk-5315
            self.dut.send_expect(
                "vlan set filter on %s" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "vlan set filter off %s" % valports[0], "testpmd> ")
            #reson dpdk-5315
            self.dut.send_expect(
                "vlan set filter on %s" % valports[1], "testpmd> ")
            self.dut.send_expect(
                "vlan set filter off %s" % valports[1], "testpmd> ")

        self.dut.send_expect("set flush_rx on", "testpmd> ")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def filter_send_packet(self, type):
        """
        Send  packet to portid
        """

        port = self.tester.get_local_port(valports[0])
        txItf = self.tester.get_interface(port)

        port = self.tester.get_local_port(valports[1])
        rxItf = self.tester.get_interface(port)

        mac = self.dut.get_mac_address(valports[0])
        self.tester.scapy_foreground()

        if (type == "syn"):
            self.tester.scapy_append(
                'sendp([Ether(dst="%s")/IP(src="2.2.2.5",dst="2.2.2.4")/TCP(dport=80,flags="S")], iface="%s")' % (mac, txItf))
        elif (type == "arp"):
            self.tester.scapy_append(
                'sendp([Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.1")], iface="%s")' % (txItf))
        elif (type == "arp_prio"):
            self.tester.scapy_append(
                'sendp([Ether(dst="ff:ff:ff:ff:ff:ff")/Dot1Q(prio=3)/ARP(pdst="192.168.1.1")], iface="%s")' % (txItf))
        elif (type == "fivetuple"):
            if self.nic == "niantic":
                self.tester.scapy_append(
                    'sendp([Ether(dst="%s")/Dot1Q(prio=3)/IP(src="2.2.2.4",dst="2.2.2.5")/TCP(sport=1,dport=1,flags=0)], iface="%s")' % (mac, txItf))
            else:
                self.tester.scapy_append(
                    'sendp([Ether(dst="%s")/Dot1Q(prio=3)/IP(src="2.2.2.4",dst="2.2.2.5")/TCP(sport=1,dport=1)], iface="%s")' % (mac, txItf))
        elif (type == "udp"):
            self.tester.scapy_append(
                'sendp([Ether(dst="%s")/IP(src="2.2.2.4",dst="2.2.2.5")/UDP(dport=64)], iface="%s")' % (mac, txItf))
        elif (type == "ip"):
            self.tester.scapy_append(
                'sendp([Ether(dst="%s")/IP(src="2.2.2.4",dst="2.2.2.5")/TCP(sport=80,dport=80,flags=0)], iface="%s")' % (mac, txItf))
        elif (type == "jumbo"):
            self.tester.scapy_append(
                'sendp([Ether(dst="%s")/IP(src="2.2.2.5",dst="2.2.2.4")/TCP(dport=80,flags="S")/Raw(load="\x50"*1500)], iface="%s")' % (mac, txItf))
        elif (type == "packet"):
            if (filters_index == 0):
                self.tester.scapy_append(
                    'sendp([Ether(dst="%s")/IP(src="2.2.2.4",dst="2.2.2.5")/TCP(sport=1,dport=1,flags=0)], iface="%s")' % (mac, txItf))
            if (filters_index == 1):
                self.tester.scapy_append(
                    'sendp([Ether(dst="%s")/Dot1Q(prio=3)/IP(src="2.2.2.4",dst="2.2.2.5")/TCP(sport=1,dport=2,flags=0)], iface="%s")' % (mac, txItf))
        self.tester.scapy_execute()

    def verify_result(self, outstring, tx_pkts, expect_queue):

        result_scanner = r"Forward Stats for RX Port= %s/Queue= ([0-9]+)" % valports[
            0]

        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(outstring)
        queue_id = m.group(1)
        if self.nic == "niantic" and self.ethertype_filter == "on" and expect_queue == "0":
            self.ethertype_filter = "off"
            self.verify(queue_id == "0", "packet pass  error")
        if expect_queue != queue_id:
            scanner = re.compile(result_scanner, re.DOTALL)
            m = scanner.search(outstring)
            queue_id = m.group(1)
            result_scanner = r"RX-packets: ([0-9]+) \s*"
            scanner = re.compile(result_scanner, re.DOTALL)
            m = scanner.search(outstring)
            p0tx_pkts = m.group(1)
            
        else:

            result_scanner = r"RX-packets: ([0-9]+) \s*"

            scanner = re.compile(result_scanner, re.DOTALL)
            m = scanner.search(outstring)
            p0tx_pkts = m.group(1)

        self.verify(p0tx_pkts == tx_pkts, "packet pass  error")

    # TODO: failing test even in non-converted version
    def test_syn_filter(self):
        """
        Enable receipt of SYN packets
        """
        self.verify(self.nic in ["niantic", "kawela_4", "bartonhills", "powerville", "sagepond", "foxville", "sageville", "fortville_eagle", "fortville_25g", "fortville_spirit", "columbiaville_25g", "columbiaville_100g"], "%s nic not support syn filter" % self.nic)
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--disable-rss --rxq=4 --txq=4 --portmask=%s --nb-cores=4 --nb-ports=1" % portMask)
        self.port_config()
        self.dut.send_expect(
            "syn_filter %s add priority high queue 2" % valports[0], "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)

        self.filter_send_packet("syn")
        time.sleep(2)

        out = self.dut.send_expect("stop", "testpmd> ")

        self.verify_result(out, tx_pkts="1", expect_queue="2")

        self.dut.send_expect("clear port stats all", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        self.filter_send_packet("arp")
        time.sleep(2)
        out = self.dut.send_expect("stop", "testpmd> ")

        self.verify_result(out, tx_pkts="1", expect_queue="0")

        self.dut.send_expect(
            "syn_filter %s del priority high queue 2" % valports[0], "testpmd> ")
        self.dut.send_expect("clear port stats all", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)
        self.filter_send_packet("syn")
        time.sleep(2)
        out = self.dut.send_expect("stop", "testpmd> ")

        self.verify_result(out, tx_pkts="1", expect_queue="0")
        self.dut.send_expect("quit", "#", timeout=30)

    def test_priority_filter(self):
        """
        priority filter
        """
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--disable-rss --rxq=4 --txq=4 --portmask=%s --nb-cores=4 --nb-ports=1" % portMask)
        self.port_config()

        if self.nic in ["niantic", "sagepond", "sageville"]:
            cmd = "5tuple_filter %s add dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask 0x1f tcp_flags 0x0 priority 3 queue 3 " % (
                valports[0])
            self.dut.send_expect("%s" % cmd, "testpmd> ")
            cmd = "5tuple_filter %s add dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 2 src_port 1 protocol 0x06 mask 0x18 tcp_flags 0x0 priority 2 queue 2 " % (
                valports[0])
            self.dut.send_expect("%s" % cmd, "testpmd> ")
            self.dut.send_expect("start", "testpmd> ", 120)
            self.filter_send_packet("fivetuple")
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="3")
            cmd = "5tuple_filter %s del dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask 0x1f tcp_flags 0x0 priority 3 queue 3 " % (
                valports[0])
            self.dut.send_expect(cmd, "testpmd> ")

            self.dut.send_expect("clear port stats all", "testpmd> ")
            self.dut.send_expect("start", "testpmd> ", 120)
            self.filter_send_packet("fivetuple")
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="2")
        elif self.nic in ["kawela_4", "fortville_eagle", "fortville_25g", "fortville_spirit", "columbiaville_25g", "columbiaville_100g"]:
            cmd = "5tuple_filter %s add dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask 0x1f tcp_flags 0x02 priority 3 queue 3" % (
                valports[0])
            self.dut.send_expect("%s" % (cmd), "testpmd> ")
            self.dut.send_expect(
                "syn_filter %s add priority high queue 2" % valports[0], "testpmd> ")

            self.dut.send_expect("start", "testpmd> ", 120)
            self.filter_send_packet("fivetuple")
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="2")
            self.dut.send_expect(
                "syn_filter %s del priority high queue 2" % valports[0], "testpmd> ")

            self.dut.send_expect("start", "testpmd> ", 120)
            self.filter_send_packet("fivetuple")
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="3")
        elif self.nic in ["bartonhills", "powerville", "foxville"]:
            self.dut.send_expect(
                "flex_filter %s add len 16 bytes 0x0123456789abcdef0000000008000000 mask 000C priority 2 queue 1" % (valports[0]), "testpmd> ")
            self.dut.send_expect(
                "2tuple_filter %s add dst_port 64 protocol 0x11 mask 1 tcp_flags 0 priority 3 queue 2" % valports[0], "testpmd> ")
            self.dut.send_expect("start", "testpmd> ", 120)
            self.filter_send_packet("udp")
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="1")
            self.dut.send_expect(
                "flex_filter %s del len 16 bytes 0x0123456789abcdef0000000008000000 mask 000C priority 2 queue 1" % valports[0], "testpmd> ")
            self.dut.send_expect("start", "testpmd> ", 120)
            self.filter_send_packet("udp")
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="2")
        else:
            self.verify(False, "%s nic not support this test" % self.nic)

    def test_five_tuple_filter(self):
        """
        five tuple filter
        """
        if self.nic in ["niantic", "kawela_4", "sagepond", "foxville", "sageville", "fortville_eagle", "fortville_25g", "fortville_spirit", "columbiaville_25g", "columbiaville_100g"]:
            self.pmdout.start_testpmd(
                "%s" % self.cores, "--disable-rss --rxq=4 --txq=4 --portmask=%s --nb-cores=4 --nb-ports=1" % portMask)
            self.port_config()

            mask = ['0x1f', '0x0']
            for case in mask:
                if case == "0x1f":
                    if self.nic in ["niantic", "sagepond", "sageville"]:
                        cmd = "5tuple_filter %s add dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask %s tcp_flags 0x0 priority 3 queue 3" % (
                            valports[0], case)
                    if self.nic in ["kawela_4", "fortville_eagle", "fortville_25g", "fortville_spirit", "columbiaville_25g", "columbiaville_100g"]:
                        cmd = "5tuple_filter %s add dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask %s tcp_flags 0x02 priority 3 queue 3" % (
                            valports[0], case)
                else:
                    if self.nic in ["niantic", "sagepond", "sageville"]:
                        cmd = "5tuple_filter %s add dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask %s tcp_flags 0x0 priority 3 queue 3" % (
                            valports[0], case)
                    if self.nic in ["kawela_4", "fortville_eagle", "fortville_25g", "fortville_spirit", "columbiaville_25g", "columbiaville_100g"]:
                        cmd = "5tuple_filter %s add dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask %s tcp_flags 0x02 priority 3 queue 3" % (
                            valports[0], case)

                self.dut.send_expect("%s" % (cmd), "testpmd> ")
                # if case == "0x1f":
                #    out = self.dut.send_expect("get_5tuple_filter %s index 1" % valports[0], "testpmd> ")
                #    self.verify('Destination IP:  0x02020205    mask: 1' in out, "set 5-tuple filter error")
                #    self.verify('Source IP:       0x02020204    mask: 1' in out, "set 5-tuple filter error")
                self.dut.send_expect("start", "testpmd> ", 120)

                self.filter_send_packet("fivetuple")

                out = self.dut.send_expect("stop", "testpmd> ")
                self.verify_result(out, tx_pkts="1", expect_queue="3")
                self.dut.send_expect("start", "testpmd> ", 120)
                self.filter_send_packet("arp")
                out = self.dut.send_expect("stop", "testpmd> ")
                self.verify_result(out, tx_pkts="1", expect_queue="0")
                if case == "0x1f":
                    if self.nic in ["niantic", "sagepond", "sageville"]:
                        cmd = "5tuple_filter %s del dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask %s tcp_flags 0x0 priority 3 queue 3" % (
                            valports[0], case)
                    if self.nic in ["kawela_4", "fortville_eagle", "fortville_25g", "fortville_spirit", "columbiaville_25g", "columbiaville_100g"]:
                        cmd = "5tuple_filter %s del dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask %s tcp_flags 0x02 priority 3 queue 3" % (
                            valports[0], case)
                else:
                    if self.nic in ["niantic", "sagepond", "sageville"]:
                        cmd = "5tuple_filter %s del dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask %s tcp_flags 0x0 priority 3 queue 3" % (
                            valports[0], case)
                    if self.nic in ["kawela_4", "fortville_eagle", "fortville_25g", "fortville_spirit", "columbiaville_25g", "columbiaville_100g"]:
                        cmd = "5tuple_filter %s del dst_ip 2.2.2.5 src_ip 2.2.2.4 dst_port 1 src_port 1 protocol 0x06 mask %s tcp_flags 0x02 priority 3 queue 3" % (
                            valports[0], case)

                self.dut.send_expect("%s" % (cmd), "testpmd> ")
                self.dut.send_expect("start", "testpmd> ", 120)
                self.filter_send_packet("fivetuple")
                out = self.dut.send_expect("stop", "testpmd> ")
                self.verify_result(out, tx_pkts="1", expect_queue="0")
            self.dut.send_expect("quit", "#", timeout=30)
        else:
            self.verify(False, "%s nic not support syn filter" % self.nic)

    def test_ethertype_filter(self):

        self.verify(self.nic in ["niantic", "kawela_4", "bartonhills", "sagepond",
                           "powerville", "fortville_eagle", "fortville_25g", "fortville_spirit",
                           "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "fortville_25g","cavium_a063", "carlsville", "foxville", "sageville", "columbiaville_25g", "columbiaville_100g"], "%s nic not support syn filter" % self.nic)
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--disable-rss --rxq=4 --txq=4 --portmask=%s --nb-cores=4 --nb-ports=1" % portMask)
        self.port_config()
        self.ethertype_filter = "on"
        ethertype = "0x0806"

        if self.nic == "cavium_a063":
            self.dut.send_expect(
                "flow create %s ingress pattern eth type is %s / end actions queue index 2 / end"%
                (valports[0], ethertype), "testpmd> ")
        else:
            self.dut.send_expect(
                "ethertype_filter %s add mac_ignr 00:00:00:00:00:00 ethertype %s fwd queue 2" %
                (valports[0], ethertype), "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)

        self.filter_send_packet("arp")
        time.sleep(2)
        out = self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("clear port stats all", "testpmd> ")

        self.verify_result(out, tx_pkts="1", expect_queue="2")
        if self.nic in ["niantic", "sagepond"]:
            self.dut.send_expect("start", "testpmd> ")
            self.filter_send_packet("arp_prio")
            time.sleep(2)
            out = self.dut.send_expect("stop", "testpmd> ")
            self.dut.send_expect("clear port stats all", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="2")
        if self.nic == "cavium_a063":
            self.dut.send_expect("flow flush %s" % (valports[0]), "testpmd> ")
        else:
            self.dut.send_expect(
                "ethertype_filter %s del mac_ignr 00:00:00:00:00:00 ethertype %s fwd queue 2" %
                (valports[0], ethertype), "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)
        self.filter_send_packet("arp")
        time.sleep(2)
        out = self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("clear port stats all", "testpmd> ")

        self.verify_result(out, tx_pkts="1", expect_queue="0")

    def test_twotuple_filter(self):

        if self.nic in ["powerville", "bartonhills", "cavium_a063", "sagepond", "foxville", "sageville", "fortville_eagle", "fortville_25g", "fortville_spirit", "columbiaville_25g", "columbiaville_100g"]:
            self.pmdout.start_testpmd(
                "%s" % self.cores, "--disable-rss --rxq=4 --txq=4 --portmask=%s --nb-cores=4 --nb-ports=1" % portMask)
            self.port_config()
            self.dut.send_expect(
                "2tuple_filter %s add dst_port 64 protocol 0x11 mask 1 tcp_flags 0 priority 3 queue 1" % valports[0], "testpmd> ")
            self.dut.send_expect("start", "testpmd> ", 120)

            self.filter_send_packet("udp")
            out = self.dut.send_expect("stop", "testpmd> ")

            self.verify_result(out, tx_pkts="1", expect_queue="1")

            self.dut.send_expect("start", "testpmd> ")

            self.filter_send_packet("syn")
            time.sleep(2)
            out = self.dut.send_expect("stop", "testpmd> ")

            self.verify_result(out, tx_pkts="1", expect_queue="0")
            self.dut.send_expect(
                "2tuple_filter %s del dst_port 64 protocol 0x11 mask 1 tcp_flags 0 priority 3 queue 1" % valports[0], "testpmd> ")
            self.dut.send_expect("start", "testpmd> ", 120)
            self.filter_send_packet("udp")
            time.sleep(2)
            out = self.dut.send_expect("stop", "testpmd> ")

            self.verify_result(out, tx_pkts="1", expect_queue="0")
            self.dut.send_expect("quit", "#")
        else:
            self.verify(False, "%s nic not support two tuple filter" % self.nic)

    def test_flex_filter(self):
        self.verify(self.nic in ["powerville", "bartonhills", "cavium_a063", "sagepond", "foxville", "sageville", "fortville_eagle", "fortville_25g", "fortville_spirit", "columbiaville_25g", "columbiaville_100g"], '%s not support flex filter' % self.nic)

        masks = ['000C', '000C']
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--disable-rss --rxq=4 --txq=4 --portmask=%s --nb-cores=4 --nb-ports=1" % portMask)
        self.port_config()
        for i in [0, 1]:
            if i == 0:
                self.dut.send_expect(
                    "flex_filter %s add len 16 bytes 0x0123456789abcdef0000000008060000 mask %s priority 3 queue 1" %
                    (valports[0], masks[i]), "testpmd> ")
            else:
                self.dut.send_expect(
                    "flex_filter %s add len 16 bytes 0x0123456789abcdef0000000008000000 mask %s priority 3 queue 1" %
                    (valports[0], masks[i]), "testpmd> ")

            self.dut.send_expect("start", "testpmd> ", 120)

            if i == 0:
                self.filter_send_packet("arp")
            else:
                self.filter_send_packet("ip")
            time.sleep(2)
            out = self.dut.send_expect("stop", "testpmd> ")

            self.verify_result(out, tx_pkts="1", expect_queue="1")

            self.dut.send_expect("start", "testpmd> ")

            if i == 0:
                self.filter_send_packet("syn")
            else:
                self.filter_send_packet("arp")
            time.sleep(2)
            out = self.dut.send_expect("stop", "testpmd> ")

            self.verify_result(out, tx_pkts="1", expect_queue="0")
            if i == 0:
                self.dut.send_expect(
                    "flex_filter %s del len 16 bytes 0x0123456789abcdef0000000008060000 mask %s priority 3 queue 1" %
                    (valports[0], masks[i]), "testpmd> ")
            else:
                self.dut.send_expect(
                    "flex_filter %s del len 16 bytes 0x0123456789abcdef0000000008000000 mask %s priority 3 queue 1" %
                    (valports[0], masks[i]), "testpmd> ")
            self.dut.send_expect("start", "testpmd> ", 120)
            if i == 0:
                self.filter_send_packet("arp")
            else:
                self.filter_send_packet("ip")
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="0")

    def test_multiple_filters_1GB(self):

        if self.nic in ["powerville", "kawela_4", "bartonhills", "sagepond", "foxville", "sageville", "fortville_eagle", "fortville_25g", "fortville_spirit", "columbiaville_25g", "columbiaville_100g"]:
            self.pmdout.start_testpmd(
                "%s" % self.cores, "--disable-rss --rxq=4 --txq=4 --portmask=%s --nb-cores=4 --nb-ports=1" % portMask)
            self.port_config()
            self.dut.send_expect(
                "syn_filter %s add priority high queue 1" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "ethertype_filter %s add mac_ignr 00:00:00:00:00:00 ethertype 0x0806 fwd queue 3" % (valports[0]), "testpmd> ")
            self.dut.send_expect("start", "testpmd> ")

            self.dut.send_expect("start", "testpmd> ")
            self.filter_send_packet("arp")
            time.sleep(2)
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="3")

            self.dut.send_expect("start", "testpmd> ")
            self.filter_send_packet("syn")
            time.sleep(2)
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="1")

            # remove all filters

            self.dut.send_expect(
                "syn_filter %s del priority high queue 1" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "ethertype_filter %s del mac_ignr 00:00:00:00:00:00 ethertype 0x0806 fwd queue 3" % valports[0], "testpmd> ")

            self.dut.send_expect("start", "testpmd> ")
            self.filter_send_packet("arp")
            time.sleep(2)
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="0")

            self.dut.send_expect("start", "testpmd> ")
            self.filter_send_packet("syn")
            time.sleep(2)
            out = self.dut.send_expect("stop", "testpmd> ")
            self.verify_result(out, tx_pkts="1", expect_queue="0")
        else:
            self.verify(False, "%s nic not support this test" % self.nic)

    def test_128_queues(self):
        # testpmd can't support assign queue to received packet, so can't test
        set_filter_flag = 1
        packet_flag = 1
        if self.kdriver == "ixgbe":
            self.dut.send_expect("sed -i -e 's/#define IXGBE_NONE_MODE_TX_NB_QUEUES 64$/#define IXGBE_NONE_MODE_TX_NB_QUEUES 128/' drivers/net/ixgbe/ixgbe_ethdev.h", "# ",30)
            self.dut.build_install_dpdk(self.target)
            global valports
            total_mbufs = self.request_mbufs(128) * len(valports)
            self.pmdout.start_testpmd(
                "all", "--disable-rss --rxq=128 --txq=128 --portmask=%s --nb-cores=4 --total-num-mbufs=%d" % (portMask, total_mbufs))
            self.dut.send_expect(
                "set stat_qmap rx %s 0 0" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "set stat_qmap rx %s 0 0" % valports[1], "testpmd> ")
            self.dut.send_expect(
                "vlan set strip off %s" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "vlan set strip off %s" % valports[1], "testpmd> ")
            self.dut.send_expect(
                "vlan set filter off %s" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "vlan set filter off %s" % valports[1], "testpmd> ")
            queue = ['64', '127', '128']

            for i in [0, 1, 2]:
                if i == 2:
                    out = self.dut.send_expect(
                        "set stat_qmap rx %s %s %s" % (valports[0], queue[i], (i + 1)), "testpmd> ")
                    if 'Invalid RX queue %s' % (queue[i]) not in out:
                        set_filter_flag = 0
                        break
                    cmd = "flow create {} ingress pattern eth / ".format(
                        valports[0]) + "ipv4 dst is 2.2.2.5 src is 2.2.2.4 / tcp dst is {} src is 1 / ".format(
                        i + 1) + "end actions queue index {} / end".format(queue[i])
                    out = self.dut.send_expect(cmd, "testpmd> ")
                    if 'Invalid argument' not in out:
                        set_filter_flag = 0
                        break
                    continue
                else:
                    self.dut.send_expect("set stat_qmap rx %s %s %s" %
                                         (valports[0], queue[i], (i + 1)), "testpmd> ")
                    cmd = "flow create {} ingress pattern eth / ".format(
                        valports[0]) + "ipv4 dst is 2.2.2.5 src is 2.2.2.4 / tcp dst is {} src is 1 / ".format(
                        i + 1) + "end actions queue index {} / end".format(queue[i])
                    self.dut.send_expect(cmd, "testpmd> ")
                    self.dut.send_expect("start", "testpmd> ", 120)
                global filters_index
                filters_index = i
                self.filter_send_packet("packet")
                time.sleep(1)
                out = self.dut.send_expect("stop", "testpmd> ")
                p = re.compile(r"Forward Stats for RX Port= \d+/Queue=(\s?\d+)")
                res = p.findall(out)
                queues = [int(i) for i in res]
                if queues[0] != int(queue[i]):
                    packet_flag = 0
                    break
            self.dut.send_expect("quit", "#", timeout=30)
            self.dut.send_expect("sed -i -e 's/#define IXGBE_NONE_MODE_TX_NB_QUEUES 128$/#define IXGBE_NONE_MODE_TX_NB_QUEUES 64/' drivers/net/ixgbe/ixgbe_ethdev.h", "# ",30)
            self.dut.build_install_dpdk(self.target)
            self.verify(set_filter_flag == 1, "set filters error")
            self.verify(packet_flag == 1, "packet pass assert error")
        else:
            self.verify(False, "%s not support this test" % self.nic)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        pass
