# BSD LICENSE
#
# Copyright(c) 2019 Intel Corporation. All rights reserved.
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


import os
from test_case import TestCase
import json
import compress_common as cc

class TestCompressdevIsalPmd(TestCase):

    def set_up_all(self):
        self.prepare_dpdk()
        cc.default_eals.update({'w': "0000:00:00.0", "vdev": "compress_isal"})
        cc.default_opts.update({"driver-name": "compress_isal"})
        self._perf_result = dict()

    def set_up(self):
        pass

    def prepare_dpdk(self):
        self.dut.send_expect(
            "sed -i 's/CONFIG_RTE_COMPRESSDEV_TEST=n$/CONFIG_RTE_COMPRESSDEV_TEST=y/' config/common_base", "# ")
        self.dut.send_expect(
            "sed -i 's/CONFIG_RTE_LIBRTE_PMD_ISAL=n$/CONFIG_RTE_LIBRTE_PMD_ISAL=y/' config/common_base", "# ")
        self.dut.build_install_dpdk(self.dut.target)

    def test_isal_pmd_unit_test(self):
        cc.run_unit(self)

    def test_isal_pmd_fixed_func(self):
        cc.default_opts.update({"huffman-enc": "fixed"})
        result = cc.run_perf(self)
        self._perf_result.update(result)

    def test_isal_pmd_dynamic_func(self):
        cc.default_opts.update({"huffman-enc": "dynamic"})
        result = cc.run_perf(self)
        self._perf_result.update(result)

    def tear_down(self):
        pass

    def tear_down_all(self):
        self.dut.kill_all()

        self.dut.send_expect(
            "sed -i 's/CONFIG_RTE_COMPRESSDEV_TEST=y$/CONFIG_RTE_COMPRESSDEV_TEST=n/' config/common_base", "# ")
        self.dut.send_expect(
            "sed -i 's/CONFIG_RTE_LIBRTE_PMD_ISAL=y$/CONFIG_RTE_LIBRTE_PMD_ISAL=n/' config/common_base", "# ")
        self.dut.build_install_dpdk(self.dut.target)

        if not self._perf_result:
            return
        with open(self.logger.log_path + "/" + self.suite_name + ".json", "w") as f:
            json.dump(self._perf_result, f, indent=4)
