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
l2tpv3 test script.
"""
import time
import re
from test_case import TestCase
from pmd_output import PmdOutput
from scapy.all import *
import random


class TestDdpL2tpv3(TestCase):

    def set_up_all(self):
        self.dut.session.copy_file_to('dep/l2tpv3oip-l4.pkg', "/tmp/")
        self.dut_testpmd = PmdOutput(self.dut)
        self.dut_ports = self.dut.get_ports(self.nic)
        self.used_dut_port = self.dut_ports[0]
        tester_port = self.tester.get_local_port(self.used_dut_port)
        self.tester_intf = self.tester.get_interface(tester_port)
        out = self.dut.send_expect("cat config/common_base", "]# ", 10)
        self.PF_Q_strip = 'CONFIG_RTE_LIBRTE_I40E_QUEUE_NUM_PER_PF'
        pattern = "(%s=)(\d*)" % self.PF_Q_strip
        self.PF_QUEUE = self.element_strip(out, pattern)
        self.PF_Q_strip = 'CONFIG_RTE_LIBRTE_I40E_QUEUE_NUM_PER_PF'

    def set_up(self):
        self.load_profile()

    def element_strip(self, out, pattern):
        """
        Strip and get queue number.
        """

        s = re.compile(pattern)
        res = s.search(out)
        if res is None:
            print('Queue number not in output.')
            return None
        else:
            result = res.group(2)
            return int(result)

    def load_profile(self):
        """
        Load profile to update FVL configuration tables, profile will be
        stored in binary file.
        """
        self.dut_testpmd.start_testpmd(
            "Default", "--pkt-filter-mode=perfect --port-topology=chained \
            --txq=%s --rxq=%s --disable-rss"
                       % (self.PF_QUEUE, self.PF_QUEUE))
        self.dut_testpmd.execute_cmd('port stop all')
        time.sleep(1)
        self.dut_testpmd.execute_cmd(
            'ddp add 0 /tmp/l2tpv3oip-l4.pkg,/tmp/l2tpv3oip-l4.bak')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        self.verify("Profile number is: 1" in out,
                    "Failed to load ddp profile!!!")
        self.dut_testpmd.execute_cmd('port start all')
        time.sleep(3)

    def l2tpv3pkts(self, keyword):
        """
        Generate L2TPv3oIPv4, L2TPv3oIPv6 and UDP  packets.
        """
        pkt = []
        if keyword is not 'def':
            if keyword is "l2tpv3oipv4":
                pkt.append("Ether()/IP(proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(proto=115)/Raw(b'\\x00\\x00\\x03\\fe9')")
            if keyword is "l2tpv3oipv4_dst":
                pkt.append("Ether()/IP(dst=\"8.8.8.8\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(dst=\"8.8.8.8\",proto=115)/Raw(b'\\x00\\x00\\x03\\xb9')")
                pkt.append("Ether()/IP(dst=\"88.8.8.8\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
            if keyword is "l2tpv3oipv4_src":
                pkt.append("Ether()/IP(src=\"1.1.1.1\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(src=\"1.1.1.1\",proto=115)/Raw(b'\\x00\\x00\\x03\\xa9')")
                pkt.append("Ether()/IP(src=\"11.1.1.1\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
            if keyword is "l2tpv3oipv4_src_dst":
                pkt.append("Ether()/IP(src=\"5.5.5.5\",dst=\"2.2.2.2\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(src=\"5.5.5.5\",dst=\"2.2.2.2\",proto=115)/Raw(b'\\x00\\x00\\x03\\xf9')")
                pkt.append("Ether()/IP(src=\"55.5.5.5\",dst=\"2.2.2.2\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(src=\"5.5.5.5\",dst=\"22.2.2.2\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
            if keyword is "l2tpv3oipv6":
                pkt.append("Ether()/IPv6(nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IPv6(nh=115)/Raw(b'\\x00\\x00\\x03\\xc9')")
            if keyword is "l2tpv3oipv6_dst":
                pkt.append("Ether()/IPv6(dst=\"8:7:6:5:4:3:2:1\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IPv6(dst=\"8:7:6:5:4:3:2:1\",nh=115)/Raw(b'\\x00\\x00\\x03\\xd9')")
                pkt.append("Ether()/IPv6(dst=\"8888:7:6:5:4:3:2:1\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
            if keyword is "l2tpv3oipv6_src":
                pkt.append("Ether()/IPv6(src=\"1:2:3:4:5:6:7:8\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IPv6(src=\"1:2:3:4:5:6:7:8\",nh=115)/Raw(b'\\x00\\x00\\x03\\xf9')")
                pkt.append("Ether()/IPv6(src=\"1111:2:3:4:5:6:7:8\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
            if keyword is "l2tpv3oipv6_src_dst":
                pkt.append(
                    "Ether()/IPv6(src=\"2:3:4:5:6:7:8:9\",dst=\"6:5:4:3:2:1:8:9\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append(
                    "Ether()/IPv6(src=\"2:3:4:5:6:7:8:9\",dst=\"6:5:4:3:2:1:8:9\",nh=115)/Raw(b'\\x00\\x00\\x03\\xf9')")
                pkt.append(
                    "Ether()/IPv6(src=\"2222:3:4:5:6:7:8:9\",dst=\"6:5:4:3:2:1:8:9\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append(
                    "Ether()/IPv6(src=\"2:3:4:5:6:7:8:9\",dst=\"6666:5:4:3:2:1:8:9\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
            if keyword is "l2tpv3_ipv4_ipv6":
                pkt.append("Ether()/IP(proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(proto=115)/Raw(b'\\x00\\x00\\x03\\xf9')")
                pkt.append("Ether()/IPv6(nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IPv6(nh=115)/Raw(b'\\x00\\x00\\x03\\xf9')")
            if keyword is "l2tpv3oip_v4src_v6src":
                pkt.append("Ether()/IP(src=\"1.3.5.7\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(src=\"1.3.5.7\",proto=115)/Raw(b'\\x00\\x00\\x03\\xa9')")
                pkt.append("Ether()/IP(src=\"11.3.5.7\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IPv6(src=\"1:3:5:7:9:2:4:6\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IPv6(src=\"1:3:5:7:9:2:4:6\",nh=115)/Raw(b'\\x00\\x00\\x03\\xf9')")
                pkt.append("Ether()/IPv6(src=\"1111:3:5:7:9:2:4:6\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
            if keyword is "l2tpv3oip_v4dst_v6dst":
                pkt.append("Ether()/IP(dst=\"9.7.5.3\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(dst=\"9.7.5.3\",proto=115)/Raw(b'\\x00\\x00\\x03\\xb9')")
                pkt.append("Ether()/IP(dst=\"99.7.5.3\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IPv6(dst=\"2:4:6:8:1:3:5:7\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IPv6(dst=\"2:4:6:8:1:3:5:7\",nh=115)/Raw(b'\\x00\\x00\\x03\\xd9')")
                pkt.append("Ether()/IPv6(dst=\"2222:4:6:8:1:3:5:7\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
            if keyword is "l2tpv3oip_v4srcdst_v6srcdst":
                pkt.append("Ether()/IP(src=\"9.8.7.6\",dst=\"4.5.6.7\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(src=\"9.8.7.6\",dst=\"4.5.6.7\",proto=115)/Raw(b'\\x00\\x00\\x03\\xf9')")
                pkt.append("Ether()/IP(src=\"99.8.7.6\",dst=\"4.5.6.7\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(src=\"9.8.7.6\",dst=\"44.5.6.7\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append(
                    "Ether()/IPv6(src=\"1:2:3:4:5:6:7:8\",dst=\"9:8:7:6:5:4:3:2\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append(
                    "Ether()/IPv6(src=\"1:2:3:4:5:6:7:8\",dst=\"9:8:7:6:5:4:3:2\",nh=115)/Raw(b'\\x00\\x00\\x03\\xf9')")
                pkt.append(
                    "Ether()/IPv6(src=\"1111:2:3:4:5:6:7:8\",dst=\"9:8:7:6:5:4:3:2\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append(
                    "Ether()/IPv6(src=\"1:2:3:4:5:6:7:8\",dst=\"9999:8:7:6:5:4:3:2\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
            if keyword is "l2tpv3oip_v4_v6_udp":
                pkt.append("Ether()/IP(dst=\"9.7.5.3\",proto=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IP(dst=\"9.7.5.3\",proto=115)/Raw(b'\\x00\\x00\\x03\\xb9')")
                pkt.append("Ether()/IPv6(dst=\"2:4:6:8:1:3:5:7\",nh=115)/Raw(b'\\x00\\x00\\x03\\xe9')")
                pkt.append("Ether()/IPv6(dst=\"2:4:6:8:1:3:5:7\",nh=115)/Raw(b'\\x00\\x00\\x03\\xd9')")
                pkt.append("Ether()/IP()/UDP()")
        return pkt

    def send_and_verify(self, keyword='def'):
        """
        Send packets and verify result.
        """
        pkt = self.l2tpv3pkts(keyword)
        qnum = []
        for i in range(len(pkt)):
            self.tester.scapy_append('sendp([%s], iface="%s")' % (pkt[i], self.tester_intf))
            self.tester.scapy_execute()
            out = self.dut.get_session_output(timeout=2)
            pattern = "port (\d)/queue (\d{1,2}): received (\d) packets"
            qnum.append(self.element_strip(out, pattern))
        return qnum

    def run_fd_test(self, keyword, crlwords_ipv4, crlwords_ipv6):
        """
        Configure Flow director rules.

        keywords: keywords have IPv4/IPv6 SIP DIP and UDP
        """
        self.dut_testpmd.execute_cmd('port stop all')
        self.dut_testpmd.execute_cmd('port config 0 pctype 28 fdir_inset clear all')
        self.dut_testpmd.execute_cmd('port config 0 pctype 38 fdir_inset clear all')
        if crlwords_ipv4 is not None:
            for field in crlwords_ipv4:
                self.dut_testpmd.execute_cmd('port config 0 pctype 28 fdir_inset set field {}'.format(field))
        if crlwords_ipv6 is not None:
            for field in crlwords_ipv6:
                self.dut_testpmd.execute_cmd('port config 0 pctype 38 fdir_inset set field {}'.format(field))
        self.dut_testpmd.execute_cmd('port start all')
        self.dut_testpmd.execute_cmd('start')
        self.dut_testpmd.execute_cmd('set verbose 1')
        qdef = []
        qnum = self.send_and_verify(keyword)
        for i in range(len(qnum)):
            self.verify(qnum[i] == 0, "Receive packet from wrong queue{}!!!".format(qnum[i]))

        queue = random.randint(1, self.PF_QUEUE - 1)

        if 'l2tpv3oipv4' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID

        if 'l2tpv3oipv4_dst' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4  dst is 8.8.8.8  / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching DIP

        if 'l2tpv3oipv4_src' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4 src is 1.1.1.1 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching SIP

        if 'l2tpv3oipv4_src_dst' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4 src is 5.5.5.5 dst is 2.2.2.2 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching SIP
            qdef.append(0)  # Default Queue number to check for in case of non matching DIP

        if 'l2tpv3oipv6' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID

        if 'l2tpv3oipv6_dst' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv6 dst is 8:7:6:5:4:3:2:1 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching DIP

        if 'l2tpv3oipv6_src' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv6 src is 1:2:3:4:5:6:7:8 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching SIP

        if 'l2tpv3oipv6_src_dst' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv6 src is 2:3:4:5:6:7:8:9 dst is 6:5:4:3:2:1:8:9 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching SIP
            qdef.append(0)  # Default Queue number to check for in case of non matching DIP

        if 'l2tpv3_ipv4_ipv6' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            queue = random.randint(1, self.PF_QUEUE - 1)
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID

        if 'l2tpv3oip_v4src_v6src' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4 src is 1.3.5.7 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching IPv4 SIP
            queue = random.randint(1, self.PF_QUEUE - 1)
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv6 src is 1:3:5:7:9:2:4:6 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching IPv6 SIP

        if 'l2tpv3oip_v4dst_v6dst' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4 dst is 9.7.5.3 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching IPv4 DIP
            queue = random.randint(1, self.PF_QUEUE - 1)
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv6 dst is 2:4:6:8:1:3:5:7 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching IPv6 DIP

        if 'l2tpv3oip_v4srcdst_v6srcdst' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4 src is 9.8.7.6 dst is 4.5.6.7 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching IPv4 SIP
            qdef.append(0)  # Default Queue number to check for in case of non matching IPv4 DIP
            queue = random.randint(1, self.PF_QUEUE - 1)
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv6 src is 1:2:3:4:5:6:7:8 dst is 9:8:7:6:5:4:3:2 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching IPv6 SIP
            qdef.append(0)  # Default Queue number to check for in case of non matching IPv6 DIP

        if 'l2tpv3oip_v4_v6_udp' is keyword:
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            queue = random.randint(1, self.PF_QUEUE - 1)
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                    queue))
            qdef.append(queue)  # Queue Number as configured in the rule for matched sessionID
            qdef.append(0)  # Default Queue number to check for in case of non matching sessionID
            queue = random.randint(1, self.PF_QUEUE - 1)
            self.dut_testpmd.execute_cmd(
                'flow create 0 ingress pattern eth / ipv4 / udp / end actions queue index {} / end'.format(queue))
            qdef.append(queue)  # Queue Number as configured in the rule

        qnum = self.send_and_verify(keyword)
        for i in range(len(qdef)):
            self.verify(qdef[i] == qnum[i], "Receive packet from wrong queue{}_{}!!!".format(qdef[i],qnum[i]))
        self.dut_testpmd.execute_cmd("flow flush 0")  # Delete all the flow director rules

    def test_l2tpv3oipv4(self):
        """
        L2TPv3 PAY is supported by NVM with profile updated.
    Default flow director input set is sessionID
        flow director works to send matched packets to configured queue,
        otherwise to queue 0.
        """
        keyword = 'l2tpv3oipv4'
        crlwords_ipv4 = range(44, 46)
        crlwords_ipv6 = None
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oipv4_src(self):
        """
        Flow director input set is sessionID + SIP for pctype 28
        """

        crlwords_ipv4 = list(range(15, 17)) + list(range(44, 46))
        crlwords_ipv6 = None
        keyword = 'l2tpv3oipv4_src'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oipv4_dst(self):
        """
        Flow director input set is sessionID + DIP for pctype 28
        """
        crlwords_ipv4 = list(range(27, 29)) + list(range(44, 46))
        crlwords_ipv6 = None
        keyword = 'l2tpv3oipv4_dst'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oipv4_src_dst(self):
        """
        Flow director input set is sessionID + SIP + DIP for pctype 28
        """
        crlwords_ipv4 = list(range(15, 17)) + list(range(27, 29)) + list(range(44, 46))
        crlwords_ipv6 = None
        keyword = 'l2tpv3oipv4_src_dst'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oipv6(self):
        """
        Flow director input set is sessionID for pctyp 38
        """
        crlwords_ipv6 = range(44, 46)
        crlwords_ipv4 = None
        keyword = 'l2tpv3oipv6'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oipv6_dst(self):
        """
        Flow director input set is sessionID +  DIP for pctype 38
        """
        crlwords_ipv4 = None
        crlwords_ipv6 = list(range(21, 29)) + list(range(44, 46))
        keyword = 'l2tpv3oipv6_dst'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oipv6_src(self):
        """
        Flow director input set is sessionID + SIP for pctype 38
        """
        crlwords_ipv4 = None
        crlwords_ipv6 = list(range(13, 21)) + list(range(44, 46))
        keyword = 'l2tpv3oipv6_src'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oipv6_src_dst(self):
        """
        Flow director input set is sessionID + SIP + DIP for pctype 38
        """
        crlwords_ipv4 = None
        crlwords_ipv6 = list(range(13, 29)) + list(range(44, 46))
        keyword = 'l2tpv3oipv6_src_dst'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3_ipv4_ipv6(self):
        """
        Flow director input set is sessionID for pctype 28 and 38
        """
        crlwords_ipv4 = range(44, 46)
        crlwords_ipv6 = range(44, 46)
        keyword = 'l2tpv3_ipv4_ipv6'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oip_v4src_v6src(self):
        """
        Flow director input set is sessionID + SIP for pctype 28 and 38
        """
        crlwords_ipv4 = list(range(15, 17)) + list(range(44, 46))
        crlwords_ipv6 = list(range(13, 21)) + list(range(44, 46))
        keyword = 'l2tpv3oip_v4src_v6src'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oip_v4dst_v6dst(self):
        """
        Flow director input set is sessionID + DIP for pctype 28 and 38
        """
        crlwords_ipv4 = list(range(27, 29)) + list(range(44, 46))
        crlwords_ipv6 = list(range(21, 29)) + list(range(44, 46))
        keyword = 'l2tpv3oip_v4dst_v6dst'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oip_v4srcdst_v6srcdst(self):
        """
        Flow director input set is sessionID + SIP + DIP for pctype 28 and 38
        """
        crlwords_ipv4 = list(range(15, 17)) + list(range(27, 29)) + list(range(44, 46))
        crlwords_ipv6 = list(range(13, 29)) + list(range(44, 46))
        keyword = 'l2tpv3oip_v4srcdst_v6srcdst'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oip_v4_v6_udp(self):
        """
        Flow director input set is sessionID for pctype 28 and 38
        """
        crlwords_ipv4 = range(44, 46)
        crlwords_ipv6 = range(44, 46)
        keyword = 'l2tpv3oip_v4_v6_udp'
        self.run_fd_test(keyword, crlwords_ipv4, crlwords_ipv6)

    def test_l2tpv3oip_load_profile(self):
        """
        Test to load the profile.
        Step1: Check if it is already loaded, if loaded delete the same
        Step2: Load the profile
        """
        self.dut_testpmd.execute_cmd('port stop all')

        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        if "L2TPv3oIP with L4 payload" in out:
            print("Profile is already loaded!!")
            out = self.dut_testpmd.execute_cmd('ddp del 0 /tmp/l2tpv3oip-l4.bak')
        out = self.dut_testpmd.execute_cmd('ddp add 0 /tmp/l2tpv3oip-l4.pkg,/tmp/l2tpv3oip-l4.bak')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        self.verify("L2TPv3oIP with L4 payload" in out, "Failed to Load DDP profile ")

    def test_l2tpv3oip_delete_profile(self):
        """
        Test to delete the profile.
        Step1: Check if profile is loaded, if loaded, delete the same
        Step2: Add the profile again
        """
        self.dut_testpmd.execute_cmd('port stop all')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')

        if "L2TPv3oIP with L4 payload" not in out:
            out = self.dut_testpmd.execute_cmd('ddp add 0 /tmp/l2tpv3oip-l4.pkg,/tmp/l2tpv3oip-l4.bak')
            out = self.dut_testpmd.execute_cmd('ddp get list 0')
            self.verify("L2TPv3oIP with L4 payload" in out, "Error in loading the Profile")
        self.dut_testpmd.execute_cmd('ddp del 0 /tmp/l2tpv3oip-l4.bak')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        self.verify("Profile number is: 0" in out, "Error in @@deleting the Profile !!")
        self.dut_testpmd.execute_cmd('ddp add 0 /tmp/l2tpv3oip-l4.pkg,/tmp/l2tpv3oip-l4.bak')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        self.verify("L2TPv3oIP with L4 payload" in out, "Error in loading the Profile")

    def test_l2tpv3oip_delete_rules(self):
        """
        Test to Add, delete and flush flow director rules
        Step1: Add 3 rules,
        Step2: Delete 1 rule,
        Step3: Flush all rules
        """
        queue = random.randint(1, self.PF_QUEUE - 1)
        self.dut_testpmd.execute_cmd(
            'flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 1001 / end actions queue index {} / end'.format(
                queue))
        self.dut_testpmd.execute_cmd(
            'flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 1002 / end actions queue index {} / end'.format(
                queue))
        self.dut_testpmd.execute_cmd(
            'flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 1003 / end actions queue index {} / end'.format(
                queue))
        out = self.dut_testpmd.execute_cmd('flow list 0')
        verify = out.splitlines()
        self.verify(len(verify) == 6, "Flow rules not added")
        self.dut_testpmd.execute_cmd('flow destroy 0 rule 0')
        out = self.dut_testpmd.execute_cmd('flow list 0')
        verify = out.splitlines()
        self.verify(len(verify) == 5, "Flow rules not destroyed")
        self.dut_testpmd.execute_cmd('flow flush 0')
        out = self.dut_testpmd.execute_cmd('flow list 0')
        verify = out.splitlines()
        self.verify(len(verify) == 1, "Flow rules not destroyed")

    def tear_down(self):
        self.dut_testpmd.execute_cmd('stop')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        if "Profile number is: 0" not in out:
            self.dut_testpmd.execute_cmd('port stop all')
            time.sleep(1)
            self.dut_testpmd.execute_cmd('ddp del 0 /tmp/l2tpv3oip-l4.bak')
            out = self.dut_testpmd.execute_cmd('ddp get list 0')
            self.verify("Profile number is: 0" in out,
                        "Failed to delete ddp profile!!!")
            self.dut_testpmd.execute_cmd('port start all')
        self.dut_testpmd.quit()

    def tear_down_all(self):
        pass
