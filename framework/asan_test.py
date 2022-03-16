import configparser
import os
import re
from contextlib import contextmanager

import xlrd

import framework.settings as settings
from framework.excel_reporter import ExcelReporter
from framework.test_result import Result

from .json_reporter import JSONReporter
from .stats_reporter import StatsReporter

ASan_CONFIG_SECT = "ASan"
ASan_FILTER_BOUNDS = "filter_bounds"
ASan_PARAM_KEY = "build_param"
ASan_CONFIG_FILE_PATH = "%s/asan.cfg" % settings.CONFIG_ROOT_PATH
COMMAND_PATTERN_OF_ADDRESS_RANDOM_SWITCH = (
    "echo %s > /proc/sys/kernel/randomize_va_space"
)
COMMAND_OF_CLOSE_ADDRESS_RANDOM = COMMAND_PATTERN_OF_ADDRESS_RANDOM_SWITCH % 0
COMMAND_OF_OPEN_ADDRESS_RANDOM = COMMAND_PATTERN_OF_ADDRESS_RANDOM_SWITCH % 2
NEW_TEST_REPORT_FILE = "asan_test_results.xls"
NEW_JSON_REPORT_FILE = "asan_test_results.json"
NEW_STATS_REPORT_FILE = "asan_statistics.txt"
ORIGIN_TEST_REPORT_FILE = "test_results.xls"
MIN_LENGTH_OF_FILTERED_OUTPUT = 50
REPORT_OUTPUT_PATH = ""


class ASanTestProcess(object):
    IS_SUPPORT_ASan_TEST = False

    @staticmethod
    def test_prepare(is_support_ASan_test, output_dir):
        if is_support_ASan_test:
            ASanTestProcess.IS_SUPPORT_ASan_TEST = True
            # use framework default or customer defined output dir
            global REPORT_OUTPUT_PATH
            REPORT_OUTPUT_PATH = output_dir
            _FrameworkADAPTER.decorator_dts_run()
            _FrameworkADAPTER.decorator_send_expect()
            _FrameworkADAPTER.decorator_build_install_dpdk()

    @staticmethod
    def test_process():
        if ASanTestProcess.IS_SUPPORT_ASan_TEST:
            report_process_obj = _NewReport()
            report_process_obj.process_report_header()
            report_process_obj.process_report_detail()
            report_process_obj.save_report()


class _FrameworkADAPTER(object):
    @staticmethod
    def decorator_build_install_dpdk():
        added_param = _ASanConfig().build_param
        if added_param is not None:
            from framework.project_dpdk import DPDKdut

            origin_func = DPDKdut.build_install_dpdk

            def new_func(*args, **kwargw):
                kwargw["extra_options"] = " ".join(
                    [kwargw.get("extra_options", ""), added_param]
                )
                origin_func(*args, **kwargw)

            DPDKdut.build_install_dpdk = new_func

    @staticmethod
    def decorator_dts_run():
        import framework.dts as dts

        origin_func = dts.dts_run_suite

        def new_func(*args, **kwargs):
            duts = args[0]
            for dut in duts:
                dut.send_expect(COMMAND_OF_CLOSE_ADDRESS_RANDOM, "#")

            origin_func(*args, **kwargs)

            for dut in duts:
                dut.send_expect(COMMAND_OF_OPEN_ADDRESS_RANDOM, "#")

        dts.dts_run_suite = new_func

    @staticmethod
    def decorator_send_expect():
        import framework.ssh_pexpect as ssh_pexpect

        origin_func = ssh_pexpect.SSHPexpect._SSHPexpect__flush

        def new_func(self):
            DELETE_CONTENT_PATTERN = r"^\s*\[?PEXPECT\]?#?\s*$"
            befored_info = re.sub(
                DELETE_CONTENT_PATTERN, "", self.session.before
            ).strip()
            if len(befored_info) > MIN_LENGTH_OF_FILTERED_OUTPUT and self.logger:
                self.logger.info(f"Buffered info: {befored_info}")
            origin_func(self)

        ssh_pexpect.SSHPexpect._SSHPexpect__flush = new_func


class _ASanConfig(object):
    def __init__(
        self,
    ):
        self.config = configparser.ConfigParser()
        self.config.read(ASan_CONFIG_FILE_PATH)
        self._filter_list = None
        self._build_params = None

    def _read_ASan_sect_conf(self, key):
        return self.config.get(ASan_CONFIG_SECT, key)

    def _set_ASan_filter(self):
        try:
            origin_filter_string = self._read_ASan_sect_conf(ASan_FILTER_BOUNDS)
            self._filter_list = [
                tuple(re.split(r":\s*", _filter))
                for _filter in re.split(r",\s*", origin_filter_string)
            ]
        except KeyError:
            self._filter_list = []

    def _set_ASan_param(self):
        try:
            param_string = self._read_ASan_sect_conf(ASan_PARAM_KEY)
        except KeyError:
            param_string = ""
        self._build_params = param_string

    @property
    def filter_list(self):
        self._set_ASan_filter()
        return self._filter_list

    @property
    def build_param(self):
        self._set_ASan_param()
        return self._build_params


