# BSD LICENSE
#
# Copyright(c) 2016-2017 Intel Corporation. All rights reserved.
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

import json

import framework.utils as utils
import tests.cryptodev_common as cc
from framework.test_case import TestCase


class UnitTestsCryptodev(TestCase):

    def set_up_all(self):
        self._app_path = self.dut.apps_name['test']
        if not cc.is_build_skip(self):
            cc.build_dpdk_with_cryptodev(self)
        cc.bind_qat_device(self, "vfio-pci")

    def set_up(self):
        pass

    def tear_down(self):
        self.dut.kill_all()

    def tear_down_all(self):
        cc.clear_dpdk_config(self)

    def _get_crypto_device(self, num):
        device = {}
        if self.get_case_cfg()["devtype"] == "crypto_aesni_mb":
            dev = "crypto_aesni_mb"
        elif self.get_case_cfg()["devtype"] == "crypto_qat":
            w = cc.get_qat_devices(self, cpm_num=1, num=num)
            device["vdev"] = None
        elif self.get_case_cfg()["devtype"] == "crypto_openssl":
            dev = "crypto_openssl"
        elif self.get_case_cfg()["devtype"] == "crypto_aesni_gcm":
            dev = "crypto_aesni_gcm"
        elif self.get_case_cfg()["devtype"] == "crypto_kasumi":
            dev = "crypto_kasumi"
        elif self.get_case_cfg()["devtype"] == "crypto_snow3g":
            dev = "crypto_snow3g"
        elif self.get_case_cfg()["devtype"] == "crypto_zuc":
            dev = "crypto_zuc"
        elif self.get_case_cfg()["devtype"] == "crypto_null":
            dev = "crypto_null"
        else:
            return {}

        if not device:
            vdev_list = []
            for i in range(num):
                vdev = "{}{}".format(dev, i)
                vdev_list.append(vdev)
            device["vdev"] = ' --vdev '.join(vdev_list)

        return device

    def test_cryptodev_qat_autotest(self):
        self.__run_unit_test("cryptodev_qat_autotest")

    def test_cryptodev_qat_asym_autotest(self):
        self.__run_unit_test("cryptodev_qat_asym_autotest")

    def _test_cryptodev_qat_perftest(self):
        self.__run_unit_test("cryptodev_qat_perftest")

    def _test_cryptodev_qat_continual_perftest(self):
        self.__run_unit_test("cryptodev_qat_continual_perftest")

    def _test_cryptodev_qat_snow3g_perftest(self):
        self.__run_unit_test("cryptodev_qat_snow3g_perftest")

    def test_cryptodev_aesni_mb_autotest(self):
        self.__run_unit_test("cryptodev_aesni_mb_autotest")

    def _test_cryptodev_aesni_mb_perftest(self):
        self.__run_unit_test("cryptodev_aesni_mb_perftest")

    def test_cryptodev_aesni_gcm_autotest(self):
        self.__run_unit_test("cryptodev_aesni_gcm_autotest")

    def _test_cryptodev_aesni_gcm_perftest(self):
        self.__run_unit_test("cryptodev_aesni_gcm_perftest")

    def test_cryptodev_sw_snow3g_autotest(self):
        self.__run_unit_test("cryptodev_sw_snow3g_autotest")

    def _test_cryptodev_sw_snow3g_perftest(self):
        self.__run_unit_test("cryptodev_sw_snow3g_perftest")

    def test_cryptodev_sw_kasumi_autotest(self):
        self.__run_unit_test("cryptodev_sw_kasumi_autotest")

    def test_cryptodev_sw_zuc_autotest(self):
        self.__run_unit_test("cryptodev_sw_zuc_autotest")

    def test_cryptodev_null_autotest(self):
        self.__run_unit_test("cryptodev_null_autotest")

    def test_cryptodev_openssl_autotest(self):
        self.__run_unit_test("cryptodev_openssl_autotest")

    def _test_cryptodev_openssl_perftest(self):
        self.__run_unit_test("cryptodev_openssl_perftest")

    def test_cryptodev_scheduler_autotest(self):
        self.__run_unit_test("cryptodev_scheduler_autotest")

    def __run_unit_test(self, testsuite, timeout=600):
        devices = self._get_crypto_device(num=1)
        eal_opt_str = cc.get_eal_opt_str(self, devices)
        w = cc.get_qat_devices(self, num=1)

        self.logger.info("STEP_TEST: " + testsuite)
        self.dut.send_expect("dmesg -C", "# ", 30)
        cmd_str = cc.get_dpdk_app_cmd_str(self._app_path, eal_opt_str + " --log-level=6 -a %s" % w[0])
        self.dut.send_expect(cmd_str, "RTE>>", 30)

        out = ""
        try:
            out = self.dut.send_expect(testsuite, "RTE>>", timeout)
            self.dut.send_expect("quit", "# ", 30)
        except Exception as ex:
            self.logger.error("Cryptodev Unit Tests Exception")
            dmesg = self.dut.alt_session.send_expect("dmesg", "# ", 30)
            self.logger.error("dmesg info:")
            self.logger.error(dmesg)

        self.logger.info(out)
        self.verify("Test OK" in out, "Test Failed")
