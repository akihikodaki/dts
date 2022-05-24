# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.
Test Timer.
"""

import re
import time

import framework.utils as utils
from framework.test_case import TestCase


class TestTimer(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.


        timer prerequisites
        """
        out = self.dut.build_dpdk_apps("examples/timer")
        self.app_timer_path = self.dut.apps_name["timer"]
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_timer_callbacks_verify(self):
        """
        Timer callbacks running on targeted cores
        """

        # get the mask for the first core
        cores = self.dut.get_core_list("1S/1C/1T")
        eal_para = self.dut.create_eal_parameters(cores="1S/1C/1T")

        # run timer on the background
        cmdline = "./%s %s " % (self.app_timer_path, eal_para) + " &"

        self.dut.send_expect(cmdline, "# ", 1)
        time.sleep(15)
        out = self.dut.get_session_output()
        self.dut.send_expect("killall timer", "# ", 5)

        # verify timer0
        utils.regexp(out, r"timer0_cb\(\) on lcore (\d+)")
        pat = re.compile(r"timer0_cb\(\) on lcore (\d+)")
        match = pat.findall(out)
        self.verify(match or match[0] == 0, "timer0 error")

        # verify timer1
        pat = re.compile(r"timer1_cb\(\) on lcore (\d+)")
        matchlist = sorted(pat.findall(out))
        self.verify(list(set(matchlist)) == cores, "timer1 error")

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
