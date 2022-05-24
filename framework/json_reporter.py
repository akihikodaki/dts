# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2017 Linaro
#

import json


class JSONReporter(object):
    def __init__(self, filename):
        self.filename = filename

    def __scan_cases(self, result, dut, target, suite):
        case_results = {}
        for case in result.all_test_cases(dut, target, suite):
            test_result = result.result_for(dut, target, suite, case)
            case_name = "{}/{}".format(suite, case)
            case_results[case_name] = test_result
            if "PASSED" in test_result:
                case_results[case_name] = "passed"
            elif "N/A" in test_result:
                case_results[case_name] = "n/a"
            elif "FAILED" in test_result:
                case_results[case_name] = "failed"
            elif "BLOCKED" in test_result:
                case_results[case_name] = "blocked"
        return case_results

    def __scan_target(self, result, dut, target):
        if result.is_target_failed(dut, target):
            return "fail"
        case_results = {}
        for suite in result.all_test_suites(dut, target):
            case_results.update(self.__scan_cases(result, dut, target, suite))
        return case_results

    def __scan_dut(self, result, dut):
        if result.is_dut_failed(dut):
            return "fail"
        target_map = {}
        target_map["dpdk_version"] = result.current_dpdk_version(dut)
        target_map["nic"] = {}
        for target in result.all_targets(dut):
            target_map["nic"]["name"] = result.current_nic(dut, target)
            target_map[target] = self.__scan_target(result, dut, target)
            target_map["nic"]["kdriver"] = result.current_kdriver(dut)
            target_map["nic"]["driver"] = result.current_driver(dut)
            target_map["nic"]["firmware"] = result.current_firmware_version(dut)
            if result.current_package_version(dut) is not None:
                target_map["nic"]["pkg"] = result.current_package_version(dut)
        return target_map

    def save(self, result):
        result_map = {}
        for dut in result.all_duts():
            result_map[dut] = self.__scan_dut(result, dut)
        with open(self.filename, "w") as outfile:
            json.dump(
                result_map, outfile, indent=4, separators=(",", ": "), sort_keys=True
            )
