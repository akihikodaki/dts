#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
A test framework for testing DPDK.
"""

import argparse
import os
import subprocess
import sys

from framework import dts

# change operation directory
cwd = os.getcwd()


def git_build_package(gitLabel, pkgName):
    """
    generate package from git, if dpdk existed will pull latest code
    """
    gitURL = r"http://dpdk.org/git/dpdk"
    gitPrefix = r"dpdk/"
    depot = r"dep"
    if os.path.exists("%s/%s" % (depot, gitPrefix)) is True:
        os.chdir("%s/%s" % (depot, gitPrefix))
        ret = os.system("git pull --force")
        os.chdir(cwd)
    else:
        print("git clone %s %s/%s" % (gitURL, depot, gitPrefix))
        ret = os.system("git clone %s %s/%s" % (gitURL, depot, gitPrefix))
    if ret != 0:
        raise EnvironmentError

    print(
        "git archive --format=tar.gz --prefix=%s %s -o %s"
        % (gitPrefix, gitLabel, pkgName)
    )
    os.chdir("%s/%s/%s" % (cwd, depot, gitPrefix))
    try:
        ret = subprocess.run(
            [
                "git",
                "archive",
                "--format=tar.gz",
                "--prefix=%s/" % gitPrefix,
                "%s" % gitLabel,
                "-o",
                "../%s" % pkgName,
            ],
            shell=False,
        )
    except Exception as e:
        print("git archive failed of : %s" % str(e))
        sys.exit()

    os.chdir(cwd)
    if ret.returncode != 0:
        print(ret)
        raise EnvironmentError


# Read cmd-line args
parser = argparse.ArgumentParser(description="DPDK test framework.")

parser.add_argument(
    "--config-file",
    default="execution.cfg",
    help="configuration file that describes the test " + "cases, DUTs and targets",
)

parser.add_argument("--git", help="git label to use as input")

parser.add_argument(
    "--patch", action="append", help="apply a patch to the package under test"
)

parser.add_argument(
    "--snapshot", default="dep/dpdk.tar.gz", help="snapshot .tgz file to use as input"
)

parser.add_argument(
    "--output", default="", help="Output directory where dts log and result saved"
)

parser.add_argument(
    "-s",
    "--skip-setup",
    action="store_true",
    help="skips all possible setup steps done on both DUT" + " and tester boards.",
)

parser.add_argument(
    "-r",
    "--read-cache",
    action="store_true",
    help="reads the DUT configuration from a cache. If not "
    + "specified, the DUT configuration will be calculated "
    + "as usual and cached.",
)

parser.add_argument(
    "-p", "--project", default="dpdk", help="specify that which project will be tested"
)

parser.add_argument(
    "--suite-dir",
    default="tests",
    help="Test suite directory where test suites will be imported",
)

parser.add_argument(
    "-t",
    "--test-cases",
    action="append",
    help="executes only the followings test cases",
)

parser.add_argument(
    "-d",
    "--dir",
    default="~/dpdk",
    help="Output directory where dpdk package is extracted",
)

parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="enable verbose output, all message output on screen",
)

parser.add_argument(
    "--virttype", default="kvm", help="set virt type,support kvm, libvirtd"
)

parser.add_argument(
    "--debug",
    action="store_true",
    help="enable debug mode, user can enter debug mode in process",
)

parser.add_argument(
    "--debugcase",
    action="store_true",
    help="enable debug mode in the first case, user can further debug",
)
parser.add_argument(
    "--re_run",
    default=0,
    help="when case failed will re-run times, and this value must >= 0",
)

parser.add_argument(
    "--commands",
    action="append",
    help="run command on tester or dut. The command format is "
    + "[commands]:dut|tester:pre-init|post-init:check|ignore",
)

parser.add_argument("--subtitle", help="add a subtitle to the rst report")

parser.add_argument(
    "--update-expected",
    action="store_true",
    help="update expected values based on test results",
)

parser.add_argument(
    "--asan", action="store_true", help="add function to support ASan test"
)

args = parser.parse_args()


# prepare DPDK source test package, DTS will exited when failed.
if args.git is not None:
    try:
        git_build_package(args.git, os.path.split(args.snapshot)[1])
    except Exception:
        print("FAILED TO PREPARE DPDK PACKAGE!!!")
        sys.exit()

# Main program begins here
dts.run_all(
    args.config_file,
    args.snapshot,
    args.git,
    args.patch,
    args.skip_setup,
    args.read_cache,
    args.project,
    args.suite_dir,
    args.test_cases,
    args.dir,
    args.output,
    args.verbose,
    args.virttype,
    args.debug,
    args.debugcase,
    args.re_run,
    args.commands,
    args.subtitle,
    args.update_expected,
    args.asan,
)
