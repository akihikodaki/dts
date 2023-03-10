# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.
Test Scattered Packets.
"""
import time

from framework.packet import Packet, strip_pktload
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

#
#
# Test class.
#


class TestScatter(TestCase):
    #
    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Scatter Prerequisites
        """
        dutPorts = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(dutPorts) >= 1, "Insufficient ports")
        self.port = dutPorts[0]
        tester_port = self.tester.get_local_port(self.port)
        self.intf = self.tester.get_interface(tester_port)

        self.pmdout = PmdOutput(self.dut)
        if self.nic in [
            "IXGBE_10G-X550EM_A_SFP",
            "IXGBE_10G-82599_SFP",
            "IXGBE_10G-X550T",
            "I40E_10G-X722_A0",
            "I40E_10G-SFP_XL710",
            "I40E_40G-QSFP_A",
            "I40E_40G-QSFP_B",
            "I40E_25G-25G_SFP28",
            "x722_37d2",
            "IXGBE_10G-82599_T3_LOM",
            "IXGBE_10G-X540T",
            "IXGBE_10G-82599_SFP_SF_QP",
            "I40E_10G-SFP_X722",
            "I40E_10G-10G_BASE_T_X722",
            "IXGBE_10G-X550EM_X_10G_T",
            "I40E_10G-10G_BASE_T_BC",
            "ICE_25G-E810C_SFP",
            "ICE_100G-E810C_QSFP",
            "ICE_25G-E823C_QSFP",
        ]:
            self.mbsize = 2048
        else:
            self.mbsize = 1024

        self.tester.send_expect("ifconfig %s mtu 9000" % self.intf, "#")

    def scatter_pktgen_send_packet(self, pktsize):
        """
        Functional test for scatter packets.
        """
        dmac = self.dut.get_mac_address(self.port)

        inst = self.tester.tcpdump_sniff_packets(self.intf)
        pkt = Packet(pkt_type="IP_RAW", pkt_len=pktsize)
        pkt.config_layer("ether", {"dst": dmac})
        pkt.send_pkt(self.tester, tx_port=self.intf)
        sniff_pkts = self.tester.load_tcpdump_sniff_packets(inst)

        res = ""
        if len(sniff_pkts):
            res = strip_pktload(sniff_pkts, layer="L4")
        return res

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_scatter_mbuf_2048(self):
        """
        Scatter 2048 mbuf
        """
        out = self.pmdout.start_testpmd(
            "1S/2C/1T",
            "--mbcache=200 --mbuf-size=%d --portmask=0x1 "
            "--max-pkt-len=9000 --port-topology=loop --tx-offloads=0x00008000"
            % (self.mbsize),
        )

        self.verify("Error" not in out, "launch error 1")

        self.dut.send_expect("set fwd mac", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ")
        self.pmdout.wait_link_status_up(self.port)

        for offset in [-1, 0, 1, 4, 5]:
            ret = self.scatter_pktgen_send_packet(self.mbsize + offset)
            self.verify("58 58 58 58 58 58 58 58" in ret, "packet receive error")

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.tester.send_expect("ifconfig %s mtu 1500" % self.intf, "#")
