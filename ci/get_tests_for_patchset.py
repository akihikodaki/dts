# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2021 University of New Hampshire Interoperability Laboratory
# Copyright(c) 2021 Intel Corporation
#

"""
This script should be run after a patchset has been applied to DTS.
It will iterate through the import tree in python, looking for any
test that could possibly have had behavior change due to the patchset.
It will then output all of those tests to standard out in a line-delimited
list.

The script will also issue warning to standard error if any of the
"protected paths" are changed. The warning will be in the format:
"WARNING: {file_name} is protected"

The script will also issue a warning if a config file is changed. This
warning is also sent to standard error and takes the form of:
"WARNING: {file_name} is a config file and was changed"

This script can either be run natively or with the provided dockerfile.
"""


import argparse
import os
import pkgutil
import re
import subprocess
import sys
from pkgutil import walk_packages
from types import ModuleType
from typing import Iterable, List

DTS_MAIN_BRANCH_REF: str = "origin/master"

DTS_TEST_MODULE_PATH: str = "tests"
# Will be unnecessary once DTS moves to a normal module structure
DTS_MODULE_PATHS: List[str] = ["framework", "nic", "dep", DTS_TEST_MODULE_PATH]

# This is primarily intended for folders which contain CI scripts, as these
# should not be modified in the course of normal CI. A file in any of these
# folders being modified will cause a warning to be emitted to standard error
DTS_PROTECTED_PATHS: List[str] = [
    "ci",
]

# This is intended to help detect when a config files have been changed.
# The intention behind this detection is to enable additional regression
# tests related to ensuring stable config file formats
DTS_CONFIG_PATHS: List[str] = [
    "conf",
    "execution.cfg",
]


def get_args() -> str:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="After a patchset is applied, run this script"
        "It will then output a list "
        "of applicable test suites to standard output, with 1 "
        "test suite per line. All other output, such as warnings,"
        " errors or informational messages will be sent to "
        "standard error. This script may produce no output at all,"
        "in which case it should be assumed that there are no "
        "applicable test suites.\n\n "
        "Exit Codes:\n"
        "value | meaning\n"
        "----- | -------\n"
        "  0   | OK   \n"
        "  1   | Error, check standard error",
    )

    dts_directory: str = os.path.dirname(
        os.path.dirname(os.path.join(os.getcwd(), __file__))
    )
    parser.add_argument(
        "-d", "--dts-directory", type=str, default=dts_directory, required=False
    )
    args = parser.parse_args()
    if not os.path.isdir(args.dts_directory):
        print(f"{args.dts_directory} is not a directory.", file=sys.stderr)
        exit(1)

    return args.dts_directory


def get_modified_files() -> List[str]:
    cmd = ["git", "diff", "--name-only", DTS_MAIN_BRANCH_REF, "HEAD"]
    process: subprocess.CompletedProcess = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        print(f"{' '.join(cmd)} returned {process.returncode}")
        exit(1)

    # This explicit conversion to utf8 will catch encoding errors
    stdout: bytes = process.stdout
    stdout_str: str = stdout.decode("utf-8")

    return stdout_str.splitlines()


def get_names_of_modified_python_files(files: List[str]) -> List[str]:
    return list(
        map(
            lambda f: str(re.sub("\\.py", "", f)),
            map(
                lambda f: os.path.basename(f),
                filter(lambda f: f.endswith(".py"), files),
            ),
        )
    )


def get_modules() -> List[ModuleType]:
    return list(
        map(lambda m: pkgutil.resolve_name(m.name), walk_packages(DTS_MODULE_PATHS))
    )


def get_module_imports(mod: ModuleType) -> Iterable[ModuleType]:
    imports = []
    for attribute_label in dir(mod):
        try:
            attribute = getattr(mod, attribute_label)
        except ModuleNotFoundError as _:  # some standard library modules don't like being directly imported
            continue
        if isinstance(attribute, type(mod)):
            imports.append(attribute)
    return imports


def get_modules_in_tree(mod: ModuleType) -> Iterable[ModuleType]:
    yield from get_module_imports(mod)


def get_only_test_suites(modules: Iterable[ModuleType]) -> Iterable[ModuleType]:
    test_package_path = os.path.join(os.getcwd(), DTS_TEST_MODULE_PATH)
    mod: ModuleType
    return filter(
        lambda mod: mod.__name__.startswith("TestSuite_"),
        filter(
            lambda mod: mod.__file__.startswith(test_package_path),
            filter(lambda mod: "__file__" in dir(mod), modules),
        ),
    )


def get_test_suite_names(modules: Iterable[ModuleType]) -> Iterable[str]:
    # Moving this into a set is there to ensure that there are no duplicates
    return set(list(map(lambda mod: re.sub("TestSuite_", "", mod.__name__), modules)))


def get_tests_to_run() -> List[str]:
    dts_directory: str
    dts_directory = get_args()

    # This all needs to be done at the top level, so I have to do it here.

    # chdir to the DTS directory, since we want that to be
    # the context for any commands that are run.
    os.chdir(dts_directory)

    for path in DTS_MODULE_PATHS:
        sys.path.append(os.path.join(dts_directory, path))

    files: List[str] = get_modified_files()
    changed_module_name = get_names_of_modified_python_files(files)

    for protected_folder in DTS_PROTECTED_PATHS:
        for file_name in files:
            if file_name.startswith(protected_folder):
                print(f"WARNING: {file_name} is protected", file=sys.stderr)

    for config_file_path in DTS_CONFIG_PATHS:
        for file_name in files:
            if file_name.startswith(config_file_path):
                print(
                    f"WARNING: {file_name} is a config file and was changed",
                    file=sys.stderr,
                )

    # Each index is 1 level of the tree
    module_list: List[ModuleType] = [
        pkgutil.resolve_name(name) for name in changed_module_name
    ]
    current_index: int = 0
    while current_index < len(module_list) and len(module_list) > 0:
        mod = module_list[current_index]
        if module_list.count(mod) == 1:
            module_list = module_list + list(get_modules_in_tree(mod))
        current_index += 1

    test_suites_to_run: List[str] = list(
        get_test_suite_names(get_only_test_suites(module_list))
    )
    test_suites_to_run.sort()
    return test_suites_to_run


def main():
    test_suites_to_run = get_tests_to_run()
    print("\n".join(test_suites_to_run))


if __name__ == "__main__":
    main()
