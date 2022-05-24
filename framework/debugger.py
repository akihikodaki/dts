# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2015 Intel Corporation
#

import code
import imp
import os
import signal
import sys
import time

from .settings import DEBUG_SETTING, DTS_PARALLEL_SETTING, load_global_setting
from .utils import GREEN, copy_instance_attr, get_subclasses

console = None  # global console object
debug_cmd = ""  # global debug state
AliveSuite = None  # global suite for run command
AliveModule = None  # global module for reload
AliveCase = None  # global case name for run command


def help_command():
    console.push("print('Help on debug module')")
    console.push("print('DESCRIPTION')")
    console.push("print('DTS debug module support few debug commands')")
    console.push("print('  - help(): help messages')")
    console.push("print('  - list(): list all connections')")
    console.push("print('  - connect(): bind to specified connection')")
    console.push("print('  -        : connect(\"dut\")')")
    console.push("print('  - quit(): quit debug module')")
    console.push("print('  - exit(): exit processing procedure')")
    console.push("print('  - debug(): call python debug module for further debug')")
    console.push("print('  - rerun(): re-run the interrupted test case')")


def list_command():
    """
    List all connection sessions and can be reference of connect command.
    """
    index = 0
    from .ssh_connection import CONNECTIONS

    for connection in CONNECTIONS:
        for name, session in list(connection.items()):
            console.push("print('connect %d: %10s')" % (index, name))
            index += 1


def connect_command(connect):
    """
    Connect to ssh session and give control to user.
    """
    from .ssh_connection import CONNECTIONS

    if type(connect) == int:
        name, session = list(CONNECTIONS[connect].items())[0]
        print(GREEN("Connecting to session[%s]" % name))
        session.session.interact()
    else:
        for connection in CONNECTIONS:
            for name, session in list(connection.items()):
                if name == connect:
                    print(GREEN("Connecting to session[%s]" % name))
                    session.session.interact()


def rerun_command():
    """
    Rerun test case specified in command line
    """
    from .test_case import TestCase

    global AliveSuite, AliveModule, AliveCase
    new_module = imp.reload(AliveModule)

    # save arguments required to initialize suite
    duts = AliveSuite.__dict__["duts"]
    tester = AliveSuite.__dict__["tester"]
    target = AliveSuite.__dict__["target"]
    suite = AliveSuite.__dict__["suite_name"]

    for test_classname, test_class in get_subclasses(new_module, TestCase):
        suite_obj = test_class(duts, tester, target, suite)

        # copy all element from previous suite to reloaded suite
        copy_instance_attr(AliveSuite, suite_obj)
        # re-run specified test case
        for case in suite_obj._get_test_cases(r"\A%s\Z" % AliveCase):
            if callable(case):
                suite_obj.logger.info("Rerun Test Case %s Begin" % case.__name__)
                suite_obj._execute_test_case(case)


def exit_command():
    """
    Exit framework.
    """
    global debug_cmd
    debug_cmd = "exit"
    sys.exit(0)


def debug_command():
    """
    Give control to python debugger pdb.
    """
    global debug_cmd
    debug_cmd = "debug"
    sys.exit(0)


def capture_handle(signum, frame):
    """
    Capture keyboard interrupt in the process of send_expect.
    """
    global debug_cmd
    debug_cmd = "waiting"


def keyboard_handle(signum, frame):
    """
    Interrupt handler for SIGINT and call code module create python interpreter.
    """
    global console
    console = code.InteractiveConsole()
    command = {}
    command["list"] = list_command
    command["exit"] = exit_command
    command["debug"] = debug_command
    command["help"] = help_command
    command["connect"] = connect_command
    command["rerun"] = rerun_command
    console.push('print("Use help command for detail information")')
    try:
        code.interact(local=command)
    except SystemExit:
        # reopen sys.stdin for after exit function stdin will be closed
        fd = os.open("/dev/stdin", 600)
        sys.stdin = os.fdopen(fd, "r")

    global debug_cmd
    if debug_cmd == "debug":
        # call python debugger
        import pdb

        pdb.set_trace()
    elif debug_cmd == "exit":
        sys.exit(0)

    debug_cmd = ""


def ignore_keyintr():
    """
    Temporary disable interrupt handler.
    """
    # signal can't be used in thread
    if (
        load_global_setting(DEBUG_SETTING) != "yes"
        or load_global_setting(DTS_PARALLEL_SETTING) == "yes"
    ):
        return

    global debug_cmd
    signal.siginterrupt(signal.SIGINT, True)
    # if there's waiting request, first handler it
    if debug_cmd == "waiting":
        keyboard_handle(signal.SIGINT, None)

    return signal.signal(signal.SIGINT, capture_handle)


def aware_keyintr():
    """
    Reenable interrupt handler.
    """
    # signal can't be used in thread
    if (
        load_global_setting(DEBUG_SETTING) != "yes"
        or load_global_setting(DTS_PARALLEL_SETTING) == "yes"
    ):
        return

    return signal.signal(signal.SIGINT, keyboard_handle)
