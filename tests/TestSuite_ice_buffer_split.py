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

from .rte_flow_common import FdirProcessing

# define length
MAC_HEADER_LEN = 14
IPV4_HEADER_LEN = 20
IPV6_HEADER_LEN = 40
UDP_HEADER_LEN = 8
TCP_HEADER_LEN = 20
SCTP_HEADER_LEN = 12
GRE_HEADER_LEN = 4
VXLAN_HEADER_LEN = 8
PAY_LEN = 30

port_buffer_split_mac_matched_pkts = {
    "mac_ipv4_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)',
    "mac_ipv4_ipv6_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/("Y"*30)',
    "mac_ipv4_udp_vxlan_mac_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/("Y"*30)',
    "mac_ipv6_udp_vxlan_ipv6_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/("Y"*30)',
    "mac_ipv4_gre_mac_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/("Y"*30)',
    "mac_ipv4_gre_ipv6_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/("Y"*30)',
}

port_buffer_split_inner_l3_matched_pkts = {
    "mac_ipv4_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)',
    "mac_ipv6_ipv4_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/IP()/("Y"*30)',
    "mac_ipv4_udp_vxlan_mac_ipv6_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IPv6()/("Y"*30)',
    "mac_ipv6_udp_vxlan_ipv4_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IP()/("Y"*30)',
    "mac_ipv4_gre_mac_ipv6_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IPv6()/("Y"*30)',
    "mac_ipv6_gre_ipv4_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/("Y"*30)',
}

port_buffer_split_inner_l4_matched_pkts = {
    "mac_ipv4_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/("Y"*30)',
    "mac_ipv4_ipv6_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/UDP()/("Y"*30)',
    "mac_ipv4_udp_vxlan_mac_ipv4_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)',
    "mac_ipv6_udp_vxlan_ipv6_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/UDP()/("Y"*30)',
    "mac_ipv6_gre_mac_ipv4_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)',
    "mac_ipv4_gre_ipv6_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP()/("Y"*30)',
    "mac_ipv6_tcp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/TCP()/("Y"*30)',
    "mac_ipv6_ipv4_tcp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/IP()/TCP()/("Y"*30)',
    "mac_ipv6_udp_vxlan_mac_ipv6_tcp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IPv6()/TCP()/("Y"*30)',
    "mac_ipv4_udp_vxlan_ipv4_tcp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN()/IP()/TCP()/("Y"*30)',
    "mac_ipv4_gre_mac_ipv6_tcp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IPv6()/TCP()/("Y"*30)',
    "mac_ipv6_gre_ipv4_tcp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/TCP()/("Y"*30)',
}

port_buffer_split_inner_l4_mismatched_pkts = {
    "mac_ipv4_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)',
    "mac_ipv4_gre_mac_ipv4_sctp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/SCTP()/("Y"*30)',
}

port_buffer_split_inner_sctp_matched_pkts = {
    "mac_ipv4_sctp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/SCTP()/("Y"*30)',
    "mac_ipv4_ipv6_sctp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/IPv6()/SCTP()/("Y"*30)',
    "mac_ipv4_udp_vxlan_mac_ipv4_sctp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP()/SCTP()/("Y"*30)',
    "mac_ipv6_udp_vxlan_ipv6_sctp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/SCTP()/("Y"*30)',
    "mac_ipv6_gre_mac_ipv4_sctp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/SCTP()/("Y"*30)',
    "mac_ipv4_gre_ipv6_sctp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/SCTP()/("Y"*30)',
}

port_buffer_split_inner_sctp_mismatched_pkts = {
    "mac_ipv4_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/("Y"*30)',
    "mac_ipv4_gre_mac_ipv4_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)',
    "mac_ipv4_gre_mac_ipv4_tcp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IP()/TCP()/("Y"*30)',
}

port_buffer_split_tunnel_matched_pkts = {
    "mac_ipv4_ipv4_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/IP()/("Y"*30)',
    "mac_ipv6_ipv6_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/IPv6()/("Y"*30)',
    "mac_ipv4_udp_vxlan_mac_ipv4_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP()/UDP()/("Y"*30)',
    "mac_ipv6_udp_vxlan_ipv6_tcp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=200, dport=4790)/VXLAN()/IPv6()/TCP()/("Y"*30)',
    "mac_ipv4_gre_mac_ipv6_sctp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/Ether(dst="00:11:22:33:44:66")/IPv6()/SCTP()/("Y"*30)',
    "mac_ipv6_gre_ipv4_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/("Y"*30)',
}

port_buffer_split_tunnel_mismatched_pkts = {
    "mac_ipv4_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/("Y"*30)',
}

queue_buffer_split_mac_matched_pkts = {
    "mac_ipv4_udp_vxlan_mac_ipv4_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1",dst="192.168.0.2")/("Y"*30)',
}

queue_buffer_split_mac_mismatched_pkts = {
    "mac_ipv4_udp_vxlan_mac_ipv4_l3src_changed_pkt": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.1.1",dst="192.168.0.2")/("Y"*30)',
    "mac_ipv4_udp_vxlan_mac_ipv4_l3dst_changed_pkt": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1",dst="192.168.1.2")/("Y"*30)',
}

queue_buffer_split_inner_ipv6_matched_pkts = {
    "mac_ipv6_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/("Y"*30)',
}

queue_buffer_split_inner_ipv6_mismatched_pkts = {
    "mac_ipv6_l3src_changed_pkt": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::8",dst="2001::2")/("Y"*30)',
    "mac_ipv6_l3dst_changed_pkt": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::9")/("Y"*30)',
}

queue_buffer_split_inner_ipv4_udp_matched_pkts = {
    "mac_ipv4_udp_vxlan_mac_ipv4_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1",dst="192.168.0.2")/UDP(dport=23)/("Y"*30)',
}

queue_buffer_split_inner_ipv4_udp_mismatched_pkts = {
    "mac_ipv4_udp_vxlan_mac_ipv4_udp_l3src_changed_pkt": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.1.1",dst="192.168.0.2")/UDP(dport=23)/("Y"*30)',
    "mac_ipv4_udp_vxlan_mac_ipv4_udp_l4dst_changed_pkt": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.1",dst="192.168.0.2")/UDP(dport=24)/("Y"*30)',
}

queue_buffer_split_inner_ipv6_udp_matched_pkts = {
    "mac_ipv6_udp_pay": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/UDP(dport=23)/("Y"*30)',
}

queue_buffer_split_inner_ipv6_udp_mismatched_pkts = {
    "mac_ipv6_udp_l3src_changed_pkt": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::8",dst="2001::2")/UDP(dport=23)/("Y"*30)',
    "mac_ipv6_udp_l4dst_changed_pkt": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/UDP(dport=24)/("Y"*30)',
}

