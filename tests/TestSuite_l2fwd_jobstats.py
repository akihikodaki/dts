# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

"""
DPDK Test suite.
Test L2fwd Jobstats
"""

import re
import time

import framework.utils as utils
from framework.test_case import TestCase


class TestL2fwdJobstats(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.verify(
            self.nic
            not in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_40G-QSFP_B",
                "I40E_25G-25G_SFP28",
                "I40E_10G-SFP_X722",
                "I40E_10G-10G_BASE_T_X722",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.verify(len(self.dut.cores) >= 4, "Insufficient cores for testing")
        cores = self.dut.get_core_list("1S/4C/1T")
        self.coremask = utils.create_mask(cores)

        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        dut_port0 = self.dut_ports[0]
        dut_port1 = self.dut_ports[1]
        self.tx_ports = [dut_port0, dut_port1]

        # build sample app
        out = self.dut.build_dpdk_apps("./examples/l2fwd-jobstats")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_l2fwd_jobstats_check(self):
        """
        Verify l2fwd jobstats is correct
        """
        path = self.dut.apps_name["l2fwd-jobstats"]
        cmd = path + " %s -- -q 2 -p 0x03 -l" % (self.eal_para)
        self.dut.send_expect(cmd, "Port statistics", 60)

        self.scapy_send_packet(100000)
        out = self.dut.get_session_output(timeout=10)

        print(out)
        send_packets = re.findall(r"Total packets sent:\s+?(\d+?)\r", out)[-1]
        receive_packets = re.findall(r"Total packets received:\s+?(\d+?)\r", out)[-1]
        self.verify(
            send_packets == receive_packets == str(100000 * len(self.tx_ports)),
            "Wrong: can't receive enough packages",
        )

    def scapy_send_packet(self, count):
        """
        Send a packet to port
        """
        for i in range(len(self.tx_ports)):
            txport = self.tester.get_local_port(self.dut_ports[i])
            mac = self.dut.get_mac_address(self.dut_ports[i])
            txItf = self.tester.get_interface(txport)
            self.tester.scapy_append(
                'sendp([Ether(dst="02:00:00:00:00", src="%s")/IP()/UDP()/Raw(\'X\'*18)], iface="%s",count=%s)'
                % (mac, txItf, count)
            )
            self.tester.scapy_execute(timeout=120)

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
