# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.

Crc autotest

"""

import framework.utils as utils
from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsCrc(TestCase):

    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.cores = self.dut.get_core_list("all")
        self.logger.warning(
            f"Test Suite {self.suite_name} is deprecated and will be removed in the next release"
        )

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_crc(self):
        """
        Run crc autotests in RTE command line.
        """

        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 60)
        out = self.dut.send_expect("crc_autotest", "RTE>>", 60)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")
        return "SUCCESS"

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
