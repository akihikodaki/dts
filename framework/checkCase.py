import collections
import json
import os

from .settings import (
    CONFIG_ROOT_PATH,
    HOST_DRIVER_SETTING,
    get_nic_name,
    load_global_setting,
)
from .utils import RED

filter_json_file = os.path.join(CONFIG_ROOT_PATH, "test_case_checklist.json")
support_json_file = os.path.join(CONFIG_ROOT_PATH, "test_case_supportlist.json")


class CheckCase(object):
    """
    Class for check test case running criteria. All information will be loaded
    from DTS_CFG_FOLDER/test_case_*list.json. Current two files are maintained. One is
    for check whether test case should skip, another one is for check whether
    current environment support test case execution.
    """

    def __init__(self):
        self.dut = None
        self.comments = ""

        self.check_function_dict = {}
        self.support_function_dict = {}
        try:
            self.check_function_dict = json.load(
                open(filter_json_file), object_pairs_hook=collections.OrderedDict
            )
        except:
            print(
                RED(
                    "Can't load check list for test cases, all case will be taken as supported"
                )
            )

        try:
            self.support_function_dict = json.load(
                open(support_json_file), object_pairs_hook=collections.OrderedDict
            )
        except:
            print(
                RED(
                    "Can't load support list for test cases, all case will be taken as supported"
                )
            )

    def check_dut(self, dut):
        """
        Change DUT instance for environment check
        """
        self.dut = dut

    def _check_os(self, os_type):
        if "all" == os_type[0].lower():
            return True
        dut_os_type = self.dut.get_os_type()
        if dut_os_type in os_type:
            return True
        else:
            return False

    def _check_nic(self, nic_type):
        if "all" == nic_type[0].lower():
            return True
        dut_nic_type = get_nic_name(self.dut.ports_info[0]["type"])
        if dut_nic_type in nic_type:
            return True
        else:
            return False

    def _check_target(self, target):
        if "all" == target[0].lower():
            return True
        if self.dut.target in target:
            return True
        else:
            return False

    def _check_host_driver(self, drivers):
        host_driver = load_global_setting(HOST_DRIVER_SETTING)
        if "all" == drivers[0].lower():
            return True
        if host_driver in drivers:
            return True
        else:
            return False

    def case_skip(self, case_name):
        """
        Check whether test case and DUT match skip criteria
        Return True if skip should skip
        """
        skip_flag = False
        self.comments = ""

        if self.dut is None:
            print(RED("No Dut assigned before case skip check"))
            return skip_flag

        if case_name in list(self.check_function_dict.keys()):
            case_checks = self.check_function_dict[case_name]
            # each case may have several checks
            for case_check in case_checks:
                # init result for each check
                skip_flag = False
                for key in list(case_check.keys()):
                    # some items like "Bug ID" and "Comments" do not need check
                    try:
                        if "Comments" == key:
                            continue
                        if "Bug ID" == key:
                            continue
                        check_function = getattr(self, "_check_%s" % key.lower())
                    except:
                        print(RED("can't check %s type" % key))

                    # skip this check if any item not matched
                    if check_function(case_check[key]):
                        skip_flag = True
                    else:
                        skip_flag = False
                        break

                # if all items matched, this case should skip
                if skip_flag:
                    if "Comments" in list(case_check.keys()):
                        self.comments = case_check["Comments"]
                    return skip_flag

        return skip_flag

    def case_support(self, case_name):
        """
        Check whether test case and DUT match support criteria
        Return False if test case not supported
        """
        support_flag = True
        self.comments = ""

        if self.dut is None:
            print(RED("No Dut assigned before case support check"))
            return support_flag

        if case_name in list(self.support_function_dict.keys()):
            # each case may have several supports
            case_supports = self.support_function_dict[case_name]
            for case_support in case_supports:
                # init result for each check
                support_flag = True
                for key in list(case_support.keys()):
                    # some items like "Bug ID" and "Comments" do not need check
                    try:
                        if "Comments" == key:
                            continue
                        if "Bug ID" == key:
                            continue
                        check_function = getattr(self, "_check_%s" % key.lower())
                    except:
                        print(RED("can't check %s type" % key))

                    # skip this case if any item not matched
                    if check_function(case_support[key]):
                        support_flag = True
                    else:
                        support_flag = False
                        break

            if support_flag is False:
                if "Comments" in list(case_support.keys()):
                    self.comments = case_support["Comments"]
                return support_flag

        return support_flag


class simple_dut(object):
    def __init__(self, os="", target="", nic=""):
        self.ports_info = [{}]
        self.os = os
        self.target = target
        self.ports_info[0]["type"] = nic

    def get_os_type(self):
        return self.os


if __name__ == "__main__":
    dut = simple_dut(os="linux", target="x86_64-native-linuxapp-gcc", nic="177d:a034")
    dut1 = simple_dut(
        os="freebsd", target="x86_64-native-linuxapp-gcc", nic="8086:158b"
    )

    # create instance for check/support case list
    case_inst = CheckCase()

    # check dut
    case_inst.check_dut(dut)
    print(case_inst.case_skip("fdir_flexword_drop_ipv4"))
    print(case_inst.comments)
    print(case_inst.case_support("Vxlan_tunnel"))
    print(case_inst.comments)

    # check other dut
    case_inst.check_dut(dut1)
    print(case_inst.case_skip("fdir_flexword_drop_ipv4"))
    print(case_inst.comments)
    print(case_inst.case_support("Vxlan_tunnel"))
    print(case_inst.comments)
