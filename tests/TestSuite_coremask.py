# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

"""
DPDK Test suite.

Test coremask parsing in DPDK.

"""

import framework.utils as utils
from framework.exception import VerifyFailure
from framework.test_case import TestCase

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
        self.app_test_path = self.dut.apps_name["test"]
        if self.dut.architecture == "i686":
            self.all_cores = self.dut.get_core_list("all", socket=0)
        else:
            self.all_cores = self.dut.get_core_list("all")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_individual_coremask(self):
        """
        Check coremask parsing for all the cores one by one.
        """

        for core in self.all_cores:

            core_mask = utils.create_mask([core])

            command = command_line % (self.app_test_path, core_mask, self.mem_channel)

            out = self.dut.send_expect(command, "RTE>>", 10)
            self.verify(
                "EAL: Detected lcore %s as core" % core in out,
                "Core %s not detected" % core,
            )

            self.verify(
                "EAL: Main lcore %s is ready" % core in out, "Core %s not ready" % core
            )

            self.dut.send_expect("quit", "# ", 10)

    def test_all_cores_coremask(self):
        """
        Check coremask parsing for all the cores at once.
        """

        core_mask = utils.create_mask(self.all_cores)

        first_core = self.all_cores[0]

        command = command_line % (self.app_test_path, core_mask, self.mem_channel)

        out = self.dut.send_expect(command, "RTE>>", 10)
        self.verify(
            "EAL: Main lcore %s is ready" % first_core in out,
            "Core %s not ready" % first_core,
        )

        self.verify(
            "EAL: Detected lcore %s as core" % first_core in out,
            "Core %s not detected" % first_core,
        )

        for core in self.all_cores[1:]:
            self.verify(
                "EAL: lcore %s is ready" % core in out, "Core %s not ready" % core
            )

            self.verify(
                "EAL: Detected lcore %s as core" % core in out,
                "Core %s not detected" % core,
            )

        self.dut.send_expect("quit", "# ", 10)

    def test_big_coremask(self):
        """
        Check coremask parsing for more cores than available.
        """
        command_line = """./%s -c %s -n %d --log-level="lib.eal,8" 2>&1 |tee out"""

        # Create a extremely big coremask
        big_coremask = "0x"
        for _ in range(0, len(self.all_cores) + 1, 4):
            big_coremask += "f"
        command = command_line % (self.app_test_path, big_coremask, self.mem_channel)
        try:
            out = self.dut.send_expect(command, "RTE>>", 10)
        except:
            self.verify("EAL: invalid coremask" in out, "Small core mask set")

        self.verify("EAL: Detected lcore 0 as core" in out, "Core 0 not detected")

        for core in self.all_cores[1:]:

            self.verify(
                "EAL: Detected lcore %s as core" % core in out,
                "Core %s not detected" % core,
            )

        self.dut.send_expect("quit", "# ", 10)

    def test_wrong_coremask(self):
        """
        Check coremask parsing for wrong coremasks.
        """

        wrong_coremasks = [
            "GARBAGE",
            "0xJF",
            "0xFJF",
            "0xFFJ",
            "0xJ11",
            "0x1J1",
            "0x11J",
            "JF",
            "FJF",
            "FFJ",
            "J11",
            "1J1",
            "11J",
            "jf",
            "fjf",
            "ffj",
            "FF0x",
            "ff0x",
            "",
            "0x",
            "0",
        ]

        for coremask in wrong_coremasks:

            command = command_line % (self.app_test_path, coremask, self.mem_channel)
            try:
                out = self.dut.send_expect(command, "# ", 5)
                self.verify(
                    "EAL: invalid coremask" in out,
                    "Wrong core mask (%s) accepted" % coremask,
                )
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
