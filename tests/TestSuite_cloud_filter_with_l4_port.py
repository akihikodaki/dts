# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
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

Test the support of generic flow API by Poll Mode Drivers.

"""

import utils
import time
import re

from test_case import TestCase
from pmd_output import PmdOutput
from settings import DRIVERS
from crb import Crb
from dut import Dut
import packet
from exception import VerifyFailure
import scapy.layers.inet
from scapy.utils import rdpcap

MAX_QUEUE = 16

class TestCloudFilterWithL4Port(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
        """
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.cores = "1S/8C/1T"
        self.pf_cores = "1S/8C/1T"
        self.pmdout = PmdOutput(self.dut)

        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_itf = self.tester.get_interface(localPort)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.pkt_obj = packet.Packet()

        self.verify(self.nic in ["fortville_eagle", "fortville_spirit", "carlsville",
                    "fortville_spirit_single", "fortpark_TLV",
                    "fortpark_BASE-T","fortville_25g"], "%s nic not support cloud filter" % self.nic)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.kill_all()

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=%d --txq=%d --disable-rss" % (MAX_QUEUE, MAX_QUEUE), "-a %s --file-prefix=test1" % self.pf_pci)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set promisc all off", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

    def destroy_env(self):
        """
        This is to stop testpmd.
        """
        self.dut.send_expect("quit", "# ")
        time.sleep(2)

    def compare_memory_rules(self, expectedRules):
        """
        dump all flow rules that have been created in memory and compare that total rules number with the given expected number
        to see if they are equal, as to get your conclusion after you have deleted any flow rule entry.
        """
        outstring = self.dut.send_expect("flow list 0", "testpmd> ", 20)
        result_scanner = r'\d*.*?\d*.*?\d*.*?=>*'
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.findall(outstring)
        print("All flow entries are: ")
        for i in range(len(m)):
            print(m[i])
        print('Expected rules are: %d - actual are: %d' % (expectedRules, len(m)))
        self.verify(expectedRules == len(m), 'Total rules number mismatched')

    def verify_rulenum(self, rule_num):
        """
        Verify all the rules created.
        """
        # check if there are expected flow rules have been created
        self.compare_memory_rules(rule_num)
        # check if one rule destroyed with success
        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ")
        self.compare_memory_rules(rule_num - 1)
        # check if all flow rules have been removed with success
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.compare_memory_rules(0)

    def sendpkt(self, pktstr, count=1):
        import sys
        py_version = sys.version
        if py_version.startswith('3.'):
            self.pkt_obj.pktgen.pkts.clear()
        else:
            del self.pkt_obj.pktgen.pkts[:]
        self.pkt_obj.append_pkt(pktstr)
        self.pkt_obj.send_pkt(self.tester, tx_port=self.tester_itf, count=count)

    def sendpkt_check_result(self, src_port, dst_port, queue, match, pctype=""):
        match_info = "/queue %d: " % queue
        # source port
        if src_port != "" and dst_port == "":
            if pctype == "ipv4-udp":
                self.sendpkt(pktstr='Ether()/IP()/UDP(sport=%s)' % src_port)
            elif pctype == "ipv4-tcp":
                self.sendpkt(pktstr='Ether()/IP()/TCP(sport=%s)' % src_port)
            elif pctype == "ipv4-sctp":
                self.sendpkt(pktstr='Ether()/IP()/SCTP(sport=%s)' % src_port)
            elif pctype == "ipv6-udp":
                self.sendpkt(pktstr='Ether()/IPv6()/UDP(sport=%s)' % src_port)
            elif pctype == "ipv6-tcp":
                self.sendpkt(pktstr='Ether()/IPv6()/TCP(sport=%s)' % src_port)
            elif pctype == "ipv6-sctp":
                self.sendpkt(pktstr='Ether()/IPv6()/SCTP(sport=%s)' % src_port)
        elif src_port == "" and dst_port != "":
            if pctype == "ipv4-udp":
                self.sendpkt(pktstr='Ether()/IP()/UDP(dport=%s)' % dst_port)
            elif pctype == "ipv4-tcp":
                self.sendpkt(pktstr='Ether()/IP()/TCP(dport=%s)' % dst_port)
            elif pctype == "ipv4-sctp":
                self.sendpkt(pktstr='Ether()/IP()/SCTP(dport=%s)' % dst_port)
            elif pctype == "ipv6-udp":
                self.sendpkt(pktstr='Ether()/IPv6()/UDP(dport=%s)' % dst_port)
            elif pctype == "ipv6-tcp":
                self.sendpkt(pktstr='Ether()/IPv6()/TCP(dport=%s)' % dst_port)
            elif pctype == "ipv6-sctp":
                self.sendpkt(pktstr='Ether()/IPv6()/SCTP(dport=%s)' % dst_port)
        elif src_port != "" and dst_port != "":
            if pctype == "ipv4-udp":
                self.sendpkt(pktstr='Ether()/IP()/UDP(sport=%s, dport=%s)' % (src_port, dst_port))

        out_pf = self.dut.get_session_output(timeout=2)
        print("out_pf is %s" % out_pf)

        if match == 1:
            self.verify(match_info in out_pf, "the packet not match the expect queue %d." % queue)
        else:
            if match_info in out_pf:
                raise Exception("the packet should not match the queue %d." % queue)

    def cloudfilter_test(
            self, ip_type='ipv4', l4_port_type='udp', src_dst='src', port_value=156, queue_id=0):

            # validate
            self.dut.send_expect(
                "flow validate 0 ingress pattern eth / %s / %s %s is %d / end actions pf / queue index %d / end"
                    % (ip_type, l4_port_type, src_dst, port_value, queue_id),
                "validated")

            # create
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / %s / %s %s is %d / end actions pf / queue index %d / end"
                    % (ip_type, l4_port_type, src_dst, port_value, queue_id),
                "created")

            # list
            self.compare_memory_rules(1)

            if src_dst is 'src':
                self.sendpkt_check_result("%d"%port_value, "", queue_id, 1, "%s-%s"%(ip_type,l4_port_type))
                self.sendpkt_check_result("%d"%(port_value-1), "", queue_id, 0, "%s-%s"%(ip_type,l4_port_type))
            else:
                self.sendpkt_check_result("", "%d"%port_value, queue_id, 1, "%s-%s"%(ip_type,l4_port_type))
                self.sendpkt_check_result("", "%d"%(port_value-1), queue_id, 0, "%s-%s"%(ip_type,l4_port_type))

            # flush
            self.dut.send_expect("flow flush 0", "testpmd> ")

            if src_dst is 'src':
                self.sendpkt_check_result("%d"%(port_value-1), "", queue_id, 0, "%s-%s"%(ip_type,l4_port_type))
            else:
                self.sendpkt_check_result("", "%d"%(port_value-1), queue_id, 0, "%s-%s"%(ip_type,l4_port_type))

            self.compare_memory_rules(0)

    def test_ipv4_udp_sport_only(self):
        # ipv4-udp
        # only src port
        self.cloudfilter_test(
            ip_type='ipv4', l4_port_type='udp', src_dst='src', port_value=156, queue_id=1)

    def test_ipv4_udp_dport_only(self):
        # ipv4-udp
        # only dst port
        self.cloudfilter_test(
            ip_type='ipv4', l4_port_type='udp', src_dst='dst', port_value=156, queue_id=1)

    def test_ipv4_tcp_sport_only(self):
        # ipv4-tcp
        # only src port
        self.cloudfilter_test(
            ip_type='ipv4', l4_port_type='tcp', src_dst='src', port_value=156, queue_id=1)

    def test_ipv4_tcp_dport_only(self):
        #ipv4-tcp
        # only dst port
        self.cloudfilter_test(
            ip_type='ipv4', l4_port_type='tcp', src_dst='dst', port_value=156, queue_id=1)

    def test_ipv4_sctp_sport_only(self):
        # ipv4-sctp
        # only src port
        self.cloudfilter_test(
            ip_type='ipv4', l4_port_type='sctp', src_dst='src', port_value=156, queue_id=1)

    def test_ipv4_sctp_dport_only(self):
        #ipv4-sctp
        # only dst port
        self.cloudfilter_test(
            ip_type='ipv4', l4_port_type='sctp', src_dst='dst', port_value=156, queue_id=1)

    def test_ipv6_udp_sport_only(self):
        # ipv6-udp
        # only src port
        self.cloudfilter_test(
            ip_type='ipv6', l4_port_type='udp', src_dst='src', port_value=156, queue_id=1)

    def test_ipv6_udp_dport_only(self):
        # ipv6-udp
        # only dst port
        self.cloudfilter_test(
            ip_type='ipv6', l4_port_type='udp', src_dst='dst', port_value=156, queue_id=1)

    def test_ipv6_tcp_sport_only(self):
        # ipv6-tcp
        # only src port
        self.cloudfilter_test(
            ip_type='ipv6', l4_port_type='tcp', src_dst='src', port_value=156, queue_id=1)

    def test_ipv6_tcp_dport_only(self):
        #ipv6-tcp
        # only dst port
        self.cloudfilter_test(
            ip_type='ipv6', l4_port_type='tcp', src_dst='dst', port_value=156, queue_id=1)

    def test_ipv6_sctp_sport_only(self):
        # ipv6-sctp
        # only src port
        self.cloudfilter_test(
            ip_type='ipv6', l4_port_type='sctp', src_dst='src', port_value=156, queue_id=1)

    def test_ipv6_sctp_dport_only(self):
        #ipv6-sctp
        # only dst port
        self.cloudfilter_test(
            ip_type='ipv6', l4_port_type='sctp', src_dst='dst', port_value=156, queue_id=1)

    def test_multi_rule(self):
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp src is 11 / end actions pf / queue index 1 / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp src is 22 / end actions pf / queue index 2 / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp src is 33 / end actions pf / queue index 3 / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp dst is 44 / end actions pf / queue index 4 / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp dst is 55 / end actions pf / queue index 5 / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp dst is 66 / end actions pf / queue index 6 / end",
            "created")

        self.sendpkt_check_result("11", "", 1, 1, "ipv4-udp")
        self.sendpkt_check_result("22", "", 2, 1, "ipv4-tcp")
        self.sendpkt_check_result("33", "", 3, 1, "ipv4-sctp")
        self.sendpkt_check_result("", "44", 4, 1, "ipv4-udp")
        self.sendpkt_check_result("", "55", 5, 1, "ipv4-tcp")
        self.sendpkt_check_result("", "66", 6, 1, "ipv4-sctp")

        # destroy
        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ")

        self.sendpkt_check_result("11", "", 1, 0, "ipv4-udp")

        self.compare_memory_rules(5)

        # flush
        self.dut.send_expect("flow flush 0", "testpmd> ")

        self.sendpkt_check_result("22", "", 2, 0, "ipv4-tcp")

        self.compare_memory_rules(0)

    def test_negative(self):
        # unsupported rules
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp src is 156 dst is 156 / end actions pf / queue index 1 / end",
            "error")

        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp src is 156 / end actions pf / queue index 1 / end",
            "create")

        # conflicted rules
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp src is 156 / end actions pf / queue index 2 / end",
            "error")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp src is 156 / end actions pf / queue index 2 / end",
            "error")

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
        self.dut.kill_all()
