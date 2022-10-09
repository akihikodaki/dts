# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

import time

from framework import packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

from .rte_flow_common import RssProcessing

mac_ipv4_basic_pkt = (
    'Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2", dst="192.168.0.3")/("X"*480)'
)
mac_ipv6_basic_pkt = (
    'Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="2001::3")/("X"*480)'
)
mac_ipv4_tcp_basic_pkt = 'Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=1026, dport=1027)/("X"*480)'
mac_ipv6_tcp_basic_pkt = 'Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="2001::3")/TCP(sport=1026, dport=1027)/("X"*480)'
mac_ipv4_udp_basic_pkt = 'Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=1026, dport=1027)/("X"*480)'
mac_ipv6_udp_basic_pkt = 'Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="2001::3")/UDP(sport=1026, dport=1027)/("X"*480)'
mac_ipv4_sctp_basic_pkt = 'Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=1026, dport=1027)/("X"*480)'
mac_ipv6_sctp_basic_pkt = 'Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="2001::3")/SCTP(sport=1026, dport=1027)/("X"*480)'

mac_ipv4_changed_pkt = [
    'Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2", dst="192.168.0.5")/("X"*480)',
    'Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.5", dst="192.168.0.3")/("X"*480)',
]

mac_ipv6_changed_pkt = [
    'Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="2001::5")/("X"*480)',
    'Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::5", dst="2001::3")/("X"*480)',
]

mac_ipv4_tcp_changed_l3_pkt = [
    'Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2", dst="192.168.0.5")/TCP(sport=1026, dport=1027)/("X"*480)',
    'Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.5", dst="192.168.0.3")/TCP(sport=1026, dport=1027)/("X"*480)',
]

mac_ipv4_tcp_changed_l4_pkt = [
    'Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=1025, dport=1027)/("X"*480)',
    'Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=1026, dport=1025)/("X"*480)',
]

mac_ipv6_tcp_changed_l3_pkt = [
    'Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="2001::5")/TCP(sport=1026, dport=1027)/("X"*480)',
    'Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::5", dst="2001::3")/TCP(sport=1026, dport=1027)/("X"*480)',
]

mac_ipv6_tcp_changed_l4_pkt = [
    'Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="2001::3")/TCP(sport=1025, dport=1027)/("X"*480)',
    'Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::2", dst="2001::3")/TCP(sport=1026, dport=1025)/("X"*480)',
]

mac_ipv4_udp_changed_l3_pkt = [
    sv.replace("/TCP", "/UDP") for sv in mac_ipv4_tcp_changed_l3_pkt
]
mac_ipv4_udp_changed_l4_pkt = [
    sv.replace("/TCP", "/UDP") for sv in mac_ipv4_tcp_changed_l4_pkt
]

mac_ipv6_udp_changed_l3_pkt = [
    sv.replace("/TCP", "/UDP") for sv in mac_ipv6_tcp_changed_l3_pkt
]
mac_ipv6_udp_changed_l4_pkt = [
    sv.replace("/TCP", "/UDP") for sv in mac_ipv6_tcp_changed_l4_pkt
]

mac_ipv4_sctp_changed_l3_pkt = [
    sv.replace("/TCP", "/SCTP") for sv in mac_ipv4_tcp_changed_l3_pkt
]
mac_ipv4_sctp_changed_l4_pkt = [
    sv.replace("/TCP", "/SCTP") for sv in mac_ipv4_tcp_changed_l4_pkt
]

mac_ipv6_sctp_changed_l3_pkt = [
    sv.replace("/TCP", "/SCTP") for sv in mac_ipv6_tcp_changed_l3_pkt
]
mac_ipv6_sctp_changed_l4_pkt = [
    sv.replace("/TCP", "/SCTP") for sv in mac_ipv6_tcp_changed_l4_pkt
]

