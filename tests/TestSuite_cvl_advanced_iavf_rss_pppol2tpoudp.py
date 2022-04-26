# BSD LICENSE
#
# Copyright(c)2020 Intel Corporation. All rights reserved.
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


import random
import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

from .rte_flow_common import RssProcessing

vector_case_1 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_2 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_FRAG",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200', frag=6)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201', frag=6)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_3 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_4 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_5 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_6 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_7 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_8 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_9 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_10 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_11 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.201')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_12 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=99)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.201')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_13 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_14 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_15 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_16 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_17 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_18 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_19 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_20 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_21 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.201')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_22 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=99)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.201')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_23 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_24 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_25 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_26 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_27 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_FRAG",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_28 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_29 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_30 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_31 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_FRAG",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_32 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_FRAG",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_33 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_34 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_35 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_36 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_37 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_38 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=99)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_39 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_40 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_41 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_42 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_43 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_44 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_45 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_46 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_47 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=24)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_48 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=99)/Raw('x' * 80)"
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_49 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_50 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_51 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_52 = [
    {
        "sub_casename": "eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=99)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=24)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_53 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_54 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_FRAG",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200', frag=6)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201', frag=6)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_55 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_56 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_57 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv4_udp_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_58 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv4_tcp_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_59 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_FRAG",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_60 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_61 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_62 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_63 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv6_udp_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_64 = [
    {
        "sub_casename": "eth_ipv4_udp_l2tpv2_ppp_ipv6_tcp_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_TCP",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "save_hash",
            },
            {
                "send_packet": [
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                    "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)",
                ],
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=99)/Raw('x' * 80)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)",
                "action": "check_no_hash",
            },
        ],
    },
]

# l2tpv2 control + data
vector_case_65 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_L2TPV2_CONTROL",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type control / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_66 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_L2TPV2_CONTROL",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type control / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_67 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_L2TPV2_CONTROL",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type control / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_68 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_L2TPV2_CONTROL",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type control / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_69 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_70 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_L2TPV2_DATA",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_71 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_L",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_72 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_L",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_73 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_74 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_75 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_O",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_76 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_O",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_77 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_L_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_78 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_L_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_79 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_80 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_L2TPV2_DATA",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_81 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_L",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_82 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_L",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_83 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_84 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_85 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_O",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_86 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_O",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_87 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_L_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_88 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_L_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_89 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_90 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_91 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_L",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_92 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_L",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_93 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_94 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_95 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_O",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_96 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_O",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_97 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_L_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_98 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_L_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_99 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_100 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_101 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_L",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_102 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_L",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_103 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_104 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_105 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_O",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_106 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_O",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b'\\x00\\x00\\x00\\x00')/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_107 = [
    {
        "sub_casename": "l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_L_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]

vector_case_108 = [
    {
        "sub_casename": "eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_L_S",
        "port_id": 0,
        "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end",
        "test": [
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "save_hash",
            },
            {
                "send_packet": "Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_different",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x2222)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_hash_same",
            },
            {
                "send_packet": "Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw(b'\\x00\\x00')",
                "action": "check_no_hash",
            },
        ],
    },
]