port_buffer_split_mac = {
    "test": [
        {
            "port_id": 0,
            "send_packet": [
                port_buffer_split_mac_matched_pkts["mac_ipv4_pay"],
                port_buffer_split_mac_matched_pkts["mac_ipv4_ipv6_pay"],
                port_buffer_split_mac_matched_pkts["mac_ipv4_udp_vxlan_mac_pay"],
                port_buffer_split_mac_matched_pkts["mac_ipv6_udp_vxlan_ipv6_pay"],
                port_buffer_split_mac_matched_pkts["mac_ipv4_gre_mac_pay"],
                port_buffer_split_mac_matched_pkts["mac_ipv4_gre_ipv6_pay"],
            ],
            "check_pkt_data": True,
            "action": "check_seg_len",
        },
        {
            "port_id": 1,
            "send_packet": [
                port_buffer_split_mac_matched_pkts["mac_ipv4_pay"],
                port_buffer_split_mac_matched_pkts["mac_ipv4_ipv6_pay"],
                port_buffer_split_mac_matched_pkts["mac_ipv4_udp_vxlan_mac_pay"],
                port_buffer_split_mac_matched_pkts["mac_ipv6_udp_vxlan_ipv6_pay"],
                port_buffer_split_mac_matched_pkts["mac_ipv4_gre_mac_pay"],
                port_buffer_split_mac_matched_pkts["mac_ipv4_gre_ipv6_pay"],
            ],
            "check_pkt_data": False,
            "action": "check_no_seg_len",
        },
    ],
}

port_buffer_split_inner_l3 = {
    "test": [
        {
            "port_id": 0,
            "send_packet": [
                port_buffer_split_inner_l3_matched_pkts["mac_ipv4_pay"],
                port_buffer_split_inner_l3_matched_pkts["mac_ipv6_ipv4_pay"],
                port_buffer_split_inner_l3_matched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv6_pay"
                ],
                port_buffer_split_inner_l3_matched_pkts["mac_ipv6_udp_vxlan_ipv4_pay"],
                port_buffer_split_inner_l3_matched_pkts["mac_ipv4_gre_mac_ipv6_pay"],
                port_buffer_split_inner_l3_matched_pkts["mac_ipv6_gre_ipv4_pay"],
            ],
            "check_pkt_data": True,
            "action": "check_seg_len",
        },
        {
            "port_id": 1,
            "send_packet": [
                port_buffer_split_inner_l3_matched_pkts["mac_ipv4_pay"],
                port_buffer_split_inner_l3_matched_pkts["mac_ipv6_ipv4_pay"],
                port_buffer_split_inner_l3_matched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv6_pay"
                ],
                port_buffer_split_inner_l3_matched_pkts["mac_ipv6_udp_vxlan_ipv4_pay"],
                port_buffer_split_inner_l3_matched_pkts["mac_ipv4_gre_mac_ipv6_pay"],
                port_buffer_split_inner_l3_matched_pkts["mac_ipv6_gre_ipv4_pay"],
            ],
            "check_pkt_data": False,
            "action": "check_no_seg_len",
        },
    ],
}

port_buffer_split_inner_l4 = {
    "test": [
        {
            "port_id": 0,
            "send_packet": [
                port_buffer_split_inner_l4_matched_pkts["mac_ipv4_udp_pay"],
                port_buffer_split_inner_l4_matched_pkts["mac_ipv4_ipv6_udp_pay"],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_udp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv6_udp_vxlan_ipv6_udp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv6_gre_mac_ipv4_udp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts["mac_ipv4_gre_ipv6_udp_pay"],
                port_buffer_split_inner_l4_matched_pkts["mac_ipv6_tcp_pay"],
                port_buffer_split_inner_l4_matched_pkts["mac_ipv6_ipv4_tcp_pay"],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv6_udp_vxlan_mac_ipv6_tcp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv4_udp_vxlan_ipv4_tcp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv4_gre_mac_ipv6_tcp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts["mac_ipv6_gre_ipv4_tcp_pay"],
            ],
            "check_pkt_data": True,
            "action": "check_seg_len",
        },
        {
            "port_id": 0,
            "send_packet": [
                port_buffer_split_inner_l4_mismatched_pkts["mac_ipv4_pay"],
                port_buffer_split_inner_l4_mismatched_pkts[
                    "mac_ipv4_gre_mac_ipv4_sctp_pay"
                ],
            ],
            "check_pkt_data": True,
            "action": "check_no_segment",
        },
        {
            "port_id": 1,
            "send_packet": [
                port_buffer_split_inner_l4_matched_pkts["mac_ipv4_udp_pay"],
                port_buffer_split_inner_l4_matched_pkts["mac_ipv4_ipv6_udp_pay"],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_udp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv6_udp_vxlan_ipv6_udp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv6_gre_mac_ipv4_udp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts["mac_ipv4_gre_ipv6_udp_pay"],
                port_buffer_split_inner_l4_matched_pkts["mac_ipv6_tcp_pay"],
                port_buffer_split_inner_l4_matched_pkts["mac_ipv6_ipv4_tcp_pay"],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv6_udp_vxlan_mac_ipv6_tcp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv4_udp_vxlan_ipv4_tcp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts[
                    "mac_ipv4_gre_mac_ipv6_tcp_pay"
                ],
                port_buffer_split_inner_l4_matched_pkts["mac_ipv6_gre_ipv4_tcp_pay"],
            ],
            "check_pkt_data": False,
            "action": "check_no_seg_len",
        },
    ],
}

port_buffer_split_inner_sctp = {
    "test": [
        {
            "port_id": 0,
            "send_packet": [
                port_buffer_split_inner_sctp_matched_pkts["mac_ipv4_sctp_pay"],
                port_buffer_split_inner_sctp_matched_pkts["mac_ipv4_ipv6_sctp_pay"],
                port_buffer_split_inner_sctp_matched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_sctp_pay"
                ],
                port_buffer_split_inner_sctp_matched_pkts[
                    "mac_ipv6_udp_vxlan_ipv6_sctp_pay"
                ],
                port_buffer_split_inner_sctp_matched_pkts[
                    "mac_ipv6_gre_mac_ipv4_sctp_pay"
                ],
                port_buffer_split_inner_sctp_matched_pkts["mac_ipv4_gre_ipv6_sctp_pay"],
            ],
            "check_pkt_data": True,
            "action": "check_seg_len",
        },
        {
            "port_id": 0,
            "send_packet": [
                port_buffer_split_inner_sctp_mismatched_pkts["mac_ipv4_pay"],
                port_buffer_split_inner_sctp_mismatched_pkts[
                    "mac_ipv4_gre_mac_ipv4_udp_pay"
                ],
                port_buffer_split_inner_sctp_mismatched_pkts[
                    "mac_ipv4_gre_mac_ipv4_tcp_pay"
                ],
            ],
            "check_pkt_data": True,
            "action": "check_no_segment",
        },
        {
            "port_id": 1,
            "send_packet": [
                port_buffer_split_inner_sctp_matched_pkts["mac_ipv4_sctp_pay"],
                port_buffer_split_inner_sctp_matched_pkts["mac_ipv4_ipv6_sctp_pay"],
                port_buffer_split_inner_sctp_matched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_sctp_pay"
                ],
                port_buffer_split_inner_sctp_matched_pkts[
                    "mac_ipv6_udp_vxlan_ipv6_sctp_pay"
                ],
                port_buffer_split_inner_sctp_matched_pkts[
                    "mac_ipv6_gre_mac_ipv4_sctp_pay"
                ],
                port_buffer_split_inner_sctp_matched_pkts["mac_ipv4_gre_ipv6_sctp_pay"],
            ],
            "check_pkt_data": False,
            "action": "check_no_seg_len",
        },
    ],
}

