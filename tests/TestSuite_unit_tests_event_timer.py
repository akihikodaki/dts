# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
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
Test Event Timer Adapter Unit test
"""

import utils

from test_case import TestCase


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
        self.app_name = self.dut.apps_name['test']

        if self.nic == "cavium_a063" or self.nic == "cavium_a064":
            self.eventdev_device_bus_id = "0002:0e:00.0"
            self.eventdev_device_id = "a0f9"
            #### Bind evendev device ####
            self.dut.bind_eventdev_port(port_to_bind=self.eventdev_device_bus_id)

            #### Configuring evendev SS0 & SSOw limits ####
            self.dut.set_eventdev_port_limits(self.eventdev_device_id, self.eventdev_device_bus_id)
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
            self.dut.send_expect("./%s -n 1 -c %s -w %s,single_ws=1,tim_stats_ena=1" % (self.app_name, self.coremask, self.eventdev_device_bus_id), "R.*T.*E.*>.*>", 60)
        elif self.nic == "cavium_a034":
            self.dut.send_expect("./%s -n 1 -c %s -w %s,timvf_stats=1" % (self.app_name, self.coremask, self.eventdev_timer_device_bus_id), "R.*T.*E.*>.*>", 60)
        out = self.dut.send_expect("event_timer_adapter_test", "RTE>>", 300)
        self.dut.send_expect("quit", "# ")
        self.verify("Test OK" in out, "Test failed")
        return 'SUCCESS'

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        if self.nic == "cavium_a063" or self.nic == "cavium_a064" :
            self.dut.unbind_eventdev_port(port_to_unbind=self.eventdev_device_bus_id)
        elif self.nic == "cavium_a034":
            self.dut.unbind_eventdev_port(port_to_unbind=self.eventdev_timer_device_bus_id)
        self.dut.kill_all()
