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
import string
import time

from framework.config import UserConf
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, check_supported_nic, skip_unsupported_pkg

from .rte_flow_common import RssProcessing

vf0_mac = "00:11:22:33:44:55"

mac_ipv4_pfcp_session_packets = {
    "match": [
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=2)/Raw("x"*80)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.25",dst="192.168.0.23")/UDP(sport=23,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)'.format(
            vf0_mac
        ),
    ],
    "mismatch": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=25)/Raw("x"*80)'.format(
            vf0_mac
        ),
    ],
}

mac_ipv4_pfcp_session = {
    "sub_casename": "mac_ipv4_pfcp_session",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_pfcp_session_packets["match"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_pfcp_session_packets["match"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_pfcp_session_packets["match"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': [i for i in mac_ipv4_pfcp_session_packets['mismatch']],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_ipv4_pfcp_session_packets["match"]
    ],
}

mac_ipv6_pfcp_session_packets = {
    "match": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=2)/Raw("x"*80)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)'.format(
            vf0_mac
        ),
    ],
    "mismatch": [
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=25)/Raw("x"*80)'.format(
            vf0_mac
        ),
    ],
}

mac_ipv6_pfcp_session = {
    "sub_casename": "mac_ipv6_pfcp_session",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv6_pfcp_session_packets["match"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv6_pfcp_session_packets["match"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_pfcp_session_packets["match"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': [i for i in mac_ipv6_pfcp_session_packets['mismatch']],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_ipv6_pfcp_session_packets["match"]
    ],
}

mac_ipv4_l2tpv3_packets = {
    "match": [
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5", proto=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.4", proto=115)/L2TP(b\'\\x00\\x00\\x00\\x12\')/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.5",dst="192.168.0.7", proto=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
    "mismatch": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=25)/Raw("x"*80)'.format(
            vf0_mac
        ),
    ],
}

