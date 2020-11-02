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

Test coremask parsing in DPDK.

"""

import utils

from exception import VerifyFailure
from test_case import TestCase

#
#
# Test class.
#

command_line = """./%s -c %s -n %d --log-level="lib.eal,8" """


class TestCoremask(TestCase):

    #
    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.

        Coremask Prerequisites.
        """

        self.port_mask = utils.create_mask(self.dut.get_ports(self.nic))
        self.mem_channel = self.dut.get_memory_channels()
        self.app_test_path = self.dut.apps_name['test']
        self.all_cores = self.dut.get_core_list("all")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def get_available_max_lcore(self):
        """
        Check available max lcore according to configuration.
        """

        config_max_lcore = self.dut.get_def_rte_config('CONFIG_RTE_MAX_LCORE')

        if config_max_lcore:
            available_max_lcore = min(int(config_max_lcore), len(self.all_cores) + 1)
        else:
            available_max_lcore = len(self.all_cores) + 1

        return available_max_lcore

    def test_individual_coremask(self):
        """
        Check coremask parsing for all the available cores one by one.
        """

        available_max_lcore = self.get_available_max_lcore()

        for core in self.all_cores[:available_max_lcore - 1]:

            core_mask = utils.create_mask([core])

            command = command_line % (self.app_test_path, core_mask,
                                      self.mem_channel)

            out = self.dut.send_expect(command, "RTE>>", 10)
            self.verify("EAL: Detected lcore %s as core" % core in out,
                        "Core %s not detected" % core)

            self.verify("EAL: Main lcore %s is ready" % core in out,
                        "Core %s not ready" % core)

            self.dut.send_expect("quit", "# ", 10)

    def test_all_cores_coremask(self):
        """
        Check coremask parsing for all the cores at once.
        """

        available_max_lcore = self.get_available_max_lcore()

        core_mask = utils.create_mask(self.all_cores[:available_max_lcore - 1])

        first_core=self.all_cores[0]

        command = command_line % (self.app_test_path, core_mask, self.mem_channel)

        out = self.dut.send_expect(command, "RTE>>", 10)
        self.verify("EAL: Main lcore %s is ready" % first_core in out,
                    "Core %s not ready" % first_core )

        self.verify("EAL: Detected lcore %s as core" % first_core in out,
                    "Core %s not detected" % first_core )

        for core in self.all_cores[1:available_max_lcore - 1]:
            self.verify("EAL: lcore %s is ready" % core in out,
                        "Core %s not ready" % core)

            self.verify("EAL: Detected lcore %s as core" % core in out,
                        "Core %s not detected" % core)

        self.dut.send_expect("quit", "# ", 10)

    def test_big_coremask(self):
        """
        Check coremask parsing for more cores than available.
        """
        command_line = """./%s -c %s -n %d --log-level="lib.eal,8" 2>&1 |tee out"""

        # Create a extremely big coremask
        big_coremask_size = self.get_available_max_lcore()
        big_coremask = "0x"
        for _ in range(0, big_coremask_size, 4):
            big_coremask += "f"
        command = command_line % (self.app_test_path, big_coremask, self.mem_channel)
        try:
            out = self.dut.send_expect(command, "RTE>>", 10)
        except:
            self.verify("EAL: invalid coremask" in out,
                        "Small core mask set")

        self.verify("EAL: Detected lcore 0 as core" in out,
                    "Core 0 not detected")

        for core in self.all_cores[1:big_coremask_size - 1]:

            self.verify("EAL: Detected lcore %s as core" % core in out,
                        "Core %s not detected" % core)

        self.dut.send_expect("quit", "# ", 10)

    def test_wrong_coremask(self):
        """
        Check coremask parsing for wrong coremasks.
        """

        wrong_coremasks = ["GARBAGE", "0xJF", "0xFJF", "0xFFJ",
                           "0xJ11", "0x1J1", "0x11J",
                           "JF", "FJF", "FFJ",
                           "J11", "1J1", "11J",
                           "jf", "fjf", "ffj",
                           "FF0x", "ff0x", "", "0x", "0"]

        for coremask in wrong_coremasks:

            command = command_line % (self.app_test_path, coremask, self.mem_channel)
            try:
                out = self.dut.send_expect(command, "# ", 5)
                self.verify("EAL: invalid coremask" in out,
                            "Wrong core mask (%s) accepted" % coremask)
            except:
                self.dut.send_expect("quit", "# ", 5)
                raise VerifyFailure("Wrong core mask (%s) accepted" % coremask)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
