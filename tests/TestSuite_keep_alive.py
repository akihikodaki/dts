# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2016 Intel Corporation
#

"""
DPDK Test suite.
Test keep alive
"""

import re
import time

import framework.utils as utils
from framework.test_case import TestCase


class TestKeepAlive(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        cores = self.dut.get_core_list("1S/4C/1T")
        self.coremask = utils.create_mask(cores)
        self.app_l2fwd_keepalive_path = self.dut.apps_name["l2fwd-keepalive"]

        # build sample app
        out = self.dut.build_dpdk_apps("./examples/l2fwd-keepalive")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_keep_alive(self):
        """
        Verify netmap compatibility with one port
        """
        eal_para = self.dut.create_eal_parameters(cores=list(range(4)))
        cmd = self.app_l2fwd_keepalive_path + " %s -- -q 8 -p ffff -K 10" % eal_para

        self.dut.send_expect(cmd, "Port statistics", 60)

        self.scapy_send_packet(2000)
        out = self.dut.get_session_output(timeout=10)
        print(out)
        p = re.compile(r"\d+")
        result = p.findall(out)
        amount = 2000 * len(self.dut_ports)
        self.verify(str(amount) in result, "Wrong: can't get <%d> package" % amount)

    def scapy_send_packet(self, nu):
        """
        Send a packet to port
        """
        for i in range(len(self.dut_ports)):
            txport = self.tester.get_local_port(self.dut_ports[i])
            mac = self.dut.get_mac_address(self.dut_ports[i])
            txItf = self.tester.get_interface(txport)
            self.tester.scapy_append(
                'sendp([Ether(dst="%s")/IP()/UDP()/Raw(\'X\'*18)], iface="%s",count=%s)'
                % (mac, txItf, nu)
            )
            self.tester.scapy_execute()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        time.sleep(2)
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