class TestCVLAdvancedIAVFRSSPPPoL2TPv2oUDP(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        prerequisites.
        """
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for testing")
        # Verify that enough threads are available
        cores = self.dut.get_core_list("1S/4C/1T")
        self.verify(cores is not None, "Insufficient cores for speed testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.tester_iface1 = self.tester.get_interface(self.tester_port1)
        self.pci0 = self.dut.ports_info[self.dut_ports[0]]["pci"]
        self.pci1 = self.dut.ports_info[self.dut_ports[1]]["pci"]
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]["intf"]

        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "vfio-pci"
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port_0, 1, driver=self.kdriver
        )
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        self.dut.send_expect(
            "ip link set %s vf 0 mac 00:11:22:33:44:55" % self.pf0_intf, "#"
        )
        self.vf0_pci = self.sriov_vfs_port[0].pci
        for port in self.sriov_vfs_port:
            port.bind_driver(self.vf_driver)

        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.launch_testpmd()
        self.symmetric = False
        self.rxq = 16
        self.rssprocess = RssProcessing(
            self, self.pmd_output, [self.tester_iface0, self.tester_iface1], self.rxq
        )
        self.logger.info(
            "rssprocess.tester_ifaces: {}".format(self.rssprocess.tester_ifaces)
        )
        self.logger.info("rssprocess.test_case: {}".format(self.rssprocess.test_case))

    def set_up(self):
        """
        Run before each test case.
        """
        self.pmd_output.execute_cmd("start")

    def destroy_vf(self):
        self.dut.send_expect("quit", "# ", 60)
        time.sleep(2)
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])

    def launch_testpmd(self, symmetric=False):
        param = "--disable-rss --rxq=16 --txq=16 --rxd=384 --txd=384"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param=param,
            eal_param=f"-w {self.vf0_pci}",
            socket=self.ports_socket,
        )
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        res = self.pmd_output.wait_link_status_up("all", timeout=15)
        self.verify(res is True, "there have port link is down")

    def switch_testpmd(self, symmetric=True):
        if symmetric != self.symmetric:
            self.pmd_output.quit()
            self.launch_testpmd(symmetric=symmetric)
            self.pmd_output.execute_cmd("start")

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_PAY(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_1)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_FRAG(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_2)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_3)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_4)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_5)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_6)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_7)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_8)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_9)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_10)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_11)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_12)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_13)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_14)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_15)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_16)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_17)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_18)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_19)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_20)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_21)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_22)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_23)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_24)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_25)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_26)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_FRAG(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_27)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_PAY(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_28)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_29)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_30)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_FRAG(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_31)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_FRAG(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_32)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_33)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_34)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_35)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_36)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_37)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_38)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_39)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_40)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_41)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_42)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_43)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_44)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_45)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_46)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_47)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_48)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_49)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_50)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_51)

    def test_case_eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_52)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_PAY(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_53)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_FRAG(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_54)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_55)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_TCP(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_56)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv4_udp_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_57)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv4_tcp_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_58)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_FRAG(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_59)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_PAY(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_60)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_61)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_TCP(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_62)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv6_udp_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_63)

    def test_case_eth_ipv4_udp_l2tpv2_ppp_ipv6_tcp_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_TCP(
        self,
    ):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_64)

    # l2tpv2 control + data
    def test_case_l2tpv2_session_id_MAC_IPV4_L2TPV2_CONTROL(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_65)

    def test_case_eth_l2_src_only_MAC_IPV4_L2TPV2_CONTROL(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_66)

    def test_case_l2tpv2_session_id_MAC_IPV6_L2TPV2_CONTROL(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_67)

    def test_case_eth_l2_src_only_MAC_IPV6_L2TPV2_CONTROL(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_68)

    def test_case_l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_69)

    def test_case_eth_l2_src_only_MAC_IPV4_L2TPV2_DATA(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_70)

    def test_case_l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_L(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_71)

    def test_case_eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_L(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_72)

    def test_case_l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_73)

    def test_case_eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_74)

    def test_case_l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_O(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_75)

    def test_case_eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_O(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_76)

    def test_case_l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_L_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_77)

    def test_case_eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_L_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_78)

    def test_case_l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_79)

    def test_case_eth_l2_src_only_MAC_IPV6_L2TPV2_DATA(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_80)

    def test_case_l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_L(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_81)

    def test_case_eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_L(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_82)

    def test_case_l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_83)

    def test_case_eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_84)

    def test_case_l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_O(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_85)

    def test_case_eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_O(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_86)

    def test_case_l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_L_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_87)

    def test_case_eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_L_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_88)

    def test_case_l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_89)

    def test_case_eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_90)

    def test_case_l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_L(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_91)

    def test_case_eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_L(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_92)

    def test_case_l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_93)

    def test_case_eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_94)

    def test_case_l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_O(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_95)

    def test_case_eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_O(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_96)

    def test_case_l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_L_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_97)

    def test_case_eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_L_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_98)

    def test_case_l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_99)

    def test_case_eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_100)

    def test_case_l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_L(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_101)

    def test_case_eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_L(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_102)

    def test_case_l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_103)

    def test_case_eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_104)

    def test_case_l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_O(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_105)

    def test_case_eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_O(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_106)

    def test_case_l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_L_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_107)

    def test_case_eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_L_S(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=vector_case_108)

    def tear_down(self):
        # destroy all flow rule on port 0
        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")

    def tear_down_all(self):
        self.destroy_vf()
        self.dut.kill_all()
