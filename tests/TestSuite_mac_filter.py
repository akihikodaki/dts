# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.
Test the support of Allowlist Features by Poll Mode Drivers
"""

import operator
import random
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

MAX_VLAN = 4095


class TestMacFilter(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        Allowlist Prerequisites:
            Two Ports
            testpmd can normally started
        """
        self.frames_to_send = 4
        # Based on h/w type, choose how many ports to use
        self.dutPorts = self.dut.get_ports()
        # Verify that enough ports are available
        self.verify(len(self.dutPorts) >= 1, "Insufficient ports")

    def set_up(self):
        """
        Run before each test case.
        Nothing to do.
        """
        portMask = utils.create_mask(self.dutPorts[:1])
        self.pmdout = PmdOutput(self.dut)
        self.pmdout.start_testpmd("Default", "--portmask=%s" % portMask)
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        # get dest address from self.target port
        out = self.dut.send_expect("show port info %d" % self.dutPorts[0], "testpmd> ")

        self.dest = self.dut.get_mac_address(self.dutPorts[0])
        mac_scanner = r"MAC address: (([\dA-F]{2}:){5}[\dA-F]{2})"

        ret = utils.regexp(out, mac_scanner)
        self.verify(ret is not None, "MAC address not found")
        self.verify(operator.eq(ret.lower(), self.dest), "MAC address wrong")

        self.max_mac_addr = utils.regexp(
            out, "Maximum number of MAC addresses: ([0-9]+)"
        )

    def allowlist_send_packet(
        self, portid, destMac="00:11:22:33:44:55", count=-1, pkt_type="UDP", vlan=""
    ):
        """
        Send 1 packet to portid.
        """
        # You can't have an optional parameter use a class attribute as it's default value
        if count == -1:
            count = self.frames_to_send

        itf = self.tester.get_interface(self.tester.get_local_port(portid))
        if pkt_type == "VLAN_UDP" and vlan is not None:
            pkt = Packet(pkt_type="VLAN_UDP")
            pkt.config_layer("vlan", {"vlan": vlan})
            pkt.config_layer("ether", {"dst": destMac})
        else:
            pkt = Packet(pkt_type="UDP")
            pkt.config_layer("ether", {"src": "52:00:00:00:00:00", "dst": destMac})
        pkt.send_pkt(self.tester, tx_port=itf, count=count)

    def test_add_remove_mac_address(self):
        """
        Add mac address and check packet can received
        Remove mac address and check packet can't received
        """
        # initialise first port without promiscuous mode
        fake_mac_addr = "00:01:01:00:00:00"
        portid = self.dutPorts[0]
        self.dut.send_expect("set promisc %d off" % portid, "testpmd> ")
        self.dut.send_expect("clear port stats all", "testpmd> ")

        # send one packet with the portid MAC address
        self.allowlist_send_packet(portid, self.dest)

        # 82599 and Intel® Ethernet 700 Series have different packet statistics when using the
        # "show port stats" command. Packets number is stripped from log.
        out = self.dut.get_session_output()
        cur_rxpkt = utils.regexp(out, "received ([0-9]+) packets")
        # check the packet increase
        self.verify(
            int(cur_rxpkt) * self.frames_to_send == self.frames_to_send,
            "Packet has not been received on default address",
        )

        # send one packet to a different MAC address
        # new_mac = self.dut.get_mac_address(portid)
        self.allowlist_send_packet(portid, fake_mac_addr)
        out = self.dut.get_session_output()
        # check the packet DO NOT increase
        self.verify(
            "received" not in out,
            "Packet has been received on a new MAC address that has been removed from the port",
        )

        # add the different MAC address
        self.dut.send_expect(
            "mac_addr add %d" % portid + " %s" % fake_mac_addr, "testpmd>"
        )
        # send again one packet to a different MAC address
        self.allowlist_send_packet(portid, fake_mac_addr)
        out = self.dut.get_session_output()
        cur_rxpkt = utils.regexp(out, "received ([0-9]+) packets")
        # check the packet increase
        self.verify(
            int(cur_rxpkt) * self.frames_to_send == self.frames_to_send,
            "Packet has not been received on a new MAC address that has been added to the port",
        )

        # remove the fake MAC address
        self.dut.send_expect(
            "mac_addr remove %d" % portid + " %s" % fake_mac_addr, "testpmd>"
        )
        # send again one packet to a different MAC address
        self.allowlist_send_packet(portid, fake_mac_addr)
        out = self.dut.get_session_output()
        # check the packet increase
        self.verify(
            "received" not in out,
            "Packet has been received on a new MAC address that has been removed from the port",
        )
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)

    def test_invalid_addresses(self):
        """
        Invalid operation:
            Add NULL MAC should not be added
            Remove using MAC will be failed
            Add Same MAC twice will be failed
            Add more than MAX number will be failed
        """
        portid = self.dutPorts[0]
        fake_mac_addr = "00:00:00:00:00:00"

        # add an address with all zeroes to the port (-EINVAL)
        out = self.dut.send_expect(
            "mac_addr add %d" % portid + " %s" % fake_mac_addr, "testpmd>"
        )
        self.verify("Invalid argument" in out, "Added a NULL MAC address")

        # remove the default MAC address (-EADDRINUSE)
        out = self.dut.send_expect(
            "mac_addr remove %d" % portid + " %s" % self.dest, "testpmd>"
        )
        self.verify("Address already in use" in out, "default address removed")

        # add same address 2 times
        fake_mac_addr = "00:00:00:00:00:01"
        out = self.dut.send_expect(
            "mac_addr add %d" % portid + " %s" % fake_mac_addr, "testpmd>"
        )
        out = self.dut.send_expect(
            "mac_addr add %d" % portid + " %s" % fake_mac_addr, "testpmd>"
        )
        self.verify("error" not in out, "added 2 times the same address with an error")

        # add 1 address more that max number
        i = 0
        base_addr = "00:01:00:00:00:"
        while i < int(self.max_mac_addr):
            new_addr = base_addr + "%0.2X" % i
            out = self.dut.send_expect(
                "mac_addr add %d" % portid + " %s" % new_addr, "testpmd>"
            )
            i = i + 1

        self.verify(
            "No space left on device" in out,
            "added 1 address more than max MAC addresses",
        )
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)

    def test_multicast_filter(self):
        """
        Add mac address and check packet can received
        Remove mac address and check packet can't received
        """
        # initialise first port without promiscuous mode
        random_vlan = random.randint(1, MAX_VLAN)
        mcast_addr = "01:00:5E:00:00:00"
        portid = self.dutPorts[0]
        self.dut.send_expect(f"set promisc {portid:d} off", "testpmd> ")
        self.dut.send_expect("clear port stats all", "testpmd> ")

        self.dut.send_expect(f"mcast_addr add {portid:d} {mcast_addr}", "testpmd>")
        self.allowlist_send_packet(portid, mcast_addr, count=1)
        time.sleep(1)
        out = self.dut.get_session_output()
        self.verify(
            "received" in out,
            "Packet has not been received when it should have on a broadcast address",
        )
        # enable vlan filter
        self.dut.send_expect("vlan set filter on 0", "testpmd> ")
        self.dut.send_expect("rx_vlan add %d 0" % random_vlan, "testpmd> ")
        # passed vlan id
        self.allowlist_send_packet(
            portid, destMac=mcast_addr, pkt_type="VLAN_UDP", vlan=random_vlan
        )
        out = self.dut.get_session_output()
        self.verify("received" in out, "Not receive vlan packet with multicast mac!!!")
        # wrong vlan id
        self.allowlist_send_packet(
            portid, destMac=mcast_addr, pkt_type="VLAN_UDP", vlan=random_vlan - 1
        )
        out = self.dut.get_session_output()
        self.verify(
            "received" not in out,
            "Wrong vlan packet can't receive with multicast mac!!!",
        )
        # disbale vlan filter and remove vlan id
        self.dut.send_expect("rx_vlan rm %d 0" % random_vlan, "testpmd> ")
        self.dut.send_expect("vlan set filter off 0", "testpmd> ")
        self.allowlist_send_packet(portid, mcast_addr, count=1)
        out = self.dut.get_session_output()
        self.verify(
            "received" in out,
            "Packet has not been received when it should have on a broadcast address",
        )
        self.dut.send_expect(f"mcast_addr remove {portid:d} {mcast_addr}", "testpmd>")
        self.allowlist_send_packet(portid, mcast_addr, count=1)
        time.sleep(1)
        out = self.dut.get_session_output()
        self.verify(
            "received" not in out,
            "Packet has been received when it should have ignored the broadcast",
        )

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)

    def tear_down(self):
        """
        Run after each test case.
        Nothing to do.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("quit", "# ", 10)
