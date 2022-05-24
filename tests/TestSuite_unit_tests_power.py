# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.

This TestSuite runs the unit tests included in DPDK for power feature.
"""

import framework.utils as utils
from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsPower(TestCase):

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
        self.cores = self.dut.get_core_list("all")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_power(self):
        """
        Run power autotest.
        """

        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 60)
        out = self.dut.send_expect("power_autotest", "RTE>>", 60)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_power_cpufreq(self):
        """
        Run power acpi cpu frequency autotest.
        """
        # This acpi driver test case need correct BIOS and Grub settings.
        # otherwise, the power lib initialization will be failed
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 60)
        out = self.dut.send_expect("power_cpufreq_autotest", "RTE>>", 60)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")

    def test_power_caps(self):
        """
        Run power acpi cpu caps autotest.
        """
        # This acpi driver test case need correct BIOS and Grub settings.
        # otherwise, the power lib initialization will be failed
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 60)
        out = self.dut.send_expect("power_caps_autotest", "RTE>>", 60)
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
