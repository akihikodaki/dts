# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.

Run Inter-VM share memory autotests
"""


import framework.utils as utils
from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsRingPmd(TestCase):

    #
    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Nothing to do here.
        """
        self.cores = self.dut.get_core_list("all")
        self.logger.warning(
            f"Test Suite {self.__name__} is deprecated and will be removed in the next release"
        )

    def set_up(self):
        """
        Run before each test case.
        Nothing to do here.
        """
        pass

    def test_ring_pmd(self):
        """
        Run Inter-VM share memory test.
        """
        dev_str1 = "net_ring0"
        dev_str2 = "net_ring1"

        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 10)
        out = self.dut.send_expect("ring_pmd_autotest", "RTE>>", 120)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Default no eth_ring devices Test failed")

        eal_params = self.dut.create_eal_parameters(
            cores=self.cores, vdevs=[dev_str1, dev_str2]
        )
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 10)
        out = self.dut.send_expect("ring_pmd_autotest", "RTE>>", 120)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Two eth_ring devices test failed")

    def tear_down(self):
        """
        Run after each test case.
        Nothing to do here.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        Nothing to do here.
        """
        pass
