# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
A base class for creating DTF test cases.
"""
import re
import signal
import time
import traceback
from functools import wraps

import framework.debugger as debugger

from .config import SuiteConf
from .exception import TimeoutException, VerifyFailure, VerifySkip
from .logger import getLogger
from .rst import RstReport
from .settings import (
    DEBUG_CASE_SETTING,
    DEBUG_SETTING,
    DRIVERS,
    ETH_700_SERIES,
    ETH_800_SERIES,
    FUNC_SETTING,
    HOST_DRIVER_SETTING,
    NICS,
    PERF_SETTING,
    SUITE_SECTION_NAME,
    UPDATE_EXPECTED,
    get_nic_name,
    load_global_setting,
)
from .test_result import Result, ResultTable
from .utils import BLUE, RED


class TestCase(object):
    def __init__(self, duts, tester, target, suitename):
        self.suite_name = suitename
        self.dut = duts[0]
        self.duts = duts
        self.tester = tester
        self.target = target

        # local variable
        self._requested_tests = None
        self._subtitle = None

        # check session and reconnect if possible
        for dutobj in self.duts:
            self._check_and_reconnect(crb=dutobj)
        self._check_and_reconnect(crb=self.tester)

        # convert netdevice to codename
        self.nic = self.dut.nic.name
        self.nic_obj = self.dut.nic
        self.kdriver = self.dut.nic.default_driver
        self.pkg = self.dut.nic.pkg

        # result object for save suite result
        self._suite_result = Result()
        self._suite_result.dut = self.dut.crb["IP"]
        self._suite_result.target = target
        self._suite_result.nic = self.nic
        self._suite_result.test_suite = self.suite_name
        if self._suite_result is None:
            raise ValueError("Result object should not None")

        # load running environment
        if load_global_setting(PERF_SETTING) == "yes":
            self._enable_perf = True
        else:
            self._enable_perf = False

        if load_global_setting(FUNC_SETTING) == "yes":
            self._enable_func = True
        else:
            self._enable_func = False

        if load_global_setting(DEBUG_SETTING) == "yes":
            self._enable_debug = True
        else:
            self._enable_debug = False

        if load_global_setting(DEBUG_CASE_SETTING) == "yes":
            self._debug_case = True
        else:
            self._debug_case = False

        self.drivername = load_global_setting(HOST_DRIVER_SETTING)

        # create rst format report for this suite
        self._rst_obj = RstReport(
            "rst_report", target, self.nic, self.suite_name, self._enable_perf
        )

        # load suite configuration
        self._suite_conf = SuiteConf(self.suite_name)
        self._suite_cfg = self._suite_conf.suite_cfg

        # command history
        self.setup_history = list()
        self.test_history = list()

    def init_log(self):
        # get log handler
        class_name = self.__class__.__name__
        self.logger = getLogger(class_name)
        self.logger.config_suite(class_name)

    def _check_and_reconnect(self, crb=None):
        try:
            result = crb.session.check_available()
        except:
            result = False

        if result is False:
            crb.reconnect_session()
            if "dut" in str(type(crb)):
                crb.send_expect("cd %s" % crb.base_dir, "#")
                crb.set_env_variable()

        try:
            result = crb.alt_session.check_available()
        except:
            result = False

        if result is False:
            crb.reconnect_session(alt_session=True)

    def set_up_all(self):
        pass

    def set_up(self):
        pass

    def tear_down(self):
        pass

    def tear_down_all(self):
        pass

    def verify(self, passed, description):
        if not passed:
            if self._enable_debug:
                print(RED("Error happened, dump command history..."))
                self.dump_history()
                print('Error "%s" happened' % RED(description))
                print(RED("History dump finished."))
            raise VerifyFailure(description)

    def skip_case(self, passed, description):
        if not passed:
            if self._enable_debug:
                print('skip case: "%s" ' % RED(description))
            raise VerifySkip(description)

    def _get_nic_driver(self, nic_name):
        if nic_name in list(DRIVERS.keys()):
            return DRIVERS[nic_name]

        return "Unknown"

    def set_check_inst(self, check=None):
        self._check_inst = check

    def rst_report(self, *args, **kwargs):
        self._rst_obj.report(*args, **kwargs)

    def result_table_create(self, header):
        self._result_table = ResultTable(header)
        self._result_table.set_rst(self._rst_obj)
        self._result_table.set_logger(self.logger)

    def result_table_add(self, row):
        self._result_table.add_row(row)

    def result_table_print(self):
        self._result_table.table_print()

    def result_table_getrows(self):
        return self._result_table.results_table_rows

    def _get_functional_cases(self):
        """
        Get all functional test cases.
        """
        return self._get_test_cases(r"test_(?!perf_)")

    def _get_performance_cases(self):
        """
        Get all performance test cases.
        """
        return self._get_test_cases(r"test_perf_")

    def _has_it_been_requested(self, test_case, test_name_regex):
        """
        Check whether test case has been requested for validation.
        """
        name_matches = re.match(test_name_regex, test_case.__name__)

        if self._requested_tests is not None:
            return name_matches and test_case.__name__ in self._requested_tests

        return name_matches

    def set_requested_cases(self, case_list):
        """
        Pass down input cases list for check
        """
        if self._requested_tests is None:
            self._requested_tests = case_list
        elif case_list is not None:
            self._requested_tests += case_list

    def set_subtitle(self, subtitle):
        """
        Pass down subtitle for Rst report
        """
        self._rst_obj._subtitle = subtitle
        self._rst_obj.write_subtitle()

    def _get_test_cases(self, test_name_regex):
        """
        Return case list which name matched regex.
        """
        for test_case_name in dir(self):
            test_case = getattr(self, test_case_name)
            if callable(test_case) and self._has_it_been_requested(
                test_case, test_name_regex
            ):
                yield test_case

    def execute_setup_all(self):
        """
        Execute suite setup_all function before cases.
        """
        # clear all previous output
        for dutobj in self.duts:
            dutobj.get_session_output(timeout=0.1)
        self.tester.get_session_output(timeout=0.1)

        # save into setup history list
        self.enable_history(self.setup_history)

        try:
            self.set_up_all()
            return True
        except VerifySkip as v:
            self.logger.info("set_up_all SKIPPED:\n" + traceback.format_exc())
            # record all cases N/A
            if self._enable_func:
                for case_obj in self._get_functional_cases():
                    self._suite_result.test_case = case_obj.__name__
                    self._suite_result.test_case_skip(str(v))
            if self._enable_perf:
                for case_obj in self._get_performance_cases():
                    self._suite_result.test_case = case_obj.__name__
                    self._suite_result.test_case_skip(str(v))
        except Exception as v:
            self.logger.error("set_up_all failed:\n" + traceback.format_exc())
            # record all cases blocked
            if self._enable_func:
                for case_obj in self._get_functional_cases():
                    self._suite_result.test_case = case_obj.__name__
                    self._suite_result.test_case_blocked(
                        "set_up_all failed: {}".format(str(v))
                    )
            if self._enable_perf:
                for case_obj in self._get_performance_cases():
                    self._suite_result.test_case = case_obj.__name__
                    self._suite_result.test_case_blocked(
                        "set_up_all failed: {}".format(str(v))
                    )
            return False

    def _execute_test_case(self, case_obj):
        """
        Execute specified test case in specified suite. If any exception occurred in
        validation process, save the result and tear down this case.
        """
        case_name = case_obj.__name__
        self._suite_result.test_case = case_obj.__name__

        self._rst_obj.write_title("Test Case: " + case_name)

        # save into test command history
        self.test_history = list()
        self.enable_history(self.test_history)

        # load suite configuration file here for rerun command
        self._suite_conf = SuiteConf(self.suite_name)
        self._suite_cfg = self._suite_conf.suite_cfg
        self._case_cfg = self._suite_conf.load_case_config(case_name)

        case_result = True
        if self._check_inst is not None:
            if self._check_inst.case_skip(case_name[len("test_") :]):
                self.logger.info("Test Case %s Result SKIPPED:" % case_name)
                self._rst_obj.write_result("N/A")
                self._suite_result.test_case_skip(self._check_inst.comments)
                return case_result

            if not self._check_inst.case_support(case_name[len("test_") :]):
                self.logger.info("Test Case %s Result SKIPPED:" % case_name)
                self._rst_obj.write_result("N/A")
                self._suite_result.test_case_skip(self._check_inst.comments)
                return case_result

        if self._enable_perf:
            self._rst_obj.write_annex_title("Annex: " + case_name)
        try:
            self.logger.info("Test Case %s Begin" % case_name)

            self.running_case = case_name
            # clean session
            for dutobj in self.duts:
                dutobj.get_session_output(timeout=0.1)
            self.tester.get_session_output(timeout=0.1)
            # run set_up function for each case
            self.set_up()
            # run test case
            case_obj()

            self._suite_result.test_case_passed()

            self._rst_obj.write_result("PASS")
            self.logger.info("Test Case %s Result PASSED:" % case_name)

        except VerifyFailure as v:
            case_result = False
            self._suite_result.test_case_failed(str(v))
            self._rst_obj.write_result("FAIL")
            self.logger.error("Test Case %s Result FAILED: " % (case_name) + str(v))
        except VerifySkip as v:
            self._suite_result.test_case_skip(str(v))
            self._rst_obj.write_result("N/A")
            self.logger.info("Test Case %s N/A: " % (case_name))
        except KeyboardInterrupt:
            self._suite_result.test_case_blocked("Skipped")
            self.logger.error("Test Case %s SKIPPED: " % (case_name))
            self.tear_down()
            raise KeyboardInterrupt("Stop DTS")
        except TimeoutException as e:
            case_result = False
            self._rst_obj.write_result("FAIL")
            self._suite_result.test_case_failed(str(e))
            self.logger.error("Test Case %s Result FAILED: " % (case_name) + str(e))
            self.logger.error("%s" % (e.get_output()))
        except Exception:
            case_result = False
            trace = traceback.format_exc()
            self._suite_result.test_case_failed(trace)
            self.logger.error("Test Case %s Result ERROR: " % (case_name) + trace)
        finally:
            # update expected
            if (
                load_global_setting(UPDATE_EXPECTED) == "yes"
                and "update_expected" in self.get_suite_cfg()
                and self.get_suite_cfg()["update_expected"] == True
            ):
                self._suite_conf.update_case_config(SUITE_SECTION_NAME)
            self.execute_tear_down()
            return case_result

    def execute_test_cases(self):
        """
        Execute all test cases in one suite.
        """
        # prepare debugger rerun case environment
        if self._enable_debug or self._debug_case:
            debugger.AliveSuite = self
            _suite_full_name = "TestSuite_" + self.suite_name
            debugger.AliveModule = __import__(
                "tests." + _suite_full_name, fromlist=[_suite_full_name]
            )

        if load_global_setting(FUNC_SETTING) == "yes":
            for case_obj in self._get_functional_cases():
                for i in range(self.tester.re_run_time + 1):
                    ret = self.execute_test_case(case_obj)

                    if ret is False and self.tester.re_run_time:
                        for dutobj in self.duts:
                            dutobj.get_session_output(timeout=0.5 * (i + 1))
                        self.tester.get_session_output(timeout=0.5 * (i + 1))
                        time.sleep(i + 1)
                        self.logger.info(
                            " Test case %s failed and re-run %d time"
                            % (case_obj.__name__, i + 1)
                        )
                    else:
                        break

        if load_global_setting(PERF_SETTING) == "yes":
            for case_obj in self._get_performance_cases():
                self.execute_test_case(case_obj)

    def execute_test_case(self, case_obj):
        """
        Execute test case or enter into debug mode.
        """
        debugger.AliveCase = case_obj.__name__

        if self._debug_case:
            self.logger.info("Rerun Test Case %s Begin" % debugger.AliveCase)
            debugger.keyboard_handle(signal.SIGINT, None)
        else:
            return self._execute_test_case(case_obj)

    def get_result(self):
        """
        Return suite test result
        """
        return self._suite_result

    def get_case_cfg(self):
        """
        Return case based configuration
        """
        return self._case_cfg

    def get_suite_cfg(self):
        """
        Return suite based configuration
        """
        return self._suite_cfg

    def update_suite_cfg(self, suite_cfg):
        """
        Update suite based configuration
        """
        self._suite_cfg = suite_cfg

    def update_suite_cfg_ele(self, key, value):
        """
        update one element of suite configuration
        """
        self._suite_cfg[key] = value

    def execute_tear_downall(self):
        """
        execute suite tear_down_all function
        """
        try:
            self.tear_down_all()
        except Exception:
            self.logger.error("tear_down_all failed:\n" + traceback.format_exc())

        for dutobj in self.duts:
            dutobj.kill_all()
        self.tester.kill_all()

        for dutobj in self.duts:
            dutobj.virt_exit()
            # destroy all vfs
            dutobj.destroy_all_sriov_vfs()

    def execute_tear_down(self):
        """
        execute suite tear_down function
        """
        try:
            self.tear_down()
        except Exception:
            self.logger.error("tear_down failed:\n" + traceback.format_exc())
            self.logger.warning(
                "tear down %s failed, might iterfere next case's result!"
                % self.running_case
            )

    def enable_history(self, history):
        """
        Enable history for all CRB's default session
        """
        for dutobj in self.duts:
            dutobj.session.set_history(history)

        self.tester.session.set_history(history)

    def dump_history(self):
        """
        Dump recorded command history
        """
        for cmd_history in self.setup_history:
            print("%-20s: %s" % (BLUE(cmd_history["name"]), cmd_history["command"]))
        for cmd_history in self.test_history:
            print("%-20s: %s" % (BLUE(cmd_history["name"]), cmd_history["command"]))

    def wirespeed(self, nic, frame_size, num_ports):
        """
        Calculate bit rate. It is depended for NICs
        """
        bitrate = 1000.0  # 1Gb ('.0' forces to operate as float)
        if self.nic == "any" or self.nic == "cfg":
            driver = self._get_nic_driver(self.dut.ports_info[0]["type"])
            nic = get_nic_name(self.dut.ports_info[0]["type"])
        else:
            driver = self._get_nic_driver(self.nic)
            nic = self.nic

        if driver == "ixgbe":
            bitrate *= 10  # 10 Gb NICs
        elif nic == "IGB_2.5G-I354_BACKPLANE_2_5GBPS":
            bitrate *= 2.5  # 2.5 Gb NICs
        elif nic in ["I40E_40G-QSFP_A", "I40E_40G-QSFP_B"]:
            bitrate *= 40
        elif nic == "I40E_10G-SFP_X710":
            bitrate *= 10
        elif nic == "I40E_10G-SFP_X722":
            bitrate *= 10
        elif driver == "thunder-nicvf":
            bitrate *= 10
        elif nic == "I40E_25G-25G_SFP28":
            bitrate *= 25
        elif nic == "ICE_25G-E810C_SFP":
            bitrate *= 25
        elif nic == "ICE_25G-E810_XXV_SFP":
            bitrate *= 25
        elif nic == "ICE_100G-E810C_QSFP":
            bitrate *= 100

        return bitrate * num_ports / 8 / (frame_size + 20)

    def bind_nic_driver(self, ports, driver=""):
        for port in ports:
            netdev = self.dut.ports_info[port]["port"]
            driver_now = netdev.get_nic_driver()
            driver_new = driver if driver else netdev.default_driver
            if driver_new != driver_now:
                netdev.bind_driver(driver=driver_new)

    def is_eth_series_nic(self, series_num: int):
        series_nic_tuple = globals().get(f"ETH_{series_num}_SERIES")
        for series_item in series_nic_tuple:
            if series_item == self.nic:
                return True
        else:
            return False


def skip_unsupported_pkg(pkgs):
    """
    Skip case which are not supported by the input pkgs
    """
    if isinstance(pkgs, str):
        pkgs = [pkgs]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            test_case = args[0]
            pkg_type = test_case.pkg.get("type")
            pkg_version = test_case.pkg.get("version")
            if not pkg_type or not pkg_version:
                raise VerifyFailure("Failed due to pkg is empty".format(test_case.pkg))
            for pkg in pkgs:
                if pkg in pkg_type:
                    raise VerifySkip(
                        "{} {} do not support this case".format(pkg_type, pkg_version)
                    )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def skip_unsupported_nic(nics):
    """
    Skip case which are not supported by the input nics
    """
    if isinstance(nics, str):
        nics = [nics]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            test_case = args[0]
            if test_case.nic in nics:
                raise VerifySkip("{} do not support this case".format(test_case.nic))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def check_supported_nic(nics):
    """
    check if the test case is supported by the input nics
    """
    if isinstance(nics, str):
        nics = [nics]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            test_case = args[0]
            if test_case.nic not in nics:
                raise VerifySkip("{} do not support this case".format(test_case.nic))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def skip_unsupported_host_driver(drivers):
    """
    Skip case which are not supported by the host driver(vfio-pci/igb_uio etc.)
    """
    if isinstance(drivers, str):
        drivers = [drivers]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            test_case = args[0]
            if test_case.drivername in drivers:
                raise VerifySkip(
                    "{} do not support this case".format(test_case.drivername)
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator
