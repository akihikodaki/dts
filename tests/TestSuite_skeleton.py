# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2016 Intel Corporation
#

"""
DPDK Test suite.
Test Skeleton.
"""
import string
import time

import framework.utils as utils
from framework.test_case import TestCase


class TestSkeleton(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        timer prerequistites
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")

        cores = self.dut.get_core_list("1S/2C/1T")
        self.coremask = utils.create_mask(cores)

        self.mac = self.dut.get_mac_address(self.dut_ports[0])
        self.app_skeleton_path = self.dut.apps_name["skeleton"]
        self.path = "./%s/build/basicfwd" % self.app_skeleton_path
        out = self.dut.build_dpdk_apps("./examples/skeleton")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_skeleton(self):
        eal_para = self.dut.create_eal_parameters(cores="1S/2C/1T")
        cmd = self.path + " %s " % eal_para
        self.dut.send_expect(cmd, "forwarding packets", 60)

        time.sleep(5)

        self.iface_port0 = self.tester.get_interface(
            self.tester.get_local_port(self.dut_ports[0])
        )
        self.iface_port1 = self.tester.get_interface(
            self.tester.get_local_port(self.dut_ports[1])
        )

        self.inst_port1 = self.tester.tcpdump_sniff_packets(self.iface_port1)
        self.scapy_send_packet(self.iface_port0)

        out_port1 = self.get_tcpdump_package(self.inst_port1)
        self.verify(
            self.mac in out_port1, "Wrong: can't get package at %s " % self.inst_port1
        )

    def scapy_send_packet(self, iface):
        """
        Send a packet to port
        """
        self.tester.scapy_append(
            'sendp([Ether(dst="%s")/IP()/UDP()/Raw(\'X\'*18)], iface="%s", count=4)'
            % (self.mac, iface)
        )
        self.tester.scapy_execute()

    def get_tcpdump_package(self, inst):
        pkts = self.tester.load_tcpdump_sniff_packets(inst)
        dsts = []
        for i in range(len(pkts)):
            dst = pkts.strip_element_layer2("dst", p_index=i)
            dsts.append(dst)
        return dsts

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
