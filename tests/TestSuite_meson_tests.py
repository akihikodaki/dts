# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test Suite.

meson autotest
"""
import os
import re
from mimetypes import init
from sre_constants import SUCCESS

import framework.utils as utils
from framework.test_case import TestCase


class TestMesonTests(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        # icc compilation cost long long time.
        self.cores = self.dut.get_core_list("all")
        self.dut_ip = self.dut.get_ip_address()
        self.timeout = 600
        # -t 2
        self.ratio = 6
        self.dut_pathlog = "fast-test.log"
        self.testlog = ""
        self.execute_wait_time = self.ratio * self.timeout * 10
        # skip scope
        self.SKIP_SCOPE = ""
        # Test log storage directory
        self.base_output = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "output"
        )
        self.dut_ports = self.dut.get_ports()

    def set_up(self):
        """
        Run before each test case.
        """
        self.meson_auto_test = {}

    def delete_exists_files(self):
        out = self.tester.send_command(
            f"ls -l {self.base_output}/{self.dut_pathlog}", "# "
        )
        if self.dut_pathlog in out:
            self.tester.send_command(f"rm -rf {self.base_output}/{self.dut_pathlog}")

    def find_text(self, res):
        pattern = r"(DPDK:fast-tests|DPDK:perf-tests|DPDK:debug-tests|DPDK:extra-tests|DPDK:driver-tests) / (\w+)\s+(\w+)\s+"
        regex = re.compile(pattern)
        mo = regex.search(res)

        if mo is None:
            return 0
        case_name = mo.group(2)
        test_result = mo.group(3)

        self.meson_auto_test[case_name] = test_result

    def check_sub_case(self):
        success = []
        skip = []
        timeout = []
        failed = []
        self.verify(
            bool(self.meson_auto_test),
            f"Test failed the meson no test results were obtained.",
        )

        for k, v in self.meson_auto_test.items():
            if v == "FAIL" and k not in self.SKIP_SCOPE:
                failed.append(k)
            elif v == "OK":
                success.append(k)
            elif v == "SKIP":
                skip.append(k)
            elif v == "TIMEOUT":
                timeout.append(k)
            else:
                failed.append(k)

        for item in skip:
            self.logger.debug(utils.RED(f"Skip sub case:{item}"))

        for item in timeout:
            self.logger.debug(utils.RED(f"TimeOut sub case:{item}"))

        if (len(failed) + len(timeout)) > 0:
            sub_fail = ""
            sub_timeout = ""
            if len(failed) > 0:
                sub_fail = "[" + ",".join(failed) + "] sub case failed. "
            if len(timeout) > 0:
                sub_timeout = "[" + ",".join(timeout) + "] sub case time out. "
            self.verify(False, f"Test failed. {sub_fail}{sub_timeout}")

    def meson_param(self, case_name):
        # add -a param when running in container
        test_args = self.get_suite_cfg().get("test_args", "")
        if self.dut_ports:
            for port in self.dut_ports:
                test_args += " -a {}".format(
                    self.dut.get_port_pci(self.dut_ports[port])
                )
        return (
            self.get_suite_cfg().get(case_name, "")
            + " "
            + self.get_suite_cfg().get("other_param", "")
            + " --test-args '{}'".format(test_args)
        )

    def copy_file_from_dut(self, case_name):
        if os.path.exists(os.path.join(self.base_output, self.dut_pathlog)):
            os.remove(os.path.join(self.base_output, self.dut_pathlog))
        src_pathlog = f"/tmp/{self.dut_pathlog}"
        self.dut.session.copy_file_from(src_pathlog, self.base_output)
        if self.testlog:
            tester_pathlog = (
                self.base_output + "/" + "{}_mesontest.log".format(case_name)
            )
            self.dut.session.copy_file_from(self.testlog, tester_pathlog)

    def insmod_kni(self):
        out = self.dut.send_expect("lsmod | grep rte_kni", "# ")

        if "rte_kni" in out:
            self.dut.send_expect("rmmod rte_kni.ko", "# ")

        out = self.dut.send_expect(
            "insmod ./%s/kmod/rte_kni.ko lo_mode=lo_mode_fifo" % (self.target), "# "
        )
        self.verify("Error" not in out, "Error loading KNI module: " + out)

    def check_meson_test_result(self, res=None):
        if not os.path.exists(f"{self.base_output}/{self.dut_pathlog}"):
            self.verify(False, "meson tests log file is not exists!!")
        if res is None:
            with open(f"{self.base_output}/{self.dut_pathlog}", "r") as file_obj:
                for files in file_obj:
                    self.find_text(files)
        else:
            self.find_text(res)
        self.check_sub_case()

    def test_fasts(self):
        param = self.meson_param("fast-tests")
        # init file name
        self.dut_pathlog = "fast-test.log"
        self.delete_exists_files()
        self.insmod_kni()
        # config test case list in conf/meson_tests.cfg
        cmds = f"meson test -C {self.target} --suite DPDK:fast-tests {param} |tee /tmp/{self.dut_pathlog}"
        out = self.dut.send_expect(cmds, "# ", self.execute_wait_time)
        # Full log written to /root/dpdk/<<build path>>/meson-logs/testlog.txt
        self.testlog = re.search(r"Full log written to (\S+)", out).groups()[0]
        self.logger.info(self.testlog)
        self.copy_file_from_dut("fast-tests")
        self.check_meson_test_result()

    def test_driver(self):
        param = self.meson_param("driver-tests")
        # init file name
        self.dut_pathlog = "driver-test.log"
        self.delete_exists_files()
        cmds = f"meson test -C {self.target} --suite DPDK:driver-tests {param} |tee /tmp/{self.dut_pathlog}"
        out = self.dut.send_expect(cmds, "# ", self.execute_wait_time)
        # Full log written to /root/dpdk/<<build path>>/meson-logs/testlog.txt
        self.testlog = re.search(r"Full log written to (\S+)", out).groups()[0]
        self.logger.info(self.testlog)
        self.copy_file_from_dut("driver-tests")
        self.check_meson_test_result()

    def test_debug(self):
        param = self.meson_param("debug-tests")
        self.dut_pathlog = "test-debug.log"
        # delete exists files
        self.delete_exists_files()
        cmds = f"meson test -C {self.target} --suite DPDK:debug-tests {param} |tee /tmp/{self.dut_pathlog}"
        out = self.dut.send_expect(cmds, "# ", self.execute_wait_time)
        # Full log written to /root/dpdk/<<build path>>/meson-logs/testlog.txt
        self.testlog = re.search(r"Full log written to (\S+)", out).groups()[0]
        self.logger.info(self.testlog)
        self.copy_file_from_dut("debug-tests")
        self.check_meson_test_result()

    def test_extra(self):
        param = self.meson_param("extra-tests")
        self.dut_pathlog = "extra-test.log"
        # delete exists files
        self.delete_exists_files()
        cmds = f"meson test -C {self.target} --suite DPDK:extra-tests {param} |tee /tmp/{self.dut_pathlog}"
        out = self.dut.send_expect(cmds, "# ", self.execute_wait_time)
        # Full log written to /root/dpdk/<<build path>>/meson-logs/testlog.txt
        self.testlog = re.search(r"Full log written to (\S+)", out).groups()[0]
        self.logger.info(self.testlog)
        self.copy_file_from_dut("extra-tests")
        self.check_meson_test_result()
        self.logger.warning(
            "Extra-tests are know issues which are recorded in DPDK commit and meson.build (detail see test plan)"
        )

    def test_perf(self):
        param = self.meson_param("perf-tests")
        # init file name
        self.dut_pathlog = "perf-test.log"
        # delete exists files
        self.delete_exists_files()
        cmds = f"meson test -C {self.target} --suite DPDK:perf-tests {param} |tee /tmp/{self.dut_pathlog}"
        out = self.dut.send_expect(cmds, "# ", self.execute_wait_time)
        # Full log written to /root/dpdk/<<build path>>/meson-logs/testlog.txt
        self.testlog = re.search(r"Full log written to (\S+)", out).groups()[0]
        self.logger.info(self.testlog)
        self.copy_file_from_dut("perf-tests")
        self.check_meson_test_result()

    def tear_down(self):
        """
        Run after each test case.
        """
        out = self.dut.send_expect("lsmod | grep rte_kni", "# ")

        if "rte_kni" in out:
            self.dut.send_expect("rmmod rte_kni.ko", "# ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
