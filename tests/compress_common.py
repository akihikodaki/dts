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
import re
import utils
from config import SuiteConf

conf = SuiteConf('compressdev_sample')

default_opts = {
        "driver-name": None,
        "seg-sz": 2048,
        "burst-sz": None,
        "compress-level": "1:1:9",
        "extended-input-sz": None,
        "num-iter": 10,
        "max-num-sgl-segs": 16,
        "external-mbufs": None,
        "huffman-enc": "dynamic",
        "ptest": None,
        "pool-sz": None
        }

default_eals = {
        "l": "0-6",
        "c": None,
        "n": None,
        "w": None,
        "vdev": None
        }


def get_qat_device_list(test_case):
    device_id = conf.suite_cfg["qat_device_id"]
    out = test_case.dut.send_expect("lspci -d:{}|awk '{{print $1}}'".format(device_id), "# ", 10)
    device_list = out.replace("\r", "\n").replace("\n\n", "\n").split("\n")

    return device_list

def bind_qat_device(test_case, driver = "igb_uio"):
    if driver == 'vfio-pci':
        test_case.dut.send_expect('modprobe vfio-pci', '#', 10)
    else:
        driver = 'igb_uio'

    # Bind QAT VF devices
    device_list = get_qat_device_list(test_case)
    device_id = conf.suite_cfg["qat_device_id"]

    test_case.dut.send_expect(
        'echo "8086 {}" > /sys/bus/pci/drivers/{}/new_id'.format(device_id, driver), "# ", 10)
    for line in device_list:
        cmd = "echo 0000:{} > /sys/bus/pci/devices/0000\:{}/driver/unbind".format(
            line, line.replace(":", "\:"))
        test_case.dut.send_expect(cmd, "# ", 10)
        cmd = "echo 0000:{} > /sys/bus/pci/drivers/{}/bind".format(
            line, driver)
        test_case.dut.send_expect(cmd, "# ", 10)

def get_opt_str(test_case, default_opts={}, override_opts={}):
    case_cfg = conf.load_case_config(test_case._suite_result.test_case)
    opts = default_opts.copy()
    for key in default_opts.keys():
        if key in case_cfg:
            opts[key] = case_cfg[key]

    opts.update(override_opts)

    opt_str = ""
    for key,value in opts.items():
        if value is None:
            continue
        dash = "-" if len(key) == 1 else "--"
        opt_str = opt_str + "{0}{1} {2} ".format(dash, key, value)

    return opt_str

def get_input_file(test_case):
    case_cfg = conf.load_case_config(test_case._suite_result.test_case)
    input_file =  conf.suite_cfg["input-file"]
    out = test_case.dut.send_expect("ls %s" % input_file, "# ", 10)
    if out == input_file:
        file_list = [input_file]
    else:
        file_list = [os.path.join(input_file, x.strip()) for x in out.split()]

    return file_list

def run_unit(test_case, eal={}):
    cores = test_case.dut.get_core_list('1S/3C/1T')
    core_mask = utils.create_mask(cores)
    mem_channels = test_case.dut.get_memory_channels()

    default = default_eals.copy()
    default['l'] = None
    default['c'] = core_mask
    default['n'] = mem_channels

    eal_str = get_opt_str(test_case, default, eal)
    cmdline = "./{target}/app/test {eal}".format(target = test_case.dut.target,
                eal = eal_str)
    test_case.dut.send_expect(cmdline, ">", 30)
    out = test_case.dut.send_expect("compressdev_autotest", ">", 30)
    test_case.dut.send_expect("quit", "# ", 30)
    print(out)

    test_case.verify("Test OK" in out, "Test Failed")

