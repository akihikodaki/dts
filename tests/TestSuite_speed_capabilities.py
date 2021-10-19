# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
# Copyright © 2018[, 2019] The University of New Hampshire. All rights reserved.
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
"""
import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestSpeedCapabilities(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.ports[0])

        for port in self.ports:
            self.tester.send_expect(f"ifconfig {self.tester.get_interface(self.tester.get_local_port(port))} mtu 5000"
                                    , "# ")

        self.pmdout = PmdOutput(self.dut)
        self.vm_env_done = False

    def test_speed_capabilities(self):
        self.pmdout.start_testpmd("Default")

        cfg_content = self.get_suite_cfg()
        expected_speeds = cfg_content.get('expected_speeds')

        detected_interfaces = []

        for port in self.ports:
            interface_name = self.tester.get_interface(self.tester.get_local_port(port))

            # Gives the speed in Mb/s
            interface_speed = self.pmdout.get_port_link_speed(port)

            self.verify(interface_name in expected_speeds, f"The interface {interface_name} does not have an expected "
                                                           f"speed associated with it.")

            detected_interfaces.append(interface_name)

            expected_speed = expected_speeds[interface_name]

            # Isolates the unit (Either M or G)
            expected_speed_unit = ''.join(i for i in expected_speed if not i.isdigit())

            # Removes the unit from the speed
            expected_speed = ''.join(i for i in expected_speed if i.isdigit())

            self.verify(len(interface_speed) > 0,
                        f"A valid speed could not be read for the interface {interface_name}.")

            # Converts Gb/s to Mb/s for consistent comparison
            if expected_speed_unit == "G":
                expected_speed += "000"

            self.verify(interface_speed == expected_speed,
                        f"Detected speed: {interface_speed} Mb/s for the interface {interface_name}, "
                        f"but expected speed: {expected_speed} Mb/s")

        for key, value in expected_speeds.items():
            self.verify(key in detected_interfaces, f"The interface {key} expected the speed {value} in "
                                                    "speed_capabilities.cfg file, but it did not detect that interface.")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop" % utils.create_mask(self.ports),
                                  socket=self.ports_socket)
        ports_num = len(self.ports)
        # link up test, to avoid failing further tests if link was down
        for i in range(ports_num):
            # sometimes output text messing up testpmd prompt so trimmed prompt
            self.dut.send_expect("set link-up port %d" % i, ">")
        # start ports, to avoid failing further tests if ports are stopped
        self.dut.send_expect("port start all", "testpmd> ", 100)
        self.dut.send_expect("quit", "# ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        if self.vm_env_done:
            self.destroy_vm_env()
        self.dut.kill_all()
