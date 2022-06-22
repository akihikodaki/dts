# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.

This TestSuite runs the unit tests included in DPDK for pmd performance.
"""

import re

from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsPmdPerf(TestCase):

    #
    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.

        Power Prerequisites
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.arch = self.target.split("-")[0]
        self.verify(
            self.arch in ["x86_64", "arm64"],
            "pmd perf request running in x86_64 or arm64",
        )
        self.burst_ctlmodes = ["poll_before_xmit", "poll_after_xmit"]
        self.rxtx_modes = ["vector", "scalar", "full", "hybrid"]
        self.anchors = ["rxtx", "rxonly", "txonly"]
        socket_id = self.dut.ports_info[0]["port"].socket
        self.cores = self.dut.get_core_list(config="1S/4C/1T", socket=socket_id)
        self.logger.warning(
            f"Test Suite {self.suite_name} is deprecated and will be removed in the next release"
        )

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_pmd_burst(self):
        """
        Run pmd stream control mode burst test case.
        """

        eal_params = self.dut.create_eal_parameters(cores=self.cores, ports=[0, 1])
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 60)
        for mode in self.burst_ctlmodes:
            self.dut.send_expect("set_rxtx_sc %s" % mode, "RTE>>", 10)
            out = self.dut.send_expect("pmd_perf_autotest", "RTE>>", 120)
            match_regex = "Result: (\d+) cycles per packet"
            m = re.compile(r"%s" % match_regex, re.S)
            result = m.search(out)
            self.verify(result, "Failed to get result")
            self.logger.info("Mode %s latency is %s" % (mode, result.group(1)))

        self.dut.send_expect("quit", "# ")

    def test_pmd_continues(self):
        """
        Run pmd stream control mode continues test case.
        """

        self.table_header = ["Mode"]
        self.table_header += self.anchors
        self.result_table_create(self.table_header)
        eal_params = self.dut.create_eal_parameters(cores=self.cores, ports=[0, 1])
        print((self.table_header))
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 60)
        for mode in self.rxtx_modes:
            table_row = [mode]
            self.dut.send_expect("set_rxtx_sc continuous", "RTE>>", 10)
            self.dut.send_expect("set_rxtx_mode %s" % mode, "RTE>>", 10)
            for anchor in self.anchors:
                self.dut.send_expect("set_rxtx_anchor %s" % anchor, "RTE>>", 10)
                out = self.dut.send_expect("pmd_perf_autotest", "RTE>>", 120)
                match_regex = "Result: (\d+) cycles per packet"
                m = re.compile(r"%s" % match_regex, re.S)
                result = m.search(out)
                self.verify(result, "Failed to get result")
                table_row.append(result.group(1))
            self.result_table_add(table_row)
        self.dut.send_expect("quit", "# ")
        self.result_table_print()

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
