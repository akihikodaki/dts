# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, check_supported_nic
from framework.utils import BLUE, GREEN, RED

rule_switch_unsupported = {
    "name": "create switch unsupported rules",
    "message": "ice_flow_create(): Failed to create flow",
    "ipv4": [
        "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask 00:ff:ff:ff:ff:ff / ipv4 / end actions drop / end",
        "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 33:00:00:00:00:02 dst mask ff:ff:ff:ff:ff:fe / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / end actions drop / end",
    ],
    "ipv4_tcp": [
        "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:fe / ipv4 / tcp / end actions drop / end",
        "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 00:01:23:45:67:89 dst mask ff:ff:ff:ff:00:ff / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
    ],
    "ipv4_udp": [
        "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:fe / ipv4 / udp / end actions drop / end",
        "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 00:01:23:45:67:89 dst mask ff:ff:ff:ff:00:ff / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / udp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
    ],
    "ipv4_sctp": [
        "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:fe / ipv4 / sctp / end actions drop / end",
        "flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / sctp / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / sctp / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.243 / sctp / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 / sctp src spec 8010 src mask 65520 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 / sctp dst spec 8010 dst mask 65520 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / sctp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
        "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 00:01:23:45:67:89 dst mask ff:ff:ff:ff:00:ff / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / sctp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
    ],
}

rule_switch_supported = {
    "name": "create switch supported rules",
    "message": "Succeeded to create (2) flow",
    "ipv4": [
        "flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:ff / ipv4 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.0 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / end actions drop / end",
    ],
    "ipv4_tcp": [
        "flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / tcp / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / tcp / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.243 / tcp / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 / tcp dst spec 8010 dst mask 65520 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
    ],
    "ipv4_udp": [
        "flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / udp / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / udp / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.243 / udp / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 / udp src spec 8010 src mask 65520 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 / udp dst spec 8010 dst mask 65520 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / udp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
    ],
}

subcases = {
    "case": [rule_switch_supported, rule_switch_unsupported],
    "result": [],
}