command_line_option_rss_ip = {
    "sub_casename": "command_line_option_rss_ip",
    "port_id": 0,
    "test": [
        {"send_packet": mac_ipv4_basic_pkt, "action": {"save_hash": "ip-ipv4"}},
        {
            "send_packet": mac_ipv4_changed_pkt,
            "action": {"check_hash_different": "ip-ipv4"},
        },
        {"send_packet": mac_ipv6_basic_pkt, "action": {"save_hash": "ip-ipv6"}},
        {
            "send_packet": mac_ipv6_changed_pkt,
            "action": {"check_hash_different": "ip-ipv4"},
        },
        # ipv4/ipv6 tcp
        {"send_packet": mac_ipv4_tcp_basic_pkt, "action": {"save_hash": "ipv4-tcp"}},
        {
            "send_packet": mac_ipv4_tcp_changed_l3_pkt,
            "action": {"check_hash_different": "ipv4-tcp"},
        },
        {
            "send_packet": mac_ipv4_tcp_changed_l4_pkt,
            "action": {"check_hash_same": "ipv4-tcp"},
        },
        {"send_packet": mac_ipv6_tcp_basic_pkt, "action": {"save_hash": "ipv6-tcp"}},
        {
            "send_packet": mac_ipv6_tcp_changed_l3_pkt,
            "action": {"check_hash_different": "ipv6-tcp"},
        },
        {
            "send_packet": mac_ipv6_tcp_changed_l4_pkt,
            "action": {"check_hash_same": "ipv6-tcp"},
        },
        # ipv4/ipv6 udp
        {"send_packet": mac_ipv4_udp_basic_pkt, "action": {"save_hash": "ipv4-udp"}},
        {
            "send_packet": mac_ipv4_udp_changed_l3_pkt,
            "action": {"check_hash_different": "ipv4-udp"},
        },
        {
            "send_packet": mac_ipv4_udp_changed_l4_pkt,
            "action": {"check_hash_same": "ipv4-udp"},
        },
        {"send_packet": mac_ipv6_udp_basic_pkt, "action": {"save_hash": "ipv6-udp"}},
        {
            "send_packet": mac_ipv6_udp_changed_l3_pkt,
            "action": {"check_hash_different": "ipv6-udp"},
        },
        {
            "send_packet": mac_ipv6_udp_changed_l4_pkt,
            "action": {"check_hash_same": "ipv6-udp"},
        },
        # ipv4/ipv6 sctp
        {"send_packet": mac_ipv4_sctp_basic_pkt, "action": {"save_hash": "ipv4-sctp"}},
        {
            "send_packet": mac_ipv4_sctp_changed_l3_pkt,
            "action": {"check_hash_different": "ipv4-sctp"},
        },
        {
            "send_packet": mac_ipv4_sctp_changed_l4_pkt,
            "action": {"check_hash_same": "ipv4-sctp"},
        },
        {"send_packet": mac_ipv6_sctp_basic_pkt, "action": {"save_hash": "ipv6-sctp"}},
        {
            "send_packet": mac_ipv6_sctp_changed_l3_pkt,
            "action": {"check_hash_different": "ipv6-sctp"},
        },
        {
            "send_packet": mac_ipv6_sctp_changed_l4_pkt,
            "action": {"check_hash_same": "ipv6-sctp"},
        },
    ],
}

command_line_option_rss_udp = {
    "sub_casename": "command_line_option_rss_udp",
    "port_id": 0,
    "test": [
        # ipv4/ipv6 udp
        {"send_packet": mac_ipv4_udp_basic_pkt, "action": {"save_hash": "ipv4-udp"}},
        {
            "send_packet": mac_ipv4_udp_changed_l3_pkt,
            "action": {"check_hash_different": "ipv4-udp"},
        },
        {
            "send_packet": mac_ipv4_udp_changed_l4_pkt,
            "action": {"check_hash_different": "ipv4-udp"},
        },
        {"send_packet": mac_ipv6_udp_basic_pkt, "action": {"save_hash": "ipv6-udp"}},
        {
            "send_packet": mac_ipv6_udp_changed_l3_pkt,
            "action": {"check_hash_different": "ipv6-udp"},
        },
        {
            "send_packet": mac_ipv6_udp_changed_l4_pkt,
            "action": {"check_hash_different": "ipv6-udp"},
        },
        # ipv4/ipv6 tcp/sctp
        {"send_packet": mac_ipv4_basic_pkt, "action": {"check_no_hash": "ip-ipv4"}},
        {"send_packet": mac_ipv6_basic_pkt, "action": {"check_no_hash": "ip-ipv6"}},
        {
            "send_packet": mac_ipv4_tcp_basic_pkt,
            "action": {"check_no_hash": "ipv4-tcp"},
        },
        {
            "send_packet": mac_ipv6_tcp_basic_pkt,
            "action": {"check_no_hash": "ipv6-tcp"},
        },
        {
            "send_packet": mac_ipv4_sctp_basic_pkt,
            "action": {"check_no_hash": "ipv4-sctp"},
        },
        {
            "send_packet": mac_ipv6_sctp_basic_pkt,
            "action": {"check_no_hash": "ipv6-sctp"},
        },
    ],
}

command_line_option_disable_rss = {
    "sub_casename": "command_line_option_disable",
    "port_id": 0,
    "test": [
        # all
        {"send_packet": mac_ipv4_basic_pkt, "action": {"check_no_hash": "ip-ipv4"}},
        {"send_packet": mac_ipv4_basic_pkt, "action": {"check_no_hash": "ip-ipv6"}},
        {
            "send_packet": mac_ipv4_tcp_basic_pkt,
            "action": {"check_no_hash": "ipv4-tcp"},
        },
        {
            "send_packet": mac_ipv6_tcp_basic_pkt,
            "action": {"check_no_hash": "ipv6-tcp"},
        },
        {
            "send_packet": mac_ipv4_udp_basic_pkt,
            "action": {"check_no_hash": "ipv4-udp"},
        },
        {
            "send_packet": mac_ipv6_udp_basic_pkt,
            "action": {"check_no_hash": "ipv6-udp"},
        },
        {
            "send_packet": mac_ipv4_sctp_basic_pkt,
            "action": {"check_no_hash": "ipv4-sctp"},
        },
        {
            "send_packet": mac_ipv6_sctp_basic_pkt,
            "action": {"check_no_hash": "ipv6-sctp"},
        },
    ],
}