port_buffer_split_tunnel = {
    "test": [
        {
            "port_id": 0,
            "send_packet": [
                port_buffer_split_tunnel_matched_pkts["mac_ipv4_ipv4_pay"],
                port_buffer_split_tunnel_matched_pkts["mac_ipv6_ipv6_pay"],
                port_buffer_split_tunnel_matched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_udp_pay"
                ],
                port_buffer_split_tunnel_matched_pkts[
                    "mac_ipv6_udp_vxlan_ipv6_tcp_pay"
                ],
                port_buffer_split_tunnel_matched_pkts["mac_ipv4_gre_mac_ipv6_sctp_pay"],
                port_buffer_split_tunnel_matched_pkts["mac_ipv6_gre_ipv4_udp_pay"],
            ],
            "check_pkt_data": True,
            "action": "check_seg_len",
        },
        {
            "port_id": 0,
            "send_packet": [
                port_buffer_split_tunnel_mismatched_pkts["mac_ipv4_udp_pay"],
            ],
            "check_pkt_data": True,
            "action": "check_no_segment",
        },
        {
            "port_id": 1,
            "send_packet": [
                port_buffer_split_tunnel_matched_pkts["mac_ipv4_ipv4_pay"],
                port_buffer_split_tunnel_matched_pkts["mac_ipv6_ipv6_pay"],
                port_buffer_split_tunnel_matched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_udp_pay"
                ],
                port_buffer_split_tunnel_matched_pkts[
                    "mac_ipv6_udp_vxlan_ipv6_tcp_pay"
                ],
                port_buffer_split_tunnel_matched_pkts["mac_ipv4_gre_mac_ipv6_sctp_pay"],
                port_buffer_split_tunnel_matched_pkts["mac_ipv6_gre_ipv4_udp_pay"],
            ],
            "check_pkt_data": False,
            "action": "check_no_seg_len",
        },
    ],
}

queue_buffer_split_mac = {
    "test": [
        {
            "port_id": 0,
            "send_packet": [
                queue_buffer_split_mac_matched_pkts["mac_ipv4_udp_vxlan_mac_ipv4_pay"],
            ],
            "check_pkt_data": True,
            "action": "check_seg_len",
        },
        {
            "port_id": 0,
            "send_packet": [
                queue_buffer_split_mac_mismatched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_l3src_changed_pkt"
                ],
                queue_buffer_split_mac_mismatched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_l3dst_changed_pkt"
                ],
            ],
            "check_pkt_data": False,
            "action": "check_mismatch_pkts",
        },
    ],
}

queue_buffer_split_inner_ipv6 = {
    "test": [
        {
            "port_id": 0,
            "send_packet": [
                queue_buffer_split_inner_ipv6_matched_pkts["mac_ipv6_pay"],
            ],
            "check_pkt_data": True,
            "action": "check_seg_len",
        },
        {
            "port_id": 0,
            "send_packet": [
                queue_buffer_split_inner_ipv6_mismatched_pkts[
                    "mac_ipv6_l3src_changed_pkt"
                ],
                queue_buffer_split_inner_ipv6_mismatched_pkts[
                    "mac_ipv6_l3dst_changed_pkt"
                ],
            ],
            "check_pkt_data": False,
            "action": "check_mismatch_pkts",
        },
    ],
}

queue_buffer_split_inner_ipv4_udp = {
    "test": [
        {
            "port_id": 0,
            "send_packet": [
                queue_buffer_split_inner_ipv4_udp_matched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_udp_pay"
                ],
            ],
            "check_pkt_data": True,
            "action": "check_seg_len",
        },
        {
            "port_id": 0,
            "send_packet": [
                queue_buffer_split_inner_ipv4_udp_mismatched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_udp_l3src_changed_pkt"
                ],
                queue_buffer_split_inner_ipv4_udp_mismatched_pkts[
                    "mac_ipv4_udp_vxlan_mac_ipv4_udp_l4dst_changed_pkt"
                ],
            ],
            "check_pkt_data": False,
            "action": "check_mismatch_pkts",
        },
    ],
}

queue_buffer_split_inner_ipv6_udp = {
    "test": [
        {
            "port_id": 0,
            "send_packet": [
                queue_buffer_split_inner_ipv6_udp_matched_pkts["mac_ipv6_udp_pay"],
            ],
            "check_pkt_data": True,
            "action": "check_seg_len",
        },
        {
            "port_id": 0,
            "send_packet": [
                queue_buffer_split_inner_ipv6_udp_mismatched_pkts[
                    "mac_ipv6_udp_l3src_changed_pkt"
                ],
                queue_buffer_split_inner_ipv6_udp_mismatched_pkts[
                    "mac_ipv6_udp_l4dst_changed_pkt"
                ],
            ],
            "check_pkt_data": False,
            "action": "check_mismatch_pkts",
        },
    ],
}

queue_buffer_split_inner_ipv4_tcp = [
    eval(
        str(queue_buffer_split_inner_ipv4_udp)
        .replace("ipv4_udp", "ipv4_tcp")
        .replace("UDP(dport", "TCP(dport")
    )
]

queue_buffer_split_inner_ipv6_tcp = [
    eval(
        str(queue_buffer_split_inner_ipv6_udp)
        .replace("ipv6_udp", "ipv6_tcp")
        .replace("UDP(dport", "TCP(dport")
    )
]

queue_buffer_split_inner_ipv4_sctp = [
    eval(
        str(queue_buffer_split_inner_ipv4_udp)
        .replace("ipv4_udp", "ipv4_sctp")
        .replace("UDP(dport", "SCTP(dport")
    )
]

queue_buffer_split_inner_ipv6_sctp = [
    eval(
        str(queue_buffer_split_inner_ipv6_udp)
        .replace("ipv6_udp", "ipv6_sctp")
        .replace("UDP(dport", "SCTP(dport")
    )
]


