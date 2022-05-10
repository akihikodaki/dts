# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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

"""
DPDK Test suite.

Generic Routing Encapsulation (GRE) is a tunneling protocol developed by 
Cisco Systems that can encapsulate a wide variety of network layer protocols 
inside virtual point-to-point links over an Internet Protocol network.

Intel® Ethernet 700 Series support GRE packet detecting, checksum computing
and filtering.
"""

import os
import re
import time

from scapy.layers.inet import IP, TCP, UDP, Ether
from scapy.layers.l2 import GRE
from scapy.layers.sctp import SCTP
from scapy.packet import bind_layers, split_layers
from scapy.utils import rdpcap, wrpcap

import framework.utils as utils
from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestIpgre(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.printFlag = self._enable_debug
        ports = self.dut.get_ports()
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_40G-QSFP_B",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_BC",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
                "cavium_a063",
                "cavium_a064",
            ],
            "GRE tunnel packet type only support by Intel® Ethernet 700 Series, "
            "Intel® Ethernet Network Adapter X710-T4L, Intel® Ethernet Network "
            "Adapter X710-T2L and cavium",
        )
        self.verify(len(ports) >= 1, "Insufficient ports for testing")
        valports = [_ for _ in ports if self.tester.get_local_port(_) != -1]
        # start testpmd
        self.dut_port = valports[0]
        self.dut_ports = self.dut.get_ports(self.nic)
        self.portMask = utils.create_mask([self.dut_ports[0]])
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.pmdout = PmdOutput(self.dut)
        tester_port = self.tester.get_local_port(self.dut_port)
        self.tester_iface = self.tester.get_interface(tester_port)
        self.tester_iface_mac = self.tester.get_mac(tester_port)
        self.initialize_port_config()

    def initialize_port_config(self):
        self.outer_mac_src = "00:00:10:00:00:00"
        self.outer_mac_dst = "11:22:33:44:55:66"
        self.outer_ip_src = "192.168.1.1"
        self.outer_ip_dst = "192.168.1.2"
        self.inner_ip_src = "192.168.2.1"
        self.inner_ip_dst = "192.168.2.2"

    def set_up(self):
        """
        Run before each test case.
        Nothing to do.
        """
        pass

    def check_packet_transmission(
        self, pkt_types, layer_configs=None, queue=None, add_filter=0
    ):
        time.sleep(1)
        for pkt_type in list(pkt_types.keys()):
            pkt_names = pkt_types[pkt_type]
            pkt = Packet(pkt_type=pkt_type)
            if layer_configs:
                for layer in list(layer_configs.keys()):
                    pkt.config_layer(layer, layer_configs[layer])
            inst = self.tester.tcpdump_sniff_packets(self.tester_iface, count=1)
            pkt.send_pkt(crb=self.tester, tx_port=self.tester_iface, count=4)
            out = self.dut.get_session_output(timeout=2)
            time.sleep(1)
            pkt = self.tester.load_tcpdump_sniff_packets(inst)
            if self.printFlag:  # debug output
                print(out)
            for pkt_layer_name in pkt_names:
                if self.printFlag:  # debug output
                    print(pkt_layer_name)
                if pkt_layer_name not in out:
                    print(utils.RED("Fail to detect %s" % pkt_layer_name))
                    if not self.printFlag:
                        raise VerifyFailure("Failed to detect %s" % pkt_layer_name)
            else:
                print(utils.GREEN("Detected %s successfully" % pkt_type))
            time.sleep(1)
            if queue == None:  # no filter
                pass
            else:
                if add_filter:  # remove filter
                    self.verify(
                        ("Receive queue=0x%s" % queue) in out,
                        "Failed to enter the right queue.",
                    )
                else:
                    self.verify(
                        ("Receive queue=0x%s" % queue) not in out,
                        "Failed to enter the right queue.",
                    )
        return pkt

    def save_ref_packet(self, pkt_types, layer_configs=None):
        for pkt_type in list(pkt_types.keys()):
            pkt_names = pkt_types[pkt_type]
            pkt = Packet(pkt_type=pkt_type)
            if layer_configs:
                for layer in list(layer_configs.keys()):
                    pkt.config_layer(layer, layer_configs[layer])
            wrpcap("/tmp/ref_pkt.pcap", pkt.pktgen.pkt)
            time.sleep(1)

    def get_chksums(self, pcap=None):
        """
        get chksum values of Outer and Inner packet L3&L4
        Skip outer udp for it will be calculated by software
        """
        chk_sums = {}
        if isinstance(pcap, str):
            pkts = rdpcap(pcap)
        else:
            pkts = pcap.pktgen.pkts
        for number in range(len(pkts)):
            if pkts[number].guess_payload_class(pkts[number]).name == "gre":
                payload = pkts[number][GRE]
            else:
                payload = pkts[number]

            if payload.guess_payload_class(payload).name == "IP":
                chk_sums["outer_ip"] = hex(payload[IP].chksum)

            if pkts[number].haslayer(GRE) == 1:
                inner = pkts[number][GRE]
                if inner.haslayer(IP) == 1:
                    chk_sums["inner_ip"] = hex(inner[IP].chksum)
                    if inner[IP].proto == 6:
                        chk_sums["inner_tcp"] = hex(inner[TCP].chksum)
                    if inner[IP].proto == 17:
                        chk_sums["inner_udp"] = hex(inner[UDP].chksum)
                    if inner[IP].proto == 132:
                        chk_sums["inner_sctp"] = hex(inner[SCTP].chksum)
                break

        return chk_sums

    def compare_checksum(self, pkt):
        chksums_ref = self.get_chksums("/tmp/ref_pkt.pcap")
        chksums = self.get_chksums(pcap=pkt)
        self.logger.info("chksums_ref :: %s" % chksums_ref)
        self.logger.info("chksums :: %s" % chksums)
        # verify saved pcap checksum same to expected checksum
        for key in chksums_ref:
            self.verify(
                int(chksums[key], 16) == int(chksums_ref[key], 16),
                "%s not matched to %s" % (key, chksums_ref[key]),
            )
        print(utils.GREEN("Checksum is ok"))

    def test_GRE_ipv4_packet_detect(self):
        """
        Start testpmd and enable rxonly forwarding mode
        Send packet as table listed and packet type match each layer
        """
        if self.nic in ["cavium_a063", "cavium_a064"]:
            pkt_types = {
                "MAC_IP_GRE_IPv4-TUNNEL_UDP_PKT": ["TUNNEL_GRE", "INNER_L4_UDP"],
                "MAC_IP_GRE_IPv4-TUNNEL_TCP_PKT": ["TUNNEL_GRE", "INNER_L4_TCP"],
                "MAC_IP_GRE_IPv4-TUNNEL_SCTP_PKT": ["TUNNEL_GRE", "INNER_L4_SCTP"],
                "MAC_VLAN_IP_GRE_IPv4-TUNNEL_UDP_PKT": ["TUNNEL_GRE", "INNER_L4_UDP"],
                "MAC_VLAN_IP_GRE_IPv4-TUNNEL_TCP_PKT": ["TUNNEL_GRE", "INNER_L4_TCP"],
                "MAC_VLAN_IP_GRE_IPv4-TUNNEL_SCTP_PKT": ["TUNNEL_GRE", "INNER_L4_SCTP"],
            }
        else:
            pkt_types = {
                "MAC_IP_GRE_IPv4-TUNNEL_UDP_PKT": ["TUNNEL_GRENAT", "INNER_L4_UDP"],
                "MAC_IP_GRE_IPv4-TUNNEL_TCP_PKT": ["TUNNEL_GRENAT", "INNER_L4_TCP"],
                "MAC_IP_GRE_IPv4-TUNNEL_SCTP_PKT": ["TUNNEL_GRENAT", "INNER_L4_SCTP"],
                "MAC_VLAN_IP_GRE_IPv4-TUNNEL_UDP_PKT": [
                    "TUNNEL_GRENAT",
                    "INNER_L4_UDP",
                ],
                "MAC_VLAN_IP_GRE_IPv4-TUNNEL_TCP_PKT": [
                    "TUNNEL_GRENAT",
                    "INNER_L4_TCP",
                ],
                "MAC_VLAN_IP_GRE_IPv4-TUNNEL_SCTP_PKT": [
                    "TUNNEL_GRENAT",
                    "INNER_L4_SCTP",
                ],
            }
        config_layers = {"ether": {"src": self.outer_mac_src}, "ipv4": {"proto": "gre"}}
        # Start testpmd and enable rxonly forwarding mode
        self.pmdout.start_testpmd(
            "Default",
            "--portmask=%s " % (self.portMask) + " --enable-rx-cksum ",
            socket=self.ports_socket,
        )

        self.dut.send_expect("set fwd rxonly", "testpmd>")
        self.dut.send_expect("set verbose 1", "testpmd>")
        self.dut.send_expect("start", "testpmd>")

        self.check_packet_transmission(pkt_types, config_layers)

        self.dut.send_expect("quit", "#")

    def test_GRE_ipv6_packet_detect(self):
        """
        Start testpmd and enable rxonly forwarding mode
        Send packet as table listed and packet type match each layer
        """
        if self.nic in ["cavium_a063", "cavium_a064"]:
            pkt_types_ipv6_ip = {
                "MAC_IPv6_GRE_IPv4-TUNNEL_UDP_PKT": ["TUNNEL_GRE", "INNER_L4_UDP"],
                "MAC_IPv6_GRE_IPv4-TUNNEL_TCP_PKT": ["TUNNEL_GRE", "INNER_L4_TCP"],
                "MAC_IPv6_GRE_IPv4-TUNNEL_SCTP_PKT": ["TUNNEL_GRE", "INNER_L4_SCTP"],
            }

            pkt_types_ipv6_ipv6 = {
                "MAC_IPv6_GRE_IPv6-TUNNEL_UDP_PKT": ["TUNNEL_GRE", "INNER_L4_UDP"],
                "MAC_IPv6_GRE_IPv6-TUNNEL_TCP_PKT": ["TUNNEL_GRE", "INNER_L4_TCP"],
            }

            pkt_types_ipv6_ipv6_SCTP = {
                "MAC_IPv6_GRE_IPv6-TUNNEL_SCTP_PKT": ["TUNNEL_GRE", "INNER_L4_SCTP"]
            }
        else:
            pkt_types_ipv6_ip = {
                "MAC_IPv6_GRE_IPv4-TUNNEL_UDP_PKT": ["TUNNEL_GRENAT", "INNER_L4_UDP"],
                "MAC_IPv6_GRE_IPv4-TUNNEL_TCP_PKT": ["TUNNEL_GRENAT", "INNER_L4_TCP"],
                "MAC_IPv6_GRE_IPv4-TUNNEL_SCTP_PKT": ["TUNNEL_GRENAT", "INNER_L4_SCTP"],
                "MAC_VLAN_IPv6_GRE_IPv4-TUNNEL_UDP_PKT": [
                    "TUNNEL_GRENAT",
                    "INNER_L4_UDP",
                    "RTE_MBUF_F_RX_VLAN",
                ],
                "MAC_VLAN_IPv6_GRE_IPv4-TUNNEL_TCP_PKT": [
                    "TUNNEL_GRENAT",
                    "INNER_L4_TCP",
                    "RTE_MBUF_F_RX_VLAN",
                ],
                "MAC_VLAN_IPv6_GRE_IPv4-TUNNEL_SCTP_PKT": [
                    "TUNNEL_GRENAT",
                    "INNER_L4_SCTP",
                    "RTE_MBUF_F_RX_VLAN",
                ],
            }

            pkt_types_ipv6_ipv6 = {
                "MAC_IPv6_GRE_IPv6-TUNNEL_UDP_PKT": ["TUNNEL_GRENAT", "INNER_L4_UDP"],
                "MAC_IPv6_GRE_IPv6-TUNNEL_TCP_PKT": ["TUNNEL_GRENAT", "INNER_L4_TCP"],
                "MAC_VLAN_IPv6_GRE_IPv6-TUNNEL_UDP_PKT": [
                    "TUNNEL_GRENAT",
                    "INNER_L4_UDP",
                    "RTE_MBUF_F_RX_VLAN",
                ],
                "MAC_VLAN_IPv6_GRE_IPv6-TUNNEL_TCP_PKT": [
                    "TUNNEL_GRENAT",
                    "INNER_L4_TCP",
                    "RTE_MBUF_F_RX_VLAN",
                ],
            }

            pkt_types_ipv6_ipv6_SCTP = {
                "MAC_IPv6_GRE_IPv6-TUNNEL_SCTP_PKT": ["TUNNEL_GRENAT", "INNER_L4_SCTP"],
                "MAC_VLAN_IPv6_GRE_IPv6-TUNNEL_SCTP_PKT": [
                    "TUNNEL_GRENAT",
                    "INNER_L4_SCTP",
                    "RTE_MBUF_F_RX_VLAN",
                ],
            }

        # Start testpmd and enable rxonly forwarding mode
        if self.nic in ["cavium_a063", "cavium_a064"]:
            self.pmdout.start_testpmd(
                "Default",
                "--portmask=%s " % (self.portMask) + " --enable-rx-cksum ",
                socket=self.ports_socket,
            )
        else:
            self.pmdout.start_testpmd(
                "Default",
                "--portmask=%s " % (self.portMask)
                + " --enable-rx-cksum --enable-hw-vlan",
                socket=self.ports_socket,
            )

        self.dut.send_expect("set fwd rxonly", "testpmd>")
        self.dut.send_expect("set verbose 1", "testpmd>")
        self.dut.send_expect("start", "testpmd>")

        # inner ipv4
        config_layers = {
            "ether": {"src": self.outer_mac_src},
            "ipv6": {"nh": 47},
            "raw": {"payload": ["78"] * 40},
        }
        self.check_packet_transmission(pkt_types_ipv6_ip, config_layers)

        # inner ipv6
        config_layers = {
            "ether": {"src": self.outer_mac_src},
            "ipv6": {"nh": 47},
            "gre": {"proto": 0x86DD},
            "raw": {"payload": ["78"] * 40},
        }
        self.check_packet_transmission(pkt_types_ipv6_ipv6, config_layers)

        # inner ipv6 SCTP
        config_layers = {
            "ether": {"src": self.outer_mac_src},
            "ipv6": {"nh": 47},
            "gre": {"proto": 0x86DD},
            "inner_ipv6": {"nh": 132},
            "raw": {"payload": ["78"] * 40},
        }
        self.check_packet_transmission(pkt_types_ipv6_ipv6_SCTP, config_layers)
        self.dut.send_expect("quit", "#")

    def test_GRE_packet_chksum_offload(self):
        """
        Start testpmd with hardware checksum offload enabled,
        Send packet with wrong IP/TCP/UDP/SCTP checksum and check forwarded packet checksum
        """
        # Start testpmd and enable rxonly forwarding mode
        self.pmdout.start_testpmd(
            "Default",
            "--portmask=%s " % (self.portMask)
            + " --enable-rx-cksum --port-topology=loop",
            socket=self.ports_socket,
        )
        self.dut.send_expect("set verbose 1", "testpmd>")
        self.dut.send_expect("set fwd csum", "testpmd>")
        self.dut.send_expect("stop", "testpmd>")
        self.dut.send_expect("port stop all", "testpmd>")
        self.dut.send_expect("csum set ip hw 0", "testpmd>")
        self.dut.send_expect("csum set udp hw 0", "testpmd>")
        if self.nic != "cavium_a063":
            self.dut.send_expect("csum set sctp hw 0", "testpmd>")
        self.dut.send_expect("csum set outer-ip hw 0", "testpmd>")
        self.dut.send_expect("csum set tcp hw 0", "testpmd>")
        self.dut.send_expect("csum parse-tunnel on 0", "testpmd>")
        self.dut.send_expect("port start all", "testpmd>")
        self.dut.send_expect("start", "testpmd>")

        # Send packet with wrong outer IP checksum and check forwarded packet IP checksum is correct
        pkt_types = {"MAC_IP_GRE_IPv4-TUNNEL_TCP_PKT": ["RTE_MBUF_F_TX_IP_CKSUM"]}
        config_layers = {
            "ether": {"src": self.outer_mac_src, "dst": self.outer_mac_dst},
            "ipv4": {
                "proto": "gre",
                "src": self.outer_ip_src,
                "dst": self.outer_ip_dst,
            },
            "inner_ipv4": {"src": self.inner_ip_src, "dst": self.inner_ip_dst},
        }
        self.save_ref_packet(pkt_types, config_layers)
        config_layers = {
            "ether": {"src": self.outer_mac_src, "dst": self.outer_mac_dst},
            "ipv4": {
                "proto": "gre",
                "src": self.outer_ip_src,
                "dst": self.outer_ip_dst,
            },
            "inner_ipv4": {
                "src": self.inner_ip_src,
                "dst": self.inner_ip_dst,
                "chksum": 0x0,
            },
        }
        pkt = self.check_packet_transmission(pkt_types, config_layers)
        self.compare_checksum(pkt)

        # Send packet with wrong inner IP checksum and check forwarded packet IP checksum is correct
        pkt_types = {"MAC_IP_GRE_IPv4-TUNNEL_TCP_PKT": ["RTE_MBUF_F_TX_IP_CKSUM"]}
        config_layers = {
            "ether": {"src": self.outer_mac_src, "dst": self.outer_mac_dst},
            "ipv4": {
                "proto": "gre",
                "src": self.outer_ip_src,
                "dst": self.outer_ip_dst,
            },
            "inner_ipv4": {"src": self.inner_ip_src, "dst": self.inner_ip_dst},
        }
        self.save_ref_packet(pkt_types, config_layers)
        config_layers = {
            "ether": {"src": self.outer_mac_src, "dst": self.outer_mac_dst},
            "ipv4": {
                "proto": "gre",
                "src": self.outer_ip_src,
                "dst": self.outer_ip_dst,
                "chksum": 0x0,
            },
            "inner_ipv4": {"src": self.inner_ip_src, "dst": self.inner_ip_dst},
        }
        pkt = self.check_packet_transmission(pkt_types, config_layers)
        self.compare_checksum(pkt)

        # Send packet with wrong inner TCP checksum and check forwarded packet TCP checksum is correct
        pkt_types = {"MAC_IP_GRE_IPv4-TUNNEL_TCP_PKT": ["RTE_MBUF_F_TX_TCP_CKSUM"]}
        config_layers = {
            "ether": {"src": self.outer_mac_src, "dst": self.outer_mac_dst},
            "ipv4": {
                "proto": "gre",
                "src": self.outer_ip_src,
                "dst": self.outer_ip_dst,
            },
            "inner_ipv4": {"src": self.inner_ip_src, "dst": self.inner_ip_dst},
            "tcp": {"src": 53, "dst": 53},
        }
        self.save_ref_packet(pkt_types, config_layers)
        config_layers = {
            "ether": {"src": self.outer_mac_src, "dst": self.outer_mac_dst},
            "ipv4": {
                "proto": "gre",
                "src": self.outer_ip_src,
                "dst": self.outer_ip_dst,
            },
            "inner_ipv4": {"src": self.inner_ip_src, "dst": self.inner_ip_dst},
            "tcp": {"chksum": 0x0},
        }
        pkt = self.check_packet_transmission(pkt_types, config_layers)
        self.compare_checksum(pkt)

        # Send packet with wrong inner UDP checksum and check forwarded packet UDP checksum is correct
        pkt_types = {"MAC_IP_GRE_IPv4-TUNNEL_UDP_PKT": ["RTE_MBUF_F_TX_UDP_CKSUM"]}
        config_layers = {
            "ether": {"src": self.outer_mac_src, "dst": self.outer_mac_dst},
            "ipv4": {
                "proto": "gre",
                "src": self.outer_ip_src,
                "dst": self.outer_ip_dst,
            },
            "inner_ipv4": {"src": self.inner_ip_src, "dst": self.inner_ip_dst},
        }
        self.save_ref_packet(pkt_types, config_layers)
        config_layers = {
            "ether": {"src": self.outer_mac_src, "dst": self.outer_mac_dst},
            "ipv4": {
                "proto": "gre",
                "src": self.outer_ip_src,
                "dst": self.outer_ip_dst,
            },
            "inner_ipv4": {"src": self.inner_ip_src, "dst": self.inner_ip_dst},
            "udp": {"chksum": 0xFFFF},
        }
        pkt = self.check_packet_transmission(pkt_types, config_layers)
        self.compare_checksum(pkt)
        if self.nic != "cavium_a063":
            # Send packet with wrong inner SCTP checksum and check forwarded packet SCTP checksum is correct
            pkt_types = {
                "MAC_IP_GRE_IPv4-TUNNEL_SCTP_PKT": ["RTE_MBUF_F_TX_SCTP_CKSUM"]
            }
            config_layers = {
                "ether": {"src": self.outer_mac_src, "dst": self.outer_mac_dst},
                "ipv4": {
                    "proto": "gre",
                    "src": self.outer_ip_src,
                    "dst": self.outer_ip_dst,
                },
                "inner_ipv4": {"src": self.inner_ip_src, "dst": self.inner_ip_dst},
                "sctp": {"src": 53, "dst": 53},
            }
            self.save_ref_packet(pkt_types, config_layers)
            config_layers = {
                "ether": {"src": self.outer_mac_src, "dst": self.outer_mac_dst},
                "ipv4": {
                    "proto": "gre",
                    "src": self.outer_ip_src,
                    "dst": self.outer_ip_dst,
                },
                "inner_ipv4": {"src": self.inner_ip_src, "dst": self.inner_ip_dst},
                "sctp": {"chksum": 0x0},
            }
            pkt = self.check_packet_transmission(pkt_types, config_layers)
            self.compare_checksum(pkt)

        self.dut.send_expect("quit", "#")

    def tear_down(self):
        """
        Run after each test case.
        Nothing to do.
        """
        self.dut.kill_all()
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        Nothing to do.
        """
        self.dut.kill_all()
        pass
