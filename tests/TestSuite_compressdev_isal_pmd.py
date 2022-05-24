# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

import copy
import json
import os

import tests.compress_common as cc
from framework.test_case import TestCase


class TestCompressdevIsalPmd(TestCase):
    def set_up_all(self):
        cc.default_eals.update({"a": "0000:00:00.0", "vdev": "compress_isal"})
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
        cc.default_opts.update(
            {
                "huffman-enc": "fixed",
                "extended-input-sz": 3244032,
                "max-num-sgl-segs": 1,
            }
        )
        result = cc.run_compress_perf(self)
        self._perf_result.update(result)

    def test_isal_pmd_dynamic_perf(self):
        cc.default_opts.update(
            {
                "huffman-enc": "dynamic",
                "extended-input-sz": 3244032,
                "max-num-sgl-segs": 1,
            }
        )
        result = cc.run_compress_perf(self)
        self._perf_result.update(result)

    def tear_down(self):
        pass

    def tear_down_all(self):
        self.dut.kill_all()
        if self._perf_result:
            with open(self.logger.log_path + "/" + self.suite_name + ".json", "a") as f:
                json.dump(self._perf_result, f, indent=4)
