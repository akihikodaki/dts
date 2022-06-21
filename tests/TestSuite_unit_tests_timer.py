# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.

Run all timer autotests
"""


import framework.utils as utils
from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsTimer(TestCase):

    #
    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.cores = self.dut.get_core_list("all")
        #
        # change timeout base number of cores on the system
        # default 60 secs
        #
        self.this_timeout = 60
        if len(self.cores) > 16:
            self.this_timeout = self.this_timeout * len(self.cores) / 16
        self.logger.warning(
            f"Test Suite {self.__name__} is deprecated and will be removed in the next release"
        )

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def get_nic_timeout(self):
        if self.nic in ["x722_37d2"]:
            return 120
        return 60

    def test_timer(self):
        """
        Run timer autotest.
        """
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        timeout = self.get_nic_timeout()
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", timeout)
        out = self.dut.send_expect("timer_autotest", "RTE>>", self.this_timeout)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_timer_perf(self):
        """
        Run timer autotest.
        """
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 60)
        out = self.dut.send_expect("timer_perf_autotest", "RTE>>", self.this_timeout)
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