class _OldExcelReport(object):
    def __init__(self):
        self._report_file = os.path.join(REPORT_OUTPUT_PATH, ORIGIN_TEST_REPORT_FILE)
        self._workbook: xlrd.Book = xlrd.open_workbook(self._report_file)
        self._sheet_obj: xlrd.sheet.Sheet = self._workbook.sheets()[0]
        self._rows = self._sheet_obj.nrows
        self.current_row_num = 0

    def generator_rows(self):
        while True:
            if self.current_row_num >= self._rows:
                raise IndexError
            row_number_of_jump_to = yield self._sheet_obj.row(self.current_row_num)
            row = (
                row_number_of_jump_to
                if row_number_of_jump_to is not None
                else self.current_row_num + 1
            )
            self.current_row_num = row


class _OldExcelReportReader(object):
    def __init__(self):
        self._old_report = _OldExcelReport()
        self._header_line_num = 1
        self._test_env_content_column = None
        self._test_suite_content_column = None
        self._gen_report_rows = self._old_report.generator_rows()
        next(self._gen_report_rows)
        self._report_content_dict = dict()
        self._current_suite = None

    def get_report_info(self):
        try:
            self._get_first_line()
            self._get_test_env()
            self._get_cases_result()
        except IndexError:
            pass
        return self._report_content_dict

    def _get_first_line(self):
        header_row_title = self._gen_report_rows.send(self._header_line_num - 1)
        header_row_content = self._gen_report_rows.send(self._header_line_num)
        cell_num = 0
        while header_row_title[cell_num].value != "Test suite":
            header_cell_title: str = header_row_title[cell_num].value
            header_cell_content = header_row_content[cell_num].value
            self._report_content_dict[
                header_cell_title.lower().replace(" ", "_")
            ] = header_cell_content
            cell_num = cell_num + 1
        self._test_env_content_column = cell_num - 1
        self._test_suite_content_column = cell_num

    @staticmethod
    def _get_value_from_cell(cells_list_of_row):
        return [cell.value for cell in cells_list_of_row]

    def _get_test_env(self):
        env_key_list = ["driver", "kdriver", "firmware", "package"]
        for env_key in env_key_list:
            env_info_row = next(self._gen_report_rows)
            env_cell_value = env_info_row[self._test_env_content_column].value
            if env_cell_value:
                env_value = env_cell_value.split(": ")[1]
                self._report_content_dict[env_key] = env_value
            else:
                self._report_content_dict[env_key] = None
                # back to previous line
                self._gen_report_rows.send(self._old_report.current_row_num - 1)

    def _get_cases_result(self):
        for row_cells in self._gen_report_rows:
            suite_content_column_begin = self._test_suite_content_column
            suite_content_column_end = self._test_suite_content_column + 3
            suite_name, case_name, original_result_msg = self._get_value_from_cell(
                row_cells[suite_content_column_begin:suite_content_column_end]
            )
            EMPTY_LINE_CONDITION = not suite_name and not case_name
            NO_CASE_LINE_CONDITION = not case_name
            SUITE_BEGIN_LINE_CONDITON = suite_name
            if EMPTY_LINE_CONDITION or NO_CASE_LINE_CONDITION:
                continue

            if SUITE_BEGIN_LINE_CONDITON:
                self._add_suite_info(suite_name)

            self._add_case_info(case_name, original_result_msg)

    def _add_suite_info(self, _suite):
        self._report_content_dict.setdefault(_suite, dict())
        self._current_suite = _suite

    def _add_case_info(self, _case, _result_msg):
        self._report_content_dict.get(self._current_suite)[_case] = _result_msg


class _SuiteLogReader(object):
    def __init__(self, suite_name):
        self._suite_name = suite_name

    @contextmanager
    def suite_log_file(self):
        from framework.test_case import TestCase
        from framework.utils import get_subclasses

        suite_full_name = "TestSuite_" + self._suite_name
        suite_module = __import__(
            "tests." + suite_full_name, fromlist=[suite_full_name]
        )
        suite_class_name = [
            test_case_name
            for test_case_name, _ in get_subclasses(suite_module, TestCase)
        ][0]
        log_file_path = os.path.join(REPORT_OUTPUT_PATH, suite_class_name)
        log_file_obj = open(log_file_path + ".log", "r")
        yield log_file_obj
        log_file_obj.close()


