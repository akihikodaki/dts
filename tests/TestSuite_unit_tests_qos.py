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

This TestSuite runs the unit tests included in DPDK for Random Early
Detection, Metering and Scheduling QoS features.
"""

import framework.utils as utils
from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsQos(TestCase):

    #
    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.

        QoS Prerequisites
        """
        self.cores = self.dut.get_core_list("all")


    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_red(self):
        """
        Run RED autotest.
        """

        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", 30)
        out = self.dut.send_expect("red_autotest", "RTE>>", 180)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_meter(self):
        """
        Run meter autotest.
        """

        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", 30)
        out = self.dut.send_expect("meter_autotest", "RTE>>", 5)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_sched(self):
        """
        Run sched autotest.
        """

        [arch, machine, env, toolchain] = self.target.split('-')
        self.verify(arch in ["x86_64" ,"arm64" ,"ppc_64"], "Sched auto_test only support in x86_64 or arm64 ppc_64")

        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name['test']
        self.dut.send_expect(app_name + eal_params,"R.*T.*E.*>.*>", 30)
        out = self.dut.send_expect("sched_autotest", "RTE>>", 5)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

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
