# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

import copy
import json
import os

import tests.compress_common as cc
from framework.test_case import TestCase


class TestCompressdevQatPmd(TestCase):
    def set_up_all(self):
        cc.bind_qat_device(self, self.drivername)
        cc.default_eals.update({"vdev": None})
        cc.default_opts.update({"driver-name": "compress_qat"})
        self.device_list = cc.get_qat_device_list(self)
        self._perf_result = dict()
        self.eals = copy.deepcopy(cc.default_eals)
        self.opts = copy.deepcopy(cc.default_opts)

    def set_up(self):
        cc.default_eals = copy.deepcopy(self.eals)
        cc.default_opts = copy.deepcopy(self.opts)

    def get_perf_default_device(self, dev_num=3):
        perf_device_list = []
        for each in self.device_list:
            if each.endswith("01.0"):
                perf_device_list.append(each)
        if len(perf_device_list) < dev_num:
            perf_device_list += list(
                set(self.device_list).difference(set(perf_device_list))
            )[: dev_num - len(perf_device_list)]
        else:
            perf_device_list = perf_device_list[:dev_num]

        return perf_device_list

    def test_qat_pmd_unit_test(self):
        cc.default_eals["a"] = self.device_list[0]
        cc.run_unit(self)

    def test_qat_pmd_fixed_func(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update({"huffman-enc": "fixed"})
        result = cc.run_compress_func(self)

    def test_qat_pmd_dynamic_func(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update({"huffman-enc": "dynamic"})
        result = cc.run_compress_func(self)

    def test_qat_pmd_big_sgl_fixed_func(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update(
            {
                "huffman-enc": "fixed",
                "seg-sz": 1024,
                "extended-input-sz": 1048576,
                "max-num-sgl-segs": 1003,
            }
        )
        result = cc.run_compress_func(self)

    def test_qat_pmd_big_sgl_dynamic_func(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update(
            {
                "huffman-enc": "dynamic",
                "seg-sz": 1024,
                "extended-input-sz": 1048576,
                "max-num-sgl-segs": 1003,
            }
        )
        result = cc.run_compress_func(self)

    def test_qat_pmd_big_seg_fixed_func(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update(
            {
                "huffman-enc": "fixed",
                "seg-sz": 59460,
                "extended-input-sz": 1048576,
                "max-num-sgl-segs": 18,
            }
        )
        result = cc.run_compress_func(self)

    def test_qat_pmd_big_seg_dynamic_func(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update(
            {
                "huffman-enc": "dynamic",
                "seg-sz": 59460,
                "extended-input-sz": 1048576,
                "max-num-sgl-segs": 18,
            }
        )
        result = cc.run_compress_func(self)

    def test_qat_pmd_external_mbufs_fixed_func(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update(
            {
                "huffman-enc": "fixed",
                "max-num-sgl-segs": 16,
                "seg-sz": 2048,
                "external-mbufs": "",
                "extended-input-sz": 300000,
            }
        )
        result = cc.run_compress_func(self)

    def test_qat_pmd_external_mbufs_dynamic_func(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update(
            {
                "huffman-enc": "dynamic",
                "max-num-sgl-segs": 16,
                "seg-sz": 2048,
                "external-mbufs": "",
                "extended-input-sz": 300000,
            }
        )
        result = cc.run_compress_func(self)

    def test_qat_pmd_im_fixed_func(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update(
            {
                "huffman-enc": "fixed",
                "seg-sz": 59460,
                "max-num-sgl-segs": 54,
                "extended-input-sz": 3251493,
            }
        )
        result = cc.run_compress_func(self)

    def test_qat_pmd_im_dynamic_func(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update(
            {
                "huffman-enc": "dynamic",
                "seg-sz": 59460,
                "max-num-sgl-segs": 54,
                "extended-input-sz": 3251493,
            }
        )
        result = cc.run_compress_func(self)

    def test_qat_pmd_fixed_perf(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
        cc.default_opts.update(
            {
                "huffman-enc": "fixed",
                "extended-input-sz": 3244032,
                "max-num-sgl-segs": 1,
            }
        )
        result = cc.run_compress_perf(self)
        self._perf_result.update(result)

    def test_qat_pmd_dynamic_perf(self):
        cc.default_eals["a"] = " -a ".join(self.get_perf_default_device())
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
            with open(
                self.logger.log_path + "/" + self.suite_name + ".json", "a"
            ) as fv:
                json.dump(self._perf_result, fv, indent=4)
