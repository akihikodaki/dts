# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2021 Intel Corporation
#

import os
import time

from framework.test_case import TestCase

from .perf_test_base import (
    IP_TYPE,
    MATCH_MODE,
    SUITE_TYPE,
    VF_L3FWD_NIC_SUPPORT,
    PerfTestBase,
)


class TestVfL3fwdKernelPf(TestCase, PerfTestBase):
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(
            self.nic in VF_L3FWD_NIC_SUPPORT, "NIC Unsupported: " + str(self.nic)
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]
        self.logger.debug(valports)
        self.verify_ports_number(valports)
        # get socket and cores
        socket = self.dut.get_numa_id(self.dut_ports[0])
        cores = self.dut.get_core_list("1S/6C/1T", socket=socket)
        self.verify(cores, "Requested 6 cores failed")
        # init l3fwd common base class parameters
        PerfTestBase.__init__(self, valports, socket, mode=SUITE_TYPE.VF)
        # preset testing environment
        self.perf_preset_test_environment(self.get_suite_cfg())

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.perf_destroy_resource()
        self.l3fwd_save_results(json_file="{}.json".format(self.suite_name))

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

    def test_perf_vf_rfc2544_ipv4_lpm(self):
        self.perf_set_cur_case("test_perf_vf_rfc2544_ipv4_lpm")
        self.qt_rfc2544(l3_proto=IP_TYPE.V4, mode=MATCH_MODE.LPM)

    def test_perf_vf_rfc2544_ipv4_em(self):
        self.perf_set_cur_case("test_perf_vf_rfc2544_ipv4_em")
        self.qt_rfc2544(l3_proto=IP_TYPE.V4, mode=MATCH_MODE.EM)

    def test_perf_vf_throughput_ipv4_lpm(self):
        self.perf_set_cur_case("test_perf_vf_throughput_ipv4_lpm")
        self.ms_throughput(l3_proto=IP_TYPE.V4, mode=MATCH_MODE.LPM)

    def test_perf_vf_throughput_ipv4_em(self):
        self.perf_set_cur_case("test_perf_vf_throughput_ipv4_em")
        self.ms_throughput(l3_proto=IP_TYPE.V4, mode=MATCH_MODE.EM)

    def test_perf_vf_rfc2544_ipv6_lpm(self):
        self.perf_set_cur_case("test_perf_vf_rfc2544_ipv6_lpm")
        self.qt_rfc2544(l3_proto=IP_TYPE.V6, mode=MATCH_MODE.LPM)

    def test_perf_vf_rfc2544_ipv6_em(self):
        self.perf_set_cur_case("test_perf_vf_rfc2544_ipv6_em")
        self.qt_rfc2544(l3_proto=IP_TYPE.V6, mode=MATCH_MODE.EM)

    def test_perf_vf_throughput_ipv6_lpm(self):
        self.perf_set_cur_case("test_perf_vf_throughput_ipv6_lpm")
        self.ms_throughput(l3_proto=IP_TYPE.V6, mode=MATCH_MODE.LPM)

    def test_perf_vf_throughput_ipv6_em(self):
        self.perf_set_cur_case("test_perf_vf_throughput_ipv6_em")
        self.ms_throughput(l3_proto=IP_TYPE.V6, mode=MATCH_MODE.EM)
