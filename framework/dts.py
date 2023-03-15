# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

import atexit  # register callback when exit
import configparser  # config parse module
import copy  # copy module for duplicate variable
import imp
import inspect  # load attribute
import json  # json format
import logging
import os  # operation system module
import re  # regular expressions module
import signal  # signal module for debug mode
import sys  # system module
import time  # time module for unique output folder
import traceback  # exception traceback

import framework.debugger as debugger
import framework.logger as logger
import framework.rst as rst  # rst file support
import framework.settings as settings  # dts settings
from framework.asan_test import ASanTestProcess

from .checkCase import CheckCase
from .config import CrbsConf
from .dut import Dut
from .excel_reporter import ExcelReporter
from .exception import ConfigParseException, TimeoutException, VerifyFailure
from .json_reporter import JSONReporter
from .logger import getLogger
from .serializer import Serializer
from .stats_reporter import StatsReporter
from .test_case import TestCase
from .test_result import Result
from .tester import Tester
from .utils import (
    check_dts_python_version,
    copy_instance_attr,
    create_parallel_locks,
    get_subclasses,
)

imp.reload(sys)

requested_tests = None
result: Result = None
excel_report = None
json_report = None
stats_report = None
log_handler = None


def dts_parse_param(config, section, log_handler):
    """
    Parse execution file parameters.
    """
    # default value
    performance = False
    functional = False
    # Set parameters
    shared_lib_parameters = ""
    try:
        shared_lib_parameters = config.get(section, "shared_lib_param")
    except Exception as e:
        shared_lib_parameters = ""
    shared_lib_parameters = shared_lib_parameters.split(":")

    parameters = config.get(section, "parameters").split(":")
    drivername = config.get(section, "drivername").split("=")[-1]

    driver = drivername.split(":")
    if len(driver) == 2:
        drivername = driver[0]
        drivermode = driver[1]
        settings.save_global_setting(settings.HOST_DRIVER_MODE_SETTING, drivermode)
    else:
        drivername = driver[0]

    settings.save_global_setting(settings.HOST_DRIVER_SETTING, drivername)

    shared_lib_paramDict = dict()
    for param in shared_lib_parameters:
        (key, _, value) = param.partition("=")
        shared_lib_paramDict[key] = value
    if (
        "use_shared_lib" in shared_lib_paramDict
        and shared_lib_paramDict["use_shared_lib"].lower() == "true"
    ):
        settings.save_global_setting(settings.HOST_SHARED_LIB_SETTING, "true")
    else:
        settings.save_global_setting(settings.HOST_SHARED_LIB_SETTING, "false")

    if "shared_lib_path" in shared_lib_paramDict:
        if not shared_lib_paramDict["shared_lib_path"] and settings.load_global_setting(
            settings.HOST_SHARED_LIB_SETTING
        ):
            raise ValueError("use shared lib but shared lib path is empty")
        settings.save_global_setting(
            settings.HOST_SHARED_LIB_PATH, shared_lib_paramDict["shared_lib_path"]
        )

    paramDict = dict()
    for param in parameters:
        (key, _, value) = param.partition("=")
        paramDict[key] = value

    if "perf" in paramDict and paramDict["perf"] == "true":
        performance = True
    if "func" in paramDict and paramDict["func"] == "true":
        functional = True

    if "nic_type" not in paramDict:
        paramDict["nic_type"] = "any"

    settings.save_global_setting(settings.HOST_NIC_SETTING, paramDict["nic_type"])

    # save perf/function setting in environment
    if performance:
        settings.save_global_setting(settings.PERF_SETTING, "yes")
    else:
        settings.save_global_setting(settings.PERF_SETTING, "no")

    if functional:
        settings.save_global_setting(settings.FUNC_SETTING, "yes")
    else:
        settings.save_global_setting(settings.FUNC_SETTING, "no")


