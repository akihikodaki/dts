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

Test moving RSS to rte_flow.

"""

import utils
import time
import re

from test_case import TestCase
from settings import HEADER_SIZE
from pmd_output import PmdOutput
from settings import DRIVERS

from project_dpdk import DPDKdut
from dut import Dut
from packet import Packet


class TestRSS_to_Rteflow(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Move RSS to rte_flow Prerequistites
        """
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")

        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_itf = self.tester.get_interface(localPort)
        self.tester_mac = self.tester.get_mac(localPort)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.pmdout = PmdOutput(self.dut)
        self.cores = "1S/2C/1T"
        self.pkt1 = "Ether(dst='%s')/IP(src='10.0.0.1',dst='192.168.0.2')/SCTP(dport=80, sport=80)/('X'*48)" % self.pf_mac
        self.pkt2 = "Ether(dst='%s')/IP(src='10.0.0.1',dst='192.168.0.2')/UDP(dport=50, sport=50)/('X'*48)" % self.pf_mac
        self.pkt3 = "Ether(dst='%s')/IP(src='10.0.0.1',dst='192.168.0.3')/TCP(dport=50, sport=50)/('X'*48)" % self.pf_mac
        self.pkt4 = "Ether(dst='%s')/IP(src='10.0.0.1',dst='192.168.0.2')/('X'*48)" % self.pf_mac
        self.pkt5 = "Ether(dst='%s')/IPv6(src='2001::1',dst='2001::2',nh=132)/SCTP(dport=80, sport=80)/('X'*48)" % self.pf_mac
        self.pkt6 = "Ether(dst='%s')/IPv6(src='2001::1',dst='2001::2')/UDP(dport=50, sport=50)/('X'*48)" % self.pf_mac
        self.pkt7 = "Ether(dst='%s')/IPv6(src='2001::2',dst='2001::3')/TCP(dport=50, sport=50)/('X'*48)" % self.pf_mac
        self.pkt8 = "Ether(dst='%s')/IPv6(src='2001::2',dst='2001::3')/('X'*48)" % self.pf_mac
        self.prio_pkt1 = "Ether(dst='%s')/Dot1Q(prio=1)/IP(src='10.0.0.1',dst='192.168.0.2')/TCP(dport=80, sport=80)/('X'*48)" % self.pf_mac
        self.prio_pkt2 = "Ether(dst='%s')/Dot1Q(prio=2)/IP(src='10.0.0.1',dst='192.168.0.2')/TCP(dport=80, sport=80)/('X'*48)" % self.pf_mac
        self.prio_pkt3 = "Ether(dst='%s')/Dot1Q(prio=3)/IP(src='10.0.0.1',dst='192.168.0.2')/TCP(dport=80, sport=80)/('X'*48)" % self.pf_mac

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.kill_all()

    def destroy_env(self):
        """
        This is to stop testpmd.
        """
        self.dut.send_expect("quit", "# ")
        time.sleep(2)

    def get_queue_number(self):
        """
        get the queue which packet enter.
        """
        outstring = self.dut.send_expect("stop", "testpmd> ")
        time.sleep(2)
        result_scanner = r"Forward Stats for RX Port= %s/Queue=\s?([0-9]+)" % self.dut_ports[0]
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(outstring)
        queue_id = m.group(1)
        print "queue is %s" % queue_id
        self.dut.send_expect("start", "testpmd> ")
        return queue_id

    def send_and_check(self, pkt, rss_queue):
        """
        send packet and check the result
        """
        self.tester.scapy_append('sendp(%s, iface="%s")' % (pkt, self.tester_itf))
        self.tester.scapy_execute()
        time.sleep(2)
        queue = self.get_queue_number()
        self.verify(queue in rss_queue, "the packet doesn't enter the expected RSS queue.")
        return queue

    def send_packet(self, ptype, itf):
        """
        Sends packets.
        """
        self.tester.scapy_foreground()
        time.sleep(2)
        for i in range(128):
            if ptype == "ipv4-udp":
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(dport=%d, sport=%d)], iface="%s")' % (
                    self.pf_mac, itf, i + 1, i + 2, i + 21, i + 22, itf)
            elif ptype == "ipv4-other":
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="192.168.0.%d", dst="192.168.0.%d")], iface="%s")' % (
                    self.pf_mac, itf, i + 1, i + 2, itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(2)

    def check_packet_queue(self, queue, out):
        """
        get the queue which packet enter.
        """
        time.sleep(2)
        if queue == "all":
            self.verify("Queue= 0" in out and "Queue= 1" in out and "Queue= 2" in out and "Queue= 3" in out,
                        "There is some queues doesn't work.")
        elif queue == "0":
            self.verify("Queue= 0" in out and "Queue= 1" not in out and "Queue= 2" not in out and "Queue= 3" not in out,
                        "RSS is enabled.")
        lines = out.split("\r\n")
        reta_line = {}
        queue_flag = 0
        packet_sumnum = 0
        # collect the hash result and the queue id
        for line in lines:
            line = line.strip()
            if queue_flag == 1:
                result_scanner = r"RX-packets:\s?([0-9]+)"
                scanner = re.compile(result_scanner, re.DOTALL)
                m = scanner.search(line)
                packet_num = m.group(1)
                packet_sumnum = packet_sumnum + int(packet_num)
                queue_flag = 0
            elif line.strip().startswith("------- Forward"):
                queue_flag = 1
            elif line.strip().startswith("RX-packets"):
                result_scanner = r"RX-packets:\s?([0-9]+)"
                scanner = re.compile(result_scanner, re.DOTALL)
                m = scanner.search(line)
                packet_rec = m.group(1)

        self.verify(packet_sumnum == int(packet_rec) == 128, "There are some packets lost.")

    def test_disable_enable_rss(self):
        """
        Disable and enable RSS.
        """
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4 --port-topology=chained")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Show port default RSS fuctions
        if (self.nic in ["fortville_eagle", "fortville_spirit",
                         "fortville_spirit_single", "fortpark_TLV"]):
            self.dut.send_expect(
                "show port 0 rss-hash", "ipv4-frag ipv4-other ipv6-frag ipv6-other ip")
        else:
            self.dut.send_expect(
                "show port 0 rss-hash", "ipv4 ipv6 ipv6-ex ip")
        self.send_packet("ipv4-other", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue("all", out)
        self.dut.send_expect("start", "testpmd> ", 120)

        # Disable RSS hash function
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types none end / end", "created")
        self.dut.send_expect(
            "show port 0 rss-hash", "RSS disabled")
        # send the packets and verify the results
        self.send_packet("ipv4-other", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue("0", out)
        self.dut.send_expect("start", "testpmd> ", 120)

        # Enable RSS hash function all
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types all end / end", "created")
        if (self.nic in ["fortville_eagle", "fortville_spirit",
                         "fortville_spirit_single", "fortpark_TLV"]):
            self.dut.send_expect(
                "show port 0 rss-hash", "all ipv4-frag ipv4-tcp ipv4-udp ipv4-sctp ipv4-other ipv6-frag ipv6-tcp ipv6-udp ipv6-sctp ipv6-other l2-payload ip udp tcp sctp")
        else:
            self.dut.send_expect(
                "show port 0 rss-hash", "all ipv4 ipv4-tcp ipv4-udp ipv6 ipv6-tcp ipv6-udp ipv6-ex ipv6-tcp-ex ipv6-udp-ex ip udp tcp")
        # send the packets and verify the results
        self.send_packet("ipv4-other", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue("all", out)

    def test_enable_ipv4_udp_rss(self):
        """
        Enable IPv4-UDP RSS.
        """
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4 --port-topology=chained")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Show port default RSS fuctions
        if (self.nic in ["fortville_eagle", "fortville_spirit",
                         "fortville_spirit_single", "fortpark_TLV"]):
            self.dut.send_expect(
                "show port 0 rss-hash", "ipv4-frag ipv4-other ipv6-frag ipv6-other ip")
        else:
            self.dut.send_expect(
                "show port 0 rss-hash", "ipv4 ipv6 ipv6-ex ip")
        self.send_packet("ipv4-other", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue("all", out)
        self.dut.send_expect("start", "testpmd> ", 120)

        self.send_packet("ipv4-udp", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        if (self.nic in ["fortville_eagle", "fortville_spirit",
                         "fortville_spirit_single", "fortpark_TLV"]):
            self.check_packet_queue("0", out)
        else:
            self.check_packet_queue("all", out)
        self.dut.send_expect("start", "testpmd> ", 120)

        # enable ipv4-udp rss function
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv4-udp end / end", "created")
        self.dut.send_expect(
            "show port 0 rss-hash", "ipv4-udp udp")
        # send the packets and verify the results
        self.send_packet("ipv4-other", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue("0", out)
        self.dut.send_expect("start", "testpmd> ", 120)

        self.send_packet("ipv4-udp", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue("all", out)

    def test_rss_queue_rule(self):
        """
        Set valid and invalid parameter.
        """
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=8 --txq=8 --port-topology=chained")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss queues 1 4 7 end / end", "created")
        # send the packets and verify the results
        # ipv4-other and ipv6-other is enabled by default.
        # i40e
        if (self.nic in ["fortville_eagle", "fortville_spirit",
                         "fortville_spirit_single", "fortpark_TLV", "fortville_25g"]):
            rss_queue = ["1", "4", "7"]
            self.send_and_check(self.pkt4, rss_queue)
            self.send_and_check(self.pkt8, rss_queue)
            rss_queue = ["0"]
            self.send_and_check(self.pkt1, rss_queue)
            self.send_and_check(self.pkt2, rss_queue)
            self.send_and_check(self.pkt3, rss_queue)
            self.send_and_check(self.pkt5, rss_queue)
            self.send_and_check(self.pkt6, rss_queue)
            self.send_and_check(self.pkt7, rss_queue)
        else:
            rss_queue = ["1", "4", "7"]
            self.send_and_check(self.pkt1, rss_queue)
            self.send_and_check(self.pkt2, rss_queue)
            self.send_and_check(self.pkt3, rss_queue)
            self.send_and_check(self.pkt4, rss_queue)
            self.send_and_check(self.pkt5, rss_queue)
            self.send_and_check(self.pkt6, rss_queue)
            self.send_and_check(self.pkt7, rss_queue)
            self.send_and_check(self.pkt8, rss_queue)

        # There can't be more than one RSS queue rule existing.
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss queues 3 end / end", "error")
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv4-udp end queues 3 end / end", "error")
        # Flush the rules and create a new RSS queue rule.
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss queues 3 end / end", "created")
        # Send the packets and verify the results
        if (self.nic in ["fortville_eagle", "fortville_spirit",
                         "fortville_spirit_single", "fortpark_TLV", "fortville_25g"]):
            rss_queue = ["3"]
            self.send_and_check(self.pkt4, rss_queue)
            self.send_and_check(self.pkt8, rss_queue)
            rss_queue = ["0"]
            self.send_and_check(self.pkt1, rss_queue)
            self.send_and_check(self.pkt2, rss_queue)
            self.send_and_check(self.pkt3, rss_queue)
            self.send_and_check(self.pkt5, rss_queue)
            self.send_and_check(self.pkt6, rss_queue)
            self.send_and_check(self.pkt7, rss_queue)
        else:
            rss_queue = ["3"]
            self.send_and_check(self.pkt1, rss_queue)
            self.send_and_check(self.pkt2, rss_queue)
            self.send_and_check(self.pkt3, rss_queue)
            self.send_and_check(self.pkt4, rss_queue)
            self.send_and_check(self.pkt5, rss_queue)
            self.send_and_check(self.pkt6, rss_queue)
            self.send_and_check(self.pkt7, rss_queue)
            self.send_and_check(self.pkt8, rss_queue)
        self.dut.send_expect("flow flush 0", "testpmd> ")

        # Set a wrong parameter: queue ID is 16
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss queues 8 end / end", "error")
        # Set all the queues to the rule
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss queues 0 1 2 3 4 5 6 7 end / end", "created")

    def test_different_types_rss_queue_rule(self):
        """
        Set valid and invalid parameter.
        """
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=8 --txq=8 --port-topology=chained")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types udp ipv4-tcp ipv6-sctp ipv4-other end queues 1 4 7 end / end", "created")
        # send the packets and verify the results
        if (self.nic in ["fortville_eagle", "fortville_spirit",
                         "fortville_spirit_single", "fortpark_TLV", "fortville_25g"]):
            rss_queue = ["1", "4", "7"]
            self.send_and_check(self.pkt2, rss_queue)
            self.send_and_check(self.pkt3, rss_queue)
            self.send_and_check(self.pkt4, rss_queue)
            self.send_and_check(self.pkt5, rss_queue)
            self.send_and_check(self.pkt6, rss_queue)
            rss_queue = ["0"]
            self.send_and_check(self.pkt1, rss_queue)
            self.send_and_check(self.pkt7, rss_queue)
            self.send_and_check(self.pkt8, rss_queue)
        else:
            rss_queue = ["1", "4", "7"]
            self.send_and_check(self.pkt2, rss_queue)
            self.send_and_check(self.pkt3, rss_queue)
            self.send_and_check(self.pkt6, rss_queue)
            rss_queue = ["0"]
            self.send_and_check(self.pkt1, rss_queue)
            self.send_and_check(self.pkt4, rss_queue)
            self.send_and_check(self.pkt5, rss_queue)
            self.send_and_check(self.pkt7, rss_queue)
            self.send_and_check(self.pkt8, rss_queue)

        # There can't be more than one RSS queue rule existing.
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv6-other end queues 3 end / end", "error")

    def test_set_key_keylen(self):
        """
        Set key and key_len.
        """
        # Only supported by i40e
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit",
                                 "fortville_spirit_single", "fortpark_TLV"], "NIC Unsupported: " + str(self.nic))
        pkt1 = "Ether(dst='%s')/IP(src='0.0.0.0',dst='4.0.0.0')/UDP(sport=100, dport=200)/('X'*48)" % self.pf_mac
        pkt2 = "Ether(dst='%s')/IP(src='0.0.0.0',dst='4.0.0.0')/UDP(sport=100, dport=201)/('X'*48)" % self.pf_mac
        pkt3 = "Ether(dst='%s')/IP(src='0.0.0.0',dst='4.0.0.0')/UDP(sport=101, dport=201)/('X'*48)" % self.pf_mac
        pkt4 = "Ether(dst='%s')/IP(src='0.0.0.0',dst='4.0.0.1')/UDP(sport=101, dport=201)/('X'*48)" % self.pf_mac
        pkt5 = "Ether(dst='%s')/IP(src='0.0.0.1',dst='4.0.0.1')/UDP(sport=101, dport=201)/('X'*48)" % self.pf_mac

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4 --port-topology=chained")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss rule
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv4-udp end / end", "created")
        out1 = self.dut.send_expect("show port 0 rss-hash key", "testpmd> ", 120)
        rss_queue = ["1"]
        self.send_and_check(pkt1, rss_queue)
        rss_queue = ["3"]
        self.send_and_check(pkt2, rss_queue)
        rss_queue = ["3"]
        self.send_and_check(pkt3, rss_queue)
        rss_queue = ["1"]
        self.send_and_check(pkt4, rss_queue)
        rss_queue = ["2"]
        self.send_and_check(pkt5, rss_queue)

        # Create a rss key rule
        self.dut.send_expect(
            "flow flush 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv4-udp end key 67108863 / end", "created")
        out2 = self.dut.send_expect("show port 0 rss-hash key", "testpmd> ", 120)
        rss_queue = ["3"]
        self.send_and_check(pkt1, rss_queue)
        rss_queue = ["3"]
        self.send_and_check(pkt2, rss_queue)
        rss_queue = ["0"]
        self.send_and_check(pkt3, rss_queue)
        rss_queue = ["1"]
        self.send_and_check(pkt4, rss_queue)
        rss_queue = ["0"]
        self.send_and_check(pkt5, rss_queue)

        self.verify(out1 != out2, "the key setting doesn't take effect.")

        # Create a rss key_len rule
        self.dut.send_expect(
            "flow flush 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv4-udp end key_len 3 / end", "created")
        # Create a rss key rule
        self.dut.send_expect(
            "flow flush 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv4-udp end key 67108863 key_len 3 / end", "created")

    def test_disable_rss_in_commandline(self):
        """
        Set RSS queue rule while disable RSS in command-line.
        """
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=8 --txq=8 --disable-rss --port-topology=chained")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types all end / end", "created")
        self.send_packet("ipv4-udp", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue("all", out)
        self.dut.send_expect("quit", "# ")

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=8 --txq=8 --disable-rss --port-topology=chained")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)
        # Create a rss queue rule
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv6-tcp ipv4-udp sctp ipv6-other end queues 5 6 7 end / end", "created")
        # send the packets and verify the results
        if (self.nic in ["fortville_eagle", "fortville_spirit",
                         "fortville_spirit_single", "fortpark_TLV", "fortville_25g"]):
            rss_queue = ["5", "6", "7"]
            self.send_and_check(self.pkt1, rss_queue)
            self.send_and_check(self.pkt2, rss_queue)
            self.send_and_check(self.pkt5, rss_queue)
            self.send_and_check(self.pkt7, rss_queue)
            self.send_and_check(self.pkt8, rss_queue)
            rss_queue = ["0"]
            self.send_and_check(self.pkt3, rss_queue)
            self.send_and_check(self.pkt4, rss_queue)
            self.send_and_check(self.pkt6, rss_queue)
        else:
            rss_queue = ["5", "6", "7"]
            self.send_and_check(self.pkt2, rss_queue)
            self.send_and_check(self.pkt7, rss_queue)
            rss_queue = ["0"]
            self.send_and_check(self.pkt1, rss_queue)
            self.send_and_check(self.pkt3, rss_queue)
            self.send_and_check(self.pkt4, rss_queue)
            self.send_and_check(self.pkt5, rss_queue)
            self.send_and_check(self.pkt6, rss_queue)
            self.send_and_check(self.pkt8, rss_queue)

        # There can't be more than one RSS queue rule existing.
        self.dut.send_expect("flow flush 0", "testpmd> ")
        rss_queue = ["0"]
        self.send_and_check(self.pkt1, rss_queue)
        self.send_and_check(self.pkt2, rss_queue)
        self.send_and_check(self.pkt3, rss_queue)
        self.send_and_check(self.pkt4, rss_queue)
        self.send_and_check(self.pkt5, rss_queue)
        self.send_and_check(self.pkt6, rss_queue)
        self.send_and_check(self.pkt7, rss_queue)
        self.send_and_check(self.pkt8, rss_queue)

    def test_flow_director_rss_rule_combination(self):
        """
        Set RSS queue rule and flow director rule in meantime.
        """
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=8 --txq=8 --pkt-filter-mode=perfect")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types udp end queues 3 4 5 end / end", "created")
        # send the packets and verify the results
        rss_queue = ["3", "4", "5"]
        self.send_and_check(self.pkt2, rss_queue)
        # Create a flow director rule
        if (self.nic in ["bartonhills", "powerville"]):
            # Create a flow director rule
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 proto is 6 / udp dst is 50 / end actions queue index 1 / end", "created")
            rss_queue = ["1"]
            pkt = "Ether(dst='%s')/IP(src='10.0.0.1',dst='192.168.0.2',proto=6)/UDP(dport=50, sport=50)/('X'*48)" % self.pf_mac
            self.send_and_check(pkt, rss_queue)
        else:
            # Create a flow director rule
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 10.0.0.1 dst is 192.168.0.2 / udp src is 50 dst is 50 / end actions queue index 1 / end", "created")
            # send the packets and verify the results
            rss_queue = ["1"]
            self.send_and_check(self.pkt2, rss_queue)
        # There can't be more than one RSS queue rule existing.
        self.dut.send_expect("flow destroy 0 rule 1", "testpmd> ")
        rss_queue = ["3", "4", "5"]
        self.send_and_check(self.pkt2, rss_queue)

    def test_queue_region_with_rss_rule_api(self):
        """
        Set RSS queue rule with queue region API.
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit",
                                 "fortville_spirit_single", "fortpark_TLV", "fortville_25g"], "NIC Unsupported: " + str(self.nic))
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=16 --txq=16 --port-topology=chained")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule.
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types tcp end queues 7 8 10 11 12 14 15 end / end", "created")
        # send the packets and verify the results
        rss_queue = ["7", "8", "10", "11", "12", "14", "15"]
        queue1 = self.send_and_check(self.prio_pkt1, rss_queue)
        queue2 = self.send_and_check(self.prio_pkt2, rss_queue)
        queue3 = self.send_and_check(self.prio_pkt3, rss_queue)
        self.verify(queue1 == queue2 == queue3, "the packet doesn't enter the expected RSS queue.")

        # Create three queue regions.
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 7 8 end / end", "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x4000 / end actions rss queues 11 12 end / end", "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x6000 / end actions rss queues 15 end / end", "created")
        # send the packets and verify the results
        rss_queue = ["7", "8"]
        queue1 = self.send_and_check(self.prio_pkt1, rss_queue)
        rss_queue = ["11", "12"]
        queue2 = self.send_and_check(self.prio_pkt2, rss_queue)
        rss_queue = ["15"]
        queue3 = self.send_and_check(self.prio_pkt3, rss_queue)

        # Destroy one queue region rule, all the rules become invalid.
        self.dut.send_expect("flow destroy 0 rule 2", "testpmd> ")
        rss_queue = ["0"]
        self.send_and_check(self.prio_pkt1, rss_queue)
        self.send_and_check(self.prio_pkt2, rss_queue)
        self.send_and_check(self.prio_pkt3, rss_queue)

    def test_queue_region_with_invalid_parameter(self):
        """
        Set RSS queue rule with invalid parameter in queue region API.
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit",
                                 "fortville_spirit_single", "fortpark_TLV", "fortville_25g"], "NIC Unsupported: " + str(self.nic))
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=16 --txq=16 --port-topology=chained")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule.
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss queues 8 10 11 12 15 end / end", "created")
        # Set a queue region with invalid queue ID
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 8 9 end / end", "error")
        # Set a queue region with discontinuous queue ID
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 8 10 end / end", "error")
        # Set a queue region with invalid queue number
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x4000 / end actions rss queues 10 11 12 end / end", "error")

    def test_queue_region_with_rss_rule_combination(self):
        """
        Set RSS queue rule with old API, while setting RSS queue rule.
        The queue region is priority to RSS queue rule.
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit",
                                 "fortville_spirit_single", "fortpark_TLV", "fortville_25g"], "NIC Unsupported: " + str(self.nic))
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=16 --txq=16 --port-topology=chained")
        self.dut.send_expect("port config all rss all", "testpmd> ", 120)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Set a queue region.
        self.dut.send_expect(
            "set port 0 queue-region region_id 0 queue_start_index 1 queue_num 1", "testpmd> ")
        self.dut.send_expect(
            "set port 0 queue-region region_id 0 flowtype 31", "testpmd> ")
        self.dut.send_expect(
            "set port 0 queue-region flush on", "testpmd> ")
        # send the packets and verify the results
        rss_queue = ["1"]
        self.send_and_check(self.pkt2, rss_queue)

        # Create a RSS queue rule.
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss queues 6 7 end / end", "testpmd> ")
        # send the packets and verify the results
        rss_queue = ["1"]
        self.send_and_check(self.pkt2, rss_queue)

        # destroy the queue region.
        self.dut.send_expect(
            "set port 0 queue-region flush off", "testpmd> ")
        # send the packets and verify the results
        rss_queue = ["6", "7"]
        self.send_and_check(self.pkt2, rss_queue)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.destroy_env()
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("quit", "# ")
        time.sleep(2)
        self.dut.kill_all()
