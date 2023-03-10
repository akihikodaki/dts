# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2015 Intel Corporation
#

"""
DPDK Test suite.

Test the support of VLAN Offload Features by Poll Mode Drivers.

"""

import time

import framework.utils as utils
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestVlan(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.


        Vlan Prerequisites
        """
        global dutRxPortId
        global dutTxPortId

        # Based on h/w type, choose how many ports to use
        ports = self.dut.get_ports()

        self.dut_ports = self.dut.get_ports(self.nic)
        self.used_dut_port_0 = self.dut_ports[0]
        self.used_tester_port = self.tester.get_local_port(self.used_dut_port_0)
        self.tester_intf_0 = self.tester.get_interface(self.used_tester_port)

        # Verify that enough ports are available
        self.verify(len(ports) >= 1, "Insufficient ports")

        valports = [_ for _ in ports if self.tester.get_local_port(_) != -1]
        dutRxPortId = valports[0]
        dutTxPortId = valports[0]
        portMask = utils.create_mask(valports[:1])

        self.pmdout = PmdOutput(self.dut)
        self.pmdout.start_testpmd(
            "Default", "--portmask=%s --port-topology=loop" % portMask
        )
        # Get the firmware version information
        try:
            self.fwversion, _, _ = self.pmdout.get_firmware_version(
                self.dut_ports[0]
            ).split()
        except ValueError:
            # nic IXGBE, IGC
            self.fwversion = self.pmdout.get_firmware_version(self.dut_ports[0]).split()
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("set promisc all off", "testpmd> ")
        self.dut.send_expect("vlan set filter on %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("vlan set strip off %s" % dutRxPortId, "testpmd> ")
        self.vlan = 51

    def get_tcpdump_package(self):
        pkts = self.tester.load_tcpdump_sniff_packets(self.inst)
        vlans = []
        for i in range(len(pkts)):
            vlan = pkts.strip_element_vlan("vlan", p_index=i)
            vlans.append(vlan)
        return vlans

    def vlan_send_packet(self, vid, num=1):
        """
        Send $num of packets to portid, if vid is -1, it means send a packet which does not include a vlan id.
        """
        self.pmdout.wait_link_status_up(dutRxPortId)
        # The package stream : testTxPort->dutRxPort->dutTxport->testRxPort
        port = self.tester.get_local_port(dutRxPortId)
        self.txItf = self.tester.get_interface(port)
        self.smac = self.tester.get_mac(port)

        port = self.tester.get_local_port(dutTxPortId)
        self.rxItf = self.tester.get_interface(port)

        # the packet dest mac must is dut tx port id when the port promisc is off
        self.dmac = self.dut.get_mac_address(dutRxPortId)

        self.inst = self.tester.tcpdump_sniff_packets(self.rxItf)
        # FIXME  send a burst with only num packet
        if vid == -1:
            pkt = Packet(pkt_type="UDP")
            pkt.config_layer("ether", {"dst": self.dmac, "src": self.smac})
        else:
            pkt = Packet(pkt_type="VLAN_UDP")
            pkt.config_layer("ether", {"dst": self.dmac, "src": self.smac})
            pkt.config_layer("vlan", {"vlan": vid})

        pkt.send_pkt(self.tester, tx_port=self.txItf, count=4, timeout=30)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_vlan_enable_receipt_strip_off(self):
        """
        Enable receipt of VLAN packets and strip off
        """
        self.dut.send_expect(
            "rx_vlan add %d %s" % (self.vlan, dutRxPortId), "testpmd> "
        )
        # Because the kernel forces enable Qinq and cannot be closed,
        # the dpdk can only add 'extend on' to make the VLAN filter work normally.
        if self.kdriver == "i40e" and self.fwversion >= "8.40":
            self.dut.send_expect("vlan set extend on %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("vlan set strip off  %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)
        out = self.dut.send_expect("show port info %s" % dutRxPortId, "testpmd> ", 20)
        self.verify("strip off" in out, "Wrong strip:" + out)

        self.vlan_send_packet(self.vlan)
        out = self.get_tcpdump_package()
        self.verify(self.vlan in out, "Wrong vlan:" + str(out))

        notmatch_vlan = self.vlan + 1
        self.vlan_send_packet(notmatch_vlan)
        out = self.get_tcpdump_package()
        self.verify(len(out) == 0, "Received unexpected packet, filter not work!!!")
        self.verify(notmatch_vlan not in out, "Wrong vlan:" + str(out))

        self.dut.send_expect("stop", "testpmd> ")

    def test_vlan_disable_receipt(self):
        """
        Disable receipt of VLAN packets
        """
        self.dut.send_expect("rx_vlan rm %d %s" % (self.vlan, dutRxPortId), "testpmd> ")
        # Because the kernel forces enable Qinq and cannot be closed,
        # the dpdk can only add 'extend on' to make the VLAN filter work normally.
        if self.kdriver == "i40e" and self.fwversion >= "8.40":
            self.dut.send_expect("vlan set extend on %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)
        self.vlan_send_packet(self.vlan)

        out = self.get_tcpdump_package()
        self.verify(len(out) == 0, "Received unexpected packet, filter not work!!!")
        self.verify(self.vlan not in out, "Wrong vlan:" + str(out))
        self.dut.send_expect("stop", "testpmd> ")

    def test_vlan_enable_receipt_strip_on(self):
        """
        Enable receipt of VLAN packets and strip on
        """
        self.dut.send_expect("vlan set strip on %s" % dutRxPortId, "testpmd> ", 20)
        self.dut.send_expect(
            "rx_vlan add %d %s" % (self.vlan, dutRxPortId), "testpmd> ", 20
        )
        out = self.dut.send_expect("show port info %s" % dutRxPortId, "testpmd> ", 20)
        self.verify("strip on" in out, "Wrong strip:" + out)

        self.dut.send_expect("start", "testpmd> ", 120)
        self.vlan_send_packet(self.vlan)
        out = self.get_tcpdump_package()
        self.verify(len(out), "Forwarded vlan packet not received!!!")
        self.verify(self.vlan not in out, "Wrong vlan:" + str(out))
        self.dut.send_expect("stop", "testpmd> ", 120)

    def test_vlan_enable_vlan_insertion(self):
        """
        Enable VLAN header insertion in transmitted packets
        """
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect(
            "tx_vlan set %s %d" % (dutTxPortId, self.vlan), "testpmd> "
        )
        self.dut.send_expect("port start all", "testpmd> ")

        filter = [{"layer": "ether", "config": {"dst": "not ff:ff:ff:ff:ff:ff"}}]
        inst = self.tester.tcpdump_sniff_packets(
            intf=self.tester_intf_0,
            filters=filter,
        )
        self.dut.send_expect("set nbport 1", "testpmd> ")
        self.dut.send_expect("start tx_first", "testpmd> ")
        pkts = self.tester.load_tcpdump_sniff_packets(inst)
        self.verify(len(pkts) > 0, f"no packets received.")
        self.verify(
            self.vlan == pkts[0].vlan,
            f"Vlan id {self.vlan} is not found in the packet.",
        )
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect("tx_vlan reset %s" % dutTxPortId, "testpmd> ", 30)
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("stop", "testpmd> ", 30)

    def tear_down(self):
        """
        Run after each test case.
        """
        if self.kdriver == "i40e" and self.fwversion >= "8.40":
            self.dut.send_expect("vlan set extend off %s" % dutRxPortId, "testpmd> ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("quit", "# ", 30)
        self.dut.kill_all()
