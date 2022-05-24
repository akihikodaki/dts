# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

import os
import re
import time

import framework.packet as packet
import framework.utils as utils
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestFlowFiltering(TestCase):
    def set_up_all(self):
        """
        Run before each test suite
        """
        # initialize ports topology
        self.dut_ports = self.dut.get_ports(self.nic)
        self.dts_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.txitf = self.tester.get_interface(
            self.tester.get_local_port(self.dut_ports[0])
        )
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        out = self.dut.build_dpdk_apps("./examples/flow_filtering")
        self.verify("Error" not in out, "Compilation failed")

    def set_up(self):
        """
        Run before each test case.
        """
        self.eal_para = self.dut.create_eal_parameters(cores=[1])
        cmd = self.dut.apps_name["flow_filtering"] + self.eal_para
        out = self.dut.send_command(cmd, timeout=15)
        self.verify("Error" not in out, "flow launch failed")

    def send_packet(self, pkg):
        """
        Send packets according to parameters.
        """
        self.pkt = packet.Packet()
        for packet_type in list(pkg.keys()):
            self.pkt.append_pkt(pkg[packet_type])
        self.pkt.send_pkt(crb=self.tester, tx_port=self.txitf, count=1)

        time.sleep(2)

    def check_flow_queue(self):
        """
        Get dut flow result
        """
        result = self.dut.get_session_output(timeout=2)
        if str.upper(self.dts_mac) in result:
            self.verify("queue" in result, "Dut receive flow failed!")
            queue_result = re.findall(r"queue=(\S+)", result)
            return queue_result
        else:
            raise Exception("Dut not receive correct package!")

    def test_flow_filtering_match_rule(self):
        pkg = {
            "IP/src1": 'Ether(dst="%s")/IP(src="0.0.0.0", dst="192.168.1.1")/Raw("x"*20)'
            % self.dts_mac,
            "IP/src2": 'Ether(dst="%s")/IP(src="0.0.0.1", dst="192.168.1.1")/Raw("x"*20)'
            % self.dts_mac,
        }
        self.send_packet(pkg)
        queue_list = self.check_flow_queue()
        self.verify(len(queue_list) == 2, "Dut receive flow queue error!")
        self.verify(
            queue_list[0] == queue_list[1] and queue_list[0] == "0x1",
            "Flow filter not match rule!",
        )

    def test_flow_filtering_dismatch_rule(self):
        pkg = {
            "IP/dst": 'Ether(dst="%s")/IP(src="0.0.0.0", dst="192.168.1.2")/Raw("x"*20)'
            % self.dts_mac
        }
        self.send_packet(pkg)
        queue_list = self.check_flow_queue()
        self.verify(
            len(queue_list) == 1 and queue_list[0] != "0x1", "Dismatch rule failed!"
        )

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("^C", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
