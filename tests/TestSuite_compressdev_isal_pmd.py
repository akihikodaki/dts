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


import copy
import json
import os

import tests.compress_common as cc
from framework.test_case import TestCase


class TestCompressdevIsalPmd(TestCase):

    def set_up_all(self):
        cc.default_eals.update({'a': "0000:00:00.0", "vdev": "compress_isal"})
        cc.default_opts.update({"driver-name": "compress_isal"})
        self._perf_result = dict()
        self.eals = copy.deepcopy(cc.default_eals)
        self.opts = copy.deepcopy(cc.default_opts)

    def set_up(self):
        cc.default_eals = copy.deepcopy(self.eals)
        cc.default_opts = copy.deepcopy(self.opts)

    def test_isal_pmd_unit_test(self):
        cc.run_unit(self)

    def test_isal_pmd_fixed_func(self):
        cc.default_opts.update({"huffman-enc": "fixed"})
        result = cc.run_compress_func(self)

    def test_isal_pmd_dynamic_func(self):
        cc.default_opts.update({"huffman-enc": "dynamic"})
        result = cc.run_compress_func(self)

    def test_isal_pmd_fixed_perf(self):
        cc.default_opts.update({"huffman-enc": "fixed", "extended-input-sz": 3244032,
            "max-num-sgl-segs": 1})
        result = cc.run_compress_perf(self)
        self._perf_result.update(result)

    def test_isal_pmd_dynamic_perf(self):
        cc.default_opts.update({"huffman-enc": "dynamic", "extended-input-sz": 3244032,
            "max-num-sgl-segs": 1})
        result = cc.run_compress_perf(self)
        self._perf_result.update(result)

    def tear_down(self):
        pass

    def tear_down_all(self):
        self.dut.kill_all()
        if self._perf_result:
            with open(self.logger.log_path + "/" + self.suite_name + ".json", "a") as f:
                json.dump(self._perf_result, f, indent=4)

