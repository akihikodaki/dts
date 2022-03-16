# BSD LICENSE
#
# Copyright(c) 2021 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json
import os
import re
import time

from scapy.contrib.gtp import *

import framework.packet as packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

from .rte_flow_common import RssProcessing

tv_packets_basic = {
    "tv_mac_ipv4": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*40)',
    "tv_mac_ipv6": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/("X"*40)',
    "tv_mac_ipv4_udp": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=1024,dport=1025)/("X"*40)',
    "tv_mac_ipv6_udp": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/UDP(sport=1024,dport=1025)/("X"*40)',
    "tv_mac_ipv4_tcp": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.3")/TCP(sport=1024,dport=1025)/("X"*40)',
    "tv_mac_ipv6_tcp": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/TCP(sport=1024,dport=1025)/("X"*40)',
    "tv_mac_ipv4_sctp": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.3")/SCTP(sport=1024,dport=1025)/("X"*40)',
    "tv_mac_ipv6_sctp": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="3ffe:2501:200:3::2",dst="3ffe:2501:200:3::3")/SCTP(sport=1024,dport=1025)/("X"*40)',
}

tvs_mac_ip = {
    "sub_casename": "tv_mac_ip",
    "port_id": 0,
    "test": [
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4"],
            "action": {"save_hash": "ipv4"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6"],
            "action": {"save_hash": "ipv6"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_udp"],
            "action": {"check_hash_same": "ipv4"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_udp"],
            "action": {"check_hash_same": "ipv6"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_tcp"],
            "action": {"check_hash_same": "ipv4"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_tcp"],
            "action": {"check_hash_same": "ipv6"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_sctp"],
            "action": {"check_hash_same": "ipv4"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_sctp"],
            "action": {"check_hash_same": "ipv6"},
        },
    ],
}

tvs_mac_udp = {
    "sub_casename": "tv_mac_udp",
    "port_id": 0,
    "test": [
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_udp"],
            "action": {"save_hash", "ipv4_udp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_udp"],
            "action": {"save_hash", "ipv6_udp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_tcp"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_tcp"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_sctp"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_sctp"],
            "action": "check_no_hash",
        },
    ],
}

tvs_mac_tcp = {
    "sub_casename": "tv_mac_tcp",
    "port_id": 0,
    "test": [
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_tcp"],
            "action": {"save_hash", "ipv4_tcp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_tcp"],
            "action": {"save_hash", "ipv6_tcp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_udp"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_udp"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_sctp"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_sctp"],
            "action": "check_no_hash",
        },
    ],
}

tvs_mac_sctp = {
    "sub_casename": "tv_mac_sctp",
    "port_id": 0,
    "test": [
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_sctp"],
            "action": {"save_hash", "ipv4_sctp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_sctp"],
            "action": {"save_hash", "ipv6_sctp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_udp"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_udp"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_tcp"],
            "action": "check_no_hash",
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_tcp"],
            "action": "check_no_hash",
        },
    ],
}

tvs_mac_all = {
    "sub_casename": "tvs_mac_all",
    "port_id": 0,
    "test": [
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4"],
            "action": {"save_hash", "ipv4_all"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6"],
            "action": {"save_hash", "ipv6_all"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_udp"],
            "action": {"check_hash_different", "ipv4_all"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_udp"],
            "action": {"check_hash_different", "ipv6_all"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_tcp"],
            "action": {"check_hash_different", "ipv4_all"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_tcp"],
            "action": {"check_hash_different", "ipv6_all"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_sctp"],
            "action": {"check_hash_different", "ipv4_all"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_sctp"],
            "action": {"check_hash_different", "ipv6_all"},
        },
    ],
}

tvs_mac_disable_rss = eval(
    str(tvs_mac_all)
    .replace("save_hash", "check_no_hash")
    .replace("check_hash_different", "check_no_hash")
)


class IAVFRSSConfigureTest(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.cores = "1S/5C/1T"
        # check core num
        core_list = self.dut.get_core_list(self.cores)
        self.verify(len(core_list) >= 5, "Insufficient cores for testing")

        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "vfio-pci"
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.create_vf()

        self.queue_num = 16
        self.param = " --rxq={} --txq={} ".format(self.queue_num, self.queue_num)
        self.pmdout = PmdOutput(self.dut)
        self.launch_testpmd(param=self.param)
        self.rssprocess = RssProcessing(
            self, self.pmdout, [self.tester_iface0], self.queue_num
        )
        self.dut_session = self.dut.new_session()

    def set_up(self):
        """
        Run before each test case.
        """
        # check testpmd process status
        cmd = "ps -aux | grep testpmd | grep -v grep"
        out = self.dut_session.send_expect(cmd, "#", 15)
        if "testpmd" not in out:
            self.restart_testpmd()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.pmdout.execute_cmd("stop")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("quit", "#")
        self.destroy_vf()
        self.dut.kill_all()

    def launch_testpmd(self, param=""):
        """
        start testpmd
        """
        # Prepare testpmd EAL and parameters
        self.pmdout.start_testpmd(
            cores=self.cores,
            param=param,
            eal_param=f"-a {self.vf0_pci}",
            socket=self.ports_socket,
        )
        # test link status
        res = self.pmdout.wait_link_status_up("all", timeout=15)
        self.verify(res is True, "there have port link is down")
        self.pmdout.execute_cmd("set fwd rxonly", "testpmd> ", 15)
        self.pmdout.execute_cmd("set verbose 1", "testpmd> ", 15)

    def restart_testpmd(self, cmd_line=""):
        """
        some case need to restart testpmd with param
        """
        self.pmdout.quit()
        params = self.param + cmd_line
        self.launch_testpmd(param=params)
        self.pmdout.execute_cmd("start")

    def create_vf(self):
        self.dut.bind_interfaces_linux("ice")
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[0], 1)
        self.sriov_vfs_port = self.dut.ports_info[self.dut_ports[0]]["vfs_port"]
        self.dut.send_expect("ifconfig %s up" % self.pf0_intf, "# ")
        self.dut.send_expect(
            "ip link set %s vf 0 mac 00:11:22:33:44:55" % self.pf0_intf, "#"
        )
        self.vf0_pci = self.sriov_vfs_port[0].pci
        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_driver)
        except Exception as e:
            self.destroy_vf()
            raise Exception(e)

    def destroy_vf(self):
        self.dut.send_expect("quit", "# ", 60)
        time.sleep(2)
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])

    def set_rss_configure(self, rss_type):
        if rss_type != "":
            self.pmdout.execute_cmd("port config all rss %s" % rss_type)
        self.pmdout.execute_cmd("start")

    def test_iavf_rss_configure_to_ip(self):
        self.set_rss_configure(rss_type="ip")
        self.rssprocess.handle_rss_distribute_cases(cases_info=tvs_mac_ip)

    def test_iavf_rss_configure_to_udp(self):
        self.set_rss_configure(rss_type="udp")
        self.rssprocess.handle_rss_distribute_cases(cases_info=tvs_mac_udp)

    def test_iavf_rss_configure_to_tcp(self):
        self.set_rss_configure(rss_type="tcp")
        self.rssprocess.handle_rss_distribute_cases(cases_info=tvs_mac_tcp)

    def test_iavf_rss_configure_to_sctp(self):
        self.set_rss_configure(rss_type="sctp")
        self.rssprocess.handle_rss_distribute_cases(cases_info=tvs_mac_sctp)

    def test_iavf_rss_configure_to_all(self):
        self.set_rss_configure(rss_type="all")
        self.rssprocess.handle_rss_distribute_cases(cases_info=tvs_mac_all)

    def test_iavf_rss_configure_to_none(self):
        self.set_rss_configure(rss_type="none")
        self.rssprocess.handle_rss_distribute_cases(cases_info=tvs_mac_disable_rss)

    def test_iavf_rss_command_line_to_ip(self):
        self.restart_testpmd(cmd_line="--rss-ip")
        self.rssprocess.handle_rss_distribute_cases(cases_info=tvs_mac_ip)

    def test_iavf_rss_command_line_to_udp(self):
        self.restart_testpmd(cmd_line="--rss-udp")
        self.rssprocess.handle_rss_distribute_cases(cases_info=tvs_mac_udp)

    def test_iavf_rss_command_line_to_none(self):
        self.restart_testpmd(cmd_line="--disable-rss")
        self.rssprocess.handle_rss_distribute_cases(cases_info=tvs_mac_disable_rss)

    def test_iavf_rss_command_line_to_default(self):
        self.restart_testpmd()
        self.rssprocess.handle_rss_distribute_cases(cases_info=tvs_mac_ip)