class TestICEDCFDisableACLFilter(TestCase):
    supported_nic = [
        "ICE_25G-E810C_SFP",
        "ICE_25G-E810_XXV_SFP",
        "ICE_100G-E810C_QSFP",
        "ICE_25G-E823C_QSFP",
    ]

    @check_supported_nic(supported_nic)
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        localPort0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_iface0 = self.tester.get_interface(localPort0)
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.dut.send_expect("ifconfig %s up" % self.tester_iface0, "# ")
        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.testpmd_status = "close"
        # bind pf to kernel
        self.dut.bind_interfaces_linux("ice")
        # set vf driver
        self.vf_driver = "vfio-pci"
        self.dut.send_expect("modprobe vfio-pci", "# ")
        self.path = self.dut.apps_name["test-pmd"]
        self.setup_1pf_2vf_env()
        self.dut.send_expect("ifconfig %s up" % self.tester_iface0, "# ", 15)

    def setup_1pf_2vf_env(self, pf_port=0, driver="default"):

        self.used_dut_port_0 = self.dut_ports[pf_port]
        # get PF interface name
        self.dut.send_expect("ethtool -i %s" % self.pf0_intf, "#")
        # generate 2 VF on PF
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 2, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        self.vf0_pci = self.sriov_vfs_port_0[0].pci
        self.vf1_pci = self.sriov_vfs_port_0[1].pci
        # set VF0 as trust
        self.dut.send_expect("ip link set %s vf 0 trust on" % self.pf0_intf, "#")
        # set VF1 mac address
        self.dut.send_expect(
            "ip link set %s vf 1 mac 00:01:23:45:67:89" % self.pf0_intf, "#"
        )
        # bind drivers
        for port in self.sriov_vfs_port_0:
            port.bind_driver(self.vf_driver)
        time.sleep(5)

    def set_up(self):
        """
        Run before each test case.
        """
        self.setup_1pf_2vf_env()

    def create_testpmd_command(self, param, acl_status):
        """
        Create testpmd command
        """
        # Prepare testpmd EAL and parameters
        if acl_status != "":
            all_eal_param = self.dut.create_eal_parameters(
                cores="1S/4C/1T",
                ports=[self.vf0_pci, self.vf1_pci],
                port_options={self.vf0_pci: "cap=dcf,acl=" + acl_status},
            )
        else:
            all_eal_param = self.dut.create_eal_parameters(
                cores="1S/4C/1T",
                ports=[self.vf0_pci, self.vf1_pci],
                port_options={self.vf0_pci: "cap=dcf"},
            )
        command = self.path + all_eal_param + "--log-level='ice,7'" + " -- -i" + param
        return command

    def launch_testpmd(self, param="", acl_status="off"):
        """
        launch testpmd with the command
        """
        time.sleep(5)
        command = self.create_testpmd_command(param, acl_status)
        out = self.dut.send_expect(command, "testpmd> ", 20)
        return out

    def create_acl_filter_rule(self, rules, check_stats):
        """
        Create acl filter rules,
        set check_stats=False to check Switch not support rules can not be created by ACL engine
        set check_stats=True to check Switch support rules can be created by Switch engine
        """
        rule_list = {}
        # switch_rule message = "Succeeded to create (2) flow"
        # failed_rule message = "ice_flow_create(): Failed to create flow"

        for item in rules.values():
            if isinstance(item, list):
                for rule in item:
                    out = self.dut.send_expect(rule, "testpmd> ")
                    # check switch not support rules
                    if check_stats == False:
                        rule_list.update(
                            {rule: False if rules["message"] in out else True}
                        )
                    # check switch support rules
                    if check_stats == True:
                        rule_list.update(
                            {rule: True if rules["message"] in out else False}
                        )

        if check_stats:
            self.verify(
                all(list(rule_list.values())),
                "all rules should be created successfully by Switch engine, result {}".format(
                    rule_list
                ),
            )
        else:
            self.verify(
                not any(list(rule_list.values())),
                "all rules should be created failed by ACL engine, result {}".format(
                    rule_list
                ),
            )

    def test_startup_time(self):
        """
        It takes too much time to enable the ACL engine when launching testpmd,
        so the startup time should be shortened after disabling ACL.
        """
        repeat_time = 6
        start_up_time_acl_off = []
        start_up_time_acl_on = []
        regex = re.compile(".*real (\d+\.\d{2}).*")
        # acl = off
        command_acl_off = self.create_testpmd_command(param="", acl_status="off")
        # acl = on
        command_acl_on = self.create_testpmd_command(param="", acl_status="")
        # record startup time
        for i in range(repeat_time):
            out_acl_off = self.dut.send_expect(
                "echo quit | time -p ./%s" % (command_acl_off),
                "#",
                120,
            )

            out_acl_on = self.dut.send_expect(
                "echo quit | time -p ./%s" % (command_acl_on),
                "#",
                120,
            )

            time_acl_on = regex.findall(out_acl_on)[0]
            time_acl_off = regex.findall(out_acl_off)[0]
            if time_acl_on != "" and time_acl_off != "":
                start_up_time_acl_off.append(eval(time_acl_off))
                start_up_time_acl_on.append(eval(time_acl_on))
            print(BLUE("%s times done, %s times totally" % (i + 1, repeat_time)))
        # get the average
        avg_start_up_time_acl_on = sum(start_up_time_acl_on) / repeat_time
        avg_start_up_time_acl_off = sum(start_up_time_acl_off) / repeat_time
        self.verify(
            avg_start_up_time_acl_on > avg_start_up_time_acl_off,
            "disable acl to reduce startup time failed!!!",
        )
        self.testpmd_status = "close"

    def test_disable_acl(self):
        """
        when creating ACL rules after disabling the ACL engine, the ACL engine will fail to create any of these rules,
        but some of them can be successfully created by the switch engine.
        """
        launch_testpmd = True
        if launch_testpmd:
            # launch testpmd
            self.launch_testpmd(acl_status="off")

        self.dut.send_expect("flow flush 0", "testpmd> ", 120)
        # test subcase
        for subcase in subcases["case"]:
            try:
                self.logger.info(
                    (GREEN("========test subcase: %s========" % subcase["name"]))
                )
                self.create_acl_filter_rule(
                    rules=subcase,
                    check_stats=False if "unsupported" in subcase["name"] else True,
                )
                self.logger.info((GREEN("case passed: %s" % subcase["name"])))

            except Exception as e:
                self.logger.warning((RED(e)))
                self.logger.info((GREEN("case failed: %s" % subcase["name"])))
                subcases["result"].append(False)
        self.verify(all(subcases["result"]), "test disable acl engine failed.")

        self.testpmd_status = "open"

    def quit_testpmd(self):
        """
        quit testpmd
        """
        if self.testpmd_status != "close":
            # destroy all flow rules on DCF
            self.dut.send_expect("flow flush 0", "testpmd> ", 15)
            self.dut.send_expect("clear port stats all", "testpmd> ", 15)
            self.dut.send_expect("quit", "#", 30)
            # kill all DPDK application
            self.dut.kill_all()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.quit_testpmd()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