class TestBufferSplit(TestCase):
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
        self.dut.build_install_dpdk(
            self.target, extra_options="-Dc_args='-DRTE_ETHDEV_DEBUG_RX=1'"
        )
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_ifaces = [
            self.tester.get_interface(self.dut.ports_map[port])
            for port in self.dut_ports
        ]
        self.pf_pci0 = self.dut.ports_info[self.dut_ports[0]]["pci"]
        self.pf_pci1 = self.dut.ports_info[self.dut_ports[1]]["pci"]

        self.rxq = 8
        self.pkt = Packet()
        self.pmdout = PmdOutput(self.dut)
        self.fdirprocess = FdirProcessing(
            self, self.pmdout, self.tester_ifaces[0], self.rxq
        )

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def launch_testpmd(self, allowlist, line_option=""):
        """
        start testpmd
        """
        # Prepare testpmd EAL and parameters
        self.pmdout.start_testpmd(
            socket=self.ports_socket,
            eal_param=allowlist + " --force-max-simd-bitwidth=64 ",
            param=" --mbuf-size=2048,2048 " + line_option,
        )
        # test link status
        res = self.pmdout.wait_link_status_up("all", timeout=15)
        self.verify(res is True, "there have port link is down")

    def launch_two_ports_testpmd_and_config_port_buffer_split(self):
        allowlist = f"-a {self.pf_pci0} -a {self.pf_pci1}"
        line_option = ""
        self.launch_testpmd(allowlist, line_option)
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("show port 0 rx_offload configuration", "testpmd> ")

    def launch_one_port_testpmd_with_multi_queues(self):
        allowlist = f"-a {self.pf_pci0}"
        line_option = "--txq=8 --rxq=8"
        self.launch_testpmd(allowlist, line_option)
        self.dut.send_expect("port stop all", "testpmd> ")

    def start_testpmd(self):
        self.dut.send_expect("show config rxhdrs", "testpmd> ")
        self.dut.send_expect(
            "port config 0 udp_tunnel_port add vxlan 4789", "testpmd> "
        )
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

    def check_pkt_data_same(self, pkt_data, expect_pkt_data):
        self.error_msgs = []
        for i in range(len(expect_pkt_data)):
            if pkt_data[i] != expect_pkt_data[i]:
                error_msg = "The packet data should be same with expect packet data"
                self.logger.error(error_msg)
                self.error_msgs.append(error_msg)
                self.verify(not self.error_msgs, "Test failed")

    def check_seg_len(self, seg_len, expected_seg_len):
        if len(seg_len) == 0:
            error_msg = "There is no segment"
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)
        else:
            for i in range(len(expected_seg_len)):
                if seg_len[i] != expected_seg_len[i]:
                    error_msg = (
                        "The segment length should be same with expected "
                        "segment length {}".format(expected_seg_len)
                    )
                    self.logger.error(error_msg)
                    self.error_msgs.append(error_msg)

    def check_no_seg_len(self, seg_len):
        for i in range(len(seg_len)):
            if seg_len[i]:
                error_msg = "The segment length should be empty"
                self.logger.error(error_msg)
                self.error_msgs.append(error_msg)

    def check_no_segment(self, seg_len, expected_no_segment):
        if len(seg_len) == 0:
            error_msg = "The segment length should not be empty"
            self.logger.error(error_msg)
            self.error_msgs.append(error_msg)
        else:
            for i in range(len(expected_no_segment)):
                if seg_len[i] != expected_no_segment[i]:
                    error_msg = (
                        "The segment length should be same with expected "
                        "no segment length {}".format(expected_no_segment)
                    )
                    self.logger.error(error_msg)
                    self.error_msgs.append(error_msg)

    def check_mismatch_pkts(
        self, queue_id, queue_id1, queue_id2, seg_len, expected_seg_len
    ):
        for i in range(len(queue_id)):
            if queue_id[i] == queue_id1 or queue_id[i] == queue_id2:
                self.logger.info(
                    "Mismatch pkt is distributed to buffer split queue by RSS, action: check_seg_len"
                )
                self.check_seg_len(seg_len[i], expected_seg_len[0])
            else:
                self.logger.info(
                    "Mismatch pkt is distributed to not buffer split queue by RSS, action: check_no_seg_len"
                )
                self.check_no_seg_len(seg_len[i])

    def get_pkt_data(self, pkts):
        pkt_data_list = []
        self.logger.info("{}".format(pkts))
        self.tester.send_expect("scapy", ">>> ")
        time.sleep(1)
        for i in range(len(pkts)):
            self.tester.send_expect("p = %s" % pkts[i], ">>>")
            out = self.tester.send_expect("hexdump(p)", ">>>")
            time.sleep(1)
            pkt_pat = "(?<=00\S\d )(.*)(?=  )"
            pkt_data = re.findall(pkt_pat, out, re.M)
            pkt_data = (" ".join(map(str, pkt_data))).replace("  ", " ")
            pkt_data = pkt_data.strip()
            self.logger.info("pkt_data: {}".format(pkt_data))
            if len(pkt_data) != 0:
                pkt_data_list.append(pkt_data)
        self.logger.info("pkt_data_list: {}".format(pkt_data_list))
        return pkt_data_list

    def send_pkt_get_output(self, pkts, port_id, count=1):
        pkt_data_list = []
        segment_len_list = []
        queue_id_list = []
        self.logger.info("----------send packet-------------")
        self.logger.info("{}".format(pkts))
        tx_port = self.tester_ifaces[port_id]
        for i in range(len(pkts)):
            self.pkt.update_pkt(pkts[i])
            time.sleep(2)
            self.pkt.send_pkt(crb=self.tester, tx_port=tx_port, count=count)
            out = self.pmdout.get_output(timeout=2)
            pkt_pat = "(?<=: )(.*)(?= \| )"
            pkt_data = re.findall(pkt_pat, out, re.M)
            pkt_data = (" ".join(map(str, pkt_data))).replace("  ", "")
            self.logger.info("pkt_data: {}".format(pkt_data))
            if len(pkt_data) != 0:
                pkt_data_list.append(pkt_data)
            segment_pat = ".*segment\s+at\s.*len=(\d+)"
            segment_infos = re.findall(segment_pat, out, re.M)
            segment_len = list(map(int, segment_infos))
            self.logger.info("segment_len: {}".format(segment_len))
            segment_len_list.append(segment_len)
            queue_pat = ".*queue_id=(\d+)"
            queue_id = re.findall(queue_pat, out, re.M)
            queue_id = list(map(int, queue_id))
            if queue_id:
                queue_id_list.append(queue_id)
        self.logger.info("pkt_data_list: {}".format(pkt_data_list))
        self.logger.info("segment_len_list: {}".format(segment_len_list))
        return pkt_data_list, segment_len_list, queue_id_list

    def handle_buffer_split_case(
        self,
        case_info,
        expected_seg_len,
        expected_no_segment,
        queue_id1,
        queue_id2,
    ):
        self.error_msgs = []
        seg_len = []
        # handle tests
        tests = case_info["test"]
        for test in tests:
            if "send_packet" in test:
                pkt_data, seg_len, queue_id = self.send_pkt_get_output(
                    test["send_packet"], port_id=test["port_id"]
                )
                if test["check_pkt_data"] == True:
                    self.logger.info("action: check_pkt_data_same")
                    expect_pkt_data = self.get_pkt_data(test["send_packet"])
                    self.check_pkt_data_same(pkt_data, expect_pkt_data)
            if "action" in test:
                self.logger.info("action: {}\n".format(test["action"]))
                if test["action"] == "check_seg_len":
                    self.check_seg_len(seg_len, expected_seg_len)
                elif test["action"] == "check_no_segment":
                    self.check_no_segment(seg_len, expected_no_segment)
                elif test["action"] == "check_no_seg_len":
                    self.check_no_seg_len(seg_len)
                else:
                    self.check_mismatch_pkts(
                        queue_id, queue_id1, queue_id2, seg_len, expected_seg_len
                    )
            self.verify(not self.error_msgs, "Test failed")

    def verify_port_buffer_split_outer_mac(self):
        self.launch_two_ports_testpmd_and_config_port_buffer_split()
        self.dut.send_expect("set rxhdrs eth", "testpmd> ")
        self.start_testpmd()

        expected_seg_len = [
            [MAC_HEADER_LEN, IPV4_HEADER_LEN + PAY_LEN],
            [MAC_HEADER_LEN, IPV4_HEADER_LEN + IPV6_HEADER_LEN + PAY_LEN],
            [
                MAC_HEADER_LEN,
                IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN
                + PAY_LEN,
            ],
            [
                MAC_HEADER_LEN,
                IPV6_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + IPV6_HEADER_LEN
                + PAY_LEN,
            ],
            [
                MAC_HEADER_LEN,
                IPV4_HEADER_LEN + GRE_HEADER_LEN + MAC_HEADER_LEN + PAY_LEN,
            ],
            [
                MAC_HEADER_LEN,
                IPV4_HEADER_LEN + GRE_HEADER_LEN + IPV6_HEADER_LEN + PAY_LEN,
            ],
        ]
        expected_no_segment = []
        queue_id1 = queue_id2 = []

        self.handle_buffer_split_case(
            port_buffer_split_mac,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )

    def verify_port_buffer_split_inner_mac(self):
        self.launch_two_ports_testpmd_and_config_port_buffer_split()
        self.dut.send_expect("set rxhdrs inner-eth", "testpmd> ")
        self.start_testpmd()

        expected_seg_len = [
            [MAC_HEADER_LEN, IPV4_HEADER_LEN + PAY_LEN],
            [MAC_HEADER_LEN, IPV4_HEADER_LEN + IPV6_HEADER_LEN + PAY_LEN],
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN,
                IPV6_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + IPV6_HEADER_LEN
                + PAY_LEN,
            ],
            [
                MAC_HEADER_LEN + IPV4_HEADER_LEN + GRE_HEADER_LEN + MAC_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN,
                IPV4_HEADER_LEN + GRE_HEADER_LEN + IPV6_HEADER_LEN + PAY_LEN,
            ],
        ]
        expected_no_segment = []
        queue_id1 = queue_id2 = []

        self.handle_buffer_split_case(
            port_buffer_split_mac,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )

    def verify_port_buffer_split_inner_l3(self, ptype):
        self.launch_two_ports_testpmd_and_config_port_buffer_split()
        self.dut.send_expect("set rxhdrs %s" % ptype, "testpmd> ")
        self.start_testpmd()

        expected_seg_len = [
            [MAC_HEADER_LEN + IPV4_HEADER_LEN, PAY_LEN],
            [MAC_HEADER_LEN + IPV6_HEADER_LEN + IPV4_HEADER_LEN, PAY_LEN],
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV6_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV6_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + IPV4_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + GRE_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV6_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN + IPV6_HEADER_LEN + GRE_HEADER_LEN + IPV4_HEADER_LEN,
                PAY_LEN,
            ],
        ]
        expected_no_segment = []
        queue_id1 = queue_id2 = []

        self.handle_buffer_split_case(
            port_buffer_split_inner_l3,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )
        self.dut.send_expect("quit", "# ")

    def verify_port_buffer_split_inner_l4(self, ptype):
        self.launch_two_ports_testpmd_and_config_port_buffer_split()
        self.dut.send_expect("set rxhdrs %s" % ptype, "testpmd> ")
        self.start_testpmd()

        expected_seg_len = [
            [MAC_HEADER_LEN + IPV4_HEADER_LEN + UDP_HEADER_LEN, PAY_LEN],
            [
                MAC_HEADER_LEN + IPV4_HEADER_LEN + IPV6_HEADER_LEN + UDP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV6_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + IPV6_HEADER_LEN
                + UDP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV6_HEADER_LEN
                + GRE_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + GRE_HEADER_LEN
                + IPV6_HEADER_LEN
                + UDP_HEADER_LEN,
                PAY_LEN,
            ],
            [MAC_HEADER_LEN + IPV6_HEADER_LEN + TCP_HEADER_LEN, PAY_LEN],
            [
                MAC_HEADER_LEN + IPV6_HEADER_LEN + IPV4_HEADER_LEN + TCP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV6_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV6_HEADER_LEN
                + TCP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + IPV4_HEADER_LEN
                + TCP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + GRE_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV6_HEADER_LEN
                + TCP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV6_HEADER_LEN
                + GRE_HEADER_LEN
                + IPV4_HEADER_LEN
                + TCP_HEADER_LEN,
                PAY_LEN,
            ],
        ]
        expected_no_segment = [
            [0, MAC_HEADER_LEN + IPV4_HEADER_LEN + PAY_LEN],
            [
                0,
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + GRE_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + SCTP_HEADER_LEN
                + PAY_LEN,
            ],
        ]
        queue_id1 = queue_id2 = []

        self.handle_buffer_split_case(
            port_buffer_split_inner_l4,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )
        self.dut.send_expect("quit", "# ")

    def verify_port_buffer_split_inner_sctp(self, ptype):
        self.launch_two_ports_testpmd_and_config_port_buffer_split()
        self.dut.send_expect("set rxhdrs %s" % ptype, "testpmd> ")
        self.start_testpmd()

        expected_seg_len = [
            [MAC_HEADER_LEN + IPV4_HEADER_LEN + SCTP_HEADER_LEN, PAY_LEN],
            [
                MAC_HEADER_LEN + IPV4_HEADER_LEN + IPV6_HEADER_LEN + SCTP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + SCTP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV6_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + IPV6_HEADER_LEN
                + SCTP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV6_HEADER_LEN
                + GRE_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + SCTP_HEADER_LEN,
                PAY_LEN,
            ],
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + GRE_HEADER_LEN
                + IPV6_HEADER_LEN
                + SCTP_HEADER_LEN,
                PAY_LEN,
            ],
        ]
        expected_no_segment = [
            [0, MAC_HEADER_LEN + IPV4_HEADER_LEN + PAY_LEN],
            [
                0,
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + GRE_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + PAY_LEN,
            ],
            [
                0,
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + GRE_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + TCP_HEADER_LEN
                + PAY_LEN,
            ],
        ]
        queue_id1 = queue_id2 = []

        self.handle_buffer_split_case(
            port_buffer_split_inner_sctp,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )
        self.dut.send_expect("quit", "# ")

    def verify_port_buffer_split_tunnel(self):
        self.launch_two_ports_testpmd_and_config_port_buffer_split()
        self.dut.send_expect("set rxhdrs grenat", "testpmd> ")
        self.start_testpmd()

        expected_seg_len = [
            [MAC_HEADER_LEN + IPV4_HEADER_LEN, IPV4_HEADER_LEN + PAY_LEN],
            [MAC_HEADER_LEN + IPV6_HEADER_LEN, IPV6_HEADER_LEN + PAY_LEN],
            [
                MAC_HEADER_LEN + IPV4_HEADER_LEN + UDP_HEADER_LEN + VXLAN_HEADER_LEN,
                MAC_HEADER_LEN + IPV4_HEADER_LEN + UDP_HEADER_LEN + PAY_LEN,
            ],
            [
                MAC_HEADER_LEN + IPV6_HEADER_LEN + UDP_HEADER_LEN + VXLAN_HEADER_LEN,
                IPV6_HEADER_LEN + TCP_HEADER_LEN + PAY_LEN,
            ],
            [
                MAC_HEADER_LEN + IPV4_HEADER_LEN + GRE_HEADER_LEN,
                MAC_HEADER_LEN + IPV6_HEADER_LEN + SCTP_HEADER_LEN + PAY_LEN,
            ],
            [
                MAC_HEADER_LEN + IPV6_HEADER_LEN + GRE_HEADER_LEN,
                IPV4_HEADER_LEN + UDP_HEADER_LEN + PAY_LEN,
            ],
        ]
        expected_no_segment = [
            [0, MAC_HEADER_LEN + IPV4_HEADER_LEN + UDP_HEADER_LEN + PAY_LEN],
        ]
        queue_id1 = queue_id2 = []

        self.handle_buffer_split_case(
            port_buffer_split_tunnel,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )

    def verify_queue_buffer_split_outer_mac(self):
        self.launch_one_port_testpmd_with_multi_queues()
        self.dut.send_expect("port 0 rxq 1 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("show port 0 rx_offload configuration", "testpmd> ")
        self.dut.send_expect("set rxhdrs eth", "testpmd> ")
        self.start_testpmd()

        fdir_rule = [
            "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 1 / mark / end",
        ]

        queue_id1 = queue_id2 = [1]
        expected_seg_len = [
            [
                MAC_HEADER_LEN,
                IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + PAY_LEN,
            ],
        ]
        expected_no_segment = []

        rule_li = self.fdirprocess.create_rule(fdir_rule[0])
        self.handle_buffer_split_case(
            queue_buffer_split_mac,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )
        self.fdirprocess.destroy_rule(port_id=0, rule_id=rule_li)

    def verify_queue_buffer_split_inner_mac(self):
        self.launch_one_port_testpmd_with_multi_queues()
        self.dut.send_expect("port 0 rxq 2 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("port 0 rxq 3 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("show port 0 rx_offload configuration", "testpmd> ")
        self.dut.send_expect("set rxhdrs inner-eth", "testpmd> ")
        self.start_testpmd()

        fdir_rule = [
            "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions rss queues 2 3 end / mark / end",
        ]

        queue_id1 = [2]
        queue_id2 = [3]
        expected_seg_len = [
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN,
                IPV4_HEADER_LEN + PAY_LEN,
            ],
        ]
        expected_no_segment = []

        rule_li = self.fdirprocess.create_rule(fdir_rule[0])
        self.handle_buffer_split_case(
            queue_buffer_split_mac,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )
        self.fdirprocess.destroy_rule(port_id=0, rule_id=rule_li)

    def verify_queue_buffer_split_inner_ipv4(self, ptype):
        self.launch_one_port_testpmd_with_multi_queues()
        self.dut.send_expect("port 0 rxq 2 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("show port 0 rx_offload configuration", "testpmd> ")
        self.dut.send_expect("set rxhdrs %s" % ptype, "testpmd> ")
        self.start_testpmd()

        fdir_rule = [
            "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 2 / mark / end",
        ]

        queue_id1 = queue_id2 = [2]
        expected_seg_len = [
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN,
                PAY_LEN,
            ],
        ]
        expected_no_segment = []

        rule_li = self.fdirprocess.create_rule(fdir_rule[0])
        self.handle_buffer_split_case(
            queue_buffer_split_mac,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )
        self.fdirprocess.destroy_rule(port_id=0, rule_id=rule_li)
        self.dut.send_expect("quit", "# ")

    def verify_queue_buffer_split_inner_ipv6(self, ptype):
        self.launch_one_port_testpmd_with_multi_queues()
        self.dut.send_expect("port 0 rxq 4 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("port 0 rxq 5 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("show port 0 rx_offload configuration", "testpmd> ")
        self.dut.send_expect("set rxhdrs %s" % ptype, "testpmd> ")
        self.start_testpmd()

        fdir_rule = [
            "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / end actions rss queues 4 5 end / mark / end",
        ]

        queue_id1 = [4]
        queue_id2 = [5]
        expected_seg_len = [
            [MAC_HEADER_LEN + IPV6_HEADER_LEN, PAY_LEN],
        ]
        expected_no_segment = []

        rule_li = self.fdirprocess.create_rule(fdir_rule[0])
        self.handle_buffer_split_case(
            queue_buffer_split_inner_ipv6,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )
        self.fdirprocess.destroy_rule(port_id=0, rule_id=rule_li)
        self.dut.send_expect("quit", "# ")

    def verify_queue_buffer_split_inner_udp(self, ptype):
        self.launch_one_port_testpmd_with_multi_queues()
        self.dut.send_expect("port 0 rxq 3 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("show port 0 rx_offload configuration", "testpmd> ")
        self.dut.send_expect("set rxhdrs %s" % ptype, "testpmd> ")
        self.start_testpmd()

        fdir_rule = [
            "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / udp dst is 23 / end actions queue index 3 / mark / end",
            "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp dst is 23 / end actions queue index 3 / mark / end",
        ]

        queue_id1 = queue_id2 = [3]
        expected_ipv4_pkts_seg_len = [
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN,
                PAY_LEN,
            ],
        ]
        expected_ipv6_pkts_seg_len = [
            [MAC_HEADER_LEN + IPV6_HEADER_LEN + UDP_HEADER_LEN, PAY_LEN],
        ]
        expected_no_segment = []

        if ptype == "ipv4-udp" or ptype == "inner-ipv4-udp":
            rule_li = self.fdirprocess.create_rule(fdir_rule[0])
            self.handle_buffer_split_case(
                queue_buffer_split_inner_ipv4_udp,
                expected_ipv4_pkts_seg_len,
                expected_no_segment,
                queue_id1,
                queue_id2,
            )
        else:
            rule_li = self.fdirprocess.create_rule(fdir_rule[1])
            self.handle_buffer_split_case(
                queue_buffer_split_inner_ipv6_udp,
                expected_ipv6_pkts_seg_len,
                expected_no_segment,
                queue_id1,
                queue_id2,
            )
        self.fdirprocess.destroy_rule(port_id=0, rule_id=rule_li)
        self.dut.send_expect("quit", "# ")

    def verify_queue_buffer_split_inner_tcp(self, ptype):
        self.launch_one_port_testpmd_with_multi_queues()
        self.dut.send_expect("port 0 rxq 2 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("port 0 rxq 3 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("show port 0 rx_offload configuration", "testpmd> ")
        self.dut.send_expect("set rxhdrs %s" % ptype, "testpmd> ")
        self.start_testpmd()

        fdir_rule = [
            "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / tcp dst is 23 / end actions rss queues 2 3 end / mark / end",
            "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / tcp dst is 23 / end actions rss queues 2 3 end / mark / end",
        ]

        queue_id1 = [2]
        queue_id2 = [3]
        expected_ipv4_pkts_seg_len = [
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + TCP_HEADER_LEN,
                PAY_LEN,
            ],
        ]
        expected_ipv6_pkts_seg_len = [
            [MAC_HEADER_LEN + IPV6_HEADER_LEN + TCP_HEADER_LEN, PAY_LEN],
        ]
        expected_no_segment = []

        if ptype == "ipv4-tcp" or ptype == "inner-ipv4-tcp":
            rule_li = self.fdirprocess.create_rule(fdir_rule[0])
            self.handle_buffer_split_case(
                queue_buffer_split_inner_ipv4_tcp[0],
                expected_ipv4_pkts_seg_len,
                expected_no_segment,
                queue_id1,
                queue_id2,
            )
        else:
            rule_li = self.fdirprocess.create_rule(fdir_rule[1])
            self.handle_buffer_split_case(
                queue_buffer_split_inner_ipv6_tcp[0],
                expected_ipv6_pkts_seg_len,
                expected_no_segment,
                queue_id1,
                queue_id2,
            )
        self.fdirprocess.destroy_rule(port_id=0, rule_id=rule_li)
        self.dut.send_expect("quit", "# ")

    def verify_queue_buffer_split_inner_sctp(self, ptype):
        self.launch_one_port_testpmd_with_multi_queues()
        self.dut.send_expect("port 0 rxq 5 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("show port 0 rx_offload configuration", "testpmd> ")
        self.dut.send_expect("set rxhdrs %s" % ptype, "testpmd> ")
        self.start_testpmd()

        fdir_rule = [
            "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / sctp dst is 23 / end actions queue index 5 / mark / end",
            "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / sctp dst is 23 / end actions queue index 5 / mark / end",
        ]

        queue_id1 = queue_id2 = [5]
        expected_ipv4_pkts_seg_len = [
            [
                MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + UDP_HEADER_LEN
                + VXLAN_HEADER_LEN
                + MAC_HEADER_LEN
                + IPV4_HEADER_LEN
                + SCTP_HEADER_LEN,
                PAY_LEN,
            ],
        ]
        expected_ipv6_pkts_seg_len = [
            [MAC_HEADER_LEN + IPV6_HEADER_LEN + SCTP_HEADER_LEN, PAY_LEN],
        ]
        expected_no_segment = []

        if ptype == "ipv4-sctp" or ptype == "inner-ipv4-sctp":
            rule_li = self.fdirprocess.create_rule(fdir_rule[0])
            self.handle_buffer_split_case(
                queue_buffer_split_inner_ipv4_sctp[0],
                expected_ipv4_pkts_seg_len,
                expected_no_segment,
                queue_id1,
                queue_id2,
            )
        else:
            rule_li = self.fdirprocess.create_rule(fdir_rule[1])
            self.handle_buffer_split_case(
                queue_buffer_split_inner_ipv6_sctp[0],
                expected_ipv6_pkts_seg_len,
                expected_no_segment,
                queue_id1,
                queue_id2,
            )
        self.fdirprocess.destroy_rule(port_id=0, rule_id=rule_li)
        self.dut.send_expect("quit", "# ")

    def verify_queue_buffer_split_tunnel(self):
        self.launch_one_port_testpmd_with_multi_queues()
        self.dut.send_expect("port 0 rxq 4 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("port 0 rxq 5 rx_offload buffer_split on", "testpmd> ")
        self.dut.send_expect("show port 0 rx_offload configuration", "testpmd> ")
        self.dut.send_expect("set rxhdrs grenat", "testpmd> ")
        self.start_testpmd()

        fdir_rule = [
            "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / udp dst is 23 / end actions rss queues 4 5 end / mark / end",
        ]

        queue_id1 = [4]
        queue_id2 = [5]
        expected_seg_len = [
            [
                MAC_HEADER_LEN + IPV4_HEADER_LEN + UDP_HEADER_LEN + VXLAN_HEADER_LEN,
                MAC_HEADER_LEN + IPV4_HEADER_LEN + UDP_HEADER_LEN + PAY_LEN,
            ],
        ]
        expected_no_segment = []

        rule_li = self.fdirprocess.create_rule(fdir_rule[0])
        self.handle_buffer_split_case(
            queue_buffer_split_inner_ipv4_udp,
            expected_seg_len,
            expected_no_segment,
            queue_id1,
            queue_id2,
        )
        self.fdirprocess.destroy_rule(port_id=0, rule_id=rule_li)

    def test_port_buffer_split_outer_mac(self):
        self.verify_port_buffer_split_outer_mac()

    def test_port_buffer_split_inner_mac(self):
        self.verify_port_buffer_split_inner_mac()

    def test_port_buffer_split_inner_l3(self):
        self.logger.info(
            "===================Test subcase 1: buffer split ipv4 ================"
        )
        self.verify_port_buffer_split_inner_l3(ptype="ipv4")

        self.logger.info(
            "===================Test subcase 2: buffer split ipv6 ================"
        )
        self.verify_port_buffer_split_inner_l3(ptype="ipv6")

        self.logger.info(
            "===================Test subcase 3: buffer split inner-ipv4 ================"
        )
        self.verify_port_buffer_split_inner_l3(ptype="inner-ipv4")

        self.logger.info(
            "===================Test subcase 4: buffer split inner-ipv6 ================"
        )
        self.verify_port_buffer_split_inner_l3(ptype="inner-ipv6")

    def test_port_buffer_split_inner_l4(self):
        self.logger.info(
            "===================Test subcase 1: buffer split ipv4-udp ================"
        )
        self.verify_port_buffer_split_inner_l4(ptype="ipv4-udp")

        self.logger.info(
            "===================Test subcase 2: buffer split ipv6-udp ================"
        )
        self.verify_port_buffer_split_inner_l4(ptype="ipv6-udp")

        self.logger.info(
            "===================Test subcase 3: buffer split ipv4-tcp ================"
        )
        self.verify_port_buffer_split_inner_l4(ptype="ipv4-tcp")

        self.logger.info(
            "===================Test subcase 4: buffer split ipv6-tcp ================"
        )
        self.verify_port_buffer_split_inner_l4(ptype="ipv6-tcp")

        self.logger.info(
            "===================Test subcase 5: buffer split inner-ipv4-udp ================"
        )
        self.verify_port_buffer_split_inner_l4(ptype="inner-ipv4-udp")

        self.logger.info(
            "===================Test subcase 6: buffer split inner-ipv6-udp ================"
        )
        self.verify_port_buffer_split_inner_l4(ptype="inner-ipv6-udp")

        self.logger.info(
            "===================Test subcase 7: buffer split inner-ipv4-tcp ================"
        )
        self.verify_port_buffer_split_inner_l4(ptype="inner-ipv4-tcp")

        self.logger.info(
            "===================Test subcase 8: buffer split inner-ipv6-tcp ================"
        )
        self.verify_port_buffer_split_inner_l4(ptype="inner-ipv6-tcp")

    def test_port_buffer_split_inner_sctp(self):
        self.logger.info(
            "===================Test subcase 1: buffer split ipv4-sctp ================"
        )
        self.verify_port_buffer_split_inner_sctp(ptype="ipv4-sctp")

        self.logger.info(
            "===================Test subcase 2: buffer split ipv6-sctp ================"
        )
        self.verify_port_buffer_split_inner_sctp(ptype="ipv6-sctp")

        self.logger.info(
            "===================Test subcase 3: buffer split inner-ipv4-sctp ================"
        )
        self.verify_port_buffer_split_inner_sctp(ptype="inner-ipv4-sctp")

        self.logger.info(
            "===================Test subcase 4: buffer split inner-ipv6-sctp ================"
        )
        self.verify_port_buffer_split_inner_sctp(ptype="inner-ipv6-sctp")

    def test_port_buffer_split_tunnel(self):
        self.verify_port_buffer_split_tunnel()

    def test_queue_buffer_split_outer_mac(self):
        self.verify_queue_buffer_split_outer_mac()

    def test_queue_buffer_split_inner_mac(self):
        self.verify_queue_buffer_split_inner_mac()

    def test_queue_buffer_split_inner_ipv4(self):
        self.logger.info(
            "===================Test subcase 1: buffer split ipv4 ================"
        )
        self.verify_queue_buffer_split_inner_ipv4(ptype="ipv4")

        self.logger.info(
            "===================Test subcase 2: buffer split inner-ipv4 ================"
        )
        self.verify_queue_buffer_split_inner_ipv4(ptype="inner-ipv4")

    def test_queue_buffer_split_inner_ipv6(self):
        self.logger.info(
            "===================Test subcase 1: buffer split ipv6 ================"
        )
        self.verify_queue_buffer_split_inner_ipv6(ptype="ipv6")

        self.logger.info(
            "===================Test subcase 2: buffer split inner-ipv6 ================"
        )
        self.verify_queue_buffer_split_inner_ipv6(ptype="inner-ipv6")

    def test_queue_buffer_split_inner_udp(self):
        self.logger.info(
            "===================Test subcase 1: buffer split ipv4-udp ================"
        )
        self.verify_queue_buffer_split_inner_udp(ptype="ipv4-udp")

        self.logger.info(
            "===================Test subcase 2: buffer split ipv6-udp ================"
        )
        self.verify_queue_buffer_split_inner_udp(ptype="ipv6-udp")

        self.logger.info(
            "===================Test subcase 3: buffer split inner-ipv4-udp ================"
        )
        self.verify_queue_buffer_split_inner_udp(ptype="inner-ipv4-udp")

        self.logger.info(
            "===================Test subcase 4: buffer split inner-ipv6-udp ================"
        )
        self.verify_queue_buffer_split_inner_udp(ptype="inner-ipv6-udp")

    def test_queue_buffer_split_inner_tcp(self):
        self.logger.info(
            "===================Test subcase 1: buffer split ipv4-tcp ================"
        )
        self.verify_queue_buffer_split_inner_tcp(ptype="ipv4-tcp")

        self.logger.info(
            "===================Test subcase 2: buffer split ipv6-tcp ================"
        )
        self.verify_queue_buffer_split_inner_tcp(ptype="ipv6-tcp")

        self.logger.info(
            "===================Test subcase 3: buffer split inner-ipv4-tcp ================"
        )
        self.verify_queue_buffer_split_inner_tcp(ptype="inner-ipv4-tcp")

        self.logger.info(
            "===================Test subcase 4: buffer split inner-ipv6-tcp ================"
        )
        self.verify_queue_buffer_split_inner_tcp(ptype="inner-ipv6-tcp")

    def test_queue_buffer_split_inner_sctp(self):
        self.logger.info(
            "===================Test subcase 1: buffer split ipv4-sctp ================"
        )
        self.verify_queue_buffer_split_inner_sctp(ptype="ipv4-sctp")

        self.logger.info(
            "===================Test subcase 2: buffer split ipv6-sctp ================"
        )
        self.verify_queue_buffer_split_inner_sctp(ptype="ipv6-sctp")

        self.logger.info(
            "===================Test subcase 3: buffer split inner-ipv4-sctp ================"
        )
        self.verify_queue_buffer_split_inner_sctp(ptype="inner-ipv4-sctp")

        self.logger.info(
            "===================Test subcase 4: buffer split inner-ipv6-sctp ================"
        )
        self.verify_queue_buffer_split_inner_sctp(ptype="inner-ipv6-sctp")

    def test_queue_buffer_split_tunnel(self):
        self.verify_queue_buffer_split_tunnel()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.pmdout.quit()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.build_install_dpdk(self.target)
        self.dut.kill_all()
