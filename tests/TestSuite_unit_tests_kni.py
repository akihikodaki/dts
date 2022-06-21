# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.

This TestSuite runs the unit tests included in DPDK for KNI feature.
"""

import framework.utils as utils
from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsKni(TestCase):

    #
    #
    # Utility methods and other non-test code.
    #

    def insmod_kni(self):

        out = self.dut.send_expect("lsmod | grep rte_kni", "# ")

        if "rte_kni" in out:
            self.dut.send_expect("rmmod rte_kni.ko", "# ")

        out = self.dut.send_expect(
            "insmod ./%s/kmod/rte_kni.ko lo_mode=lo_mode_fifo" % (self.target), "# "
        )

        self.verify("Error" not in out, "Error loading KNI module: " + out)

        self.logger.warning(
            f"Test Suite {self.__name__} is deprecated and will be removed in the next release"
        )

    #
    #
    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run at the start of each test suite.

        KNI Prerequisites
        """
        self.cores = self.dut.get_core_list("all")
        self.insmod_kni()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_kni(self):
        """
        Run kni autotest.
        """
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 60)
        out = self.dut.send_expect("kni_autotest", "RTE>>", 60)
        self.dut.send_expect("quit", "# ")

        self.verify("Test OK" in out, "Test Failed")

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("rmmod rte_kni", "# ", 5)