class _NewReport(object):
    def __init__(self):
        self._excel_report_file = os.path.join(REPORT_OUTPUT_PATH, NEW_TEST_REPORT_FILE)
        self._json_report_file = os.path.join(REPORT_OUTPUT_PATH, NEW_JSON_REPORT_FILE)
        self._stats_report_file = os.path.join(
            REPORT_OUTPUT_PATH, NEW_STATS_REPORT_FILE
        )
        self._remove_history_asan_report()
        self._excel_report = ExcelReporter(self._excel_report_file)
        self._json_report = JSONReporter(self._json_report_file)
        self._stats_report = StatsReporter(self._stats_report_file)
        self._result_obj = Result()
        self._old_report_reader = _OldExcelReportReader()
        self._old_report_content: dict = self._old_report_reader.get_report_info()
        self._new_suites_result = dict()
        self._ASan_filter = _ASanConfig().filter_list
        self._current_case = None
        self._current_suite = None
        self._filtered_line_cache = []
        self._filter_begin = None
        self._filter_end = None

    def process_report_header(self):
        head_key_list = [
            "dut",
            "kdriver",
            "firmware",
            "package",
            "driver",
            "dpdk_version",
            "target",
            "nic",
        ]
        for head_key in head_key_list:
            head_value = self._old_report_content.setdefault(head_key, None)
            self._old_report_content.pop(head_key)
            setattr(self._result_obj, head_key, head_value)

    def process_report_detail(self):
        for suite in self._old_report_content.keys():
            self._get_suite_new_result(suite)
            self._parse_suite_result_to_result_obj()

    def _get_suite_new_result(self, suite):
        suite_log_reader = _SuiteLogReader(suite)
        self._current_suite = suite
        gen_suite_lines = suite_log_reader.suite_log_file()
        self._get_case_result(gen_suite_lines)

    def _parse_suite_result_to_result_obj(self):
        self._result_obj.test_suite = self._current_suite
        for case in self._old_report_content[self._current_suite]:
            self._result_obj.test_case = case
            if case in self._new_suites_result:
                self._result_obj._Result__set_test_case_result(
                    *self._new_suites_result[case]
                )
            else:
                origin_result = self._get_origin_case_result(case)
                self._result_obj._Result__set_test_case_result(*origin_result)

    def save_report(self):
        for report in (self._excel_report, self._json_report, self._stats_report):
            report.save(self._result_obj)

    def _remove_history_asan_report(self):
        for file in (
            self._excel_report_file,
            self._json_report_file,
            self._stats_report_file,
        ):
            if os.path.exists(file):
                os.remove(file)

    def _get_origin_case_result(self, case_name):
        origin_cases_result: dict = self._old_report_content.get(self._current_suite)
        origin_case_result: str = origin_cases_result.get(case_name)
        CASE_RESULT_AND_MSG_PATTERN = r"(\S+)\s?(.*)"
        result, msg = re.search(
            CASE_RESULT_AND_MSG_PATTERN, origin_case_result
        ).groups()
        if msg:
            msg = msg.replace("'", "").replace('"', "")

        return result, msg

    def _get_case_result(self, suite_log_reader):
        with suite_log_reader as log_file:
            for line in log_file:
                self._filter_asan_except(line)

            self._log_file_end_handler()

    def _filter_asan_except(self, line):
        CASE_LOG_BEGIN_PATTERN = r"Test Case test_(\w+) Begin"
        case_begin_match = re.search(CASE_LOG_BEGIN_PATTERN, line)

        if case_begin_match:
            case_name = case_begin_match.groups()[0]
            self._case_begin_handler(case_name)
            return

        for filter_tuple in self._ASan_filter:
            begin_filter, end_filter = filter_tuple
            if begin_filter in line:
                self._filter_matched_begin_handler(begin_filter, line)
                return

            if self._filter_begin is not None:
                self._filter_matched_line_handler(line)
                return

            if end_filter in line:
                self._filter_matched_end_handler(end_filter, line)
                return

    def _case_begin_handler(self, case_name):
        self._save_previous_case_result_and_clean_env()
        self._current_case = case_name

    def _filter_matched_begin_handler(self, begin_key, line):
        self._filter_begin = begin_key
        self._filtered_line_cache.append(line)

    def _filter_matched_line_handler(self, line):
        self._filtered_line_cache.append(line)

    def _filter_matched_end_handler(self, end_key, line):
        self._filtered_line_cache.append(line)
        self._filter_begin = end_key

    def _log_file_end_handler(self):
        self._save_previous_case_result_and_clean_env()

    def _save_previous_case_result_and_clean_env(self):
        exist_previous_case_condition = self._current_case is not None
        origin_report_contain_previous_case_result = (
            self._current_case in self._old_report_content.get(self._current_suite)
        )

        if exist_previous_case_condition and origin_report_contain_previous_case_result:
            self._save_case_result()

        self._filtered_line_cache.clear()
        self._filter_begin = None
        self._filter_end = None

    def _save_case_result(self):
        cached_content = self._get_filtered_cached_result()
        if self._current_case in self._new_suites_result:
            # Run multiple times and keep the last result
            self._new_suites_result.pop(self._current_case)

        if cached_content:
            # filter hit scene
            self._new_suites_result[self._current_case] = ("FAILED", cached_content)
        else:
            # filter not hit scene
            self._new_suites_result[self._current_case] = self._get_origin_case_result(
                self._current_case
            )

    def _get_filtered_cached_result(self):
        ASan_FILTER_CONTENT_PATTERN = (
            rf"{self._filter_begin}[\s\S]+(?!{self._filter_end})?"
        )
        key_search_result = re.findall(
            ASan_FILTER_CONTENT_PATTERN, "".join(self._filtered_line_cache)
        )

        return key_search_result[0] if key_search_result else ""
