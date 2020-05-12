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

This TestSuite runs the unit tests included in DPDK for X710/XL710/XXV710 loopback mode.
"""

import utils
import re
import time
from test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsLoopback(TestCase):

    #
    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.

        Power Prerequisites
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_itf = self.tester.get_interface(localPort)
        self.cores = self.dut.get_core_list("all")

        [self.arch, machine, env, toolchain] = self.target.split('-')
        self.verify(self.arch in ["x86_64", "arm64"], "pmd perf request running in x86_64 or arm64")
        self.max_traffic_burst = self.get_max_traffic_burst()
        self.dut.send_expect("sed -i -e 's/#define MAX_TRAFFIC_BURST              %s/#define MAX_TRAFFIC_BURST              32/' app/test/test_pmd_perf.c" % self.max_traffic_burst, "# ", 30)
        self.tmp_path = '/tmp/test_pmd_perf.c'
        self.dut.send_expect("cp app/test/test_pmd_perf.c %s" % self.tmp_path, "# ")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def get_max_traffic_burst(self):
        pmd_file = self.dut.send_expect("cat app/test/test_pmd_perf.c", "# ", 30)
        result_scanner = r"#define MAX_TRAFFIC_BURST\s+([0-9]+)"
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(pmd_file)
        max_traffic_burst = m.group(1)
        return max_traffic_burst

    def test_loopback_mode(self):
        """
        Run pmd stream control mode burst test case.
        """
        self.dut.send_expect("sed -i -e 's/lpbk_mode = 0/lpbk_mode = 1/' app/test/test_pmd_perf.c", "# ", 30)
        out = self.dut.send_expect("make -j %s app/test_sub O=%s" % (self.dut.number_of_cores, self.target), "#")
        self.verify("Error" not in out, "compilation l3fwd-power error")
        self.verify("No such" not in out, "Compilation error")

        self.tester.send_expect("rm -rf ./getPackageByTcpdump.cap", "#")
        self.tester.send_expect("tcpdump -i %s ether[12:2] != '0x88cc' -w ./getPackageByTcpdump.cap 2> /dev/null& " % self.tester_itf, "#")
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        self.dut.send_expect("./%s/app/test %s" % (self.target, eal_params), "R.*T.*E.*>.*>", 60)
        out = self.dut.send_expect("pmd_perf_autotest", "RTE>>", 120)
        print(out)
        self.dut.send_expect("quit", "# ")

        self.verify("Test OK" in out, "Test failed")
        self.tester.send_expect("killall tcpdump", "#")
        tester_out = self.tester.send_expect("tcpdump -nn -e -v -r ./getPackageByTcpdump.cap", "#")
        self.verify("ethertype" not in tester_out, "Test failed")

    def test_link_mode(self):
        """
        Run pmd stream control mode burst test case.
        """
        self.dut.send_expect("sed -i -e 's/lpbk_mode = 1/lpbk_mode = 0/' app/test/test_pmd_perf.c", "# ", 30)
        self.dut.send_expect("sed -i -e '/check_all_ports_link_status(nb_ports, RTE_PORT_ALL);/a\        sleep(6);' app/test/test_pmd_perf.c", "# ", 30)
        out = self.dut.send_expect("make -j %s app/test_sub O=%s" % (self.dut.number_of_cores, self.target), "#")
        self.verify("Error" not in out, "compilation l3fwd-power error")
        self.verify("No such" not in out, "Compilation error")

        self.tester.send_expect("rm -rf ./getPackageByTcpdump.cap", "#")
        self.tester.send_expect("tcpdump -i %s -w ./getPackageByTcpdump.cap 2> /dev/null& " % self.tester_itf, "#")
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        self.dut.send_expect("./%s/app/test %s" % (self.target, eal_params), "R.*T.*E.*>.*>", 60)
        self.dut.send_command("pmd_perf_autotest", 30)
        # There is no packet loopback, so the test is hung.
        # It needs to kill the process manually.
        self.dut.kill_all()
        self.tester.send_expect("killall tcpdump", "#")
        tester_out = self.tester.send_expect("tcpdump -nn -e -v -r ./getPackageByTcpdump.cap", "#")
        self.verify("ethertype IPv4" in tester_out, "Test failed")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("cp %s app/test/test_pmd_perf.c" % self.tmp_path, "# ")
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("cp %s app/test/test_pmd_perf.c" % self.tmp_path, "# ")
        self.dut.send_expect("sed -i -e 's/#define MAX_TRAFFIC_BURST              32/#define MAX_TRAFFIC_BURST              %s/' app/test/test_pmd_perf.c" % self.max_traffic_burst, "# ", 30)
        out = self.dut.send_expect("make -j %s app/test_sub O=%s" % (self.dut.number_of_cores, self.target), "#")
        self.verify("Error" not in out, "compilation l3fwd-power error")
        self.verify("No such" not in out, "Compilation error")
        self.dut.kill_all()