def dts_parse_config(config, section):
    """
    Parse execution file configuration.
    """
    duts = [dut_.strip() for dut_ in config.get(section, "crbs").split(",")]
    targets = [target.strip() for target in config.get(section, "targets").split(",")]
    test_suites = [
        suite.strip() for suite in config.get(section, "test_suites").split(",")
    ]
    try:
        rx_mode = config.get(section, "rx_mode").strip().lower()
    except:
        rx_mode = "default"

    try:
        dcf_mode = config.get(section, "dcf_mode").strip().lower()
    except:
        dcf_mode = ""

    settings.save_global_setting(settings.DPDK_RXMODE_SETTING, rx_mode)
    settings.save_global_setting(settings.DPDK_DCFMODE_SETTING, dcf_mode)

    suite_list_dedup = {}
    ## suite_list_dedup[suite_name] := { True | Set | ... }
    ## True := All Cases to Run
    ## Set := Listed Cases to Run
    for suite in test_suites:
        if suite == "":
            pass
        elif ":" in suite:
            suite_name = suite[: suite.find(":")]
            case_list_str = suite[suite.find(":") + 1 :]
            case_list = case_list_str.split("\\")
            if not suite_name in suite_list_dedup:
                suite_list_dedup[suite_name] = set()
            if isinstance(suite_list_dedup[suite_name], set):
                suite_list_dedup[suite_name].update(case_list)
            elif suite_list_dedup[suite_name] == True:
                pass
        else:
            suite_list_dedup[suite] = True

    test_suites = []
    for suite in suite_list_dedup:
        if suite_list_dedup[suite] == True:
            test_suites.append(suite)
        elif isinstance(suite_list_dedup[suite], set) and suite_list_dedup[suite]:
            test_suites.append(suite + ":" + "\\".join(suite_list_dedup[suite]))

    return duts, targets, test_suites


def dts_parse_commands(commands):
    """
    Parse command information from dts arguments
    """
    dts_commands = []

    if commands is None:
        return dts_commands

    args_format = {"shell": 0, "crb": 1, "stage": 2, "check": 3, "max_num": 4}
    cmd_fmt = r"\[(.*)\]"

    for command in commands:
        args = command.split(":")
        if len(args) != args_format["max_num"]:
            log_handler.error("Command [%s] is lack of arguments" % command)
            raise VerifyFailure("commands input is not corrected")
            continue
        dts_command = {}

        m = re.match(cmd_fmt, args[0])
        if m:
            cmds = m.group(1).split(",")
            shell_cmd = ""
            for cmd in cmds:
                shell_cmd += cmd
                shell_cmd += " "
            dts_command["command"] = shell_cmd[:-1]
        else:
            dts_command["command"] = args[0]
        if args[1] == "tester":
            dts_command["host"] = "tester"
        else:
            dts_command["host"] = "dut"
        if args[2] == "post-init":
            dts_command["stage"] = "post-init"
        else:
            dts_command["stage"] = "pre-init"
        if args[3] == "ignore":
            dts_command["verify"] = False
        else:
            dts_command["verify"] = True

        dts_commands.append(dts_command)

    return dts_commands


def dts_run_commands(crb, dts_commands):
    """
    Run dts input commands
    """
    for dts_command in dts_commands:
        command = dts_command["command"]
        if dts_command["host"] in crb.NAME:
            if crb.stage == dts_command["stage"]:
                ret = crb.send_expect(command, expected="# ", verify=True)
                if type(ret) is int:
                    log_handler.error("[%s] return failure" % command)
                    if dts_command["verify"] is True:
                        raise VerifyFailure("Command execution failed")


def get_project_obj(project_name, super_class, crbInst, serializer, dut_id):
    """
    Load project module and return crb instance.
    """
    project_obj = None
    PROJECT_MODULE_PREFIX = "project_"
    try:
        _project_name = PROJECT_MODULE_PREFIX + project_name
        project_module = __import__(
            "framework." + _project_name, fromlist=[_project_name]
        )

        for project_subclassname, project_subclass in get_subclasses(
            project_module, super_class
        ):
            project_obj = project_subclass(crbInst, serializer, dut_id)
        if project_obj is None:
            project_obj = super_class(crbInst, serializer, dut_id)
    except Exception as e:
        log_handler.info("LOAD PROJECT MODULE INFO: " + str(e))
        project_obj = super_class(crbInst, serializer, dut_id)

    return project_obj


