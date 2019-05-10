# BSD LICENSE
#
# Copyright(c) 2019 Intel Corporation. All rights reserved.
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
Test L2fwd Jobstats
"""

import time
import re
import utils
from test_case import TestCase


class TestL2fwdJobstats(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.verify(self.nic not in ["fortville_eagle", "fortville_spirit",
                                 "fortville_spirit_single", "fortville_25g", "fortpark_TLV"],
                    "NIC Unsupported: " + str(self.nic))
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.verify(len(self.dut.cores) >= 4, "Insufficient cores for testing")
        cores = self.dut.get_core_list("1S/4C/1T")
        self.coremask = utils.create_mask(cores)

        dut_port0 = self.dut_ports[0]
        dut_port1 = self.dut_ports[1]
        self.tx_ports = [dut_port0, dut_port1]

        # build sample app
        out = self.dut.build_dpdk_apps("./examples/l2fwd-jobstats")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_l2fwd_jobstats_check(self):
        """
        Verify l2fwd jobstats is correct
        """
        path = "./examples/l2fwd-jobstats/build/l2fwd-jobstats"
        cmd = path + " -c %s -n 4 -- -q 2 -p 0x03 -l" % (self.coremask)
        self.dut.send_expect(cmd, "Port statistics", 60)

        self.scapy_send_packet(100000)
        out = self.dut.get_session_output(timeout=10)

        print out
        send_packets = re.findall(r"Total packets sent:\s+?(\d+?)\r", out)[-1]
        receive_packets = re.findall(r"Total packets received:\s+?(\d+?)\r", out)[-1]
        self.verify(send_packets == receive_packets == str(100000*len(self.tx_ports)), "Wrong: can't receive enough packages")

    def scapy_send_packet(self, count):
        """
        Send a packet to port
        """
        for i in range(len(self.tx_ports)):
            txport = self.tester.get_local_port(self.dut_ports[i])
            mac = self.dut.get_mac_address(self.dut_ports[i])
            txItf = self.tester.get_interface(txport)
            self.tester.scapy_append(
                'sendp([Ether(dst="02:00:00:00:00", src="%s")/IP()/UDP()/Raw(\'X\'*18)], iface="%s",count=%s)' % (mac, txItf, count))
            self.tester.scapy_execute(timeout=90)

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
