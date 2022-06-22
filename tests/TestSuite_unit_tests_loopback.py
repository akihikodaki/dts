# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.

This TestSuite runs the unit tests included in DPDK for X710/XL710/XXV710 loopback mode.
"""

import re
import time

import framework.utils as utils
from framework.test_case import TestCase

#
#
# Test class.
#


class TestUnitTestsLoopback(TestCase):

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
        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_itf = self.tester.get_interface(localPort)
        self.cores = self.dut.get_core_list("all")

        [self.arch, machine, env, toolchain] = self.target.split("-")
        self.verify(
            self.arch in ["x86_64", "arm64"],
            "pmd perf request running in x86_64 or arm64",
        )
        self.max_traffic_burst = self.get_max_traffic_burst()
        self.dut.send_expect(
            "sed -i -e 's/#define MAX_TRAFFIC_BURST              %s/#define MAX_TRAFFIC_BURST              32/' app/test/test_pmd_perf.c"
            % self.max_traffic_burst,
            "# ",
            30,
        )
        self.tmp_path = "/tmp/test_pmd_perf.c"
        self.dut.send_expect("rm -fr %s" % self.tmp_path, "# ")
        self.dut.send_expect("cp app/test/test_pmd_perf.c %s" % self.tmp_path, "# ")
        self.logger.warning(
            f"Test Suite {self.suite_name} is deprecated and will be removed in the next release"
        )

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def get_max_traffic_burst(self):
        pmd_file = self.dut.send_expect(
            "cat app/test/test_pmd_perf.c", "# ", 30, trim_whitespace=False
        )
        result_scanner = r"#define MAX_TRAFFIC_BURST\s+([0-9]+)"
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(pmd_file)
        max_traffic_burst = m.group(1)
        return max_traffic_burst

    def test_loopback_mode(self):
        """
        Run pmd stream control mode burst test case.
        """
        self.dut.send_expect(
            "sed -i -e 's/lpbk_mode = 0/lpbk_mode = 1/' app/test/test_pmd_perf.c",
            "# ",
            30,
        )
        self.dut.build_install_dpdk(self.target)

        self.tester.send_expect("rm -rf ./getPackageByTcpdump.cap", "#")
        self.tester.send_expect(
            "tcpdump -i %s ether[12:2] != '0x88cc' -w ./getPackageByTcpdump.cap 2> /dev/null& "
            % self.tester_itf,
            "#",
        )
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 60)
        out = self.dut.send_expect("pmd_perf_autotest", "RTE>>", 120)
        print(out)
        self.dut.send_expect("quit", "# ")

        self.verify("Test OK" in out, "Test failed")
        self.tester.send_expect("killall tcpdump", "#")
        tester_out = self.tester.send_expect(
            "tcpdump -nn -e -v -r ./getPackageByTcpdump.cap", "#"
        )
        self.verify("ethertype" not in tester_out, "Test failed")

    def test_link_mode(self):
        """
        Run pmd stream control mode burst test case.
        """
        self.dut.send_expect(
            "sed -i -e 's/lpbk_mode = 1/lpbk_mode = 0/' app/test/test_pmd_perf.c",
            "# ",
            30,
        )
        self.dut.send_expect(
            "sed -i -e '/check_all_ports_link_status(nb_ports, RTE_PORT_ALL);/a\        sleep(6);' app/test/test_pmd_perf.c",
            "# ",
            30,
        )
        self.dut.build_install_dpdk(self.target)

        self.tester.send_expect("rm -rf ./getPackageByTcpdump.cap", "#")
        self.tester.send_expect(
            "tcpdump -i %s -w ./getPackageByTcpdump.cap 2> /dev/null& "
            % self.tester_itf,
            "#",
        )
        eal_params = self.dut.create_eal_parameters(cores=self.cores)
        app_name = self.dut.apps_name["test"]
        self.dut.send_expect(app_name + eal_params, "R.*T.*E.*>.*>", 60)
        self.dut.send_command("pmd_perf_autotest", 30)
        # There is no packet loopback, so the test is hung.
        # It needs to kill the process manually.
        self.dut.kill_all()
        self.tester.send_expect("killall tcpdump", "#")
        tester_out = self.tester.send_expect(
            "tcpdump -nn -e -v -r ./getPackageByTcpdump.cap", "#"
        )
        self.verify("ethertype IPv4" in tester_out, "Test failed")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("rm -fr app/test/test_pmd_perf.c", "# ")
        self.dut.send_expect("cp %s app/test/test_pmd_perf.c" % self.tmp_path, "# ")
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect(
            "sed -i -e 's/#define MAX_TRAFFIC_BURST              32/#define MAX_TRAFFIC_BURST              %s/' app/test/test_pmd_perf.c"
            % self.max_traffic_burst,
            "# ",
            30,
        )
        self.dut.build_install_dpdk(self.target)
        self.dut.kill_all()