def dts_log_testsuite(duts, tester, suite_obj, log_handler, test_classname):
    """
    Change to SUITE self logger handler.
    """
    log_handler.config_suite(test_classname, "dts")
    tester.logger.config_suite(test_classname, "tester")
    if hasattr(tester, "logger_alt"):
        tester.logger_alt.config_suite(test_classname, "tester")
    if hasattr(tester, "logger_scapy"):
        tester.logger_scapy.config_suite(test_classname, "tester")

    for dutobj in duts:
        dutobj.logger.config_suite(test_classname, "dut")
        dutobj.test_classname = test_classname

    try:
        if tester.it_uses_external_generator():
            if (
                tester.is_pktgen
                and hasattr(tester, "pktgen")
                and getattr(tester, "pktgen")
            ):
                tester.pktgen.logger.config_suite(test_classname, "pktgen")
    except Exception as ex:
        pass


def dts_log_execution(duts, tester, log_handler):
    """
    Change to DTS default logger handler.
    """
    log_handler.config_execution("dts")
    tester.logger.config_execution("tester")

    for dutobj in duts:
        dutobj.logger.config_execution(
            "dut" + settings.LOG_NAME_SEP + "%s" % dutobj.crb["My IP"]
        )

    try:
        if tester.it_uses_external_generator():
            if (
                tester.is_pktgen
                and hasattr(tester, "pktgen")
                and getattr(tester, "pktgen")
            ):
                tester.pktgen.logger.config_execution("pktgen")
    except Exception as ex:
        pass


def dts_crbs_init(
    crbInsts, skip_setup, read_cache, project, base_dir, serializer, virttype
):
    """
    Create dts dut/tester instance and initialize them.
    """
    duts = []

    serializer.set_serialized_filename(
        settings.FOLDERS["Output"] + "/.%s.cache" % crbInsts[0]["IP"]
    )
    serializer.load_from_file()

    testInst = copy.copy(crbInsts[0])
    testInst["My IP"] = crbInsts[0]["tester IP"]
    tester = get_project_obj(project, Tester, testInst, serializer, dut_id=0)

    dut_id = 0
    for crbInst in crbInsts:
        dutInst = copy.copy(crbInst)
        dutInst["My IP"] = crbInst["IP"]
        dutobj = get_project_obj(project, Dut, dutInst, serializer, dut_id=dut_id)
        duts.append(dutobj)
        dut_id += 1

    dts_log_execution(duts, tester, log_handler)

    tester.duts = duts
    show_speedup_options_messages(read_cache, skip_setup)
    tester.set_speedup_options(read_cache, skip_setup)
    try:
        tester.init_ext_gen()
    except Exception as e:
        log_handler.error(str(e))
        tester.close()
        for dutobj in duts:
            dutobj.close()
        raise e

    nic = settings.load_global_setting(settings.HOST_NIC_SETTING)
    for dutobj in duts:
        dutobj.tester = tester
        dutobj.setup_virtenv(virttype)
        dutobj.set_speedup_options(read_cache, skip_setup)
        dutobj.set_directory(base_dir)
        # save execution nic setting
        dutobj.set_nic_type(nic)

    return duts, tester


def dts_crbs_exit(duts, tester):
    """
    Call dut and tester exit function after execution finished
    """
    for dutobj in duts:
        dutobj.crb_exit()

    tester.crb_exit()


def dts_run_prerequisties(duts, tester, pkgName, patch, dts_commands, serializer):
    """
    Run dts prerequisties function.
    """
    try:
        dts_run_commands(tester, dts_commands)
        tester.prerequisites()
        dts_run_commands(tester, dts_commands)
    except Exception as ex:
        log_handler.error(" PREREQ EXCEPTION " + traceback.format_exc())
        log_handler.info("CACHE: Discarding cache.")
        serializer.discard_cache()
        settings.report_error("TESTER_SETUP_ERR")
        return False

    try:
        for dutobj in duts:
            dts_run_commands(dutobj, dts_commands)
            dutobj.set_package(pkgName, patch)
            dutobj.prerequisites()
            dts_run_commands(dutobj, dts_commands)

        serializer.save_to_file()
    except Exception as ex:
        log_handler.error(" PREREQ EXCEPTION " + traceback.format_exc())
        result.add_failed_dut(duts[0], str(ex))
        log_handler.info("CACHE: Discarding cache.")
        serializer.discard_cache()
        settings.report_error("DUT_SETUP_ERR")
        return False
    else:
        result.remove_failed_dut(duts[0])


