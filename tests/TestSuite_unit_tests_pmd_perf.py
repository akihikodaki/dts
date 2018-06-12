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

This TestSuite runs the unit tests included in DPDK for pmd performance.
"""

import utils
import re
from test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsPmdPerf(TestCase):

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
        [self.arch, machine, env, toolchain] = self.target.split('-')
        self.verify(self.arch in ["x86_64", "arm64"], "pmd perf request running in x86_64 or arm64")
        self.burst_ctlmodes = ['poll_before_xmit', 'poll_after_xmit']
        self.rxtx_modes = ['vector', 'scalar', 'full', 'hybrid']
        self.anchors = ['rxtx', 'rxonly', 'txonly']

        # for better scalar performance data, need disble CONFIG_RTE_IXGBE_INC_VECTOR
        [arch, machine, env, toolchain] = self.target.split('-')
        self.dut.send_expect("sed -i -e 's/CONFIG_RTE_IXGBE_INC_VECTOR=y/CONFIG_RTE_IXGBE_INC_VECTOR=n/' config/common_%s" % env, "# ", 30)
        self.dut.build_install_dpdk(self.target)
        out = self.dut.build_dpdk_apps('./test/test/')
        self.verify('make: Leaving directory' in out, "Compilation failed")
        self.dut.send_expect("mv -f ./test/test/test ./test/test/test_scalar", "# ")
        self.dut.send_expect("sed -i -e 's/CONFIG_RTE_IXGBE_INC_VECTOR=n/CONFIG_RTE_IXGBE_INC_VECTOR=y/' config/common_%s" % env, "# ", 30)
        self.dut.build_install_dpdk(self.target)
        out = self.dut.build_dpdk_apps('./test/test/')
        self.verify('make: Leaving directory' in out, "Compilation failed")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def get_core_from_socket(self):
       """
       select  the port and lcores from same socket.
       """
    
       out = self.dut.send_expect("./usertools/cpu_layout.py", "#", 10)
       k = re.search("Core 0 (.*)", out)
       result = re.findall("(\d+),", k.group())
       socket_id = self.dut.ports_info[0]['port'].socket
       if socket_id == 0 or socket_id == -1:
          return  int(result[0])
       else:
          return  int(result[1])

    def test_pmd_burst(self):
        """
        Run pmd stream control mode burst test case.
        """

        self.core = self.get_core_from_socket()
        self.dut.send_expect("./test/test/test -n 1 --lcores='%d-%d'" % (self.core, self.core + 1), "R.*T.*E.*>.*>", 60)
        for mode in self.burst_ctlmodes:
            self.dut.send_expect("set_rxtx_sc %s" % mode, "RTE>>", 10)
            out = self.dut.send_expect("pmd_perf_autotest", "RTE>>", 120)
            match_regex = "Result: (\d+) cycles per packet"
            m = re.compile(r"%s" % match_regex, re.S)
            result = m.search(out)
            self.logger.info("Mode %s latency is %s" % (mode, result.group(1)))

        self.dut.send_expect("quit", "# ")

    def test_pmd_continues(self):
        """
        Run pmd stream control mode continues test case.
        """
        
        self.core = self.get_core_from_socket()
        self.table_header = ['Mode']
        self.table_header += self.anchors
        self.result_table_create(self.table_header)
        print self.table_header

        for mode in self.rxtx_modes:
            if mode is "scalar":
                self.dut.send_expect("./test/test/test_scalar -n 1 --lcores='%d-%d'" % (self.core, self.core + 1), "R.*T.*E.*>.*>", 60)
            else:
                self.dut.send_expect("./test/test/test -n 1 --lcores='%d-%d'" % (self.core, self.core + 1), "R.*T.*E.*>.*>", 60)

            table_row = [mode]
            self.dut.send_expect("set_rxtx_sc continuous", "RTE>>", 10)
            self.dut.send_expect("set_rxtx_mode %s" % mode, "RTE>>",10)
            for anchor in self.anchors:
                self.dut.send_expect("set_rxtx_anchor %s" % anchor, "RTE>>", 10)
                out = self.dut.send_expect("pmd_perf_autotest", "RTE>>", 120)
                match_regex = "Result: (\d+) cycles per packet"
                m = re.compile(r"%s" % match_regex, re.S)
                result = m.search(out)
                table_row.append(result.group(1))

            self.dut.send_expect("quit", "# ")
            self.result_table_add(table_row)

        self.result_table_print()

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
