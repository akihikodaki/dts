# BSD LICENSE
#
# Copyright (c) <2019> Intel Corporation
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


import re

import framework.utils as utils
import tests.cryptodev_common as cc
from framework.test_case import TestCase


class FipCryptodev(TestCase):
    def set_up_all(self):
        out = self.dut.build_dpdk_apps("./examples/fips_validation")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")
        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        cc.bind_qat_device(self, "vfio-pci")
        self._app_path = self.dut.apps_name["fips_validation"]
        self._default_fips_opts = {
            "req-file": None,
            "rsp-file": None,
            "cryptodev": None,
            "path-is-folder": "",
            "cryptodev-id": 0,
            "self-test": "",
        }
        self.FIP_path = "/root/FIPS"

    def set_up(self):
        pass

    def tear_down(self):
        self.dut.kill_all()

    def tear_down_all(self):
        pass

    # Private functions
    def _get_fips_opt_str(self):
        return cc.get_opt_str(self, self._default_fips_opts, {})

    def _run_fips(self, eal_opt_str, fips_opt_str):
        cmd_str = cc.get_dpdk_app_cmd_str(self._app_path, eal_opt_str, fips_opt_str)
        self.logger.info(cmd_str)
        try:
            out = self.dut.send_expect(cmd_str, "#", 600)
        except Exception as ex:
            self.logger.error(ex)
            raise ex
        return out

    def compare_resp_file(self, eal_opt_str, fips_opt_str):
        out = self._run_fips(eal_opt_str, fips_opt_str)
        check_out = out[out.index("Done") :]
        self.verify("Error" not in check_out, " req file error")
        rep_list = re.findall(r"FIPS/(.*)/req/(.*).req", out)

        for alog_name, file_name in rep_list:
            out = self.dut.send_expect(
                "diff %s/%s/resp/%s.rsp %s/%s/fax/%s.rsp | grep -v '#' | grep -v '\---'"
                % (
                    self.FIP_path,
                    alog_name,
                    file_name,
                    self.FIP_path,
                    alog_name,
                    file_name,
                ),
                "#",
            )
            lines = re.split("\r\n", out)
            self.verify(len(lines) <= 2, "%s.req file comparison failed!" % file_name)

    def test_fips_aesni_mb_aes(self):
        eal_opt_str = cc.get_eal_opt_str(self)
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_aesni_mb_3des(self):
        eal_opt_str = cc.get_eal_opt_str(self)
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_aesni_mb_hmac(self):
        eal_opt_str = cc.get_eal_opt_str(self)
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_aesni_mb_ccm(self):
        eal_opt_str = cc.get_eal_opt_str(self)
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_aesni_mb_cmac(self):
        eal_opt_str = cc.get_eal_opt_str(self)
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_qat_gcm(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": None})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_qat_aes(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": None})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_qat_3des(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": None})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_qat_hmac(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": None})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_qat_ccm(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": None})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_qat_cmac(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": None})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_openssl_gcm(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": "crypto_openssl_pmd_1"})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_openssl_aes(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": "crypto_openssl_pmd_1"})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_openssl_3des(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": "crypto_openssl_pmd_1"})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_openssl_hmac(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": "crypto_openssl_pmd_1"})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_openssl_ccm(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": "crypto_openssl_pmd_1"})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_aesni_gcm_gcm(self):
        eal_opt_str = cc.get_eal_opt_str(self, {"vdev": "crypto_aesni_gcm_pmd_1"})
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_self_test(self):
        eal_opt_str = cc.get_eal_opt_str(
            self,
            {
                "l": None,
                "n": None,
            },
        )
        fips_opt_str = self._get_fips_opt_str()
        self.compare_resp_file(eal_opt_str, fips_opt_str)

    def test_fips_broken_test(self):
        eal_opt_str = cc.get_eal_opt_str(
            self,
            {
                "l": None,
                "n": None,
            },
        )
        fips_opt_str = cc.get_opt_str(
            self,
            self._default_fips_opts,
            {"cryptodev-id": None, "broken-test-id": 15, "broken-test-dir": "dec"},
        )
        out = self._run_fips(eal_opt_str, fips_opt_str)
        self.verify("Failed init" in out, "test Failed!")