def dts_run_target(duts, tester, targets, test_suites, subtitle):
    """
    Run each target in execution targets.
    """
    for target in targets:
        log_handler.info("\nTARGET " + target)
        result.target = target

        try:
            drivername = settings.load_global_setting(settings.HOST_DRIVER_SETTING)
            if drivername == "":
                for dutobj in duts:
                    dutobj.set_target(target, bind_dev=False)
            else:
                for dutobj in duts:
                    dutobj.set_target(target)
        except AssertionError as ex:
            log_handler.error(" TARGET ERROR: " + str(ex))
            settings.report_error("DPDK_BUILD_ERR")
            result.add_failed_target(result.dut, target, str(ex))
            continue
        except Exception as ex:
            settings.report_error("GENERIC_ERR")
            log_handler.error(" !!! DEBUG IT: " + traceback.format_exc())
            result.add_failed_target(result.dut, target, str(ex))
            continue
        else:
            result.remove_failed_target(result.dut, target)

        dts_run_suite(duts, tester, test_suites, target, subtitle)

    tester.restore_interfaces()

    for dutobj in duts:
        dutobj.stop_ports()
        dutobj.restore_interfaces()
        dutobj.restore_modules()


def dts_run_suite(duts, tester, test_suites, target, subtitle):
    """
    Run each suite in test suite list.
    """
    for suite_name in test_suites:
        try:
            # check whether config the test cases
            append_requested_case_list = None
            if ":" in suite_name:
                case_list = suite_name[suite_name.find(":") + 1 :]
                append_requested_case_list = case_list.split("\\")
                suite_name = suite_name[: suite_name.find(":")]
            result.test_suite = suite_name
            _suite_full_name = "TestSuite_" + suite_name
            suite_module = __import__(
                "tests." + _suite_full_name, fromlist=[_suite_full_name]
            )
            for test_classname, test_class in get_subclasses(suite_module, TestCase):

                suite_obj = test_class(duts, tester, target, suite_name)
                suite_obj.init_log()
                suite_obj.set_requested_cases(requested_tests)
                suite_obj.set_requested_cases(append_requested_case_list)
                suite_obj.set_check_inst(check=check_case_inst)
                suite_obj.set_subtitle(subtitle)
                result.nic = suite_obj.nic

                dts_log_testsuite(duts, tester, suite_obj, log_handler, test_classname)

                log_handler.info("\nTEST SUITE : " + test_classname)
                log_handler.info("NIC :        " + result.nic)

                if suite_obj.execute_setup_all():
                    suite_obj.execute_test_cases()

                # save suite cases result
                result.copy_suite(suite_obj.get_result())

                log_handler.info("\nTEST SUITE ENDED: " + test_classname)
                dts_log_execution(duts, tester, log_handler)
        except VerifyFailure:
            settings.report_error("SUITE_EXECUTE_ERR")
            log_handler.error(" !!! DEBUG IT: " + traceback.format_exc())
        except KeyboardInterrupt:
            # stop/save result/skip execution
            log_handler.error(" !!! STOPPING DTS")
            break
        except Exception as e:
            settings.report_error("GENERIC_ERR")
            log_handler.error(str(e))
        finally:
            try:
                suite_obj.execute_tear_downall()
            except Exception as e:
                settings.report_error("GENERIC_ERR")
                log_handler.error(str(e))
            try:
                save_all_results()
            except Exception as e:
                settings.report_error("GENERIC_ERR")
                log_handler.error(str(e))


