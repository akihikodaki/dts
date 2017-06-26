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

import utils
import re
import time
from test_case import TestCase

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
        global default
        default = self.dut.send_expect("cat config/common_base |grep IEEE1588=", "# ") 

        # Change the config file to support IEEE1588 and recompile the package.
        self.dut.send_expect("sed -i -e 's/%s$/CONFIG_RTE_LIBRTE_IEEE1588=y/' config/common_base" % default, "# ", 30)
        self.dut.skip_setup = False
        self.dut.build_install_dpdk(self.target)

        # build sample app
        out = self.dut.send_expect("make -C examples/ptpclient", "# ")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

        port = self.tester.get_local_port(dutPorts[0])
        self.itf0 = self.tester.get_interface(port)

    def set_up(self):
        """
        Run before each test case.
        """        
        pass

    def average(self, seq):
        total = 0
        for num in range(0,len(seq)):
            total+=seq[num]
        return total / num

    def creat_table(self,num):
        self.header_row = ["NIC","%s" % self.nic]
        self.result_table_create(self.header_row)
        results_row = ['average value(us)']
        results_row.append(num)
        self.result_table_add(results_row)
        self.result_table_print()

    def kill_ptpclient(self):
        out_ps = self.dut.send_expect("ps -C ptpclient -L -opid,args", "# ")
        utils.regexp(out_ps, r'(\d+) ./examples/ptpclient')
        pid = re.compile(r'(\d+) ./examples/ptpclient')
        pid_num = list(set(pid.findall(out_ps)))
        out_ps = self.dut.send_expect("kill %s" % pid_num[0], "# ")

    def test_ptpclient(self):
        """
        ptp client test case.
        """
        # use the first port on that self.nic
        self.tester.send_expect("ptp4l -i %s -2 -m -S &" % self.itf0, "ptp4l")

        # run ptpclient on the background
        self.dut.send_expect("./examples/ptpclient/build/ptpclient -c f -n 3 -- -T 0 -p 0x1 " + "&", "Delta between master and slave", 60)
        time.sleep(3)
        out = self.dut.get_session_output()
        self.kill_ptpclient()

        self.verify("T1" and "T2" and "T3" and "T4" in out, "T1,T2,T3,T4 clock error")
        utils.regexp(out, r'Delta between master and slave clocks\:(\d+)ns')
        pat = re.compile(r'Delta between master and slave clocks\:(\d+)ns')
        Delta_list = pat.findall(out)
        Delta = map(int, Delta_list) 
        Delta_ns = self.average(Delta)
        Delta_us = Delta_ns / 1000.0

        print "Delta:", Delta

        self.creat_table(Delta_us)

    def test_update_system(self):
       
        #set the dut system time
        self.dut.send_expect("date -s '2000-01-01 00:00:00'", "# ")
        d_time = self.dut.send_expect("date '+%Y-%m-%d %H:%M'","# ")
        self.verify(d_time == '2000-01-01 00:00', "set the time error")

        self.tester.send_expect("ptp4l -i %s -2 -m -S &" % self.itf0, "ptp4l")

        # run ptpclient on the background
        self.dut.send_expect("./examples/ptpclient/build/ptpclient -c f -n 3 -- -T 1 -p 0x1" + "&", "Delta between master and slave", 60)
        time.sleep(3)
        out = self.dut.get_session_output()

        self.kill_ptpclient()

        self.verify("T1" and "T2" and "T3" and "T4" in out, "T1,T2,T3,T4 clock error")
        utils.regexp(out, r'Delta between master and slave clocks\:(\d+)ns')
        pat = re.compile(r'Delta between master and slave clocks\:(\d+)ns')
        Delta_list = pat.findall(out)
        Delta = map(int, Delta_list)
        Delta_ns = self.average(Delta)
        Delta_us = Delta_ns / 1000.0

        print "Delta:", Delta

        self.creat_table(Delta_us)

        tester_out = self.tester.send_expect("date '+%Y-%m-%d %H:%M'", "# ")
        dut_out = self.dut.send_expect("date '+%Y-%m-%d %H:%M'", "# ")

        if tester_out == dut_out:
            self.verify(tester_out == dut_out, "the DUT time synchronous error")
        else:
            tester_out = self.tester.send_expect("date '+%Y-%m-%d %H:%M'", "# ")
            dut_out = self.dut.send_expect("date '+%Y-%m-%d %H:%M'", "# ")
            self.verify(tester_out == dut_out, "the DUT time synchronous error")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.tester.send_expect("killall ptp4l" , "# ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        # Restore the config file and recompile the package.
        self.dut.send_expect("sed -i -e 's/CONFIG_RTE_LIBRTE_IEEE1588=y$/%s/' config/common_base" % default, "# ", 30)
        self.dut.build_install_dpdk(self.target)
