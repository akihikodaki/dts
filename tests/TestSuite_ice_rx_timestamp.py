# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import copy
import os
import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.utils import GREEN, RED

tv_packets_basic = {
    "tv_mac": 'Ether(dst="68:05:CA:C1:BA:28")/("X"*480)',
    "tv_mac_ipv4": 'Ether(dst="68:05:CA:C1:BA:28")/IP(src="192.168.0.2",dst="192.168.0.3")/("X"*480)',
    "tv_mac_ipv6": 'Ether(dst="68:05:CA:C1:BA:28")/IPv6(src="2001::2", dst="2001::3")/("X"*480)',
    "tv_mac_ipv4_udp": 'Ether(dst="68:05:CA:C1:BA:28")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=1026, dport=1027)/("X"*480)',
    "tv_mac_ipv6_udp": 'Ether(dst="68:05:CA:C1:BA:28")/IPv6(src="2001::2", dst="2001::3")/UDP(sport=1026, dport=1027)/("X"*480)',
    "tv_mac_ipv4_tcp": 'Ether(dst="68:05:CA:C1:BA:28")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=1026, dport=1027)/("X"*480)',
    "tv_mac_ipv6_tcp": 'Ether(dst="68:05:CA:C1:BA:28")/IPv6(src="2001::2", dst="2001::3")/TCP(sport=1026, dport=1027)/("X"*480)',
    "tv_mac_ipv4_sctp": 'Ether(dst="68:05:CA:C1:BA:28")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=1026, dport=1027)/("X"*480)',
    "tv_mac_ipv6_sctp": 'Ether(dst="68:05:CA:C1:BA:28")/IPv6(src="2001::2", dst="2001::3")/SCTP(sport=1026, dport=1027)/("X"*480)',
}

command_line_option_with_timestamp = {
    "port_id": 0,
    "test": [
        {
            "send_packet": tv_packets_basic["tv_mac"],
            "action": {"check_timestamp": "ether"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4"],
            "action": {"check_timestamp": "ipv4"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6"],
            "action": {"check_timestamp": "ipv6"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_udp"],
            "action": {"check_timestamp": "ipv4-udp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_udp"],
            "action": {"check_timestamp": "ipv6-udp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_tcp"],
            "action": {"check_timestamp": "ipv4-tcp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_tcp"],
            "action": {"check_timestamp": "ipv6-tcp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv4_sctp"],
            "action": {"check_timestamp": "ipv4-sctp"},
        },
        {
            "send_packet": tv_packets_basic["tv_mac_ipv6_sctp"],
            "action": {"check_timestamp": "ipv6-sctp"},
        },
    ],
}


class TestICERxTimestamp(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
        """
        self.verify(
            self.nic
            in ["ICE_25G-E810C_SFP", "ICE_100G-E810C_QSFP", "ICE_25G-E823C_QSFP"],
            "%s nic not support timestamp" % self.nic,
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.pkt = Packet()
        self.pmdout = PmdOutput(self.dut)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]["pci"]

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def launch_testpmd(self, line_option=""):
        """
        start testpmd
        """
        # Prepare testpmd EAL and parameters
        self.pmdout.start_testpmd(
            param=line_option,
            eal_param=f"-a {self.pf_pci}",
            socket=self.ports_socket,
        )
        # test link status
        res = self.pmdout.wait_link_status_up("all", timeout=15)
        self.verify(res is True, "there have port link is down")
        self.pmdout.execute_cmd("set fwd rxonly")
        self.pmdout.execute_cmd("set verbose 1")
        self.pmdout.execute_cmd("start")

    def check_timestamp_increment(self, out):
        timestamps = self.get_timestamp(out)
        if len(timestamps) == 0:
            error_msg = "There is no timestamp value"
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)
        else:
            for i in range(len(timestamps) - 1):
                if timestamps[i + 1] <= timestamps[i]:
                    error_msg = "The timestamp values should be increment"
                    self.logger.error(error_msg)
                    self.error_msgs.append(error_msg)

    def check_no_timestamp(self, out):
        timestamps = self.get_timestamp(out)
        if len(timestamps) != 0:
            error_msg = "The timestamp value should be empty"
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)

    def send_pkt_get_output(self, pkts, port_id=0, count=3):
        self.logger.info("----------send packet-------------")
        self.logger.info("{}".format(pkts))
        self.pkt.update_pkt(pkts)
        self.pkt.send_pkt(crb=self.tester, tx_port=self.tester_iface0, count=count)
        out = self.pmdout.get_output(timeout=1)
        pkt_pattern = (
            "port\s%d/queue\s\d+:\sreceived\s(\d+)\spackets.+?\n.*length=\d{2,}\s"
            % port_id
        )
        reveived_data = re.findall(pkt_pattern, out)
        reveived_pkts = sum(map(int, [i[0] for i in reveived_data]))
        return out

    def get_timestamp(self, out):
        timestamp_pat = ".*timestamp\s(\w+)"
        timestamp_infos = re.findall(timestamp_pat, out, re.M)
        timestamp_infos = list(map(int, timestamp_infos))
        self.logger.info("timestamp_infos: {}".format(timestamp_infos))
        return timestamp_infos

    def handle_timestamp_case(self, case_info, enable_timestamp=True):
        self.error_msgs = []
        out = ""
        # handle tests
        tests = case_info["test"]
        for test in tests:
            if "send_packet" in test:
                out = self.send_pkt_get_output(test["send_packet"])
            if "action" in test:
                if enable_timestamp:
                    self.check_timestamp_increment(out)
                else:
                    self.check_no_timestamp(out)
        self.verify(not self.error_msgs, "some cases failed")

    def test_without_timestamp(self):
        self.launch_testpmd(line_option="--rxq=16 --txq=16")
        self.handle_timestamp_case(
            command_line_option_with_timestamp, enable_timestamp=False
        )

    def test_single_queue_with_timestamp(self):
        self.launch_testpmd(line_option="--enable-rx-timestamp")
        self.handle_timestamp_case(command_line_option_with_timestamp)

    def test_multi_queues_with_timestamp(self):
        self.launch_testpmd(line_option="--rxq=16 --txq=16 --enable-rx-timestamp")
        self.handle_timestamp_case(command_line_option_with_timestamp)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.pmdout.execute_cmd("quit", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
