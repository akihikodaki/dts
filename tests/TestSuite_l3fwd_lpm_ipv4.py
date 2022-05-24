# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2021 Intel Corporation
#

"""
DPDK Test suite.
Layer-3 forwarding test script.
"""
from framework.test_case import TestCase

from .perf_test_base import IP_TYPE, MATCH_MODE, PerfTestBase


class TestL3fwdLpmIpv4(TestCase, PerfTestBase):

    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run at the start of each test suite.
        L3fwd Prerequisites
        """
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]
        self.logger.debug(valports)
        self.verify_ports_number(valports)
        # get socket and cores
        socket = self.dut.get_numa_id(self.dut_ports[0])
        cores = self.dut.get_core_list("1S/8C/1T", socket=socket)
        self.verify(cores is not None, "Insufficient cores for speed testing")
        # init l3fwd common base class parameters
        PerfTestBase.__init__(self, valports, socket)
        # preset testing environment
        self.perf_preset_test_environment(self.get_suite_cfg())

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.l3fwd_save_results(json_file="%s.json" % self.suite_name)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        self.perf_reset_cur_case()

    def test_perf_throughput_ipv4_lpm(self):
        self.perf_set_cur_case("test_perf_throughput_ipv4_lpm")
        self.ms_throughput(l3_proto=IP_TYPE.V4, mode=MATCH_MODE.LPM)
