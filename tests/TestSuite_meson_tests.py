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
        self.execute_wait_time = self.ratio * self.timeout * 10
        # skip scope
        self.SKIP_SCOPE = ""
        # Test log storage directory
        self.base_output = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "output"
        )

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

    def check_scp_file_valid_between_dut(self):
        out = self.tester.send_command(
            f"scp root@{self.dut_ip}:/root/{self.dut_pathlog} {self.base_output}",
            timeout=15,
        )
        if "Are you sure you want to continue connecting" in out:
            out = self.tester.send_command("yes", timeout=20)
        for item in range(30):
            if "password" in out:
                self.tester.send_command(self.dut.get_password(), timeout=20)
                break

        out = self.tester.send_command(
            f"ls -l {self.base_output}/{self.dut_pathlog}", "# "
        )
        self.verify(
            "No such file or directory" not in out, "No test result log was obtained!"
        )

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
        # init file name
        self.dut_pathlog = "fast-test.log"
        self.delete_exists_files()
        self.insmod_kni()
        cmds = f'meson test -C x86_64-native-linuxapp-gcc/ --suite DPDK:fast-tests -t {self.ratio} --test-args="-c 0xff" |tee /root/{self.dut_pathlog}'
        out = self.dut.send_expect(cmds, "# ", self.execute_wait_time)
        self.logger.info(out)
        self.check_scp_file_valid_between_dut()
        self.check_meson_test_result()

    def test_driver(self):
        # init file name
        self.dut_pathlog = "driver-test.log"
        self.delete_exists_files()
        cmds = f'meson test -C x86_64-native-linuxapp-gcc/ --suite DPDK:driver-tests -t {self.ratio} --test-args="-c 0xff" |tee /root/{self.dut_pathlog}'
        out = self.dut.send_expect(cmds, "# ", self.execute_wait_time)
        self.logger.info(out)
        self.check_scp_file_valid_between_dut()
        self.check_meson_test_result()

    def test_debug(self):
        self.dut_pathlog = "test-debug.log"
        # delete exists files
        self.delete_exists_files()
        cmds = f'meson test -C x86_64-native-linuxapp-gcc/ --suite DPDK:debug-tests -t {self.ratio} --test-args="-c 0xff" |tee /root/{self.dut_pathlog}'
        out = self.dut.send_expect(cmds, "# ", self.execute_wait_time)
        self.logger.info(out)
        self.check_scp_file_valid_between_dut()
        self.check_meson_test_result()

    def test_extra(self):
        self.dut_pathlog = "extra-test.log"
        # delete exists files
        self.delete_exists_files()
        cmds = f'meson test -C x86_64-native-linuxapp-gcc/ --suite DPDK:extra-tests -t {self.ratio} --test-args="-c 0xff" |tee /root/{self.dut_pathlog}'
        out = self.dut.send_expect(cmds, "# ", self.execute_wait_time)
        self.logger.info(out)
        self.check_scp_file_valid_between_dut()
        self.check_meson_test_result()
        self.logger.warning(
            "Extra-tests are know issues which are recorded in DPDK commit and meson.build (detail see test plan)"
        )

    def test_perf(self):
        # init file name
        self.dut_pathlog = "perf-test.log"
        # delete exists files
        self.delete_exists_files()
        cmds = f'meson test -C x86_64-native-linuxapp-gcc/ --suite DPDK:perf-tests -t {self.ratio} --test-args="-c 0xff" |tee /root/{self.dut_pathlog}'
        out = self.dut.send_expect(cmds, "# ", self.execute_wait_time)
        self.logger.info(out)
        self.check_scp_file_valid_between_dut()
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
