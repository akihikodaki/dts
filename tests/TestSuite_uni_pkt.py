# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.

Unified packet type flag is supposed to recognize packet types and support all
possible PMDs.

This 32 bits of packet_type can be divided into several sub fields to
indicate different packet type information of a packet. The initial design
is to divide those bits into fields for L2 types, L3 types, L4 types, tunnel
types, inner L2 types, inner L3 types and inner L4 types. All PMDs should
translate the offloaded packet types into these 7 fields of information, for
user applications
"""

import re
import time

import framework.utils as utils
from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestUniPacket(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        ports = self.dut.get_ports()
        self.verify(len(ports) >= 2, "Insufficient ports for testing")
        valports = [_ for _ in ports if self.tester.get_local_port(_) != -1]
        # start testpmd
        self.dut_port = valports[0]
        socket_id = self.dut.get_numa_id(self.dut_port)
        tester_port = self.tester.get_local_port(self.dut_port)
        self.tester_iface = self.tester.get_interface(tester_port)
        self.pmd = PmdOutput(self.dut)
        self.pmd.start_testpmd(socket=socket_id)
        self.dut.send_expect("set fwd rxonly", "testpmd>")
        self.dut.send_expect("set verbose 1", "testpmd>")
        self.dut.send_expect("start", "testpmd>")
        self.pmd.wait_link_status_up(port_id=self.dut_port)

    def set_up(self):
        """
        Run before each test case.
        Nothing to do.
        """
        pass

    def run_test(self, pkt_types):
        time.sleep(1)
        for pkt_type in list(pkt_types.keys()):
            pkt_names = pkt_types[pkt_type]
            pkt = Packet(pkt_type=pkt_type)
            pkt.send_pkt(self.tester, tx_port=self.tester_iface, count=4)
            out = self.dut.get_session_output(timeout=2)
            pattern = re.compile(r"hw ptype: (.*?)sw")
            hw_ptype = re.findall(pattern, out)
            for pkt_layer_name in pkt_names:
                for tag in hw_ptype:
                    if pkt_layer_name.strip() not in tag:
                        print((utils.RED("Fail to detect %s" % pkt_layer_name)))
                        raise VerifyFailure("Failed to detect %s" % pkt_layer_name)
            print((utils.GREEN("Detected %s successfully" % pkt_type)))

    def test_l2pkt_detect(self):
        """
        Check whether L2 packet can be detected"
        """
        self.verify(
            (
                self.is_eth_series_nic(700)
                or "I40E_10G-SFP_X722" in self.nic
                or "I40E_10G-10G_BASE_T_BC" in self.nic
                or self.is_eth_series_nic(800)
                or "I40E_10G-10G_BASE_T_X722" in self.nic
            ),
            "L2 packet detect only support by Intel® Ethernet 700 Series",
        )
        # Change this code start for DPDK-15109, the share code doest not support TIMESYNC, once /supported then will enable
        if self.is_eth_series_nic(800):
            self.L2_types = {
                "ARP": "L2_ETHER_ARP",
                "LLDP": "L2_ETHER_LLDP",
            }
        else:
            self.L2_types = {
                "TIMESYNC": "L2_ETHER_TIMESYNC",
                "ARP": "L2_ETHER_ARP",
                "LLDP": "L2_ETHER_LLDP",
            }
        # Change this code end for DPDK-15109, the share code doest not support TIMESYNC, once supported then will enable
        for l2_type in list(self.L2_types.keys()):
            pkt_name = self.L2_types[l2_type]
            pkt = Packet(pkt_type=l2_type)
            pkt.send_pkt(self.tester, tx_port=self.tester_iface)
            out = self.dut.get_session_output(timeout=2)
            if pkt_name in out:
                print((utils.GREEN("Detected L2 %s successfully" % l2_type)))
            else:
                raise VerifyFailure("Failed to detect L2 %s" % l2_type)

    def test_IPv4_L4(self):
        """
        checked that whether L3 and L4 packet can be normally detected.
        """
        if (
            self.is_eth_series_nic(700)
            or "I40E_10G-SFP_X722" in self.nic
            or "I40E_10G-10G_BASE_T_BC" in self.nic
            or self.is_eth_series_nic(800)
            or "x722" in self.nic
            or "I40E_10G-10G_BASE_T_X722" in self.nic
        ):
            outerL4Type = "L4_NONFRAG"
            ipv4_default_packet_type = ["L2_ETHER", "L3_IPV4_EXT_UNKNOWN"]
        elif (
            "IXGBE_10G-82599_SFP" in self.nic
            or "IGB_1G-I350_COPPER" in self.nic
            or "cavium" in self.nic
            or "IXGBE_10G-X540T" in self.nic
            or "IXGBE_10G-X550T" in self.nic
            or "IXGBE_10G-X550EM_X_10G_T" in self.nic
            or "IGB_1G-I210_COPPER" in self.nic
            or "IGC-I225_LM" in self.nic
            or "IGC-I226_LM" in self.nic
        ):
            outerL4Type = ""
            ipv4_default_packet_type = ["L2_ETHER", "L3_IPV4"]
        pktType = {
            "MAC_IP_PKT": ipv4_default_packet_type + [outerL4Type],
            "MAC_IP_UDP_PKT": ipv4_default_packet_type + ["L4_UDP"],
            "MAC_IP_TCP_PKT": ipv4_default_packet_type + ["L4_TCP"],
            "MAC_IP_SCTP_PKT": ipv4_default_packet_type + ["L4_SCTP"],
            "MAC_IP_ICMP_PKT": ipv4_default_packet_type + ["L4_ICMP"],
            "MAC_IPFRAG_TCP_PKT": ipv4_default_packet_type + ["L4_FRAG"],
            "MAC_IPihl_PKT": ["L2_ETHER", "L3_IPV4_EXT"],
            "MAC_IPihl_SCTP_PKT": ["L2_ETHER", "L3_IPV4_EXT", "L4_SCTP"],
        }

        # delete the unsupported packet based on nic type
        if (
            self.is_eth_series_nic(700)
            or "I40E_10G-SFP_X722" in self.nic
            or "I40E_10G-10G_BASE_T_BC" in self.nic
            or self.is_eth_series_nic(800)
            or "x722" in self.nic
            or "I40E_10G-10G_BASE_T_X722" in self.nic
        ):
            pktType.pop("MAC_IPihl_PKT")
            pktType.pop("MAC_IPihl_SCTP_PKT")
        elif (
            "IXGBE_10G-82599_SFP" in self.nic
            or "IGB_1G-I350_COPPER" in self.nic
            or "cavium" in self.nic
            or "IXGBE_10G-X540T" in self.nic
            or "IXGBE_10G-X550T" in self.nic
            or "IXGBE_10G-X550EM_X_10G_T" in self.nic
            or "IGB_1G-I210_COPPER" in self.nic
        ):
            pktType.pop("MAC_IP_ICMP_PKT")
            pktType.pop("MAC_IPFRAG_TCP_PKT")

        self.run_test(pktType)

    def test_IPv6_L4(self):
        """
        checked that whether IPv6 and L4 packet can be normally detected.
        """
        if (
            self.is_eth_series_nic(700)
            or "I40E_10G-SFP_X722" in self.nic
            or "I40E_10G-10G_BASE_T_BC" in self.nic
            or self.is_eth_series_nic(800)
            or "x722" in self.nic
            or "I40E_10G-10G_BASE_T_X722" in self.nic
        ):
            outerL4Type = "L4_NONFRAG"
            ipv6_default_packet_type = ["L2_ETHER", "L3_IPV6_EXT_UNKNOWN"]
        elif (
            "IXGBE_10G-82599_SFP" in self.nic
            or "IGB_1G-I350_COPPER" in self.nic
            or "cavium" in self.nic
            or "IXGBE_10G-X540T" in self.nic
            or "IXGBE_10G-X550T" in self.nic
            or "IXGBE_10G-X550EM_X_10G_T" in self.nic
            or "IGB_1G-I210_COPPER" in self.nic
            or "IGC-I225_LM" in self.nic
            or "IGC-I226_LM" in self.nic
        ):
            outerL4Type = ""
            ipv6_default_packet_type = ["L2_ETHER", "L3_IPV6"]

        pktType = {
            "MAC_IPv6_PKT": ipv6_default_packet_type + [outerL4Type],
            "MAC_IPv6_UDP_PKT": ipv6_default_packet_type + ["L4_UDP"],
            "MAC_IPv6_TCP_PKT": ipv6_default_packet_type + ["L4_TCP"],
            "MAC_IPv6FRAG_PKT_F": ipv6_default_packet_type + ["L4_FRAG"],
            "MAC_IPv6FRAG_PKT_N": ["L3_IPV6_EXT"],
        }

        # delete the unsupported packet based on nic type
        if (
            self.is_eth_series_nic(700)
            or "I40E_10G-SFP_X722" in self.nic
            or "I40E_10G-10G_BASE_T_BC" in self.nic
            or self.is_eth_series_nic(800)
            or "x722" in self.nic
            or "I40E_10G-10G_BASE_T_X722" in self.nic
        ):
            pktType.pop("MAC_IPv6FRAG_PKT_N")
        elif (
            "IXGBE_10G-82599_SFP" in self.nic
            or "IGB_1G-I350_COPPER" in self.nic
            or "cavium" in self.nic
            or "IXGBE_10G-X540T" in self.nic
            or "IXGBE_10G-X550T" in self.nic
            or "IXGBE_10G-X550EM_X_10G_T" in self.nic
            or "IGB_1G-I210_COPPER" in self.nic
        ):
            pktType.pop("MAC_IPv6FRAG_PKT_F")

        self.run_test(pktType)

    def test_IP_in_IPv4_tunnel(self):
        """
        checked that whether IP in IPv4 tunnel packet can be normally
        detected by Intel® Ethernet 700 Series.
        """
        self.verify(
            (
                self.is_eth_series_nic(700)
                or "I40E_10G-SFP_X722" in self.nic
                or "I40E_10G-10G_BASE_T_BC" in self.nic
                or self.is_eth_series_nic(800)
                or "I40E_10G-10G_BASE_T_X722" in self.nic
            ),
            "IP in IPv4 tunnel packet type detect only support by Intel® Ethernet 700 Series",
        )
        ipv4_in_ipv4_packet_type = [
            "L2_ETHER",
            "L3_IPV4_EXT_UNKNOWN",
            "TUNNEL_IP",
            "INNER_L3_IPV4_EXT_UNKNOWN",
        ]
        ipv6_in_ipv4_packet_type = [
            "L2_ETHER",
            "L3_IPV4_EXT_UNKNOWN",
            "TUNNEL_IP",
            "INNER_L3_IPV6_EXT_UNKNOWN",
        ]

        pktType = {
            "MAC_IP_IPFRAG_UDP_PKT": ipv4_in_ipv4_packet_type + ["INNER_L4_FRAG"],
            "MAC_IP_IP_PKT": ipv4_in_ipv4_packet_type + ["INNER_L4_NONFRAG"],
            "MAC_IP_IP_UDP_PKT": ipv4_in_ipv4_packet_type + ["INNER_L4_UDP"],
            "MAC_IP_IP_TCP_PKT": ipv4_in_ipv4_packet_type + ["INNER_L4_TCP"],
            "MAC_IP_IP_SCTP_PKT": ipv4_in_ipv4_packet_type + ["INNER_L4_SCTP"],
            "MAC_IP_IP_ICMP_PKT": ipv4_in_ipv4_packet_type + ["INNER_L4_ICMP"],
            "MAC_IP_IPv6FRAG_PKT": ipv6_in_ipv4_packet_type + ["INNER_L4_FRAG"],
            "MAC_IP_IPv6_PKT": ipv6_in_ipv4_packet_type + ["INNER_L4_NONFRAG"],
            "MAC_IP_IPv6_UDP_PKT": ipv6_in_ipv4_packet_type + ["INNER_L4_UDP"],
            "MAC_IP_IPv6_TCP_PKT": ipv6_in_ipv4_packet_type + ["INNER_L4_TCP"],
            "MAC_IP_IPv6_SCTP_PKT": ipv6_in_ipv4_packet_type + ["INNER_L4_SCTP"],
            "MAC_IP_IPv6_ICMP_PKT": ipv6_in_ipv4_packet_type + ["INNER_L4_ICMP"],
        }

        self.run_test(pktType)

    def test_IPv6_in_IPv4_tunnel(self):
        """
        checked that whether IPv4 in IPv6 tunnel packet can be normally
        detected.
        """
        self.verify(
            self.nic
            in [
                "ICE_25G-E810C_SFP",
                "ICE_25G-E823C_QSFP",
                "ICE_100G-E810C_QSFP",
                "IXGBE_10G-82599_SFP",
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "IGB_1G-I350_COPPER",
                "I40E_10G-SFP_X722",
                "I40E_10G-10G_BASE_T_X722",
                "I40E_25G-25G_SFP28",
                "I40E_40G-QSFP_B",
                "I40E_10G-10G_BASE_T_BC",
                "IGC-I225_LM",
                "IGC-I226_LM",
            ],
            "not support %s" % self.nic,
        )
        pktType = {
            "MAC_IP_IPv6_PKT": ["L2_ETHER", "L3_IPV4", "TUNNEL_IP", "INNER_L3_IPV6"],
            "MAC_IP_IPv6EXT2_PKT": [
                "L2_ETHER",
                "L3_IPV4",
                "TUNNEL_IP",
                "INNER_L3_IPV6_EXT",
            ],
            "MAC_IP_IPv6_UDP_PKT": [
                "L2_ETHER",
                "L3_IPV4",
                "TUNNEL_IP",
                "INNER_L3_IPV6",
                "INNER_L4_UDP",
            ],
            "MAC_IP_IPv6_TCP_PKT": [
                "L2_ETHER",
                "L3_IPV4",
                "TUNNEL_IP",
                "INNER_L3_IPV6",
                "INNER_L4_TCP",
            ],
            "MAC_IP_IPv6EXT2_UDP_PKT": [
                "L2_ETHER",
                "L3_IPV4",
                "TUNNEL_IP",
                "INNER_L3_IPV6_EXT",
                "INNER_L4_UDP",
            ],
            "MAC_IP_IPv6EXT2_TCP_PKT": [
                "L2_ETHER",
                "L3_IPV4",
                "TUNNEL_IP",
                "INNER_L3_IPV6_EXT",
                "INNER_L4_TCP",
            ],
        }
        self.run_test(pktType)

    def test_IP_in_IPv6_tunnel(self):
        """
        checked that whether IP in IPv6 tunnel packet can be normally
        detected by Intel® Ethernet 700 Series.
        """
        self.verify(
            (
                self.is_eth_series_nic(700)
                or "I40E_10G-SFP_X722" in self.nic
                or "I40E_10G-10G_BASE_T_BC" in self.nic
                or self.is_eth_series_nic(800)
                or "I40E_10G-10G_BASE_T_X722" in self.nic
            ),
            "IP in IPv6 tunnel packet type detect only support by Intel® Ethernet 700 Series",
        )
        ipv4_in_ipv6_packet_type = [
            "L2_ETHER",
            "L3_IPV4_EXT_UNKNOWN",
            "TUNNEL_IP",
            "INNER_L3_IPV4_EXT_UNKNOWN",
        ]
        ipv6_in_ipv6_packet_type = [
            "L2_ETHER",
            "L3_IPV4_EXT_UNKNOWN",
            "TUNNEL_IP",
            "INNER_L3_IPV6_EXT_UNKNOWN",
        ]

        pktType = {
            "MAC_IP_IPFRAG_UDP_PKT": ipv4_in_ipv6_packet_type + ["INNER_L4_FRAG"],
            "MAC_IP_IP_PKT": ipv4_in_ipv6_packet_type + ["INNER_L4_NONFRAG"],
            "MAC_IP_IP_UDP_PKT": ipv4_in_ipv6_packet_type + ["INNER_L4_UDP"],
            "MAC_IP_IP_TCP_PKT": ipv4_in_ipv6_packet_type + ["INNER_L4_TCP"],
            "MAC_IP_IP_SCTP_PKT": ipv4_in_ipv6_packet_type + ["INNER_L4_SCTP"],
            "MAC_IP_IP_ICMP_PKT": ipv4_in_ipv6_packet_type + ["INNER_L4_ICMP"],
            "MAC_IP_IPv6FRAG_PKT": ipv6_in_ipv6_packet_type + ["INNER_L4_FRAG"],
            "MAC_IP_IPv6_PKT": ipv6_in_ipv6_packet_type + ["INNER_L4_NONFRAG"],
            "MAC_IP_IPv6_UDP_PKT": ipv6_in_ipv6_packet_type + ["INNER_L4_UDP"],
            "MAC_IP_IPv6_TCP_PKT": ipv6_in_ipv6_packet_type + ["INNER_L4_TCP"],
            "MAC_IP_IPv6_SCTP_PKT": ipv6_in_ipv6_packet_type + ["INNER_L4_SCTP"],
            "MAC_IP_IPv6_ICMP_PKT": ipv6_in_ipv6_packet_type + ["INNER_L4_ICMP"],
        }
        self.run_test(pktType)

    def test_NVGRE_tunnel(self):
        """
        checked that whether NVGRE tunnel packet can be normally detected
        by Intel® Ethernet 700 Series.
        """
        self.verify(
            (
                self.is_eth_series_nic(700)
                or "I40E_10G-SFP_X722" in self.nic
                or "I40E_10G-10G_BASE_T_BC" in self.nic
                or self.is_eth_series_nic(800)
                or "I40E_10G-10G_BASE_T_X722" in self.nic
            ),
            "NVGRE tunnel packet type detect only support by Intel® Ethernet 700 Series",
        )
        nvgre_base_packet_type = ["L2_ETHER", "L3_IPV4_EXT_UNKNOWN", "TUNNEL_GRENAT"]
        # INNER IPV4 not with vlan
        nvgre_ipv4_default_packet_type = nvgre_base_packet_type + [
            "INNER_L2_ETHER",
            "INNER_L3_IPV4_EXT_UNKNOWN",
        ]
        # INNER IPV6 not with vlan
        nvgre_ipv6_default_packet_type = nvgre_base_packet_type + [
            "INNER_L2_ETHER",
            "INNER_L3_IPV6_EXT_UNKNOWN",
        ]
        # INNER IPV4 with vlan
        nvgre_ipv4_vlan_packet_type = nvgre_base_packet_type + [
            "INNER_L2_ETHER_VLAN",
            "INNER_L3_IPV4_EXT_UNKNOWN",
        ]
        # INNER IPV6 with vlan
        nvgre_ipv6_vlan_packet_type = nvgre_base_packet_type + [
            "INNER_L2_ETHER_VLAN",
            "INNER_L3_IPV6_EXT_UNKNOWN",
        ]

        pktType = {
            "MAC_IP_NVGRE_MAC_IPFRAG_PKT": nvgre_ipv4_default_packet_type
            + ["INNER_L4_FRAG"],
            "MAC_IP_NVGRE_MAC_IP_PKT": nvgre_ipv4_default_packet_type
            + ["INNER_L4_NONFRAG"],
            "MAC_IP_NVGRE_MAC_VLAN_PKT": nvgre_base_packet_type + ["INNER_L2_ETHER"],
            "MAC_IP_NVGRE_MAC_VLAN_IPFRAG_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_FRAG"],
            "MAC_IP_NVGRE_MAC_VLAN_IP_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_NONFRAG"],
            "MAC_IP_NVGRE_MAC_VLAN_IP_UDP_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_UDP"],
            "MAC_IP_NVGRE_MAC_VLAN_IP_TCP_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_TCP"],
            "MAC_IP_NVGRE_MAC_VLAN_IP_SCTP_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_SCTP"],
            "MAC_IP_NVGRE_MAC_VLAN_IP_ICMP_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_ICMP"],
            "MAC_IP_NVGRE_MAC_VLAN_IPv6FRAG_PKT": nvgre_ipv6_vlan_packet_type
            + ["INNER_L4_FRAG"],
            "MAC_IP_NVGRE_MAC_VLAN_IPv6_PKT": nvgre_ipv6_vlan_packet_type
            + ["INNER_L4_NONFRAG"],
            "MAC_IP_NVGRE_MAC_VLAN_IPv6_UDP_PKT": nvgre_ipv6_vlan_packet_type
            + ["INNER_L4_UDP"],
            "MAC_IP_NVGRE_MAC_VLAN_IPv6_TCP_PKT": nvgre_ipv6_vlan_packet_type
            + ["INNER_L4_TCP"],
            "MAC_IP_NVGRE_MAC_VLAN_IPv6_SCTP_PKT": nvgre_ipv6_vlan_packet_type
            + ["INNER_L4_SCTP"],
            "MAC_IP_NVGRE_MAC_VLAN_IPv6_ICMP_PKT": nvgre_ipv6_vlan_packet_type
            + ["INNER_L4_ICMP"],
        }
        self.run_test(pktType)

    def test_NVGRE_in_IPv6_tunnel(self):
        """
        checked that whether NVGRE in IPv6 tunnel packet can be normally
        detected by Intel® Ethernet 700 Series.
        """
        self.verify(
            (
                self.is_eth_series_nic(700)
                or "I40E_10G-SFP_X722" in self.nic
                or "I40E_10G-10G_BASE_T_BC" in self.nic
                or self.is_eth_series_nic(800)
                or "I40E_10G-10G_BASE_T_X722" in self.nic
            ),
            "NVGRE in IPv6 detect only support by Intel® Ethernet 700 Series",
        )
        nvgre_base_packet_type = ["L2_ETHER", "L3_IPV6_EXT_UNKNOWN", "TUNNEL_GRENAT"]
        # INNER IPV4 not with vlan
        nvgre_ipv4_default_packet_type = nvgre_base_packet_type + [
            "INNER_L2_ETHER",
            "INNER_L3_IPV4_EXT_UNKNOWN",
        ]
        # INNER IPV6 not with vlan
        nvgre_ipv6_default_packet_type = nvgre_base_packet_type + [
            "INNER_L2_ETHER",
            "INNER_L3_IPV6_EXT_UNKNOWN",
        ]
        # INNER IPV4 with vlan
        nvgre_ipv4_vlan_packet_type = nvgre_base_packet_type + [
            "INNER_L2_ETHER_VLAN",
            "INNER_L3_IPV4_EXT_UNKNOWN",
        ]
        # INNER IPV6 with vlan
        nvgre_ipv6_vlan_packet_type = nvgre_base_packet_type + [
            "INNER_L2_ETHER_VLAN",
            "INNER_L3_IPV6_EXT_UNKNOWN",
        ]

        pkt_types = {
            "MAC_IPv6_NVGRE_MAC_PKT": nvgre_base_packet_type + ["INNER_L2_ETHER"],
            "MAC_IPv6_NVGRE_MAC_IPFRAG_PKT": nvgre_ipv4_default_packet_type
            + ["INNER_L4_FRAG"],
            "MAC_IPv6_NVGRE_MAC_IP_PKT": nvgre_ipv4_default_packet_type
            + ["INNER_L4_NONFRAG"],
            "MAC_IPv6_NVGRE_MAC_IP_UDP_PKT": nvgre_ipv4_default_packet_type
            + ["INNER_L4_UDP"],
            "MAC_IPv6_NVGRE_MAC_IP_TCP_PKT": nvgre_ipv4_default_packet_type
            + ["INNER_L4_TCP"],
            "MAC_IPv6_NVGRE_MAC_IP_SCTP_PKT": nvgre_ipv4_default_packet_type
            + ["INNER_L4_SCTP"],
            "MAC_IPv6_NVGRE_MAC_IP_ICMP_PKT": nvgre_ipv4_default_packet_type
            + ["INNER_L4_ICMP"],
            "MAC_IPv6_NVGRE_MAC_IPv6FRAG_PKT": nvgre_ipv6_default_packet_type
            + ["INNER_L4_FRAG"],
            "MAC_IPv6_NVGRE_MAC_IPv6_PKT": nvgre_ipv6_default_packet_type
            + ["INNER_L4_NONFRAG"],
            "MAC_IPv6_NVGRE_MAC_IPv6_UDP_PKT": nvgre_ipv6_default_packet_type
            + ["INNER_L4_UDP"],
            "MAC_IPv6_NVGRE_MAC_IPv6_TCP_PKT": nvgre_ipv6_default_packet_type
            + ["INNER_L4_TCP"],
            "MAC_IPv6_NVGRE_MAC_VLAN_IPFRAG_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_FRAG"],
            "MAC_IPv6_NVGRE_MAC_VLAN_IP_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_NONFRAG"],
            "MAC_IPv6_NVGRE_MAC_VLAN_IP_UDP_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_UDP"],
            "MAC_IPv6_NVGRE_MAC_VLAN_IP_TCP_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_TCP"],
            "MAC_IPv6_NVGRE_MAC_VLAN_IP_SCTP_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_SCTP"],
            "MAC_IPv6_NVGRE_MAC_VLAN_IP_ICMP_PKT": nvgre_ipv4_vlan_packet_type
            + ["INNER_L4_ICMP"],
            "MAC_IPv6_NVGRE_MAC_VLAN_IPv6FRAG_PKT": nvgre_ipv6_vlan_packet_type
            + ["INNER_L4_FRAG"],
            "MAC_IPv6_NVGRE_MAC_VLAN_IPv6_PKT": nvgre_ipv6_vlan_packet_type
            + ["INNER_L4_NONFRAG"],
            "MAC_IPv6_NVGRE_MAC_VLAN_IPv6_UDP_PKT": nvgre_ipv6_vlan_packet_type
            + ["INNER_L4_UDP"],
            "MAC_IPv6_NVGRE_MAC_VLAN_IPv6_TCP_PKT": nvgre_ipv6_vlan_packet_type
            + ["INNER_L4_TCP"],
        }

        self.run_test(pkt_types)

        pkt_nvgre = [
            [
                "MAC_IPv6_NVGRE_MAC_IPv6_SCTP_PKT",
                nvgre_ipv6_default_packet_type + ["INNER_L4_SCTP"],
                [
                    "ether",
                    "ipv6",
                    "nvgre",
                    "inner_mac",
                    "inner_ipv6",
                    "inner_sctp",
                    "raw",
                ],
            ],
            [
                "MAC_IPv6_NVGRE_MAC_IPv6_ICMP_PKT",
                nvgre_ipv6_default_packet_type + ["INNER_L4_ICMP"],
                [
                    "ether",
                    "ipv6",
                    "nvgre",
                    "inner_mac",
                    "inner_ipv6",
                    "inner_icmp",
                    "raw",
                ],
            ],
            [
                "MAC_IPv6_NVGRE_MAC_VLAN_IPv6_SCTP_PKT",
                nvgre_ipv6_vlan_packet_type + ["INNER_L4_SCTP"],
                [
                    "ether",
                    "ipv6",
                    "nvgre",
                    "inner_mac",
                    "inner_vlan",
                    "inner_ipv6",
                    "inner_sctp",
                    "raw",
                ],
            ],
            [
                "MAC_IPv6_NVGRE_MAC_VLAN_IPv6_ICMP_PKT",
                nvgre_ipv6_vlan_packet_type + ["INNER_L4_ICMP"],
                [
                    "ether",
                    "ipv6",
                    "nvgre",
                    "inner_mac",
                    "inner_vlan",
                    "inner_ipv6",
                    "inner_icmp",
                    "raw",
                ],
            ],
        ]
        self.run_nvgre_cope(pkt_nvgre)

    def run_nvgre_cope(self, pkt_nvgre):
        time.sleep(1)
        for pkts in pkt_nvgre:
            pkt = Packet()
            pkt.assign_layers(pkts[2])
            if "inner_icmp" in pkts[2]:
                pkt.config_layers([("ipv6", {"nh": 47}), ("inner_ipv6", {"nh": 58})])
            else:
                pkt.config_layers([("ipv6", {"nh": 47}), ("inner_ipv6", {"nh": 132})])
            pkt.send_pkt(self.tester, tx_port=self.tester_iface)
            out = self.dut.get_session_output(timeout=2)
            for pkt_layer_name in pkts[1]:
                if pkt_layer_name not in out:
                    print((utils.RED("Fail to detect %s" % pkt_layer_name)))
                    raise VerifyFailure("Failed to detect %s" % pkt_layer_name)
            print((utils.GREEN("Detected %s successfully" % pkts[0])))

    def test_GRE_tunnel(self):
        """
        checked that whether GRE tunnel packet can be normally detected by Intel® Ethernet 700 Series.
        """
        self.verify(
            (
                self.is_eth_series_nic(700)
                or "I40E_10G-SFP_X722" in self.nic
                or "I40E_10G-10G_BASE_T_BC" in self.nic
                or self.is_eth_series_nic(800)
                or "I40E_10G-10G_BASE_T_X722" in self.nic
            ),
            "GRE tunnel packet type detect only support by Intel® Ethernet 700 Series",
        )
        base_packet_type = [" L2_ETHER", " L3_IPV4_EXT_UNKNOWN", "TUNNEL_GRENAT"]
        pktType = {
            "MAC_IP_GRE_IPFRAG_PKT": base_packet_type
            + ["INNER_L3_IPV4_EXT_UNKNOWN", "INNER_L4_FRAG"],
            "MAC_IP_GRE_IP_PKT": base_packet_type
            + ["INNER_L3_IPV4_EXT_UNKNOWN", "INNER_L4_NONFRAG"],
            "MAC_IP_GRE_IP_UDP_PKT": base_packet_type
            + ["INNER_L3_IPV4_EXT_UNKNOWN", "INNER_L4_UDP"],
            "MAC_IP_GRE_IP_TCP_PKT": base_packet_type
            + ["INNER_L3_IPV4_EXT_UNKNOWN", "INNER_L4_TCP"],
            "MAC_IP_GRE_IP_SCTP_PKT": base_packet_type
            + ["INNER_L3_IPV4_EXT_UNKNOWN", "INNER_L4_SCTP"],
            "MAC_IP_GRE_IP_ICMP_PKT": base_packet_type
            + ["INNER_L3_IPV4_EXT_UNKNOWN", "INNER_L4_ICMP"],
            "MAC_IP_GRE_PKT": base_packet_type,
        }
        self.run_test(pktType)

    def test_Vxlan_tunnel(self):
        """
        checked that whether Vxlan tunnel packet can be normally detected by Intel® Ethernet 700 Series.
        """
        self.verify(
            (
                self.is_eth_series_nic(700)
                or "I40E_10G-SFP_X722" in self.nic
                or "I40E_10G-10G_BASE_T_BC" in self.nic
                or self.is_eth_series_nic(800)
                or "I40E_10G-10G_BASE_T_X722" in self.nic
            ),
            "Vxlan tunnel packet type detect only support by Intel® Ethernet 700 Series",
        )

        self.dut.send_expect("rx_vxlan_port add 4789 0", "testpmd>", 10)
        self.dut.send_expect("set fwd rxonly", "testpmd>")
        self.dut.send_expect("set verbose 1", "testpmd>")
        self.dut.send_expect("start", "testpmd>")
        vxlan_ipv4_default_packet_type = [
            "L2_ETHER",
            "L3_IPV4_EXT_UNKNOWN",
            "TUNNEL_GRENAT",
            "INNER_L2_ETHER",
            "INNER_L3_IPV4_EXT_UNKNOWN",
        ]
        vxlan_ipv6_default_packet_type = [
            "L2_ETHER",
            "L3_IPV4_EXT_UNKNOWN",
            "TUNNEL_GRENAT",
            "INNER_L2_ETHER",
            "INNER_L3_IPV6_EXT_UNKNOWN",
        ]

        pktType = {
            "MAC_IP_UDP_VXLAN_MAC_IPFRAG_PKT": vxlan_ipv4_default_packet_type
            + ["INNER_L4_FRAG"],
            "MAC_IP_UDP_VXLAN_MAC_IP_PKT": vxlan_ipv4_default_packet_type
            + ["INNER_L4_NONFRAG"],
            "MAC_IP_UDP_VXLAN_MAC_IP_UDP_PKT": vxlan_ipv4_default_packet_type
            + ["INNER_L4_UDP"],
            "MAC_IP_UDP_VXLAN_MAC_IP_TCP_PKT": vxlan_ipv4_default_packet_type
            + ["INNER_L4_TCP"],
            "MAC_IP_UDP_VXLAN_MAC_IP_SCTP_PKT": vxlan_ipv4_default_packet_type
            + ["INNER_L4_SCTP"],
            "MAC_IP_UDP_VXLAN_MAC_IP_ICMP_PKT": vxlan_ipv4_default_packet_type
            + ["INNER_L4_ICMP"],
            "MAC_IP_UDP_VXLAN_MAC_IPv6FRAG_PKT": vxlan_ipv6_default_packet_type
            + ["INNER_L4_FRAG"],
            "MAC_IP_UDP_VXLAN_MAC_IPv6_PKT": vxlan_ipv6_default_packet_type
            + ["INNER_L4_NONFRAG"],
            "MAC_IP_UDP_VXLAN_MAC_IPv6_UDP_PKT": vxlan_ipv6_default_packet_type
            + ["INNER_L4_UDP"],
            "MAC_IP_UDP_VXLAN_MAC_IPv6_TCP_PKT": vxlan_ipv6_default_packet_type
            + ["INNER_L4_TCP"],
            "MAC_IP_UDP_VXLAN_MAC_IPv6_SCTP_PKT": vxlan_ipv6_default_packet_type
            + ["INNER_L4_SCTP"],
            "MAC_IP_UDP_VXLAN_MAC_IPv6_ICMP_PKT": vxlan_ipv6_default_packet_type
            + ["INNER_L4_ICMP"],
            "MAC_IP_UDP_VXLAN_MAC_PKT": [
                "L2_ETHER",
                "L3_IPV4_EXT_UNKNOWN",
                "TUNNEL_GRENAT",
                "INNER_L2_ETHER",
            ],
        }
        self.run_test(pktType)

    def test_nsh(self):
        """
        check if NSH packets can be normally detected by X722 and Intel® Ethernet 700 Series
        """
        self.verify(
            self.kdriver == "i40e",
            "NSH packet detection only supported by i40e driver nic",
        )

        nsh_packets = {
            "ether+nsh": "Ether(type=0x894f)/NSH(length=0x6,nextproto=0x0,spi=0x000002,si=0xff)",
            "ether+nsh+ip": 'Ether(dst="00:00:00:00:01:00",type=0x894f)/NSH(length=0x6,nextproto=0x1,spi=0x000002,si=0xff)/IP()',
            "ether+nsh+ip+icmp": "Ether(type=0x894f)/NSH(length=0x6,nextproto=0x1,spi=0x000002,si=0xff)/IP()/ICMP()",
            "ether+nsh+ip_frag": 'Ether(dst="00:00:00:00:01:00",type=0x894f)/NSH(length=0x6,nextproto=0x1,spi=0x000002,si=0xff)/IP(frag=1,flags="MF")',
            "ether+nsh+ip+tcp": "Ether(type=0x894f)/NSH(length=0x6,nextproto=0x1,spi=0x000002,si=0xff)/IP()/TCP()",
            "ether+nsh+ip+udp": 'Ether(dst="00:00:00:00:01:00",type=0x894f)/NSH(length=0x6,nextproto=0x1,spi=0x000002,si=0xff)/IP()/UDP()',
            "ether+nsh+ip+sctp": "Ether(type=0x894f)/NSH(length=0x6,nextproto=0x1,spi=0x000002,si=0xff)/IP()/SCTP(tag=1)/SCTPChunkData(data='X' * 16)",
            "ether+nsh+ipv6": "Ether(type=0x894f)/NSH(length=0x6,nextproto=0x2,spi=0x000002,si=0xff)/IPv6()",
            "ether+nsh+ipv6+icmp": 'Ether(type=0x894f)/NSH(length=0x6,nextproto=0x2,spi=0x000002,si=0xff)/IPv6(src="2001::1",dst="2003::2",nh=0x3A)/ICMP()',
            "ether+nsh+ipv6_frag": 'Ether(dst="00:00:00:00:01:00",type=0x894f)/NSH(length=0x6,nextproto=0x2,spi=0x000002,si=0xff)/IPv6()/IPv6ExtHdrFragment()',
            "ether+nsh+ipv6+tcp": "Ether(type=0x894f)/NSH(length=0x6,nextproto=0x2,spi=0x000002,si=0xff)/IPv6()/TCP()",
            "ether+nsh+ipv6+udp": 'Ether(dst="00:00:00:00:01:00",type=0x894f)/NSH(length=0x6,nextproto=0x2,spi=0x000002,si=0xff)/IPv6()/UDP()',
            "ether+nsh+ipv6+sctp": 'Ether(type=0x894f)/NSH(length=0x6,nextproto=0x2,spi=0x000002,si=0xff)/IPv6(nh=0x84)/SCTP(tag=1)/SCTPChunkData(b"x" * 16)',
        }
        nsh_detect_message = {
            "ether+nsh": "L2_ETHER_NSH",
            "ether+nsh+ip": "L2_ETHER_NSH L3_IPV4_EXT_UNKNOWN L4_NONFRAG",
            "ether+nsh+ip+icmp": "L2_ETHER_NSH L3_IPV4_EXT_UNKNOWN L4_ICMP",
            "ether+nsh+ip_frag": "L2_ETHER_NSH L3_IPV4_EXT_UNKNOWN L4_FRAG",
            "ether+nsh+ip+tcp": "L2_ETHER_NSH L3_IPV4_EXT_UNKNOWN L4_TCP",
            "ether+nsh+ip+udp": "L2_ETHER_NSH L3_IPV4_EXT_UNKNOWN L4_UDP",
            "ether+nsh+ip+sctp": "L2_ETHER_NSH L3_IPV4_EXT_UNKNOWN L4_SCTP",
            "ether+nsh+ipv6": "L2_ETHER_NSH L3_IPV6_EXT_UNKNOWN L4_NONFRAG",
            "ether+nsh+ipv6+icmp": "L2_ETHER_NSH L3_IPV6_EXT_UNKNOWN L4_ICMP",
            "ether+nsh+ipv6_frag": "L2_ETHER_NSH L3_IPV6_EXT_UNKNOWN L4_FRAG",
            "ether+nsh+ipv6+tcp": "L2_ETHER_NSH L3_IPV6_EXT_UNKNOWN L4_TCP",
            "ether+nsh+ipv6+udp": "L2_ETHER_NSH L3_IPV6_EXT_UNKNOWN L4_UDP",
            "ether+nsh+ipv6+sctp": "L2_ETHER_NSH L3_IPV6_EXT_UNKNOWN L4_SCTP",
        }

        for packet in nsh_packets:
            pk = Packet(nsh_packets[packet])
            pk.send_pkt(self.tester, self.tester_iface)
            out = self.dut.get_session_output(timeout=2)
            self.verify(
                nsh_detect_message[packet] in out,
                "Packet Detection Error for : %s" % packet,
            )
            print((utils.GREEN("Detected packet %s Successfully" % packet)))

    def tear_down(self):
        """
        Run after each test case.
        Nothing to do.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        Nothing to do.
        """
        self.dut.kill_all()
        pass
