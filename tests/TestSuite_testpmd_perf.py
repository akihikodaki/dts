# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2021 Intel Corporation
#

"""
DPDK Test suite.
testpmd perf test script.
"""

from framework.test_case import TestCase

from .perf_test_base import BIN_TYPE, IP_TYPE, MATCH_MODE, PerfTestBase


class TestTestpmdPerf(TestCase, PerfTestBase):

    #
    # Test cases.
    #
    @property
    def supported_nics(self):
        return [
            "IXGBE_10G-82599_SFP",
            "I40E_25G-25G_SFP28",
            "I40E_40G-QSFP_A",
            "ICE_100G-E810C_QSFP",
            "ICE_25G-E810C_SFP",
            "ConnectX5_MT4121",
            "ConnectX4_LX_MT4117",
        ]

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(self.nic in self.supported_nics, "Not required NIC ")
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]
        self.logger.debug(valports)
        self.verify_ports_number(valports)
        # get socket and cores
        socket = self.dut.get_numa_id(self.dut_ports[0])
        # init common base class parameters
        PerfTestBase.__init__(self, valports, socket, bin_type=BIN_TYPE.PMD)
        # preset testing environment
        self.perf_preset_test_environment(self.get_suite_cfg())

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.perf_test_save_results()
        self.perf_destroy_resource()

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

    def test_perf_rfc2544_ipv4_lpm(self):
        self.perf_set_cur_case("test_perf_rfc2544_ipv4_lpm")
        self.qt_rfc2544(l3_proto=IP_TYPE.V4, mode=MATCH_MODE.LPM)

    def test_perf_rfc2544_ipv6_lpm(self):
        self.perf_set_cur_case("test_perf_rfc2544_ipv6_lpm")
        self.qt_rfc2544(l3_proto=IP_TYPE.V6, mode=MATCH_MODE.LPM)
