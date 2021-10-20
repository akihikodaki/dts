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
Test cmdline.
"""

import framework.utils as utils
from framework.test_case import TestCase


class TestCmdline(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        Cmdline Prerequisites:
            cmdline build pass
            At least one core in DUT
        """
        out = self.dut.build_dpdk_apps('examples/cmdline')
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

        # Run cmdline app
        self.app_cmdline_path = self.dut.apps_name['cmdline']
        self.eal_para = self.dut.create_eal_parameters(cores="1S/1C/1T")
        self.dut.send_expect(r'./%s %s' % (self.app_cmdline_path, self.eal_para), "> ", 10)
    def set_up(self):
        """
        Run before each test case.
        Nothing to do.
        """
        pass

    def test_cmdline_sample_commands(self):
        """
        Sample commands test.
        """

        # add a test object with an IP address associated
        out = self.dut.send_expect("add object 192.168.0.1", "example> ")
        self.verify("Object object added, ip=192.168.0.1" in out, "add command error")

        # verify the object existence
        out = self.dut.send_expect("add object 192.168.0.1", "example> ")
        self.verify("Object object already exist" in out, "double add command error")

        # show the object result by 'show' command
        out = self.dut.send_expect("show object", "example> ")
        self.verify("Object object, ip=192.168.0.1" in out, "show command error")

        # delete the object in cmdline
        out = self.dut.send_expect("del object", "example> ")
        self.verify("Object object removed, ip=192.168.0.1" in out, "del command error")

        # double delete the object to verify the correctness
        out = self.dut.send_expect("del object", "example> ", 1)
        self.verify("Bad arguments" in out, "double del command error")

        # verify no such object anymore
        out = self.dut.send_expect("show object", "example> ", 1)
        self.verify("Bad arguments" in out, "final show command error")

        # verify the help command
        out = self.dut.send_expect("help", "example> ", 1)

        """
        Demo example of command line interface in RTE

        This is a readline-like interface that can be used to
        debug your RTE application. It supports some features
        of GNU readline like completion, cut/paste, and some
        other special bindings.

        This demo shows how rte_cmdline library can be
        extended to handle a list of objects. There are
        3 commands:
        - add obj_name IP
        - del obj_name
        - show obj_name
        """
        self.verify(" " in out, "help command error")

        out = self.dut.send_expect("?", "example> ", 1)
        """
        show [Mul-choice STRING]: Show/del an object
        del [Mul-choice STRING]: Show/del an object
        add [Fixed STRING]: Add an object (name, val)
        help [Fixed STRING]: show help
        """
        self.verify(" " in out, "? command error")

    def tear_down(self):
        """
        Run after each test case.
        Nothing to do.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        Stop cmdline app.
        """
        self.dut.kill_all()