def run_all(
    config_file,
    pkgName,
    git,
    patch,
    skip_setup,
    read_cache,
    project,
    suite_dir,
    test_cases,
    base_dir,
    output_dir,
    verbose,
    virttype,
    debug,
    debugcase,
    re_run,
    commands,
    subtitle,
    update_expected,
    asan,
):
    """
    Main process of DTS, it will run all test suites in the config file.
    """

    global requested_tests
    global result
    global excel_report
    global json_report
    global stats_report
    global log_handler
    global check_case_inst

    # check the python version of the server that run dts
    check_dts_python_version()

    # save global variable
    serializer = Serializer()

    # load check/support case lists
    check_case_inst = CheckCase()

    # prepare the output folder
    if output_dir == "":
        output_dir = settings.FOLDERS["Output"]

    # prepare ASan test
    ASanTestProcess.test_prepare(asan, output_dir)
    # register generate ASan report action
    atexit.register(ASanTestProcess.test_process)

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # enable debug mode
    if debug is True:
        settings.save_global_setting(settings.DEBUG_SETTING, "yes")
    if debugcase is True:
        settings.save_global_setting(settings.DEBUG_CASE_SETTING, "yes")

    # enable update-expected
    if update_expected is True:
        settings.save_global_setting(settings.UPDATE_EXPECTED, "yes")

    # init log_handler handler
    if verbose is True:
        logger.set_verbose()

    re_run = int(re_run)
    if re_run < 0:
        re_run = 0

    logger.log_dir = output_dir
    log_handler = getLogger("dts")
    log_handler.config_execution("dts")

    # run designated test case
    requested_tests = test_cases

    # Read config file
    dts_cfg_folder = settings.load_global_setting(settings.DTS_CFG_FOLDER)
    if dts_cfg_folder != "":
        config_file = dts_cfg_folder + os.sep + config_file

    config = configparser.SafeConfigParser()
    load_cfg = config.read(config_file)
    if len(load_cfg) == 0:
        raise ConfigParseException(config_file)

    # parse commands
    dts_commands = dts_parse_commands(commands)

    os.environ["TERM"] = "dumb"

    # change rst output folder
    rst.path2Result = output_dir

    # report objects
    excel_report = ExcelReporter(output_dir + "/test_results.xls")
    json_report = JSONReporter(output_dir + "/test_results.json")
    stats_report = StatsReporter(output_dir + "/statistics.txt")
    result = Result()

    crbs_conf = CrbsConf()
    crbs = crbs_conf.load_crbs_config()

    # for all Execution sections
    for section in config.sections():
        crbInsts = list()
        dts_parse_param(config, section, log_handler)

        # verify if the delimiter is good if the lists are vertical
        duts, targets, test_suites = dts_parse_config(config, section)
        for dut in duts:
            log_handler.info("\nDUT " + dut)

        # look up in crbs - to find the matching IP
        for dut in duts:
            for crb in crbs:
                if crb["section"] == dut:
                    crbInsts.append(crb)
                    break

        # only run on the dut in known crbs
        if len(crbInsts) == 0:
            log_handler.error(" SKIP UNKNOWN CRB")
            continue

        result.dut = duts[0]

        # init global lock
        create_parallel_locks(len(duts))

        # init dut, tester crb
        duts, tester = dts_crbs_init(
            crbInsts, skip_setup, read_cache, project, base_dir, serializer, virttype
        )
        tester.set_re_run(re_run)
        # register exit action
        atexit.register(quit_execution, duts, tester)

        check_case_inst.check_dut(duts[0])

        # Run DUT prerequisites
        if (
            dts_run_prerequisties(
                duts, tester, pkgName, patch, dts_commands, serializer
            )
            is False
        ):
            dts_crbs_exit(duts, tester)
            continue
        result.kdriver = duts[0].nic.default_driver + "-" + duts[0].nic.driver_version
        result.firmware = duts[0].nic.firmware
        result.package = (
            duts[0].nic.pkg["type"] + " " + duts[0].nic.pkg["version"]
            if duts[0].nic.pkg
            else None
        )
        result.driver = settings.load_global_setting(settings.HOST_DRIVER_SETTING)
        result.dpdk_version = duts[0].dpdk_version
        dts_run_target(duts, tester, targets, test_suites, subtitle)

        dts_crbs_exit(duts, tester)


def show_speedup_options_messages(read_cache, skip_setup):
    if read_cache:
        log_handler.info("CACHE: All configuration will be read from cache.")
    else:
        log_handler.info("CACHE: Cache will not be read.")

    if skip_setup:
        log_handler.info("SKIP: Skipping DPDK setup.")
    else:
        log_handler.info("SKIP: The DPDK setup steps will be executed.")


def save_all_results():
    """
    Save all result to files.
    """
    excel_report.save(result)
    json_report.save(result)
    stats_report.save(result)


def quit_execution(duts, tester):
    """
    Close session to DUT and tester before quit.
    Return exit status when failure occurred.
    """
    # close all nics
    for dutobj in duts:
        if getattr(dutobj, "ports_info", None) and dutobj.ports_info:
            for port_info in dutobj.ports_info:
                netdev = port_info["port"]
                netdev.close()
        # close all session
        dutobj.close()
    if tester is not None:
        tester.close()
    log_handler.info("DTS ended")

    # return value
    settings.exit_error()