rss_configure_to_ip = {
    "sub_casename": "rss_configure_to_ip",
    "port_id": 0,
    "test": command_line_option_rss_ip["test"],
}

rss_configure_to_udp = eval(
    str(command_line_option_rss_udp).replace(
        "command_line_option_rss_udp", "rss_configure_to_udp"
    )
)

rss_configure_to_tcp = eval(
    str(rss_configure_to_udp)
    .replace("to_udp", "to_tcp")
    .replace("/UDP", "/UDP1")
    .replace("-udp", "-udp1")
    .replace("/TCP", "/UDP")
    .replace("-tcp", "-udp")
    .replace("/UDP1", "/TCP")
    .replace("-udp1", "-tcp")
)

rss_configure_to_sctp = eval(
    str(rss_configure_to_udp)
    .replace("to_udp", "to_sctp")
    .replace("/UDP", "/UDP1")
    .replace("-udp", "-udp1")
    .replace("/SCTP", "/UDP")
    .replace("-sctp", "-udp")
    .replace("/UDP1", "/SCTP")
    .replace("-udp1", "-sctp")
)

rss_configure_to_all = eval(
    str(command_line_option_rss_ip)
    .replace("to_udp", "to_all")
    .replace("check_hash_same", "check_hash_different")
)

rss_configure_to_default = eval(
    str(command_line_option_rss_ip)
    .replace("to_udp", "to_all")
    .replace("check_hash_same", "check_hash_different")
)


class RSSConfigureTest(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.dut.bind_interfaces_linux(self.drivername)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        # self.cores = "1S/8C/1T"
        self.pmdout = PmdOutput(self.dut)

        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.__tx_iface = self.tester.get_interface(localPort)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]["pci"]
        self.verify(
            self.nic
            in ["ICE_25G-E810C_SFP", "ICE_25G-E810_XXV_SFP", "ICE_100G-E810C_QSFP"],
            "%s nic not support ethertype filter" % self.nic,
        )
        self.rsspro = RssProcessing(self, self.pmdout, [self.__tx_iface], rxq=16)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def launch_testpmd(self, line_option="", rss_type=""):
        self.pmdout.start_testpmd(
            ports=[self.pf_pci], param="--rxq=16 --txq=16 " + line_option
        )
        self.pmdout.execute_cmd("set fwd rxonly")
        self.pmdout.execute_cmd("set verbose 1")
        if rss_type != "":
            self.pmdout.execute_cmd("port config all rss %s" % rss_type)
        self.pmdout.execute_cmd("start")

    def test_command_line_option_rss_ip(self):
        self.launch_testpmd(line_option="--rss-ip")
        self.rsspro.handle_rss_distribute_cases(command_line_option_rss_ip)

    def test_command_line_option_rss_udp(self):
        self.launch_testpmd(line_option="--rss-udp")
        self.rsspro.handle_rss_distribute_cases(command_line_option_rss_udp)

    def test_command_line_option_rss_disable(self):
        self.launch_testpmd(line_option="--disable-rss")
        self.rsspro.handle_rss_distribute_cases(command_line_option_disable_rss)

    def test_command_line_option_rss_default(self):
        self.launch_testpmd()
        self.rsspro.handle_rss_distribute_cases(command_line_option_rss_ip)

    def test_rss_configure_to_ip(self):
        self.launch_testpmd(rss_type="ip")
        self.rsspro.handle_rss_distribute_cases(rss_configure_to_ip)

    def test_rss_configure_to_udp(self):
        self.launch_testpmd(rss_type="udp")
        self.rsspro.handle_rss_distribute_cases(rss_configure_to_udp)

    def test_rss_configure_to_tcp(self):
        self.launch_testpmd(rss_type="tcp")
        self.rsspro.handle_rss_distribute_cases(rss_configure_to_tcp)

    def test_rss_configure_to_sctp(self):
        self.launch_testpmd(rss_type="sctp")
        self.rsspro.handle_rss_distribute_cases(rss_configure_to_sctp)

    def test_rss_configure_to_all(self):
        self.launch_testpmd(rss_type="all")
        self.rsspro.handle_rss_distribute_cases(rss_configure_to_all)

    def test_rss_configure_to_default(self):
        self.launch_testpmd(rss_type="default")
        self.rsspro.handle_rss_distribute_cases(rss_configure_to_default)

    def test_rss_configure_to_none(self):
        self.launch_testpmd(rss_type="none")
        self.rsspro.handle_rss_distribute_cases(command_line_option_disable_rss)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.pmdout.execute_cmd("quit", "# ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
