# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

"""
DPDK Test suite.
Test Event Timer Adapter Unit test
"""

import framework.utils as utils
from framework.test_case import TestCase


class TestUnitTestEventTimer(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.

        PMD prerequisites.
        """

        cores = self.dut.get_core_list("all")
        self.coremask = utils.create_mask(cores)
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports()
        self.app_name = self.dut.apps_name["test"]

        if self.nic == "cavium_a063" or self.nic == "cavium_a064":
            self.eventdev_device_bus_id = "0002:0e:00.0"
            self.eventdev_device_id = "a0f9"
            #### Bind evendev device ####
            self.dut.bind_eventdev_port(port_to_bind=self.eventdev_device_bus_id)

            #### Configuring evendev SS0 & SSOw limits ####
            self.dut.set_eventdev_port_limits(
                self.eventdev_device_id, self.eventdev_device_bus_id
            )
        elif self.nic == "cavium_a034":
            self.eventdev_timer_device_bus_id = "0000:0a:01.0"
            self.dut.bind_eventdev_port(port_to_bind=self.eventdev_timer_device_bus_id)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_event_timer_adapter(self):
        """
        Event Timer Adapter Autotest
        """

        if self.nic == "cavium_a063" or self.nic == "cavium_a064":
            self.dut.send_expect(
                "./%s -n 1 -c %s -a %s,single_ws=1,tim_stats_ena=1"
                % (self.app_name, self.coremask, self.eventdev_device_bus_id),
                "R.*T.*E.*>.*>",
                60,
            )
        elif self.nic == "cavium_a034":
            self.dut.send_expect(
                "./%s -n 1 -c %s -a %s,timvf_stats=1"
                % (self.app_name, self.coremask, self.eventdev_timer_device_bus_id),
                "R.*T.*E.*>.*>",
                60,
            )
        out = self.dut.send_expect("event_timer_adapter_test", "RTE>>", 300)
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
        if self.nic == "cavium_a063" or self.nic == "cavium_a064":
            self.dut.unbind_eventdev_port(port_to_unbind=self.eventdev_device_bus_id)
        elif self.nic == "cavium_a034":
            self.dut.unbind_eventdev_port(
                port_to_unbind=self.eventdev_timer_device_bus_id
            )
        self.dut.kill_all()