mac_ipv4_l2tpv3 = {
    "sub_casename": "mac_ipv4_l2tpv3",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_l2tpv3_packets["match"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_l2tpv3_packets["match"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_l2tpv3_packets["match"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': [i for i in mac_ipv4_l2tpv3_packets['mismatch']],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_ipv4_l2tpv3_packets["match"]
    ],
}

mac_ipv6_l2tpv3_packets = {
    "match": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP(b\'\\x00\\x00\\x00\\x12\')/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
    "mismatch": [
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5", proto=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=25)/Raw("x"*80)'.format(
            vf0_mac
        ),
    ],
}

mac_ipv6_l2tpv3 = {
    "sub_casename": "mac_ipv6_l2tpv3",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv6_l2tpv3_packets["match"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv6_l2tpv3_packets["match"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_l2tpv3_packets["match"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': [i for i in mac_ipv6_l2tpv3_packets['mismatch']],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_ipv6_l2tpv3_packets["match"]
    ],
}

mac_ipv4_esp_packets = {
    "match": [
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=12)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.4",dst="192.168.0.7",proto=50)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
    "mismatch": [
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5", proto=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=12)/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
}

mac_ipv4_esp = {
    "sub_casename": "mac_ipv4_esp",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_esp_packets["match"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_esp_packets["match"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_esp_packets["match"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': [
        #         i for i in mac_ipv4_esp_packets['mismatch']],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_ipv4_esp_packets["match"]
    ],
}

mac_ipv4_udp_esp_packets = {
    "match": [
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=12)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.4",dst="192.168.0.7")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
    "mismatch": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25,dport=23)/Raw("x"*80)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
}

mac_ipv4_udp_esp = {
    "sub_casename": "mac_ipv4_udp_esp",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / esp / end actions rss types esp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_udp_esp_packets["match"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_udp_esp_packets["match"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_udp_esp_packets["match"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': [i for i in mac_ipv4_udp_esp_packets['mismatch']],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_ipv4_esp_packets["match"]
    ],
}

mac_ipv6_esp_packets = {
    "match": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=12)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=50)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
    "mismatch": [
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)'.format(
            vf0_mac
        ),
    ],
}

mac_ipv6_esp = {
    "sub_casename": "mac_ipv6_esp",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / esp / end actions rss types esp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv6_esp_packets["match"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv6_esp_packets["match"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_esp_packets["match"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': [i for i in mac_ipv6_esp_packets['mismatch']],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_ipv6_esp_packets["match"]
    ],
}

mac_ipv6_udp_esp_packets = {
    "match": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=12)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
    "mismatch": [
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
}

mac_ipv6_udp_esp = {
    "sub_casename": "mac_ipv6_udp_esp",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / esp / end actions rss types esp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv6_udp_esp_packets["match"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv6_udp_esp_packets["match"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_udp_esp_packets["match"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': [i for i in mac_ipv6_udp_esp_packets['mismatch']],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_ipv6_udp_esp_packets["match"]
    ],
}

mac_ipv4_ah_packets = {
    "match": [
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=12)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IP(src="192.168.0.4",dst="192.168.0.8",proto=51)/AH(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
    "mismatch": [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25,dport=23)/Raw("x"*80)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
}

mac_ipv4_ah = {
    "sub_casename": "mac_ipv4_ah",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / ah / end actions rss types ah end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_ah_packets["match"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_ah_packets["match"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_ah_packets["match"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': mac_ipv4_ah_packets['mismatch'],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_ipv4_ah_packets["match"]
    ],
}

mac_ipv6_ah_packets = {
    "match": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=12)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=51)/AH(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
    ],
    "mismatch": [
        'Ether(dst="{}")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=11)/Raw("x"*480)'.format(
            vf0_mac
        ),
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)'.format(
            vf0_mac
        ),
    ],
}

mac_ipv6_ah = {
    "sub_casename": "mac_ipv6_ah",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / ah / end actions rss types ah end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv6_ah_packets["match"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv6_ah_packets["match"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_ah_packets["match"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': [i for i in mac_ipv6_ah_packets['mismatch']],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_ipv6_ah_packets["match"]
    ],
}

mac_vlan_ipv4_pay_packets = {
    "match": {
        "mac_vlan_ipv4_pay": [
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:99", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/Raw("x" * 80)'.format(
                vf0_mac
            ),
        ],
    },
    "mismatch": [
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'.format(
            vf0_mac
        )
    ],
}

mac_vlan_ipv4_pay = {
    "sub_casename": "mac_vlan_ipv4_pay",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / vlan / ipv4 / end actions rss types c-vlan end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_vlan_ipv4_pay_packets["match"]["mac_vlan_ipv4_pay"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_vlan_ipv4_pay_packets["match"]["mac_vlan_ipv4_pay"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_vlan_ipv4_pay_packets["match"]["mac_vlan_ipv4_pay"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': mac_vlan_ipv4_pay_packets['mismatch'][0],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_vlan_ipv4_pay_packets["match"]["mac_vlan_ipv4_pay"]
    ],
}

mac_vlan_ipv4_udp_pay_packets = {
    "match": {
        "mac_vlan_ipv4_udp_pay": [
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:99", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/UDP(sport=19,dport=99)/Raw("x" * 80)'.format(
                vf0_mac
            ),
        ]
    },
    "mismatch": [
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
    ],
}

mac_vlan_ipv4_udp_pay = {
    "sub_casename": "mac_vlan_ipv4_udp_pay",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / vlan / ipv4 / udp / end actions rss types c-vlan end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_vlan_ipv4_udp_pay_packets["match"][
                "mac_vlan_ipv4_udp_pay"
            ][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_vlan_ipv4_udp_pay_packets["match"][
                "mac_vlan_ipv4_udp_pay"
            ][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_vlan_ipv4_udp_pay_packets["match"][
                "mac_vlan_ipv4_udp_pay"
            ][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': mac_vlan_ipv4_udp_pay_packets['mismatch'],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_vlan_ipv4_udp_pay_packets["match"]["mac_vlan_ipv4_udp_pay"]
    ],
}

mac_vlan_ipv4_tcp_pay_packets = {
    "match": {
        "mac_vlan_ipv4_tcp_pay": [
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:99", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/TCP(sport=19,dport=99)/Raw("x" * 80)'.format(
                vf0_mac
            ),
        ]
    },
    "mismatch": [
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
    ],
}

mac_vlan_ipv4_tcp_pay = {
    "sub_casename": "mac_vlan_ipv4_tcp_pay",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / vlan / ipv4 / tcp / end actions rss types c-vlan end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_vlan_ipv4_tcp_pay_packets["match"][
                "mac_vlan_ipv4_tcp_pay"
            ][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_vlan_ipv4_tcp_pay_packets["match"][
                "mac_vlan_ipv4_tcp_pay"
            ][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_vlan_ipv4_tcp_pay_packets["match"][
                "mac_vlan_ipv4_tcp_pay"
            ][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': mac_vlan_ipv4_tcp_pay_packets['mismatch'],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_vlan_ipv4_tcp_pay_packets["match"]["mac_vlan_ipv4_tcp_pay"]
    ],
}

mac_vlan_ipv4_sctp_pay_packets = {
    "match": {
        "mac_vlan_ipv4_sctp_pay": [
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:99", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.5")/SCTP(sport=19,dport=99)/Raw("x" * 80)'.format(
                vf0_mac
            ),
        ]
    },
    "mismatch": [
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
    ],
}

mac_vlan_ipv4_sctp_pay = {
    "sub_casename": "mac_vlan_ipv4_sctp_pay",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / vlan / ipv4 / sctp / end actions rss types c-vlan end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_vlan_ipv4_sctp_pay_packets["match"][
                "mac_vlan_ipv4_sctp_pay"
            ][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_vlan_ipv4_sctp_pay_packets["match"][
                "mac_vlan_ipv4_sctp_pay"
            ][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_vlan_ipv4_sctp_pay_packets["match"][
                "mac_vlan_ipv4_sctp_pay"
            ][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': mac_vlan_ipv4_sctp_pay_packets['mismatch'],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_vlan_ipv4_sctp_pay_packets["match"]["mac_vlan_ipv4_sctp_pay"]
    ],
}

mac_vlan_ipv6_pay_packets = {
    "match": {
        "mac_vlan_ipv6_pay": [
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:99", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("y" * 80)'.format(
                vf0_mac
            ),
        ]
    },
    "mismatch": [
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'.format(
            vf0_mac
        )
    ],
}

mac_vlan_ipv6_pay = {
    "sub_casename": "mac_vlan_ipv6_pay",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / vlan / ipv6 / end actions rss types c-vlan end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_vlan_ipv6_pay_packets["match"]["mac_vlan_ipv6_pay"][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_vlan_ipv6_pay_packets["match"]["mac_vlan_ipv6_pay"][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_vlan_ipv6_pay_packets["match"]["mac_vlan_ipv6_pay"][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': mac_vlan_ipv6_pay_packets['mismatch'],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_vlan_ipv6_pay_packets["match"]["mac_vlan_ipv6_pay"]
    ],
}

mac_vlan_ipv6_udp_pay_packets = {
    "match": {
        "mac_vlan_ipv6_udp_pay": [
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:99", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=99)/Raw("x" * 80)'.format(
                vf0_mac
            ),
        ]
    },
    "mismatch": [
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
    ],
}

mac_vlan_ipv6_udp_pay = {
    "sub_casename": "mac_vlan_ipv6_udp_pay",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / vlan / ipv6 / udp / end actions rss types c-vlan end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_vlan_ipv6_udp_pay_packets["match"][
                "mac_vlan_ipv6_udp_pay"
            ][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_vlan_ipv6_udp_pay_packets["match"][
                "mac_vlan_ipv6_udp_pay"
            ][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_vlan_ipv6_udp_pay_packets["match"][
                "mac_vlan_ipv6_udp_pay"
            ][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': mac_vlan_ipv6_udp_pay_packets['mismatch'],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_vlan_ipv6_udp_pay_packets["match"]["mac_vlan_ipv6_udp_pay"]
    ],
}

mac_vlan_ipv6_tcp_pay_packets = {
    "match": {
        "mac_vlan_ipv6_tcp_pay": [
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:99", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x" * 80)'.format(
                vf0_mac
            ),
        ]
    },
    "mismatch": [
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
    ],
}

mac_vlan_ipv6_tcp_pay = {
    "sub_casename": "mac_vlan_ipv6_tcp_pay",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / vlan / ipv6 / tcp / end actions rss types c-vlan end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_vlan_ipv6_tcp_pay_packets["match"][
                "mac_vlan_ipv6_tcp_pay"
            ][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_vlan_ipv6_tcp_pay_packets["match"][
                "mac_vlan_ipv6_tcp_pay"
            ][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_vlan_ipv6_tcp_pay_packets["match"][
                "mac_vlan_ipv6_tcp_pay"
            ][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': mac_vlan_ipv6_tcp_pay_packets['mismatch'],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_vlan_ipv6_tcp_pay_packets["match"]["mac_vlan_ipv6_tcp_pay"]
    ],
}

mac_vlan_ipv6_sctp_pay_packets = {
    "match": {
        "mac_vlan_ipv6_sctp_pay": [
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)'.format(
                vf0_mac
            ),
            'Ether(src="10:22:33:44:55:99", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/SCTP(sport=25,dport=99)/Raw("x" * 80)'.format(
                vf0_mac
            ),
        ]
    },
    "mismatch": [
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
        'Ether(src="10:22:33:44:55:66", dst="{}",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'.format(
            vf0_mac
        ),
    ],
}

mac_vlan_ipv6_sctp_pay = {
    "sub_casename": "mac_vlan_ipv6_sctp_pay",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / vlan / ipv6 / sctp / end actions rss types c-vlan end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_vlan_ipv6_sctp_pay_packets["match"][
                "mac_vlan_ipv6_sctp_pay"
            ][0],
            "action": "save_hash",
        },
        {
            "send_packet": mac_vlan_ipv6_sctp_pay_packets["match"][
                "mac_vlan_ipv6_sctp_pay"
            ][1],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_vlan_ipv6_sctp_pay_packets["match"][
                "mac_vlan_ipv6_sctp_pay"
            ][2],
            "action": "check_hash_same",
        },
        # {
        #     'send_packet': mac_vlan_ipv6_sctp_pay_packets['mismatch'],
        #     'action': 'check_no_hash_or_different',
        # },
    ],
    "post-test": [
        {"send_packet": pkt, "action": "check_no_hash_or_different"}
        for pkt in mac_vlan_ipv6_sctp_pay_packets["match"]["mac_vlan_ipv6_sctp_pay"]
    ],
}


class ICE_advance_iavf_rss_vlan_ah_l2tp_pfcp(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
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

        self.used_dut_port = self.dut_ports[0]
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.vf_flag = False
        self.create_iavf()

        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.symmetric = False
        self.rxq = 16
        self.rsspro = RssProcessing(
            self, self.pmd_output, [self.tester_iface0, self.tester_iface1], self.rxq
        )
        self.logger.info(
            "rssprocess.tester_ifaces: {}".format(self.rsspro.tester_ifaces)
        )
        self.logger.info("rssprocess.test_case: {}".format(self.rsspro.test_case))
        self.switch_testpmd(symmetric=self.symmetric)
        self.dut_session = self.dut.new_session()

    def set_up(self):
        """
        Run before each test case.
        """
        # check testpmd process status
        cmd = "ps -aux | grep testpmd | grep -v grep"
        out = self.dut_session.send_expect(cmd, "#", 15)
        if "testpmd" not in out:
            self.switch_testpmd(symmetric=False)

        if self.running_case == "test_unsupported_pattern_with_OS_default_package":
            self.dut.kill_all()
            self.switch_testpmd(symmetric=True)

    def create_iavf(self):
        if self.vf_flag is False:
            self.dut.bind_interfaces_linux("ice")
            # get priv-flags default stats
            self.flag = "vf-vlan-pruning"
            self.default_stats = self.dut.get_priv_flags_state(
                self.pf_interface, self.flag
            )
            if self.default_stats:
                self.dut.send_expect(
                    "ethtool --set-priv-flags %s %s off"
                    % (self.pf_interface, self.flag),
                    "# ",
                )
            self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 1)
            self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]["vfs_port"]
            self.vf_flag = True
            try:
                for port in self.sriov_vfs_port:
                    port.bind_driver(self.drivername)
                self.vf0_prop = {"opt_host": self.sriov_vfs_port[0].pci}
                self.dut.send_expect("ifconfig %s up" % self.pf_interface, "# ")
                self.dut.send_expect(
                    "ip link set %s vf 0 mac %s" % (self.pf_interface, vf0_mac), "# "
                )
            except Exception as e:
                self.destroy_iavf()
                raise Exception(e)

    def destroy_iavf(self):
        if self.vf_flag is True:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.vf_flag = False

    def tear_down(self):
        """
        Run after each test case.
        """
        # destroy all flow rule on port 0
        self.pmd_output.execute_cmd("flow flush 0", timeout=1)
        self.pmd_output.execute_cmd("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("start")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.destroy_iavf()
        if self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s %s"
                % (self.pf_interface, self.flag, self.default_stats),
                "# ",
            )

    def launch_testpmd(self, symmetric=False):
        param = "--rxq=16 --txq=16"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param=param,
            ports=[self.sriov_vfs_port[0].pci],
            socket=self.ports_socket,
        )
        self.symmetric = symmetric
        if symmetric:
            # Need config rss in setup
            self.pmd_output.execute_cmd("port config all rss all")
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        res = self.pmd_output.wait_link_status_up("all", timeout=15)
        self.verify(res is True, "there have port link is down")

    def switch_testpmd(self, symmetric=False):
        self.dut.kill_all()
        self.launch_testpmd(symmetric)
        self.pmd_output.execute_cmd("start")

    def _gener_str(self, str_len=6):
        return "".join(random.sample(string.ascii_letters + string.digits, k=str_len))

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_pfcp_session(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv4_pfcp_session)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv6_pfcp_session(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv6_pfcp_session)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_l2tpv3(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv4_l2tpv3)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv6_l2tpv3(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv6_l2tpv3)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv4_esp(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv4_esp)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv4_udp_esp(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv4_udp_esp)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv6_esp(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv6_esp)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv6_udp_esp(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv6_udp_esp)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv4_ah(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv4_ah)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv6_ah(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv6_ah)

    def test_wrong_hash_input_set(self):
        rule_list = [
            "flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types l2-src-only l2-dst-only end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp l3-src-only end key_len 0 queues end / end",
        ]

        for rule in rule_list:
            self.rsspro.validate_rule(
                rule, check_stats=False, check_msg="Invalid argument"
            )
            self.rsspro.create_rule(rule, check_stats=False, msg="Invalid argument")

    def test_void_action(self):
        rule = "flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions end"
        self.rsspro.create_rule(rule, check_stats=False, msg="Invalid argument")
        self.rsspro.check_rule(stats=False, rule_list=[rule])

    def test_delete_nonexisting_rule(self):
        self.rsspro.check_rule(stats=False)
        out = self.dut.send_command("flow destroy 0 rule 0", timeout=1)
        self.verify(
            "error" not in out, "delete nonexisting rule raise err,expected no err"
        )
        self.dut.send_command("flow flush 0", timeout=1)

    @skip_unsupported_pkg(["comms", "wireless"])
    def test_unsupported_pattern_with_OS_default_package(self):
        rule_list = [
            "flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / ah / end actions rss types ah end key_len 0 queues end / end",
        ]
        self.rsspro.create_rule(rule_list, check_stats=False, msg="Invalid argument")
        self.rsspro.check_rule(stats=False)
        self.dut.kill_all()
        self.switch_testpmd(symmetric=False)

    def test_invalid_port(self):
        rule = "flow create 1 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end"
        self.rsspro.create_rule(rule, check_stats=False, msg="No such device")
        self.rsspro.check_rule(stats=False, rule_list=[rule])
        pattern = "Invalid port 1"
        out = self.dut.send_command("flow list 1", timeout=1)
        result = re.search(r"%s" % pattern, out)
        self.verify(
            result,
            "actual result not match expected,expected result is:{}".format(pattern),
        )

    def test_mac_vlan_ipv4_pay(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv4_pay)

    def test_mac_vlan_ipv4_udp_pay(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv4_udp_pay)

    def test_mac_vlan_ipv4_tcp_pay(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv4_tcp_pay)

    def test_mac_vlan_ipv4_sctp_pay(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv4_sctp_pay)

    def test_mac_vlan_ipv6_pay(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv6_pay)

    def test_mac_vlan_ipv6_udp_pay(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv6_udp_pay)

    def test_mac_vlan_ipv6_tcp_pay(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv6_tcp_pay)

    def test_mac_vlan_ipv6_sctp_pay(self):
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv6_sctp_pay)
