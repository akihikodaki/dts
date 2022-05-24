# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.
Test HelloWorld example.
"""

import framework.utils as utils
from framework.test_case import TestCase


class TestHelloWorld(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        hello_world Prerequisites:
            helloworld build pass
        """
        out = self.dut.build_dpdk_apps("examples/helloworld")
        self.app_helloworld_path = self.dut.apps_name["helloworld"]

        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_up(self):
        """
        Run before each test case.
        Nothing to do.
        """
        pass

    def test_hello_world_single_core(self):
        """
        Run hello world on single lcores
        Only received hello message from core0
        """

        # get the mask for the first core
        cores = self.dut.get_core_list("1S/1C/1T")
        eal_para = self.dut.create_eal_parameters(cores="1S/1C/1T")
        cmdline = "./%s %s" % (self.app_helloworld_path, eal_para)
        out = self.dut.send_expect(cmdline, "# ", 30)
        self.verify(
            "hello from core %s" % cores[0] in out,
            "EAL not started on core%s" % cores[0],
        )

    def test_hello_world_all_cores(self):
        """
        Run hello world on all lcores
        Received hello message from all lcores
        """

        # get the maximum logical core number
        cores = self.dut.get_core_list("all")
        eal_para = self.dut.create_eal_parameters(cores=cores)

        cmdline = "./%s %s " % (self.app_helloworld_path, eal_para)
        out = self.dut.send_expect(cmdline, "# ", 50)
        for core in cores:
            self.verify(
                "hello from core %s" % core in out,
                "EAL not started on core%s" % core,
            )

    def tear_down(self):
        """
        Run after each test case.
        Nothing to do.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        Nothing to do.
        """
        pass
