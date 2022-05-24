# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

"""
DPDK Test suite.
Test example_build.
"""

import re
import time

from framework.test_case import TestCase


class TestExamplebuild(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        pass

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_example_build(self):
        """
        Verify example applications compile successfully
        """
        out = self.dut.send_expect("ls /root/intel-cmt-cat-master/lib", "#")
        if "No such file or directory" not in out:
            self.dut.send_expect(
                "export PQOS_INSTALL_PATH=/root/intel-cmt-cat-master/lib", "#"
            )
        out = self.dut.build_dpdk_apps("./examples", "#")
        verify_info = [
            "Error",
            "Stop",
            "terminate",
            "failed",
            "No such file",
            "no input files",
            "not found",
            "No rule",
        ]
        for failed_info in verify_info:
            self.verify(failed_info not in out, "Test failed")

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
