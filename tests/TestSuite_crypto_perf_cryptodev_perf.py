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

import re
import json
from test_case import TestCase
import cryptodev_common as cc


class PerfTestsCryptodev(TestCase):

    def set_up_all(self):
        self._perf_result = {}
        self._default_crypto_perf_opts = {
            "ptest": "throughput",
            "silent": "",
            "pool-sz": None,
            "total-ops": "1000000",
            "burst-sz": "32",
            "buffer-sz": "64",
            "devtype": None,
            "segments-nb": None,
            "optype": "cipher-then-auth",
            "sessionless": None,
            "out-of-place": None,
            "test-file": None,
            "test-name": None,
            "cipher-algo": None,
            "cipher-op": None,
            "cipher-key-sz": None,
            "cipher-iv-sz": None,
            "auth-algo": None,
            "auth-op": None,
            "auth-key-sz": None,
            "auth-iv-sz": None,
            "aead-algo": None,
            "aead-op": None,
            "aead-key-sz": None,
            "aead-iv-sz": None,
            "aead-aad-sz": None,
            "digest-sz": None,
            "csv-friendly": None
        }
        self._app_path = self.dut.apps_name['test-crypto-perf']
        page_size = self.dut.send_expect("awk '/Hugepagesize/ {print $2}' /proc/meminfo", "# ")
        if int(page_size) == 1024 * 1024:
            self.dut.send_expect('echo 0 > /sys/kernel/mm/hugepages/hugepages-%skB/nr_hugepages' % (page_size), '# ', 5)
            self.dut.send_expect('echo 16 > /sys/kernel/mm/hugepages/hugepages-%skB/nr_hugepages' % (page_size), '# ', 5)

        if not cc.is_build_skip(self):
            cc.build_dpdk_with_cryptodev(self)

        cc.bind_qat_device(self, "vfio-pci")
        src_files = ['dep/test_aes_cbc.data', 'dep/test_aes_gcm.data']
        self.dut_file_dir = '/tmp'
        for file in src_files:
            self.dut.session.copy_file_to(file, self.dut_file_dir)

    def tear_down_all(self):
        cc.clear_dpdk_config(self)

        if not self._perf_result:
            return

        with open(self.logger.log_path + "/" + "perf_cryptodev_result.json", "w") as fv:
            json.dump(self._perf_result, fv, indent=4)

    def set_up(self):
        pass

    def tear_down(self):
        self.dut.kill_all()

    def test_verify_aesni_mb(self):
        self._run_crypto_func()

    def test_verify_qat(self):
        self._run_crypto_func()

    def test_verify_openssl_qat(self):
        self._run_crypto_func()

    def test_verify_openssl(self):
        self._run_crypto_func()

    def test_latency_qat(self):
        self._run_crypto_func()

    def test_latency_auth_qat(self):
        self._run_crypto_func()

    def test_latency_aead_qat(self):
        self._run_crypto_func()

    def test_latency_aesni_gcm(self):
        self._run_crypto_func()

    def test_latency_auth_aesni_mb(self):
        self._run_crypto_func()

    def test_latency_aesni_mb(self):
        self._run_crypto_func()

    def test_qat_aes_cbc_sha1_hmac(self):
        self._run_crypto_perf_throughput()

    def test_sw_aes_cbc_sha1_hmac(self):
        self._run_crypto_perf_throughput()

    def test_qat_aes_cbc_sha2_hmac(self):
        self._run_crypto_perf_throughput()

    def test_sw_aes_cbc_sha2_hmac(self):
        self._run_crypto_perf_throughput()

    def test_qat_aes_gcm(self):
        self._run_crypto_perf_throughput()

    def test_sw_aes_gcm(self):
        self._run_crypto_perf_throughput()

    def test_qat_encrypt_aes_docsisbpi(self):
        self._run_crypto_perf_throughput()

    def test_sw_encrypt_aes_docsisbpi(self):
        self._run_crypto_perf_throughput()

    def test_qat_decrypt_aes_docsisbpi(self):
        self._run_crypto_perf_throughput()

    def test_sw_decrypt_aes_docsisbpi(self):
        self._run_crypto_perf_throughput()

    def test_qat_kasumi(self):
        self._run_crypto_perf_throughput()

    def test_sw_kasumi(self):
        self._run_crypto_perf_throughput()

    def test_qat_snow3g(self):
        self._run_crypto_perf_throughput()

    def test_sw_snow3g(self):
        self._run_crypto_perf_throughput()

    def test_qat_zuc(self):
        self._run_crypto_perf_throughput()

    def test_sw_zuc(self):
        self._run_crypto_perf_throughput()

    def test_scheduler_aes_cbc_sha1_hmac(self):
        self._run_crypto_perf_throughput()

    def test_scheduler_aes_cbc_sha2_hmac(self):
        self._run_crypto_perf_throughput()

    def test_scheduler_aes_gcm(self):
        self._run_crypto_perf_throughput()

    def test_scheduler_kasumi(self):
        self._run_crypto_perf_throughput()

    def test_scheduler_snow3g(self):
        self._run_crypto_perf_throughput()

    def test_scheduler_zuc(self):
        self._run_crypto_perf_throughput()

    # Private functions
    def _run_crypto_func(self):
        if cc.is_test_skip(self):
            return

        cores = ','.join(self.dut.get_core_list("1S/2C/1T"))
        config = {'l': cores}
        devices = self._get_crypto_device(1)
        if not devices:
            self.logger.info("can not get device or unsupported, skip.")
            return

        config.update(devices)
        eal_opt_str = cc.get_eal_opt_str(self, config)
        crypto_func_opt_str = self._get_crypto_perf_opt_str()

        cmd_str = cc.get_dpdk_app_cmd_str(self._app_path,
                                          eal_opt_str,
                                          crypto_func_opt_str)
        try:
            self.dut.send_expect(cmd_str + ">%s/%s.txt" % (
                self.dut_file_dir, self.running_case), "#", 600)
        except Exception as ex:
            self.logger.error(ex)
            raise ex

        out = self.dut.send_command("cat %s/%s.txt" % (
            self.dut_file_dir, self.running_case), 30)

        self.verify('Error' not in out, "Test function failed")
        self.verify('failed' not in out, "Test function failed")

    def _run_crypto_perf(self):
        if cc.is_test_skip(self):
            return "skip"

        self.c_num, self.t_num = self._get_core_and_thread_num()
        devices = self._get_crypto_device(self.t_num)
        if not devices:
            self.logger.info("can not get device or unsupported, skip.")
            return "skip"

        eal_opt_str = cc.get_eal_opt_str(self, devices)
        crypto_perf_opt_str = self._get_crypto_perf_opt_str()

        cmd_str = cc.get_dpdk_app_cmd_str(self._app_path,
                                          eal_opt_str,
                                          crypto_perf_opt_str)
        try:
            out = self.dut.send_expect(cmd_str, "#", 600)
        except Exception as ex:
            self.logger.error(ex)
            raise ex

        results = self._parse_output(out)

        return results

    def _get_crypto_perf_opt_str(self, override_crypto_perf_opts={}):
        return cc.get_opt_str(self, self._default_crypto_perf_opts,
                              override_crypto_perf_opts)

    def _parse_output(self, output):
        try:
            lines = output.split("\r\n")
            line_nb = len(lines)
            self.logger.debug("Total output lines: " + str(line_nb))

            for line_index in range(line_nb):
                if lines[line_index].startswith("    lcore id"):
                    self.logger.debug("data output line from: " + str(line_index))
                    break
            data_line = line_index - 2

            results = []
            pattern = re.compile(r'\s+')
            for line in lines[data_line:-1]:
                print(line)
                result = {}
                result_list = pattern.split(line.strip(" "))
                if len(result_list) != 10 or result_list[0] == "lcore" or not result_list[0]:
                    continue
                result["lcore_id"] = int(result_list[0])
                result["buf_size"] = int(result_list[1])
                result["burst_size"] = int(result_list[2])
                result["enqueue"] = int(result_list[3])
                result["dequeue"] = int(result_list[4])
                result["enqueue_failures"] = int(result_list[5])
                result["dequeue_failures"] = int(result_list[6])
                result["mops"] = float(result_list[7])
                result["gbps"] = float(result_list[8])
                result["cycle_buf"] = float(result_list[9])
                results.append(result)

            self.logger.debug(results)
            return results
        except Exception as ex:
            self.logger.error(ex)
            return []

    def _stat_results_by_buf_size(self, results):
        stats_results = {}
        for result in results:
            buf_size = result["buf_size"]
            if buf_size in stats_results:
                stats_results[buf_size]["lcore_id"] = \
                      str(stats_results[buf_size]["lcore_id"]) \
                      + ":" + str(result["lcore_id"])
                stats_results[buf_size]["enqueue"] = \
                    stats_results[buf_size]["enqueue"] + \
                    result["enqueue"]
                stats_results[buf_size]["enqueue_failures"] = \
                    stats_results[buf_size]["enqueue_failures"] + \
                    result["enqueue_failures"]
                stats_results[buf_size]["dequeue_failures"] = \
                    stats_results[buf_size]["dequeue_failures"] + \
                    result["dequeue_failures"]
                stats_results[buf_size]["mops"] = \
                    stats_results[buf_size]["mops"] + \
                    result["mops"]
                stats_results[buf_size]["gbps"] = \
                    stats_results[buf_size]["gbps"] + \
                    result["gbps"]
                stats_results[buf_size]["cycle_buf"] = \
                    stats_results[buf_size]["cycle_buf"] + \
                    result["cycle_buf"]
                stats_results[buf_size]["nr"] = stats_results[buf_size]["nr"] + 1
            else:
                stats_results[buf_size] = result
                stats_results[buf_size]["nr"] = 1
        self.logger.debug(stats_results)
        return stats_results

    def _get_core_and_thread_num(self):
        cpu_info ={}
        out = self.dut.send_expect("lscpu", "#")
        for each_line in out.split('\n'):
            if each_line.find(':') == -1:
                continue
            key, value = each_line.split(':')
            cpu_info[key] = value.strip()
        core, thread = 0, 0
        lcores = self.get_case_cfg()["l"].split(",")
        for lcore in lcores[1:]:
            if int(lcore.strip()) < int(cpu_info['Core(s) per socket']) * int(cpu_info['Socket(s)']):
                core += 1
                thread += 1
            elif int(lcore) < int(cpu_info['CPU(s)']):
                thread += 1
        return core, thread

    def _get_crypto_device(self, num):
        device = {}
        if self.get_case_cfg()["devtype"] == "crypto_aesni_mb":
            dev = "crypto_aesni_mb"
        elif self.get_case_cfg()["devtype"] == "crypto_qat":
            w = cc.get_qat_devices(self, cpm_num=1, num=num)
            device["w"] = ' -w '.join(w)
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
        elif self.get_case_cfg()["devtype"] == "crypto_scheduler":
            dev = "crypto_scheduler"
            w = cc.get_qat_devices(self, cpm_num=3, num=num * 3)
            if not w:
                return {}
            vdev_list = []
            for i in range(num):
                vdev = "{}{},slave={}_qat_sym,slave={}_qat_sym,slave={}_qat_sym,mode=round-robin".format(dev,
                        i, w[i*3], w[i*3 + 1], w[i*3 + 2])
                vdev_list.append(vdev)
            device["w"] = ' -w '.join(w)
            device["vdev"] = ' --vdev '.join(vdev_list)
        else:
            return {}

        if not device:
            vdev_list = []
            for i in range(num):
                vdev = "{}{}".format(dev, i)
                vdev_list.append(vdev)
            device["w"] = "0000:00:00.0"
            device["vdev"] = ' --vdev '.join(vdev_list)

        return device

    def _run_crypto_perf_throughput(self):
        results = self._run_crypto_perf()
        if results == "skip":
            return
        self.verify(results, "test results is none, Test Failed")
        stats_results = self._stat_results_by_buf_size(results)
        json_result = []

        framesizes = self.get_case_cfg()['buffer-sz'].split(',')
        running_case = self.running_case
        dut = self.dut.crb["IP"]
        dut_index = self._suite_result.internals.index(dut)
        target_index = self._suite_result.internals[dut_index+1].index(self.target)
        suite_index = self._suite_result.internals[dut_index+1][target_index+2].index(self.suite_name)
        case_index = self._suite_result.internals[dut_index+1][target_index+2][suite_index+1].index(running_case)
        self._suite_result.internals[dut_index+1][target_index+2][suite_index+1].pop(case_index+1)
        self._suite_result.internals[dut_index+1][target_index+2][suite_index+1].pop(case_index)

        for buf_size in framesizes:
            buf_size = int(buf_size)
            status = "PASS"
            self._suite_result.test_case = '_'.join([running_case,
                str(buf_size), "{}C{}T".format(self.c_num, self.t_num)])
            if buf_size in stats_results.keys():
                try:
                    values = stats_results[buf_size]
                    perf_info = self.format_json(buf_size, values, status)
                    json_result.append(perf_info)

                    if perf_info['status'] == "PASS":
                        self._suite_result.test_case_passed()
                    else:
                        status = "FAIL"
                        self._suite_result.test_case_failed("Test failed")
                except Exception as ex:
                    self.logger.error(ex)
                    status = "FAIL"
                    self._suite_result.test_case_failed("Test failed")
            else:
                status = "FAIL"
                self._suite_result.test_case_failed("Test failed")

        self._perf_result[self.running_case] = json_result
        self.logger.debug(self._perf_result)
        self.verify(status == "PASS", "Test Failed")

    def format_json(self, buf_size, values, status="PASS"):
        status, delta = "PASS", 0
        # delta, status
        if 'accepted_tolerance' in self.get_suite_cfg():
            self.accepted_gap = self.get_suite_cfg()['accepted_tolerance']
            if self.running_case in self.get_suite_cfg()['expected_throughput']:
                self.expected_throughput =\
                        self.get_suite_cfg()['expected_throughput'][self.running_case][buf_size]
                delta = (values["gbps"] - self.expected_throughput)/self.expected_throughput
                delta = round(delta, 4)
            if abs(delta) > self.accepted_gap:
                self.logger.warning("Failed, buf_size: {}, delta: {}, > accepted tolerance {}"\
                        .format(buf_size, delta, self.accepted_gap))
                status = "FAIL"

        perf_info={
                "status": status,
                "performance":
                [
                    {
                        "name": "throughput",
                        "value": values["gbps"],
                        "unit": "Gbps",
                        "delta": delta
                    },
                    {
                        "name":"failed_enq",
                        "unit": "ops",
                        "value": values["enqueue_failures"]
                    },
                    {
                        "name":"failed_deq",
                        "unit": "ops",
                        "value": values["dequeue_failures"]
                    },
                    {
                        "name":"throughput_mops",
                        "unit": "Mops",
                        "value": values["mops"]
                    },
                    {
                        "name":"cycle_buf",
                        "unit": "Cycles",
                        "value": values["cycle_buf"]/values["nr"]
                    },
                ],
                "parameters":
                [
                    {
                        "name": "core_num/thread_num",
                        "unit": "C/T",
                        "value": "{}/{}".format(self.c_num, self.t_num)
                    },
                    {
                        "name":"frame_size",
                        "unit": "bytes",
                        "value": buf_size
                    },
                    {
                        "name":"burst_size",
                        "unit": "bytes",
                        "value": values["burst_size"]
                    },
                    {
                        "name":"total_ops",
                        "unit": "ops",
                        "value": values["enqueue"]
                    },
                    ]
                }
        return perf_info

