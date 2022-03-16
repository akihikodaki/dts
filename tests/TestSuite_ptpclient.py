# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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
Test support of IEEE1588 Precise Time Protocol.
"""

import re
import time

import framework.utils as utils
from framework.test_case import TestCase


class TestPtpClient(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        IEEE1588 Prerequisites
        """
        out = self.tester.send_expect("ptp4l -v", "# ")
        self.verify("command not found" not in out, "ptp4l not install")
        dutPorts = self.dut.get_ports()
        self.verify(len(dutPorts) > 0, "No ports found for " + self.nic)

        # recompile the package with extra options of support IEEE1588.
        self.dut.skip_setup = False
        self.dut.build_install_dpdk(
            self.target, extra_options="-Dc_args=-DRTE_LIBRTE_IEEE1588"
        )

        # build sample app
        out = self.dut.build_dpdk_apps("examples/ptpclient")
        self.app_ptpclient_path = self.dut.apps_name["ptpclient"]
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")
        self.app_name = self.app_ptpclient_path[
            self.app_ptpclient_path.rfind("/") + 1 :
        ]
        port = self.tester.get_local_port(dutPorts[0])
        self.itf0 = self.tester.get_interface(port)
        self.eal_para = self.dut.create_eal_parameters()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def average(self, seq):
        total = 0
        for num in range(0, len(seq)):
            total += seq[num]
        return total / num

    def creat_table(self, num):
        self.header_row = ["NIC", "%s" % self.nic]
        self.result_table_create(self.header_row)
        results_row = ["average value(us)"]
        results_row.append(num)
        self.result_table_add(results_row)
        self.result_table_print()

    def kill_ptpclient(self):
        self.dut.send_expect("killall %s" % self.app_name, "# ")

    def test_ptpclient(self):
        """
        ptp client test case.
        """
        # use the first port on that self.nic
        if self.nic in ["cavium_a063", "cavium_a064"]:
            self.tester.send_expect("ptp4l -i %s -2 -m &" % self.itf0, "ptp4l")
        else:
            self.tester.send_expect("ptp4l -i %s -2 -m -S &" % self.itf0, "ptp4l")

        # run ptpclient on the background
        self.dut.send_expect(
            "./%s %s -- -T 0 -p 0x1 " % (self.app_ptpclient_path, self.eal_para) + "&",
            "Delta between master and slave",
            60,
        )
        time.sleep(3)
        out = self.dut.get_session_output()
        self.kill_ptpclient()

        self.verify("T1" and "T2" and "T3" and "T4" in out, "T1,T2,T3,T4 clock error")
        utils.regexp(out, r"Delta between master and slave clocks\:(-?\d+)ns")
        pat = re.compile(r"Delta between master and slave clocks\:(-?\d+)ns")
        Delta_list = pat.findall(out)
        Delta = list(map(int, Delta_list))
        Delta_ns = self.average(Delta)
        Delta_us = Delta_ns / 1000.0

        print("Delta:", Delta)

        self.creat_table(Delta_us)

    def test_update_system(self):

        # set the dut system time
        self.dut.send_expect("date -s '2000-01-01 00:00:00'", "# ")
        d_time = self.dut.send_expect("date '+%Y-%m-%d %H:%M'", "# ")
        self.verify(d_time == "2000-01-01 00:00", "set the time error")

        if self.nic in ["cavium_a063", "cavium_a064"]:
            self.tester.send_expect("ptp4l -i %s -2 -m &" % self.itf0, "ptp4l")
        else:
            self.tester.send_expect("ptp4l -i %s -2 -m -S &" % self.itf0, "ptp4l")

        # run ptpclient on the background
        self.dut.send_expect(
            "./%s %s -- -T 1 -p 0x1" % (self.app_ptpclient_path, self.eal_para) + "&",
            "Delta between master and slave",
            60,
        )
        time.sleep(3)
        out = self.dut.get_session_output()

        self.kill_ptpclient()

        self.verify("T1" and "T2" and "T3" and "T4" in out, "T1,T2,T3,T4 clock error")
        utils.regexp(out, r"Delta between master and slave clocks\:(-?\d+)ns")
        pat = re.compile(r"Delta between master and slave clocks\:(-?\d+)ns")
        Delta_list = pat.findall(out)
        Delta = list(map(int, Delta_list))
        Delta_ns = self.average(Delta)
        Delta_us = Delta_ns / 1000.0

        print("Delta:", Delta)

        self.creat_table(Delta_us)

        tester_out = self.tester.send_expect("date -u '+%Y-%m-%d %H:%M'", "# ")
        dut_out = self.dut.send_expect("date -u '+%Y-%m-%d %H:%M'", "# ")
        # some times, when using data cmdline get dut system time, after kill ptpclient example.
        # the output will include kill process info, at that time need get system time again.
        if len(dut_out) != len(tester_out):
            dut_out = self.dut.send_expect("date -u '+%Y-%m-%d %H:%M'", "# ")
        # In rare cases minute may change while getting time. So get time again
        if dut_out != tester_out:
            tester_out = self.tester.send_expect("date -u '+%Y-%m-%d %H:%M'", "# ")
            dut_out = self.dut.send_expect("date -u '+%Y-%m-%d %H:%M'", "# ")

        self.verify(tester_out == dut_out, "the DUT time synchronous error")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.tester.send_expect("killall ptp4l", "# ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        # Restore the systime from RTC time.
        out = self.dut.send_expect("hwclock", "# ")
        rtc_time = re.findall(r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})", out)[0]
        self.dut.send_command('date -s "%s"' % rtc_time, "# ")
        # recompile the package without extra options of support IEEE1588.
        self.dut.build_install_dpdk(self.target)