def run_perf(test_case, eal={}, opt={}):
    eal_str = get_opt_str(test_case, default_eals, eal)
    opt_str = get_opt_str(test_case, default_opts, opt)
    input_file = get_input_file(test_case)

    result = {}
    for each_file in input_file:
        test_case.logger.info("Testing file: {}".format(each_file))

        cmdline = "./{target}/app/dpdk-test-compress-perf {eal}\
                -- --input-file {file} {opt}"

        cmdline = cmdline.format(target = test_case.dut.target,
                eal = eal_str,
                file = each_file,
                opt = opt_str)

        out = test_case.dut.send_expect(cmdline, "# ", 300)
        test_case.verify("failed" not in out and "FATAL" not in out,
                "Test Failed: Parameter or the value error")

        case_name = test_case._suite_result.test_case
        res = format_perf_data(case_name, out)
        test_case.verify(res, "Test Failed: can't get performance data")

        file_name = os.path.basename(each_file).split('.')[0]
        result.update({case_name + '_' + file_name: res})

    return result

def parse_perf_output(output):
    try:
        lines = output.split("\r\n")
        line_nb = len(lines)

        # Find perf data line
        for line_index in range(line_nb):
            if lines[line_index].strip().startswith("lcore:"):
                break
        data_line = line_index + 1

        results = []
        pattern = re.compile(r'\s+')
        for line in lines[data_line:]:
            result = {}
            result_list = pattern.split(line.strip())
            if not result_list[0].isdigit():
                continue
            print(line)
            result["lcore_id"] = int(result_list[0])
            result["level"] = int(result_list[1])
            result["comp_size"] = int(result_list[2])
            result["comp_ratio"] = float(result_list[3])
            result["comp"] = float(result_list[4])
            result["decomp"] = float(result_list[5])
            results.append(result)

        stats_results = _stat_results_by_level(results)
        return stats_results
    except Exception as ex:
        raise ex

def _stat_results_by_level(results):
    stats_results = {}
    for result in results:
        level = result["level"]
        if level in stats_results:
            stats_results[level]["lcore_id"] = \
                    str(stats_results[level]["lcore_id"]) \
                    + "," + str(result["lcore_id"])
            stats_results[level]["comp_size"] = \
                    stats_results[level]["comp_size"] + \
                    result["comp_size"]
            stats_results[level]["comp_ratio"] = \
                    stats_results[level]["comp_ratio"] + \
                    result["comp_ratio"]
            stats_results[level]["comp"] = \
                    stats_results[level]["comp"] + \
                    result["comp"]
            stats_results[level]["decomp"] = \
                    stats_results[level]["decomp"] + \
                    result["decomp"]
            stats_results[level]["nr"] =\
                    stats_results[level]["nr"] + 1
        else:
            stats_results[level] = result
            stats_results[level]["nr"] = 1

    return stats_results

def format_perf_data(flag, output):
    stats_results = parse_perf_output(output)

    json_result = []
    for level, values in stats_results.items():
        status, delta = "PASS", 0
        try:
            if 'accepted_tolerance' in  conf.suite_cfg:
                accepted_gap =  conf.suite_cfg['accepted_tolerance']
                expected_throughput =\
                conf.suite_cfg['expected_throughput'][flag][level]
                delta = (values["comp"] - expected_throughput)/expected_throughput
                if abs(delta) > accepted_gap:
                    status = "FAIL"

            perf_info={
                    "status": status,
                    "performance":[
                        {
                            "name": "comp",
                            "value": round(values["comp"], 2),
                            "unit": "Gbps",
                            "delta": round(delta, 2)
                        },
                        {
                            "name":"decomp",
                            "unit": "Gbps",
                            "value": round(values["decomp"], 2)
                        },
                        {
                            "name":"comp_size",
                            "unit": "bytes",
                            "value": values["comp_size"]
                        },
                        {
                            "name":"comp_ratio",
                            "unit": "%",
                            "value": round(values["comp_ratio"]/values["nr"], 2)
                        },
                    ],
                    "parameters":[
                        {
                            "name": "level",
                            "unit": "",
                            "value": level
                        },
                        {
                            "name": "core_num",
                            "unit": "core",
                            "value": values["nr"]
                        },
                    ]
                }
            json_result.append(perf_info)
        except Exception as err:
            print(err)
    return json_result
