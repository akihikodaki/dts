# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

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
        self.logger.warning(
            f"Test Suite {self.__name__} is deprecated and will be removed in the next release"
        )

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
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 30)
        out = self.dut.send_expect("red_autotest", "RTE>>", 180)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_meter(self):
        """
        Run meter autotest.
        """

        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 30)
        out = self.dut.send_expect("meter_autotest", "RTE>>", 5)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_sched(self):
        """
        Run sched autotest.
        """

        [arch, machine, env, toolchain] = self.target.split("-")
        self.verify(
            arch in ["x86_64", "arm64", "ppc_64"],
            "Sched auto_test only support in x86_64 or arm64 ppc_64",
        )

        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 30)
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
