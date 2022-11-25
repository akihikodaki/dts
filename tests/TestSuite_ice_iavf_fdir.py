# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

import re
import time
from multiprocessing import Manager, Process

import framework.utils as utils
import tests.rte_flow_common as rfc
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, skip_unsupported_pkg
from framework.utils import GREEN, RED

from .rte_flow_common import TXQ_RXQ_NUMBER

MAC_IPV4_PAY = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw("x" * 80)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.1.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=3, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=9) / Raw("x" * 80)',
    ],
}

MAC_IPV4_PAY_MULTICAST = {
    "match": [
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", proto=255, ttl=2, tos=4) / Raw("X" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", proto=255, ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw("x" * 80)',
    ],
    "mismatch": [
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.22",dst="224.0.0.1", proto=255, ttl=2, tos=4) / Raw("X" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.2", proto=255, ttl=2, tos=4) / Raw("X" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", proto=1, ttl=2, tos=4) / Raw("X" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", proto=255, ttl=3, tos=4) / Raw("X" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", proto=255, ttl=2, tos=9) / Raw("X" * 80)',
    ],
}

MAC_IPV4_PAY_protocol = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.19",dst="192.168.0.21", proto=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=17)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=17, ttl=2, tos=4)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=17)/Raw("x" * 80)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", proto=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=6)/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4)/SCTP()/Raw("x" * 80)',
    ],
}

MAC_IPV4_PAY_multicast_protocol = {
    "match": [
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", proto=1)/Raw("x" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.19",dst="224.0.0.1", proto=1)/Raw("x" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", proto=17)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", proto=17, ttl=2, tos=4)/Raw("x" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", proto=17)/Raw("x" * 80)',
    ],
    "mismatch": [
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.2", proto=1)/Raw("x" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", proto=6)/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1")/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="11:22:33:44:55:66")/IP(src="192.168.0.20",dst="224.0.0.1", ttl=2, tos=4)/SCTP()/Raw("x" * 80)',
    ],
}

MAC_IPV4_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.19",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=21,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=24)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)',
    ],
}

MAC_IPV6_PAY_MULTICAST = {
    "match": [
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2", src="2001::2", nh=0, tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::1", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2", src="2001::1", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2", src="2001::2", nh=2, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2", src="2001::2", nh=0, tc=2, hlim=2)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2", src="2001::2", nh=0, tc=1, hlim=5)/("X"*480)',
    ],
}

MAC_IPV4_TCP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.19",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=21,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=24)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
    ],
}

MAC_IPV4_SCTP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw("x" * 80)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.19",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=21,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=24)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /SCTP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /SCTP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4)/Raw("x" * 80)',
    ],
}

MAC_IPV6_PAY = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::1", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=2, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=2, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=5)/("X"*480)',
    ],
}

MAC_IPV6_PAY_protocol = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=17, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=17)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", nh=1)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=1)/TCP(sport=22,dport=23)/("X"*480)',
    ],
}

MAC_IPV6_PAY_multicast_protocol = {
    "match": [
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2", src="2001::2", nh=17, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2")/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2", nh=17)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2")/UDP(sport=22,dport=23)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2", nh=6)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::3", nh=1)/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2")/SCTP()/("X"*480)',
        'Ether(dst="11:22:33:44:55:66")/IPv6(dst="ff01::2", nh=1)/TCP(sport=22,dport=23)/("X"*480)',
    ],
}

MAC_IPV6_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)',
    ],
}

tv_mac_ipv4_pay_queue_index_multicast = {
    "name": "test_mac_ipv4_pay_queue_index_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 224.0.0.1 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / mark / end",
    "scapy_str": MAC_IPV4_PAY_MULTICAST,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0},
}

tv_mac_ipv4_pay_rss_multicast = {
    "name": "test_mac_ipv4_pay_rss_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 224.0.0.1 proto is 255 ttl is 2 tos is 4 / end actions rss queues 2 3 end / mark / end",
    "scapy_str": MAC_IPV4_PAY_MULTICAST,
    "check_param": {"port_id": 0, "queue": [2, 3], "mark_id": 0},
}

tv_mac_ipv4_pay_passthru_multicast = {
    "name": "test_mac_ipv4_pay_passthru_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 224.0.0.1 proto is 255 ttl is 2 tos is 4 / end actions passthru / mark / end",
    "scapy_str": MAC_IPV4_PAY_MULTICAST,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_pay_drop_multicast = {
    "name": "test_mac_ipv4_pay_drop_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 224.0.0.1 proto is 255 ttl is 2 tos is 4 / end actions drop / mark / end",
    "scapy_str": MAC_IPV4_PAY_MULTICAST,
    "check_param": {"port_id": 0, "drop": 1, "mark_id": 0},
}

tv_mac_ipv4_pay_mark_rss_multicast = {
    "name": "test_mac_ipv4_pay_mark_rss_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 224.0.0.1 proto is 255 ttl is 2 tos is 4 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_PAY_MULTICAST,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_pay_mark_multicast = {
    "name": "test_mac_ipv4_pay_mark_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 224.0.0.1 proto is 255 ttl is 2 tos is 4 / end actions mark / end",
    "scapy_str": MAC_IPV4_PAY_MULTICAST,
    "check_param": {"port_id": 0, "mark_id": 0},
}

tv_mac_ipv6_pay_queue_index_multicast = {
    "name": "test_mac_ipv4_pay_queue_index_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is ff01::2 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions queue index 15 / mark / end",
    "scapy_str": MAC_IPV6_PAY_MULTICAST,
    "check_param": {"port_id": 0, "queue": 15, "mark_id": 0},
}

tv_mac_ipv6_pay_rss_multicast = {
    "name": "test_mac_ipv6_pay_rss_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is ff01::2 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark / end",
    "scapy_str": MAC_IPV6_PAY_MULTICAST,
    "check_param": {
        "port_id": 0,
        "queue": [8, 9, 10, 11, 12, 13, 14, 15],
        "mark_id": 0,
    },
}

tv_mac_ipv6_pay_passthru_multicast = {
    "name": "test_mac_ipv6_pay_passthru_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is ff01::2 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions passthru / mark / end",
    "scapy_str": MAC_IPV6_PAY_MULTICAST,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv6_pay_drop_multicast = {
    "name": "test_mac_ipv6_pay_drop_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is ff01::2 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions drop / mark / end",
    "scapy_str": MAC_IPV6_PAY_MULTICAST,
    "check_param": {"port_id": 0, "drop": 1, "mark_id": 0},
}

tv_mac_ipv6_pay_mark_rss_multicast = {
    "name": "test_mac_ipv6_pay_mark_rss_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is ff01::2 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark / rss / end",
    "scapy_str": MAC_IPV6_PAY_MULTICAST,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv6_pay_mark_multicast = {
    "name": "test_mac_ipv6_pay_mark_multicast",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is ff01::2 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark / end",
    "scapy_str": MAC_IPV6_PAY_MULTICAST,
    "check_param": {"port_id": 0, "mark_id": 0},
}

MAC_IPV6_TCP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
    ],
}

MAC_IPV6_SCTP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/TCP(sport=22,dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6(nh=44)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6()/TCP(sport=22,dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x35)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(nh=44)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IP()/Raw("x"*20)'
    ],
}

MAC_IPV6_GTPU_EH = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/ICMP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/TCP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/UDP()/Raw("x"*20)',
    ],
}

MAC_IPV6_GTPU = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/ICMP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw("x"*20)',
    ],
}

MAC_IPV4_L2TPv3 = {
    "match": [
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.3', proto=115)/L2TP(b'\\x00\\x00\\x00\\x11')/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.1.3', proto=115)/L2TP(b'\\x00\\x00\\x00\\x11')/Raw('x'*480)",
    ],
    "mismatch": [
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.3', proto=115)/L2TP(b'\\x00\\x00\\x00\\x12')/Raw('x'*480)"
    ],
}

MAC_IPV6_L2TPv3 = {
    "match": [
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888',nh=115)/L2TP(b'\\x00\\x00\\x00\\x11')/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:9999',nh=115)/L2TP(b'\\x00\\x00\\x00\\x11')/Raw('x'*480)",
    ],
    "mismatch": [
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888',nh=115)/L2TP(b'\\x00\\x00\\x00\\x12')/Raw('x'*480)"
    ],
}

MAC_IPV4_ESP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21",proto=50)/ESP(spi=7)/Raw("x"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22",dst="192.168.0.21",proto=50)/ESP(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.11",proto=50)/ESP(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21",proto=50)/ESP(spi=17)/Raw("x"*480)',
    ],
}

MAC_IPV6_ESP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2",nh=50)/ESP(spi=7)/Raw("x"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::8",dst="2001::2",nh=50)/ESP(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::9",nh=50)/ESP(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2",nh=50)/ESP(spi=17)/Raw("x"*480)',
    ],
}

MAC_IPV4_AH = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",proto=51)/AH(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3",proto=51)/AH(spi=7)/Raw("x"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",proto=51)/AH(spi=17)/Raw("x"*480)'
    ],
}

MAC_IPV6_AH = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",nh=51)/AH(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:9999",nh=51)/AH(spi=7)/Raw("x"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",nh=51)/AH(spi=17)/Raw("x"*480)'
    ],
}

MAC_IPV4_NAT_T_ESP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(dport=4500)/ESP(spi=7)/Raw("x"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22",dst="192.168.0.21")/UDP(dport=4500)/ESP(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.11")/UDP(dport=4500)/ESP(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(dport=4500)/ESP(spi=17)/Raw("x"*480)',
    ],
}

MAC_IPV6_NAT_T_ESP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/UDP(dport=4500)/ESP(spi=7)/Raw("x"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::8",dst="2001::2")/UDP(dport=4500)/ESP(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::9")/UDP(dport=4500)/ESP(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="2001::1",dst="2001::2")/UDP(dport=4500)/ESP(spi=17)/Raw("x"*480)',
    ],
}

L2_Ethertype = [
    'Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x" *80)',
    'Ether(dst="00:11:22:33:44:55", type=0x8863)/IP()/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:55", type=0x8864)/IP()/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:55")/ARP(pdst="192.168.1.1")',
    'Ether(dst="00:11:22:33:44:55", type=0x0806)/Raw("x" *80)',
    'Ether(dst="00:11:22:33:44:55",type=0x8100)',
    'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)',
    'Ether(dst="00:11:22:33:44:55",type=0x88f7)/"\\x00\\x02"',
    'Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(label=0xee456)/IP()',
]

PFCP = [
    'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=22, dport=8805)/PFCP(S=0)',
    'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=22, dport=8805)/PFCP(S=1, seid=123)',
    'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=22, dport=8805)/PFCP(S=0)',
    'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=22, dport=8805)/PFCP(S=1, seid=256)',
    'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=22, dport=23)/Raw("x"*20)',
]

CREATE_2048_RULES_4_VFS = [
    'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.7.255", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.7.255", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.7.255", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.7.255", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
]

tv_l2_ethertype_queue_index = {
    "name": "test_l2_ethertype_queue_index",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions queue index 1 / mark id 1 / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions queue index 2 / mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions queue index 3 / mark id 3 / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions queue index 4 / mark id 4 / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions queue index 5 / mark id 5 / end",
    ],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "queue": 1, "mark_id": 1},
        {"port_id": 0, "queue": 1, "mark_id": 1},
        {"port_id": 0, "queue": 2, "mark_id": 2},
        {"port_id": 0, "queue": 2, "mark_id": 2},
        {"port_id": 0, "queue": 3, "mark_id": 3},
        {"port_id": 0, "queue": 3, "mark_id": 3},
        {"port_id": 0, "queue": 4, "mark_id": 4},
        {"port_id": 0, "queue": 4, "mark_id": 4},
        {"port_id": 0, "queue": 5, "mark_id": 5},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_l2_ethertype_queue_group = {
    "name": "test_l2_ethertype_queue_group",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions rss queues 0 1 end / mark id 0 / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions rss queues 2 3 end / mark id 1 / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions rss queues 4 5 end / mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions rss queues 6 7 end / mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions rss queues 9 10 end / mark id 3 / end",
    ],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 3},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_l2_ethertype_passthru = {
    "name": "test_l2_ethertype_passthru",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions passthru / mark / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions passthru / mark id 1 / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions passthru / mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions passthru / mark id 3 / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions passthru / mark id 4 / end",
    ],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 3},
        {"port_id": 0, "queue": 0, "mark_id": 3},
        {"port_id": 0, "queue": 0, "mark_id": 4},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_l2_ethertype_mark_rss = {
    "name": "test_l2_ethertype_mark_rss",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions rss / mark id 0 / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions mark id 1 / rss / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions mark / rss / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions rss / mark / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions mark id 3 / rss / end",
    ],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 3},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_l2_ethertype_mark = {
    "name": "test_l2_ethertype_mark",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions mark id 0 / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions mark id 1 / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions mark / end",
    ],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_l2_ethertype_drop = {
    "name": "test_l2_ethertype_drop",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions drop / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions drop / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions drop / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions drop / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions drop / end",
    ],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_pfcp_queue_index = {
    "name": "test_pfcp_queue_index",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / end",
    ],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "queue": 1},
        {"port_id": 0, "queue": 2},
        {"port_id": 0, "queue": 3},
        {"port_id": 0, "queue": 4},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_pfcp_queue_group = {
    "name": "test_pfcp_queue_group",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions rss queues 2 3 end / mark id 0 / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions rss queues 4 5 6 7 end / mark id 1 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark id 2 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions rss queues 3 4 5 6 end / mark id 3 / end",
    ],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": [4, 5, 6, 7], "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": [3, 4, 5, 6], "mark_id": 3},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_pfcp_passthru = {
    "name": "test_pfcp_passthru",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions passthru / mark id 0 / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions passthru / mark id 1 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions passthru / mark id 2 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions passthru / mark id 3 / end",
    ],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "passthru": 1, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "passthru": 1, "mark_id": 3},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_pfcp_mark_rss = {
    "name": "test_pfcp_mark_rss",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions mark / rss / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions mark id 1 / rss / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions mark id 2 / rss / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions mark id 3 / rss / end",
    ],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "passthru": 1, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "passthru": 1, "mark_id": 3},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_pfcp_mark = {
    "name": "test_pfcp_mark",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions mark / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions mark id 1 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions mark id 2 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions mark id 4294967294 / end",
    ],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "passthru": 1, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "passthru": 1, "mark_id": 4294967294},
        {"port_id": 0, "passthru": 1},
    ],
}

tv_pfcp_drop = {
    "name": "test_pfcp_drop",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions drop / end",
    ],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "passthru": 1},
    ],
}

MAC_IPV4_TCP_WITHOUT = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=RandShort(),dport=RandShort())'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())',
        'Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())/SCTP()',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=RandShort(),dport=RandShort())',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/TCP(sport=RandShort(),dport=RandShort())',
    ],
}

MAC_IPV4_UDP_WITHOUT = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=RandShort(),dport=RandShort())'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())',
        'Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())/SCTP()',
        'Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=RandShort(),dport=RandShort())',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=RandShort(),dport=RandShort())',
    ],
}

MAC_IPV6_TCP_WITHOUT = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6()/TCP(sport=RandShort(),dport=RandShort())'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=RandShort(),dport=RandShort())',
        'Ether(dst="00:11:22:33:44:55")/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=RandShort(),dport=RandShort())',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/SCTP(sport=RandShort(),dport=RandShort())',
    ],
}

MAC_IPV6_UDP_WITHOUT = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=RandShort(),dport=RandShort())'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=RandShort(),dport=RandShort())',
        'Ether(dst="00:11:22:33:44:55")/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/TCP(sport=RandShort(),dport=RandShort())',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/SCTP(sport=RandShort(),dport=RandShort())',
    ],
}

# inner L3/L4 packets
MAC_IPV4_GTPU_IPV4 = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21", frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/ICMP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.22", dst="192.168.0.23")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_IPV4_TCP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)'
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.22", dst="192.168.0.23")/TCP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_IPV4_TCP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/TCP()/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/TCP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_IPV4_UDP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)'
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.22", dst="192.168.0.23")/UDP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/UDP(sport=22, dport=23)/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_IPV4_UDP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP()/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/UDP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_IPV4 = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21", frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/ICMP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.22", dst="192.168.0.23")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_IPV4_TCP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.22", dst="192.168.0.23")/TCP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_IPV4_TCP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/TCP()/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/TCP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_IPV4_UDP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.22", dst="192.168.0.23")/UDP(sport=25, dport=24)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/UDP(sport=22, dport=23)/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_IPV4_UDP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/UDP()/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/UDP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_DL_IPV4 = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21", frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/ICMP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.22", dst="192.168.0.23")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_DL_IPV4_TCP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.22", dst="192.168.0.23")/TCP(sport=25, dport=24)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_DL_IPV4_TCP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP()/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/TCP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_DL_IPV4_UDP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.22", dst="192.168.0.23")/UDP(sport=25, dport=24)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_DL_IPV4_UDP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP()/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/UDP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_UL_IPV4 = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21", frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/ICMP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.22", dst="192.168.0.23")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_UL_IPV4_TCP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)'
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.22", dst="192.168.0.23")/TCP(sport=25, dport=24)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_UL_IPV4_TCP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/TCP()/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/TCP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_UL_IPV4_UDP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)'
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.22", dst="192.168.0.23")/UDP(sport=25, dport=24)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_UL_IPV4_UDP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/UDP()/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/UDP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_IPV6 = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_IPV6_TCP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)'
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/TCP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_IPV6_TCP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/TCP()/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/TCP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_IPV6_UDP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)'
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/UDP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_IPV6_UDP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/UDP()/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_IPV6 = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_IPV6_TCP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/TCP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_IPV6_TCP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/TCP()/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_IPV6_UDP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/UDP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_IPV6_UDP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/UDP()/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_DL_IPV6 = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_DL_IPV6_TCP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/TCP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_DL_IPV6_TCP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/TCP()/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/TCP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_DL_IPV6_UDP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/UDP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_DL_IPV6_UDP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/UDP()/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/UDP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_UL_IPV6 = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_UL_IPV6_TCP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)'
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/TCP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_UL_IPV6_TCP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/TCP()/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/TCP()/("X"*480)',
    ],
}

MAC_IPV4_GTPU_EH_UL_IPV6_UDP = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)'
    ],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/UDP(sport=24, dport=25)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/UDP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/Raw("x"*20)',
    ],
}

MAC_IPV4_GTPU_EH_UL_IPV6_UDP_WITHOUT_INPUTSET = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/UDP()/("X"*480)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/TCP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/ICMP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/UDP()/("X"*480)',
    ],
}

MAC_IPV4_GRE_IPV4 = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=4)/Raw("x" * 80)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.22",dst="192.168.0.21", tos=4)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.22", tos=4)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=8)/Raw("x" * 80)',
    ],
}

MAC_IPV4_GRE_IPV4_TCP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.22",dst="192.168.0.21", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.22", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=8)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=4)/TCP(sport=21,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=4)/TCP(sport=22,dport=24)/Raw("x" * 80)',
    ],
}

MAC_IPV4_GRE_IPV6_TCP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1)/TCP(sport=22,dport=23)/Raw("x" * 80)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::3",tc=1)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=2)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1)/TCP(sport=21,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1)/TCP(sport=22,dport=24)/Raw("x" * 80)',
    ],
}

MAC_IPV6_GRE_IPV4 = eval(str(MAC_IPV4_GRE_IPV4).replace("IP()", "IPv6()"))

MAC_IPV4_GRE_IPV6 = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1)/Raw("x" * 80)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::3",tc=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=2)/Raw("x" * 80)',
    ],
}

tv_mac_ipv4_pay_queue_index = {
    "name": "test_mac_ipv4_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "queue": 1},
}

tv_mac_ipv4_pay_queue_group = {
    "name": "test_mac_ipv4_pay_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 1 end / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "queue": [0, 1]},
}

tv_mac_ipv4_pay_passthru = {
    "name": "test_mac_ipv4_pay_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "passthru": 1},
}

tv_mac_ipv4_pay_mark_rss = {
    "name": "test_mac_ipv4_pay_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_pay_mark = {
    "name": "test_mac_ipv4_pay_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_pay_drop = {
    "name": "test_mac_ipv4_pay_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_udp_queue_index = {
    "name": "test_mac_ipv4_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0},
}

tv_mac_ipv4_udp_drop = {
    "name": "test_mac_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_udp_queue_group = {
    "name": "test_mac_ipv4_udp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions rss queues 1 2 3 4 end / mark id 4294967294 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 4294967294},
}

tv_mac_ipv4_udp_passthru = {
    "name": "test_mac_ipv4_udp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_udp_mark_rss = {
    "name": "test_mac_ipv4_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv4_udp_mark = {
    "name": "test_mac_ipv4_udp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_tcp_queue_index = {
    "name": "test_mac_ipv4_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 15 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "queue": 15},
}

tv_mac_ipv4_tcp_drop = {
    "name": "test_mac_ipv4_tcp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_tcp_queue_group = {
    "name": "test_mac_ipv4_tcp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 1},
}

tv_mac_ipv4_tcp_passthru = {
    "name": "test_mac_ipv4_tcp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions passthru / mark id 2 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv4_tcp_mark_rss = {
    "name": "test_mac_ipv4_tcp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 0 / rss / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_tcp_mark = {
    "name": "test_mac_ipv4_tcp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 0 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_sctp_queue_index = {
    "name": "test_mac_ipv4_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 tag is 1 / end actions queue index 0 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "queue": 0},
}

tv_mac_ipv4_sctp_drop = {
    "name": "test_mac_ipv4_sctp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions drop / mark / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_sctp_queue_group = {
    "name": "test_mac_ipv4_sctp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions rss queues 14 15 end / mark id 15 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "queue": [14, 15], "mark_id": 15},
}

tv_mac_ipv4_sctp_passthru = {
    "name": "test_mac_ipv4_sctp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions passthru / mark id 0 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_sctp_mark_rss = {
    "name": "test_mac_ipv4_sctp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_sctp_mark = {
    "name": "test_mac_ipv4_sctp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions mark / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv6_pay_queue_index = {
    "name": "test_mac_ipv6_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions queue index 15 / mark id 1 / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "queue": 15, "mark_id": 1},
}

tv_mac_ipv6_pay_drop = {
    "name": "test_mac_ipv6_pay_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions drop / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv6_pay_queue_group = {
    "name": "test_mac_ipv6_pay_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark id 2 / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {
        "port_id": 0,
        "queue": [8, 9, 10, 11, 12, 13, 14, 15],
        "mark_id": 2,
    },
}

tv_mac_ipv6_pay_passthru = {
    "name": "test_mac_ipv6_pay_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions passthru / mark id 3 / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 3},
}

tv_mac_ipv6_pay_mark_rss = {
    "name": "test_mac_ipv6_pay_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark id 4 / rss / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 4},
}

tv_mac_ipv6_pay_mark = {
    "name": "test_mac_ipv6_pay_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark id 5 / rss / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 5},
}

tv_mac_ipv6_udp_queue_index = {
    "name": "test_mac_ipv6_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 2 / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "queue": 2},
}

tv_mac_ipv6_udp_queue_group = {
    "name": "test_mac_ipv6_udp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "queue": [1, 2]},
}

tv_mac_ipv6_udp_drop = {
    "name": "test_mac_ipv6_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv6_udp_passthru = {
    "name": "test_mac_ipv6_udp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions passthru / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1},
}

tv_mac_ipv6_udp_mark_rss = {
    "name": "test_mac_ipv6_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark / rss / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv6_udp_mark = {
    "name": "test_mac_ipv6_udp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv6_tcp_queue_index = {
    "name": "test_mac_ipv6_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 2 / mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "queue": 2, "mark_id": 0},
}

tv_mac_ipv6_tcp_queue_group = {
    "name": "test_mac_ipv6_tcp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "queue": [2, 3], "mark_id": 0},
}

tv_mac_ipv6_tcp_drop = {
    "name": "test_mac_ipv6_tcp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv6_tcp_passthru = {
    "name": "test_mac_ipv6_tcp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions passthru / mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv6_tcp_mark_rss = {
    "name": "test_mac_ipv6_tcp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions mark / rss / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv6_tcp_mark = {
    "name": "test_mac_ipv6_tcp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv6_sctp_queue_index = {
    "name": "test_mac_ipv6_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions queue index 3 / mark id 0 / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "queue": 3, "mark_id": 0},
}

tv_mac_ipv6_sctp_drop = {
    "name": "test_mac_ipv6_sctp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv6_sctp_queue_group = {
    "name": "test_mac_ipv6_sctp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions rss queues 12 13 end / mark id 0 / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "queue": [12, 13], "mark_id": 0},
}

tv_mac_ipv6_sctp_passthru = {
    "name": "test_mac_ipv6_sctp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions passthru / mark id 0 / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv6_sctp_mark_rss = {
    "name": "test_mac_ipv6_sctp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv6_sctp_mark = {
    "name": "test_mac_ipv6_sctp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions mark id 2 / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv4_gtpu_eh_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_drop = {
    "name": "test_mac_ipv4_gtpu_eh_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 2 3 end / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_mark = {
    "name": "test_mac_ipv4_gtpu_eh_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 0},
}

tv_mac_ipv4_gtpu_queue_index = {
    "name": "test_mac_ipv4_gtpu_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions queue index 1 / mark id 0 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_drop = {
    "name": "test_mac_ipv4_gtpu_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_queue_group = {
    "name": "test_mac_ipv4_gtpu_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions rss queues 1 2 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1},
}

tv_mac_ipv4_gtpu_passthru = {
    "name": "test_mac_ipv4_gtpu_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions passthru / mark id 2 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 2},
}

tv_mac_ipv4_gtpu_mark_rss = {
    "name": "test_mac_ipv4_gtpu_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark id 3 / rss / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 3},
}

tv_mac_ipv4_gtpu_mark = {
    "name": "test_mac_ipv4_gtpu_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark id 4 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 4},
}

tv_mac_ipv4_gtpu_eh_4tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_4tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_4tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_eh_4tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv4_gtpu_eh_4tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_eh_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_eh_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv4_gtpu_eh_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_eh_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_eh_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv4_gtpu_eh_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_3tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_3tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_3tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_3tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_3tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_3tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_3tuple_drop = {
    "name": "test_mac_ipv4_gtpu_3tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv4_gtpu_3tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_3tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv4_gtpu_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_gtpu_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv4_gtpu_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_eh_4tuple_queue_index = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv6_gtpu_eh_4tuple_queue_group = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv6_gtpu_eh_4tuple_passthru = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_eh_4tuple_drop = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv6_gtpu_eh_4tuple_mark_rss = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_eh_dstip_queue_index = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv6_gtpu_eh_dstip_queue_group = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv6_gtpu_eh_dstip_passthru = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_eh_dstip_drop = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv6_gtpu_eh_dstip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_eh_srcip_queue_index = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv6_gtpu_eh_srcip_queue_group = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv6_gtpu_eh_srcip_passthru = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_eh_srcip_drop = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv6_gtpu_eh_srcip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_3tuple_queue_index = {
    "name": "test_mac_ipv6_gtpu_3tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv6_gtpu_3tuple_queue_group = {
    "name": "test_mac_ipv6_gtpu_3tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv6_gtpu_3tuple_passthru = {
    "name": "test_mac_ipv6_gtpu_3tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_3tuple_drop = {
    "name": "test_mac_ipv6_gtpu_3tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions drop / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv6_gtpu_3tuple_mark_rss = {
    "name": "test_mac_ipv6_gtpu_3tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_dstip_queue_index = {
    "name": "test_mac_ipv6_gtpu_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv6_gtpu_dstip_queue_group = {
    "name": "test_mac_ipv6_gtpu_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv6_gtpu_dstip_passthru = {
    "name": "test_mac_ipv6_gtpu_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_dstip_drop = {
    "name": "test_mac_ipv6_gtpu_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv6_gtpu_dstip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_srcip_queue_index = {
    "name": "test_mac_ipv6_gtpu_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv6_gtpu_srcip_queue_group = {
    "name": "test_mac_ipv6_gtpu_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv6_gtpu_srcip_passthru = {
    "name": "test_mac_ipv6_gtpu_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv6_gtpu_srcip_drop = {
    "name": "test_mac_ipv6_gtpu_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "drop": True},
}

tv_mac_ipv6_gtpu_srcip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {
        "match": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
        "mismatch": [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True},
}

tv_mac_ipv4_l2tpv3_queue_index = {
    "name": "test_mac_ipv4_l2tpv3_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV4_L2TPv3,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7},
}

tv_mac_ipv4_l2tpv3_queue_group = {
    "name": "test_mac_ipv4_l2tpv3_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV4_L2TPv3,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6},
}

tv_mac_ipv4_l2tpv3_mark = {
    "name": "test_mac_ipv4_l2tpv3_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV4_L2TPv3,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15},
}

tv_mac_ipv6_l2tpv3_queue_index = {
    "name": "test_mac_ipv6_l2tpv3_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 17 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV6_L2TPv3,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7},
}

tv_mac_ipv6_l2tpv3_queue_group = {
    "name": "test_mac_ipv6_l2tpv3_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 17 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV6_L2TPv3,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6},
}

tv_mac_ipv6_l2tpv3_mark = {
    "name": "test_mac_ipv6_l2tpv3_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 17 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV6_L2TPv3,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15},
}

tv_mac_ipv4_esp_queue_index = {
    "name": "test_mac_ipv4_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV4_ESP,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7},
}

tv_mac_ipv4_esp_queue_group = {
    "name": "test_mac_ipv4_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV4_ESP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6},
}

tv_mac_ipv4_esp_passthru = {
    "name": "test_mac_ipv4_esp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_esp_drop = {
    "name": "test_mac_ipv4_esp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions drop / end",
    "scapy_str": MAC_IPV4_ESP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_esp_mark_rss = {
    "name": "test_mac_ipv4_esp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV4_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv4_esp_mark = {
    "name": "test_mac_ipv4_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV4_ESP,
    "check_param": {"port_id": 0, "mark_id": 15},
}

tv_mac_ipv6_esp_queue_index = {
    "name": "test_mac_ipv6_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV6_ESP,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7},
}

tv_mac_ipv6_esp_queue_group = {
    "name": "test_mac_ipv6_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV6_ESP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6},
}

tv_mac_ipv6_esp_passthru = {
    "name": "test_mac_ipv6_esp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV6_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv6_esp_drop = {
    "name": "test_mac_ipv6_esp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions drop / end",
    "scapy_str": MAC_IPV6_ESP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv6_esp_mark_rss = {
    "name": "test_mac_ipv6_esp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV6_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv6_esp_mark = {
    "name": "test_mac_ipv6_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV6_ESP,
    "check_param": {"port_id": 0, "mark_id": 15},
}

tv_mac_ipv4_ah_queue_index = {
    "name": "test_mac_ipv4_ah_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / ah spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV4_AH,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7},
}

tv_mac_ipv4_ah_queue_group = {
    "name": "test_mac_ipv4_ah_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / ah spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV4_AH,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6},
}

tv_mac_ipv4_ah_mark = {
    "name": "test_mac_ipv4_ah_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / ah spi is 7 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV4_AH,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15},
}

tv_mac_ipv6_ah_queue_index = {
    "name": "test_mac_ipv6_ah_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ah spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV6_AH,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7},
}

tv_mac_ipv6_ah_queue_group = {
    "name": "test_mac_ipv6_ah_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ah spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV6_AH,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6},
}

tv_mac_ipv6_ah_mark = {
    "name": "test_mac_ipv6_ah_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ah spi is 7 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV6_AH,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15},
}

tv_mac_ipv4_nat_t_esp_queue_index = {
    "name": "test_mac_ipv4_nat_t_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV4_NAT_T_ESP,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7},
}

tv_mac_ipv4_nat_t_esp_queue_group = {
    "name": "test_mac_ipv4_nat_t_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV4_NAT_T_ESP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6},
}

tv_mac_ipv4_nat_t_esp_passthru = {
    "name": "test_mac_ipv4_nat_t_esp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_NAT_T_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_nat_t_esp_drop = {
    "name": "test_mac_ipv4_nat_t_esp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions drop / end",
    "scapy_str": MAC_IPV4_NAT_T_ESP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_nat_t_esp_mark_rss = {
    "name": "test_mac_ipv4_nat_t_esp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV4_NAT_T_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv4_nat_t_esp_mark = {
    "name": "test_mac_ipv4_nat_t_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV4_NAT_T_ESP,
    "check_param": {"port_id": 0, "mark_id": 15},
}

tv_mac_ipv6_nat_t_esp_queue_index = {
    "name": "test_mac_ipv6_nat_t_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV6_NAT_T_ESP,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7},
}

tv_mac_ipv6_nat_t_esp_queue_group = {
    "name": "test_mac_ipv6_nat_t_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV6_NAT_T_ESP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6},
}

tv_mac_ipv6_nat_t_esp_passthru = {
    "name": "test_mac_ipv6_nat_t_esp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV6_NAT_T_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv6_nat_t_esp_drop = {
    "name": "test_mac_ipv6_nat_t_esp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions drop / end",
    "scapy_str": MAC_IPV6_NAT_T_ESP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv6_nat_t_esp_mark_rss = {
    "name": "test_mac_ipv6_nat_t_esp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV6_NAT_T_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv6_nat_t_esp_mark = {
    "name": "test_mac_ipv6_nat_t_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV6_NAT_T_ESP,
    "check_param": {"port_id": 0, "mark_id": 15},
}

# mac_ipv4_tcp_without_input_set
tv_mac_ipv4_tcp_without_input_set_queue_index = {
    "name": "test_mac_ipv4_tcp_without_input_set_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_TCP_WITHOUT,
    "count": 10,
    "check_param": {"port_id": 0, "queue": 1},
}

tv_mac_ipv4_tcp_without_input_set_queue_group = {
    "name": "test_mac_ipv4_tcp_without_input_set_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss queues 0 1 2 3 end / end",
    "scapy_str": MAC_IPV4_TCP_WITHOUT,
    "count": 10,
    "check_param": {"port_id": 0, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_tcp_without_input_set_passthru = {
    "name": "test_mac_ipv4_tcp_without_input_set_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_TCP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_tcp_without_input_set_drop = {
    "name": "test_mac_ipv4_tcp_without_input_set_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP_WITHOUT,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_tcp_without_input_set_mark_rss = {
    "name": "test_mac_ipv4_tcp_without_input_set_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV4_TCP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv4_tcp_without_input_set_mark = {
    "name": "test_mac_ipv4_tcp_without_input_set_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_TCP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

# mac_ipv4_udp_without_input_set
tv_mac_ipv4_udp_without_input_set_queue_index = {
    "name": "test_mac_ipv4_udp_without_input_set_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_UDP_WITHOUT,
    "count": 10,
    "check_param": {"port_id": 0, "queue": 1},
}

tv_mac_ipv4_udp_without_input_set_queue_group = {
    "name": "test_mac_ipv4_udp_without_input_set_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss queues 0 1 2 3 end / end",
    "scapy_str": MAC_IPV4_UDP_WITHOUT,
    "count": 10,
    "check_param": {"port_id": 0, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_udp_without_input_set_passthru = {
    "name": "test_mac_ipv4_udp_without_input_set_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_UDP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_udp_without_input_set_drop = {
    "name": "test_mac_ipv4_udp_without_input_set_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP_WITHOUT,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_udp_without_input_set_mark_rss = {
    "name": "test_mac_ipv4_udp_without_input_set_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV4_UDP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv4_udp_without_input_set_mark = {
    "name": "test_mac_ipv4_udp_without_input_set_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_UDP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

# mac_ipv6_tcp_without_input_set
tv_mac_ipv6_tcp_without_input_set_queue_index = {
    "name": "test_mac_ipv6_tcp_without_input_set_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 / tcp / end actions queue index 1 / end",
    "scapy_str": MAC_IPV6_TCP_WITHOUT,
    "count": 10,
    "check_param": {"port_id": 0, "queue": 1},
}

tv_mac_ipv6_tcp_without_input_set_queue_group = {
    "name": "test_mac_ipv6_tcp_without_input_set_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss queues 0 1 2 3 end / end",
    "scapy_str": MAC_IPV6_TCP_WITHOUT,
    "count": 10,
    "check_param": {"port_id": 0, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv6_tcp_without_input_set_passthru = {
    "name": "test_mac_ipv6_tcp_without_input_set_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV6_TCP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv6_tcp_without_input_set_drop = {
    "name": "test_mac_ipv6_tcp_without_input_set_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV6_TCP_WITHOUT,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv6_tcp_without_input_set_mark_rss = {
    "name": "test_mac_ipv6_tcp_without_input_set_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 / tcp / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV6_TCP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv6_tcp_without_input_set_mark = {
    "name": "test_mac_ipv6_tcp_without_input_set_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 / tcp / end actions mark id 1 / end",
    "scapy_str": MAC_IPV6_TCP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

# mac_ipv6_udp_without_input_set
tv_mac_ipv6_udp_without_input_set_queue_index = {
    "name": "test_mac_ipv6_udp_without_input_set_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / end actions queue index 1 / end",
    "scapy_str": MAC_IPV6_UDP_WITHOUT,
    "count": 10,
    "check_param": {"port_id": 0, "queue": 1},
}

tv_mac_ipv6_udp_without_input_set_queue_group = {
    "name": "test_mac_ipv6_udp_without_input_set_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss queues 0 1 2 3 end / end",
    "scapy_str": MAC_IPV6_UDP_WITHOUT,
    "count": 10,
    "check_param": {"port_id": 0, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv6_udp_without_input_set_passthru = {
    "name": "test_mac_ipv6_udp_without_input_set_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV6_UDP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv6_udp_without_input_set_drop = {
    "name": "test_mac_ipv6_udp_without_input_set_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / end actions drop / end",
    "scapy_str": MAC_IPV6_UDP_WITHOUT,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv6_udp_without_input_set_mark_rss = {
    "name": "test_mac_ipv6_udp_without_input_set_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV6_UDP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv6_udp_without_input_set_mark = {
    "name": "test_mac_ipv6_udp_without_input_set_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / end actions mark id 1 / end",
    "scapy_str": MAC_IPV6_UDP_WITHOUT,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

# inner L3/L4 cases
# mac_ipv4_gtpu_ipv4 test case
tv_mac_ipv4_gtpu_ipv4_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_ipv4_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_inner_tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv4_tcp test case
tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_tcp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / ipv4 / tcp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_tcp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_tcp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_tcp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv4_udp test case
tv_mac_ipv4_gtpu_ipv4_udp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv4_udp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / ipv4 / udp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv4_udp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv4_udp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv4_udp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_eh_ipv4 test case
tv_mac_ipv4_gtpu_eh_ipv4_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_eh_ipv4_tcp test case
tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_eh_ipv4_udp test case
tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# MAC_IPV4_GTPU_EH_DL_ipv4 test case
tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv4_tcp test case
tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv4_udp test case
tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 dst is 192.168.0.21 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# MAC_IPV4_GTPU_EH_UL_ipv4 test case
tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv4_tcp test case
tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv4_udp test case
tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 dst is 192.168.0.21 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV4_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv6 test case
tv_mac_ipv4_gtpu_ipv6_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_ipv6_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_inner_tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv6_tcp test case
tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_tcp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / ipv6 / tcp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_tcp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_tcp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_tcp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv6_udp test case
tv_mac_ipv4_gtpu_ipv6_udp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_ipv6_udp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / ipv6 / udp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_ipv6_udp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_ipv6_udp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_ipv6_udp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_eh_ipv4 test case
tv_mac_ipv4_gtpu_eh_ipv6_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_eh_ipv6_tcp test case
tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / gtp_psc / ipv6 / tcp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_eh_ipv6_udp test case
tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_GTPU_EH_DL_ipv4 test case
tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv6_tcp test case
tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv6_udp test case
tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_DL_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_GTPU_EH_UL_ipv4 test case
tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv6_tcp test case
tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_TCP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# mac_ipv4_gtpu_ipv6_udp test case
tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_passthru = {
    "name": "tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp src is 22 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp src is 22 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp src is 22 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp src is 22 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp src is 22 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp dst is 23 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp dst is 23 / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4  / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_drop = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH_UL_IPV6_UDP_WITHOUT_INPUTSET,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

# gre tunnel inner fdir
tv_mac_ipv4_gre_ipv4_queue_index = {
    "name": "test_mac_ipv4_gre_ipv4_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_GRE_IPV4,
    "check_param": {"port_id": 0, "queue": 1},
}

tv_mac_ipv4_gre_ipv4_rss_queue = {
    "name": "mac_ipv4_gre_ipv4_rss_queue",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions rss queues 2 3 end / end",
    "scapy_str": MAC_IPV4_GRE_IPV4,
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_mac_ipv4_gre_ipv4_passthru = {
    "name": "mac_ipv4_gre_ipv4_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions passthru / end",
    "scapy_str": MAC_IPV4_GRE_IPV4,
    "check_param": {"port_id": 0, "passthru": 1},
}

tv_mac_ipv4_gre_ipv4_drop = {
    "name": "mac_ipv4_gre_ipv4_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions drop / end",
    "scapy_str": MAC_IPV4_GRE_IPV4,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gre_ipv4_mark_rss = {
    "name": "mac_ipv4_gre_ipv4_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_GRE_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0},
}

tv_mac_ipv4_gre_ipv4_mark = {
    "name": "mac_ipv4_gre_ipv4_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions mark id 5 / end",
    "scapy_str": MAC_IPV4_GRE_IPV4,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 5},
}

tv_mac_ipv4_gre_ipv6_queue_index = {
    "name": "test_mac_ipv4_gre_ipv6_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions queue index 15 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GRE_IPV6,
    "check_param": {"port_id": 0, "queue": 15, "mark_id": 1},
}

tv_mac_ipv4_gre_ipv6_drop = {
    "name": "test_mac_ipv4_gre_ipv6_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions drop / end",
    "scapy_str": MAC_IPV4_GRE_IPV6,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gre_ipv6_rss_queue = {
    "name": "test_mac_ipv4_gre_ipv6_rss_queue",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark id 2 / end",
    "scapy_str": MAC_IPV4_GRE_IPV6,
    "check_param": {
        "port_id": 0,
        "queue": [8, 9, 10, 11, 12, 13, 14, 15],
        "mark_id": 2,
    },
}

tv_mac_ipv4_gre_ipv6_passthru = {
    "name": "test_mac_ipv4_gre_ipv6_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions passthru / mark id 3 / end",
    "scapy_str": MAC_IPV4_GRE_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 3},
}

tv_mac_ipv4_gre_ipv6_mark_rss = {
    "name": "test_mac_ipv4_gre_ipv6_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions mark id 4 / rss / end",
    "scapy_str": MAC_IPV4_GRE_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 4},
}

tv_mac_ipv4_gre_ipv6_mark = {
    "name": "test_mac_ipv4_gre_ipv6_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions mark id 5 / rss / end",
    "scapy_str": MAC_IPV4_GRE_IPV6,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 5},
}

tv_mac_ipv4_gre_ipv4_tcp_queue_index = {
    "name": "test_mac_ipv4_gre_ipv4_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end",
    "scapy_str": MAC_IPV4_GRE_IPV4_TCP,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0},
}

tv_mac_ipv4_gre_ipv4_tcp_rss_queue = {
    "name": "mac_ipv4_gre_ipv4_tcp_rss_queue",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions rss queues 1 2 3 4 end / mark id 4294967294 / end",
    "scapy_str": MAC_IPV4_GRE_IPV4_TCP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 4294967294},
}

tv_mac_ipv4_gre_ipv4_tcp_passthru = {
    "name": "mac_ipv4_gre_ipv4_tcp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GRE_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gre_ipv4_tcp_drop = {
    "name": "mac_ipv4_gre_ipv4_tcp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GRE_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gre_ipv4_tcp_mark_rss = {
    "name": "mac_ipv4_gre_ipv4_tcp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 2 / rss / end ",
    "scapy_str": MAC_IPV4_GRE_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2},
}

tv_mac_ipv4_gre_ipv4_tcp_mark = {
    "name": "mac_ipv4_gre_ipv4_tcp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 1 / end ",
    "scapy_str": MAC_IPV4_GRE_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1},
}

tv_mac_ipv4_gre_ipv6_tcp_queue_index = {
    "name": "test_mac_ipv4_gre_ipv6_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 6 / mark id 4 / end",
    "scapy_str": MAC_IPV4_GRE_IPV6_TCP,
    "check_param": {"port_id": 0, "queue": 6, "mark_id": 4},
}

tv_mac_ipv4_gre_ipv6_tcp_rss_queue = {
    "name": "mac_ipv4_gre_ipv6_tcp_rss_queue",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions rss queues 4 5 6 7 end / mark id 4294967294 / end",
    "scapy_str": MAC_IPV4_GRE_IPV6_TCP,
    "check_param": {"port_id": 0, "queue": [4, 5, 6, 7], "mark_id": 4294967294},
}

tv_mac_ipv4_gre_ipv6_tcp_passthru = {
    "name": "mac_ipv4_gre_ipv6_tcp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions passthru / mark id 7 / end",
    "scapy_str": MAC_IPV4_GRE_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 7},
}

tv_mac_ipv4_gre_ipv6_tcp_drop = {
    "name": "mac_ipv4_gre_ipv6_tcp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_GRE_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1},
}

tv_mac_ipv4_gre_ipv6_tcp_mark_rss = {
    "name": "mac_ipv4_gre_ipv6_tcp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions mark id 6 / rss / end ",
    "scapy_str": MAC_IPV4_GRE_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 6},
}

tv_mac_ipv4_gre_ipv6_tcp_mark = {
    "name": "mac_ipv4_gre_ipv6_tcp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions mark id 3 / end ",
    "scapy_str": MAC_IPV4_GRE_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 3},
}

vectors_ipv4_pay = [
    tv_mac_ipv4_pay_queue_index,
    tv_mac_ipv4_pay_mark_rss,
    tv_mac_ipv4_pay_passthru,
    tv_mac_ipv4_pay_drop,
    tv_mac_ipv4_pay_queue_group,
    tv_mac_ipv4_pay_mark,
]

vectors_ipv4_pay_multicast = [
    tv_mac_ipv4_pay_queue_index_multicast,
    tv_mac_ipv4_pay_rss_multicast,
    tv_mac_ipv4_pay_passthru_multicast,
    tv_mac_ipv4_pay_drop_multicast,
    tv_mac_ipv4_pay_mark_rss_multicast,
    tv_mac_ipv4_pay_mark_multicast,
]

vectors_ipv4_udp = [
    tv_mac_ipv4_udp_drop,
    tv_mac_ipv4_udp_queue_group,
    tv_mac_ipv4_udp_queue_index,
    tv_mac_ipv4_udp_mark_rss,
    tv_mac_ipv4_udp_passthru,
    tv_mac_ipv4_udp_mark,
]

vectors_ipv6_pay_multicast = [
    tv_mac_ipv6_pay_queue_index_multicast,
    tv_mac_ipv6_pay_rss_multicast,
    tv_mac_ipv6_pay_passthru_multicast,
    tv_mac_ipv6_pay_drop_multicast,
    tv_mac_ipv6_pay_mark_rss_multicast,
    tv_mac_ipv6_pay_mark_multicast,
]

vectors_ipv4_tcp = [
    tv_mac_ipv4_tcp_drop,
    tv_mac_ipv4_tcp_queue_group,
    tv_mac_ipv4_tcp_queue_index,
    tv_mac_ipv4_tcp_mark_rss,
    tv_mac_ipv4_tcp_passthru,
    tv_mac_ipv4_tcp_mark,
]

vectors_ipv4_sctp = [
    tv_mac_ipv4_sctp_drop,
    tv_mac_ipv4_sctp_queue_group,
    tv_mac_ipv4_sctp_queue_index,
    tv_mac_ipv4_sctp_passthru,
    tv_mac_ipv4_sctp_mark_rss,
    tv_mac_ipv4_sctp_mark,
]

vectors_ipv6_pay = [
    tv_mac_ipv6_pay_drop,
    tv_mac_ipv6_pay_queue_group,
    tv_mac_ipv6_pay_queue_index,
    tv_mac_ipv6_pay_mark_rss,
    tv_mac_ipv6_pay_passthru,
    tv_mac_ipv6_pay_mark,
]

vectors_ipv6_udp = [
    tv_mac_ipv6_udp_drop,
    tv_mac_ipv6_udp_queue_group,
    tv_mac_ipv6_udp_queue_index,
    tv_mac_ipv6_udp_passthru,
    tv_mac_ipv6_udp_mark_rss,
    tv_mac_ipv6_udp_mark,
]

vectors_ipv6_tcp = [
    tv_mac_ipv6_tcp_drop,
    tv_mac_ipv6_tcp_queue_group,
    tv_mac_ipv6_tcp_queue_index,
    tv_mac_ipv6_tcp_mark_rss,
    tv_mac_ipv6_tcp_passthru,
    tv_mac_ipv6_tcp_mark,
]

vectors_ipv6_sctp = [
    tv_mac_ipv6_sctp_queue_index,
    tv_mac_ipv6_sctp_drop,
    tv_mac_ipv6_sctp_queue_group,
    tv_mac_ipv6_sctp_passthru,
    tv_mac_ipv6_sctp_mark_rss,
    tv_mac_ipv6_sctp_mark,
]

vectors_ipv4_gtpu_eh = [
    tv_mac_ipv4_gtpu_eh_drop,
    tv_mac_ipv4_gtpu_eh_mark_rss,
    tv_mac_ipv4_gtpu_eh_queue_index,
    tv_mac_ipv4_gtpu_eh_queue_group,
    tv_mac_ipv4_gtpu_eh_passthru,
    tv_mac_ipv4_gtpu_eh_mark,
    tv_mac_ipv4_gtpu_eh_4tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_4tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_4tuple_passthru,
    tv_mac_ipv4_gtpu_eh_4tuple_drop,
    tv_mac_ipv4_gtpu_eh_4tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_dstip_drop,
    tv_mac_ipv4_gtpu_eh_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_srcip_drop,
    tv_mac_ipv4_gtpu_eh_srcip_mark_rss,
]

vectors_ipv4_gtpu = [
    tv_mac_ipv4_gtpu_drop,
    tv_mac_ipv4_gtpu_mark_rss,
    tv_mac_ipv4_gtpu_queue_index,
    tv_mac_ipv4_gtpu_queue_group,
    tv_mac_ipv4_gtpu_passthru,
    tv_mac_ipv4_gtpu_mark,
    tv_mac_ipv4_gtpu_3tuple_queue_index,
    tv_mac_ipv4_gtpu_3tuple_queue_group,
    tv_mac_ipv4_gtpu_3tuple_passthru,
    tv_mac_ipv4_gtpu_3tuple_drop,
    tv_mac_ipv4_gtpu_3tuple_mark_rss,
    tv_mac_ipv4_gtpu_dstip_queue_index,
    tv_mac_ipv4_gtpu_dstip_queue_group,
    tv_mac_ipv4_gtpu_dstip_passthru,
    tv_mac_ipv4_gtpu_dstip_drop,
    tv_mac_ipv4_gtpu_dstip_mark_rss,
    tv_mac_ipv4_gtpu_srcip_queue_index,
    tv_mac_ipv4_gtpu_srcip_queue_group,
    tv_mac_ipv4_gtpu_srcip_passthru,
    tv_mac_ipv4_gtpu_srcip_drop,
    tv_mac_ipv4_gtpu_srcip_mark_rss,
]

vectors_ipv6_gtpu_eh = [
    tv_mac_ipv6_gtpu_eh_4tuple_queue_index,
    tv_mac_ipv6_gtpu_eh_4tuple_queue_group,
    tv_mac_ipv6_gtpu_eh_4tuple_passthru,
    tv_mac_ipv6_gtpu_eh_4tuple_drop,
    tv_mac_ipv6_gtpu_eh_4tuple_mark_rss,
    tv_mac_ipv6_gtpu_eh_dstip_queue_index,
    tv_mac_ipv6_gtpu_eh_dstip_queue_group,
    tv_mac_ipv6_gtpu_eh_dstip_passthru,
    tv_mac_ipv6_gtpu_eh_dstip_drop,
    tv_mac_ipv6_gtpu_eh_dstip_mark_rss,
    tv_mac_ipv6_gtpu_eh_srcip_queue_index,
    tv_mac_ipv6_gtpu_eh_srcip_queue_group,
    tv_mac_ipv6_gtpu_eh_srcip_passthru,
    tv_mac_ipv6_gtpu_eh_srcip_drop,
    tv_mac_ipv6_gtpu_eh_srcip_mark_rss,
]

vectors_ipv6_gtpu = [
    tv_mac_ipv6_gtpu_3tuple_queue_index,
    tv_mac_ipv6_gtpu_3tuple_queue_group,
    tv_mac_ipv6_gtpu_3tuple_passthru,
    tv_mac_ipv6_gtpu_3tuple_drop,
    tv_mac_ipv6_gtpu_3tuple_mark_rss,
    tv_mac_ipv6_gtpu_dstip_queue_index,
    tv_mac_ipv6_gtpu_dstip_queue_group,
    tv_mac_ipv6_gtpu_dstip_passthru,
    tv_mac_ipv6_gtpu_dstip_drop,
    tv_mac_ipv6_gtpu_dstip_mark_rss,
    tv_mac_ipv6_gtpu_srcip_queue_index,
    tv_mac_ipv6_gtpu_srcip_queue_group,
    tv_mac_ipv6_gtpu_srcip_passthru,
    tv_mac_ipv6_gtpu_srcip_drop,
    tv_mac_ipv6_gtpu_srcip_mark_rss,
]

vectors_pfcp = [
    tv_pfcp_queue_index,
    tv_pfcp_queue_group,
    tv_pfcp_passthru,
    tv_pfcp_drop,
    tv_pfcp_mark,
    tv_pfcp_mark_rss,
]

vectors_l2_ethertype = [
    tv_l2_ethertype_drop,
    tv_l2_ethertype_queue_index,
    tv_l2_ethertype_queue_group,
    tv_l2_ethertype_passthru,
    tv_l2_ethertype_mark,
    tv_l2_ethertype_mark_rss,
]

vectors_ipv4_l2tpv3 = [
    tv_mac_ipv4_l2tpv3_queue_index,
    tv_mac_ipv4_l2tpv3_queue_group,
    tv_mac_ipv4_l2tpv3_mark,
]

vectors_ipv6_l2tpv3 = [
    tv_mac_ipv6_l2tpv3_queue_index,
    tv_mac_ipv6_l2tpv3_queue_group,
    tv_mac_ipv6_l2tpv3_mark,
]

vectors_ipv4_esp = [
    tv_mac_ipv4_esp_queue_index,
    tv_mac_ipv4_esp_queue_group,
    tv_mac_ipv4_esp_mark,
    tv_mac_ipv4_esp_drop,
    tv_mac_ipv4_esp_mark_rss,
    tv_mac_ipv4_esp_passthru,
]

vectors_ipv6_esp = [
    tv_mac_ipv6_esp_queue_index,
    tv_mac_ipv6_esp_queue_group,
    tv_mac_ipv6_esp_mark,
    tv_mac_ipv6_esp_drop,
    tv_mac_ipv6_esp_mark_rss,
    tv_mac_ipv6_esp_passthru,
]

vectors_ipv4_ah = [
    tv_mac_ipv4_ah_queue_index,
    tv_mac_ipv4_ah_queue_group,
    tv_mac_ipv4_ah_mark,
]

vectors_ipv6_ah = [
    tv_mac_ipv6_ah_queue_index,
    tv_mac_ipv6_ah_queue_group,
    tv_mac_ipv6_ah_mark,
]

vectors_ipv4_nat_t_esp = [
    tv_mac_ipv4_nat_t_esp_queue_index,
    tv_mac_ipv4_nat_t_esp_queue_group,
    tv_mac_ipv4_nat_t_esp_mark,
    tv_mac_ipv4_nat_t_esp_drop,
    tv_mac_ipv4_nat_t_esp_mark_rss,
    tv_mac_ipv4_nat_t_esp_passthru,
]

vectors_ipv6_nat_t_esp = [
    tv_mac_ipv6_nat_t_esp_queue_index,
    tv_mac_ipv6_nat_t_esp_queue_group,
    tv_mac_ipv6_nat_t_esp_mark,
    tv_mac_ipv6_nat_t_esp_drop,
    tv_mac_ipv6_nat_t_esp_mark_rss,
    tv_mac_ipv6_nat_t_esp_passthru,
]

vectors_ipv4_tcp_without_input_set = [
    tv_mac_ipv4_tcp_without_input_set_queue_index,
    tv_mac_ipv4_tcp_without_input_set_queue_group,
    tv_mac_ipv4_tcp_without_input_set_mark_rss,
    tv_mac_ipv4_tcp_without_input_set_passthru,
    tv_mac_ipv4_tcp_without_input_set_drop,
    tv_mac_ipv4_tcp_without_input_set_mark,
]

vectors_ipv4_udp_without_input_set = [
    tv_mac_ipv4_udp_without_input_set_queue_index,
    tv_mac_ipv4_udp_without_input_set_queue_group,
    tv_mac_ipv4_udp_without_input_set_mark_rss,
    tv_mac_ipv4_udp_without_input_set_passthru,
    tv_mac_ipv4_udp_without_input_set_drop,
    tv_mac_ipv4_udp_without_input_set_mark,
]

vectors_ipv6_tcp_without_input_set = [
    tv_mac_ipv6_tcp_without_input_set_queue_index,
    tv_mac_ipv6_tcp_without_input_set_queue_group,
    tv_mac_ipv6_tcp_without_input_set_mark_rss,
    tv_mac_ipv6_tcp_without_input_set_passthru,
    tv_mac_ipv6_tcp_without_input_set_drop,
    tv_mac_ipv6_tcp_without_input_set_mark,
]

vectors_ipv6_udp_without_input_set = [
    tv_mac_ipv6_udp_without_input_set_queue_index,
    tv_mac_ipv6_udp_without_input_set_queue_group,
    tv_mac_ipv6_udp_without_input_set_mark_rss,
    tv_mac_ipv6_udp_without_input_set_passthru,
    tv_mac_ipv6_udp_without_input_set_drop,
    tv_mac_ipv6_udp_without_input_set_mark,
]

vectors_ipv4_gtpu_ipv4 = [
    tv_mac_ipv4_gtpu_ipv4_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_ipv4_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_ipv4_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_ipv4_inner_srcip_drop,
    tv_mac_ipv4_gtpu_ipv4_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_ipv4_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_ipv4_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_ipv4_inner_dstip_drop,
    tv_mac_ipv4_gtpu_ipv4_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_ipv4_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_ipv4_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_ipv4_inner_tuple_drop,
    tv_mac_ipv4_gtpu_ipv4_inner_tuple_mark_rss,
]

vectors_ipv4_gtpu_ipv4_tcp = [
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_ipv4_tcp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_tcp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_ipv4_tcp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_ipv4_tcp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_ipv4_tcp_without_inputset_drop,
    tv_mac_ipv4_gtpu_ipv4_tcp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_ipv4_udp = [
    tv_mac_ipv4_gtpu_ipv4_udp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_ipv4_udp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_ipv4_udp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_ipv4_udp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_ipv4_udp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_ipv4_udp_without_inputset_drop,
    tv_mac_ipv4_gtpu_ipv4_udp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_ipv4 = [
    tv_mac_ipv4_gtpu_eh_ipv4_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_inner_tuple_mark_rss,
]

vectors_ipv4_gtpu_eh_ipv4_tcp = [
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_ipv4_udp = [
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_dl_ipv4 = [
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_inner_tuple_mark_rss,
]

vectors_ipv4_gtpu_eh_dl_ipv4_tcp = [
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_tcp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_dl_ipv4_udp = [
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv4_udp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_ul_ipv4 = [
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_inner_tuple_mark_rss,
]

vectors_ipv4_gtpu_eh_ul_ipv4_tcp = [
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_tcp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_ul_ipv4_udp = [
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv4_udp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_ipv6 = [
    tv_mac_ipv4_gtpu_ipv6_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_ipv6_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_ipv6_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_ipv6_inner_srcip_drop,
    tv_mac_ipv4_gtpu_ipv6_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_ipv6_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_ipv6_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_ipv6_inner_dstip_drop,
    tv_mac_ipv4_gtpu_ipv6_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_ipv6_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_ipv6_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_ipv6_inner_tuple_drop,
    tv_mac_ipv4_gtpu_ipv6_inner_tuple_mark_rss,
]

vectors_ipv4_gtpu_ipv6_tcp = [
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_ipv6_tcp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_tcp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_ipv6_tcp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_ipv6_tcp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_ipv6_tcp_without_inputset_drop,
    tv_mac_ipv4_gtpu_ipv6_tcp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_ipv6_udp = [
    tv_mac_ipv4_gtpu_ipv6_udp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_ipv6_udp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_ipv6_udp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_ipv6_udp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_ipv6_udp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_ipv6_udp_without_inputset_drop,
    tv_mac_ipv4_gtpu_ipv6_udp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_ipv6 = [
    tv_mac_ipv4_gtpu_eh_ipv6_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_inner_tuple_mark_rss,
]

vectors_ipv4_gtpu_eh_ipv6_tcp = [
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_tcp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_ipv6_udp = [
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_ipv6_udp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_dl_ipv6 = [
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_inner_tuple_mark_rss,
]

vectors_ipv4_gtpu_eh_dl_ipv6_tcp = [
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_tcp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_dl_ipv6_udp = [
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_dl_ipv6_udp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_ul_ipv6 = [
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_inner_tuple_mark_rss,
]

vectors_ipv4_gtpu_eh_ul_ipv6_tcp = [
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_tcp_without_inputset_mark_rss,
]

vectors_ipv4_gtpu_eh_ul_ipv6_udp = [
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstip_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_tuple_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_srcport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_inner_dstport_mark_rss,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_queue_index,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_queue_group,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_passthru,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_drop,
    tv_mac_ipv4_gtpu_eh_ul_ipv6_udp_without_inputset_mark_rss,
]

# gre tunnel inner
vectors_ipv4_gre_ipv4 = [
    tv_mac_ipv4_gre_ipv4_queue_index,
    tv_mac_ipv4_gre_ipv4_rss_queue,
    tv_mac_ipv4_gre_ipv4_passthru,
    tv_mac_ipv4_gre_ipv4_drop,
    tv_mac_ipv4_gre_ipv4_mark_rss,
    tv_mac_ipv4_gre_ipv4_mark,
]

vectors_ipv6_gre_ipv4 = [
    eval(
        str(each)
        .replace("ipv4_gre_ipv4", "ipv6_gre_ipv4")
        .replace("IP()", "IPv6()")
        .replace("eth / ipv4", "eth / ipv6")
    )
    for each in vectors_ipv4_gre_ipv4
]

vectors_ipv4_gre_ipv6 = [
    tv_mac_ipv4_gre_ipv6_queue_index,
    tv_mac_ipv4_gre_ipv6_rss_queue,
    tv_mac_ipv4_gre_ipv6_passthru,
    tv_mac_ipv4_gre_ipv6_drop,
    tv_mac_ipv4_gre_ipv6_mark_rss,
    tv_mac_ipv4_gre_ipv6_mark,
]

vectors_ipv6_gre_ipv6 = [
    eval(
        str(each)
        .replace("ipv4_gre_ipv6", "ipv6_gre_ipv6")
        .replace("IP()", "IPv6()")
        .replace("eth / ipv4", "eth / ipv6")
    )
    for each in vectors_ipv4_gre_ipv6
]

vectors_ipv4_gre_ipv4_tcp = [
    tv_mac_ipv4_gre_ipv4_tcp_queue_index,
    tv_mac_ipv4_gre_ipv4_tcp_rss_queue,
    tv_mac_ipv4_gre_ipv4_tcp_passthru,
    tv_mac_ipv4_gre_ipv4_tcp_drop,
    tv_mac_ipv4_gre_ipv4_tcp_mark_rss,
    tv_mac_ipv4_gre_ipv4_tcp_mark,
]

vectors_ipv6_gre_ipv4_tcp = [
    eval(
        str(each)
        .replace("ipv4_gre_ipv4", "ipv6_gre_ipv4")
        .replace("eth / ipv4", "eth / ipv6")
        .replace("IP()", "IPv6()")
    )
    for each in vectors_ipv4_gre_ipv4_tcp
]

vectors_ipv4_gre_ipv6_tcp = [
    tv_mac_ipv4_gre_ipv6_tcp_queue_index,
    tv_mac_ipv4_gre_ipv6_tcp_rss_queue,
    tv_mac_ipv4_gre_ipv6_tcp_passthru,
    tv_mac_ipv4_gre_ipv6_tcp_drop,
    tv_mac_ipv4_gre_ipv6_tcp_mark_rss,
    tv_mac_ipv4_gre_ipv6_tcp_mark,
]

vectors_ipv6_gre_ipv6_tcp = [
    eval(
        str(each)
        .replace("ipv4_gre_ipv6", "ipv6_gre_ipv6")
        .replace("eth / ipv4", "eth / ipv6")
        .replace("IP()", "IPv6()")
    )
    for each in vectors_ipv4_gre_ipv6_tcp
]

vectors_ipv4_gre_ipv4_udp = [
    eval(str(each).replace("tcp", "udp").replace("TCP", "UDP"))
    for each in vectors_ipv4_gre_ipv4_tcp
]

vectors_ipv6_gre_ipv4_udp = [
    eval(str(each).replace("tcp", "udp").replace("TCP", "UDP"))
    for each in vectors_ipv6_gre_ipv4_tcp
]

vectors_ipv4_gre_ipv6_udp = [
    eval(str(each).replace("tcp", "udp").replace("TCP", "UDP"))
    for each in vectors_ipv4_gre_ipv6_tcp
]

vectors_ipv6_gre_ipv6_udp = [
    eval(str(each).replace("tcp", "udp").replace("TCP", "UDP"))
    for each in vectors_ipv6_gre_ipv6_tcp
]


class TestICEIAVFFdir(TestCase):
    def rte_flow_process(self, vectors):
        test_results = {}
        for tv in vectors:
            try:
                port_id = tv["check_param"]["port_id"]
                self.dut.send_expect("flow flush %d" % port_id, "testpmd> ", 120)

                # validate rule
                self.validate_fdir_rule(tv["rule"], check_stats=True)
                self.check_fdir_rule(port_id=port_id, stats=False)

                # create rule
                rule_li = self.create_fdir_rule(tv["rule"], check_stats=True)
                if "gtpu_eh" in tv["name"]:
                    gtpu_rss = [
                        "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end"
                    ]
                    gtpu_rss_rule_li = self.create_fdir_rule(gtpu_rss, check_stats=True)

                if "count" in tv:
                    out1 = self.send_pkts_getouput(
                        pkts=tv["scapy_str"]["match"], count=tv["count"]
                    )
                    rfc.check_iavf_fdir_mark(
                        out1, pkt_num=tv["count"], check_param=tv["check_param"]
                    )
                else:
                    # send and check match packets
                    out1 = self.send_pkts_getouput(pkts=tv["scapy_str"]["match"])
                    rfc.check_iavf_fdir_mark(
                        out1,
                        pkt_num=len(tv["scapy_str"]["match"]),
                        check_param=tv["check_param"],
                    )
                # send and check mismatch packets
                out2 = self.send_pkts_getouput(pkts=tv["scapy_str"]["mismatch"])
                rfc.check_iavf_fdir_mark(
                    out2,
                    pkt_num=len(tv["scapy_str"]["mismatch"]),
                    check_param=tv["check_param"],
                    stats=False,
                )
                # list and destroy rule
                if "gtpu_eh" in tv["name"]:
                    self.check_fdir_rule(
                        port_id=port_id, rule_list=rule_li + gtpu_rss_rule_li
                    )
                else:
                    self.check_fdir_rule(port_id=port_id, rule_list=rule_li)
                self.destroy_fdir_rule(rule_id=rule_li, port_id=port_id)
                # send matched packet
                out3 = self.send_pkts_getouput(pkts=tv["scapy_str"]["match"])
                rfc.check_iavf_fdir_mark(
                    out3,
                    pkt_num=len(tv["scapy_str"]["match"]),
                    check_param=tv["check_param"],
                    stats=False,
                )
                # check not rule exists
                if "gtpu_eh" in tv["name"]:
                    self.check_fdir_rule(port_id=port_id, rule_list=gtpu_rss_rule_li)
                else:
                    self.check_fdir_rule(port_id=port_id, stats=False)
                test_results[tv["name"]] = True
                print((GREEN("case passed: %s" % tv["name"])))
            except Exception as e:
                print((RED(e)))
                test_results[tv["name"]] = False
                continue
        failed_cases = []
        for k, v in list(test_results.items()):
            if not v:
                failed_cases.append(k)
        self.verify(all(test_results.values()), "{} failed.".format(failed_cases))

    def multirules_process(self, vectors, port_id=0):
        # create rules on only one port
        test_results = {}
        rule_li = []
        for tv in vectors:
            try:
                port_id = port_id
                pkts = tv["scapy_str"]
                check_param = tv["check_param"]
                self.destroy_fdir_rule(rule_id=rule_li, port_id=port_id)
                # validate rules
                self.validate_fdir_rule(tv["rule"], check_stats=True)

                # create rules
                rule_li = self.create_fdir_rule(tv["rule"], check_stats=True)

                for i in range(len(pkts)):
                    port_id = check_param[i]["port_id"]
                    out = self.send_pkts_getouput(pkts=pkts[i])
                    rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param=check_param[i])
                test_results[tv["name"]] = True
                print((GREEN("case passed: %s" % tv["name"])))
            except Exception as e:
                print((RED(e)))
                test_results[tv["name"]] = False
                continue
        failed_cases = []
        for k, v in list(test_results.items()):
            if not v:
                failed_cases.append(k)
        self.verify(all(test_results.values()), "{} failed.".format(failed_cases))

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
        self.verify(cores is not None, "Insufficient cores for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        localPort0 = self.tester.get_local_port(self.dut_ports[0])
        localPort1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_iface0 = self.tester.get_interface(localPort0)
        self.tester_iface1 = self.tester.get_interface(localPort1)
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.pf1_intf = self.dut.ports_info[self.dut_ports[1]]["intf"]
        self.pf0_mac = self.dut.get_mac_address(0)
        self.pf1_mac = self.dut.get_mac_address(1)

        # bind pf to kernel
        for port in self.dut_ports:
            netdev = self.dut.ports_info[port]["port"]
            netdev.bind_driver(driver="ice")

        # set vf driver
        self.vf_driver = "vfio-pci"
        self.dut.send_expect("modprobe vfio-pci", "#")
        self.suite_config = rfc.get_suite_config(self)

        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.path = self.dut.apps_name["test-pmd"]

        self.src_file_dir = "dep/"
        self.dut_file_dir = "/tmp/"
        self.q_num = TXQ_RXQ_NUMBER

    def ip_link_set(self, host_intf=None, cmd=None, port=None, types=None, value=0):
        if host_intf is None or cmd is None or port is None or types is None:
            return
        set_command = f"ip link set {host_intf} {cmd} {port} {types} {value}"
        out = self.dut.send_expect(set_command, "# ")
        if "RTNETLINK answers: Invalid argument" in out:
            self.dut.send_expect(set_command, "# ")

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.restore_interfaces_linux()
        self.setup_2pf_4vf_env()
        time.sleep(1)
        self.launch_testpmd()

    def setup_2pf_4vf_env(self, driver="default"):

        # get PF interface name
        self.used_dut_port_0 = self.dut_ports[0]
        self.used_dut_port_1 = self.dut_ports[1]

        # generate 2 VFs on PF
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 2, driver=driver)
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_1, 2, driver=driver)
        self.sriov_vfs_pf0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        self.sriov_vfs_pf1 = self.dut.ports_info[self.used_dut_port_1]["vfs_port"]

        self.host_intf_0 = self.dut.ports_info[self.used_dut_port_0]["intf"]
        self.host_intf_1 = self.dut.ports_info[self.used_dut_port_0]["intf"]

        if self.running_case in [
            "test_pfcp_vlan_strip_off_sw_checksum",
            "test_pfcp_vlan_strip_on_hw_checksum",
        ]:
            self.ip_link_set(
                host_intf=self.host_intf_0,
                cmd="vf",
                port=0,
                types="trust",
                value="on",
            )
            self.ip_link_set(
                host_intf=self.host_intf_0,
                cmd="vf",
                port=0,
                types="spoofchk",
                value="off",
            )
            self.ip_link_set(
                host_intf=self.host_intf_1,
                cmd="vf",
                port=0,
                types="trust",
                value="on",
            )
            self.ip_link_set(
                host_intf=self.host_intf_1,
                cmd="vf",
                port=0,
                types="spoofchk",
                value="off",
            )

        self.dut.send_expect(
            "ip link set %s vf 0 mac 00:11:22:33:44:55" % self.pf0_intf, "#"
        )
        self.dut.send_expect(
            "ip link set %s vf 1 mac 00:11:22:33:44:66" % self.pf0_intf, "#"
        )
        self.dut.send_expect(
            "ip link set %s vf 0 mac 00:11:22:33:44:77" % self.pf1_intf, "#"
        )
        self.dut.send_expect(
            "ip link set %s vf 1 mac 00:11:22:33:44:88" % self.pf1_intf, "#"
        )

        # bind VF0 and VF1 to dpdk driver
        try:
            for vf_port in self.sriov_vfs_pf0:
                vf_port.bind_driver(self.vf_driver)
            for vf_port in self.sriov_vfs_pf1:
                vf_port.bind_driver(self.vf_driver)

        except Exception as e:
            self.destroy_env()
            raise Exception(e)
        out = self.dut.send_expect("./usertools/dpdk-devbind.py -s", "#")
        print(out)

    def setup_npf_nvf_env(self, pf_num=2, vf_num=2, driver="default"):

        # get PF interface name
        self.used_dut_port_0 = self.dut_ports[0]
        self.used_dut_port_1 = self.dut_ports[1]
        try:
            # generate vf on pf
            if pf_num == 1:
                self.dut.generate_sriov_vfs_by_port(
                    self.used_dut_port_0, vf_num, driver=driver
                )
                self.sriov_vfs_pf0 = self.dut.ports_info[self.used_dut_port_0][
                    "vfs_port"
                ]
                # bind VF0 and VF1 to dpdk driver
                for vf_port in self.sriov_vfs_pf0:
                    vf_port.bind_driver(self.vf_driver)
            else:
                self.dut.generate_sriov_vfs_by_port(
                    self.used_dut_port_0, vf_num, driver=driver
                )
                self.dut.generate_sriov_vfs_by_port(
                    self.used_dut_port_1, vf_num, driver=driver
                )
                self.sriov_vfs_pf0 = self.dut.ports_info[self.used_dut_port_0][
                    "vfs_port"
                ]
                self.sriov_vfs_pf1 = self.dut.ports_info[self.used_dut_port_1][
                    "vfs_port"
                ]
                for vf_port in self.sriov_vfs_pf0:
                    vf_port.bind_driver(self.vf_driver)
                for vf_port in self.sriov_vfs_pf1:
                    vf_port.bind_driver(self.vf_driver)

        except Exception as e:
            self.destroy_env()
            raise Exception(e)
        out = self.dut.send_expect("./usertools/dpdk-devbind.py -s", "#")
        print(out)

    def destroy_env(self):
        """
        This is to stop testpmd and destroy 1pf and 2vfs environment.
        """
        self.dut.send_expect("quit", "# ", 60)
        time.sleep(2)
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[1])

    def config_testpmd(self):
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("vlan set filter on 0")
        self.pmd_output.execute_cmd("rx_vlan add 1 0")
        # specify a fixed rss-hash-key for Intel® Ethernet 800 Series ether
        self.pmd_output.execute_cmd(
            "port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd"
        )
        self.pmd_output.execute_cmd(
            "port config 1 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd"
        )
        if self.running_case in [
            "test_mac_ipv4_pay_multicast",
            "test_mac_ipv4_multicast_protocol",
            "test_mac_ipv6_pay_multicast",
            "test_mac_ipv6_multicast_protocol",
        ]:
            self.pmd_output.execute_cmd("set promisc all off")
            self.pmd_output.execute_cmd("set allmulti all on")
            # add multicast mac address to pmd
            self.pmd_output.execute_cmd("mcast_addr add 0 11:22:33:44:55:66")
        res = self.pmd_output.wait_link_status_up("all", timeout=15)
        self.verify(res is True, "there have port link is down")
        self.pmd_output.execute_cmd("start")

    def launch_testpmd(self):
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param="--rxq={} --txq={}".format(self.q_num, self.q_num),
            eal_param="-a %s -a %s"
            % (self.sriov_vfs_pf0[0].pci, self.sriov_vfs_pf0[1].pci),
            socket=self.ports_socket,
        )
        self.config_testpmd()

    def send_packets(self, packets, pf_id=0, count=1):
        self.pkt.update_pkt(packets)
        tx_port = self.tester_iface0 if pf_id == 0 else self.tester_iface1
        self.pkt.send_pkt(crb=self.tester, tx_port=tx_port, count=count)

    def send_pkts_getouput(self, pkts, pf_id=0, count=1):
        """
        if pkt_info is True, we need to get packet infomation to check the RSS hash and FDIR.
        if pkt_info is False, we just need to get the packet number and queue number.
        """
        self.send_packets(pkts, pf_id, count)
        time.sleep(1)
        out_info = self.dut.get_session_output(timeout=1)
        out_pkt = self.pmd_output.execute_cmd("stop")
        out = out_info + out_pkt
        self.pmd_output.execute_cmd("start")
        return out

    def validate_fdir_rule(self, rule, check_stats=None):
        # validate rule.
        p = "Flow rule validated"
        rule_list = []
        if isinstance(rule, list):
            for i in rule:
                length = len(i)
                rule_rep = i[0:5] + "validate" + i[11:length]
                out = self.pmd_output.execute_cmd(rule_rep)
                if (p in out) and ("Failed" not in out):
                    rule_list.append(True)
                else:
                    rule_list.append(False)
        elif isinstance(rule, str):
            length = len(rule)
            rule_rep = rule[0:5] + "validate" + rule[11:length]
            out = self.pmd_output.execute_cmd(rule_rep)
            if (p in out) and ("Failed" not in out):
                rule_list.append(True)
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            self.verify(
                all(rule_list), "some rules validate failed, result %s" % rule_list
            )
        elif check_stats == False:
            self.verify(
                not any(rule_list),
                "all rules should validate failed, result %s" % rule_list,
            )

    def create_fdir_rule(self, rule, check_stats=None):
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        if isinstance(rule, list):
            for i in rule:
                out = self.pmd_output.execute_cmd(i)
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        elif isinstance(rule, str):
            out = self.pmd_output.execute_cmd(rule)
            m = p.search(out)
            if m:
                rule_list.append(m.group(1))
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            self.verify(
                all(rule_list), "some rules create failed, result %s" % rule_list
            )
        elif check_stats == False:
            self.verify(
                not any(rule_list),
                "all rules should create failed, result %s" % rule_list,
            )
        return rule_list

    def destroy_fdir_rule(self, rule_id, port_id=0):
        if isinstance(rule_id, list):
            for i in rule_id:
                out = self.pmd_output.execute_cmd(
                    "flow destroy %s rule %s" % (port_id, i)
                )
                p = re.compile(r"Flow rule #(\d+) destroyed")
                m = p.search(out)
                self.verify(m, "flow rule %s delete failed" % rule_id)
        else:
            out = self.pmd_output.execute_cmd(
                "flow destroy %s rule %s" % (port_id, rule_id)
            )
            p = re.compile(r"Flow rule #(\d+) destroyed")
            m = p.search(out)
            self.verify(m, "flow rule %s delete failed" % rule_id)

    def check_fdir_rule(self, port_id=0, stats=True, rule_list=None):
        out = self.pmd_output.execute_cmd("flow list %s" % port_id)
        p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
        if stats:
            self.verify(p.search(out), "flow rule on port %s is not existed" % port_id)
            if rule_list:
                p = re.compile("^(\d+)\s")
                li = out.splitlines()
                res = list(filter(bool, list(map(p.match, li))))
                result = [i.group(1) for i in res]
                self.verify(
                    sorted(result) == sorted(rule_list),
                    "check rule list failed. expect %s, result %s"
                    % (rule_list, result),
                )
        else:
            self.verify(not p.search(out), "flow rule on port %s is existed" % port_id)

    def check_rule_number(self, port_id=0, num=0):
        out = self.dut.send_command("flow list %s" % port_id, timeout=30)
        result_scanner = r"\d*.*?\d*.*?\d*.*?=>*"
        scanner = re.compile(result_scanner, re.DOTALL)
        li = scanner.findall(out)
        if num == 0:
            self.verify(not li, "there should be no rule listed")
        else:
            print(len(li))
            self.verify(len(li) == num, "the amount of rules is wrong.")
        return out

    def test_mac_ipv4_pay(self):
        self.rte_flow_process(vectors_ipv4_pay)

    def test_mac_ipv4_pay_multicast(self):
        self.rte_flow_process(vectors_ipv4_pay_multicast)

    def test_mac_ipv4_udp(self):
        self.rte_flow_process(vectors_ipv4_udp)

    def test_mac_ipv4_tcp(self):
        self.rte_flow_process(vectors_ipv4_tcp)

    def test_mac_ipv4_sctp(self):
        self.rte_flow_process(vectors_ipv4_sctp)

    def test_mac_ipv6_pay(self):
        self.rte_flow_process(vectors_ipv6_pay)

    def test_mac_ipv6_pay_multicast(self):
        self.rte_flow_process(vectors_ipv6_pay_multicast)

    def test_mac_ipv6_udp(self):
        self.rte_flow_process(vectors_ipv6_udp)

    def test_mac_ipv6_tcp(self):
        self.rte_flow_process(vectors_ipv6_tcp)

    def test_mac_ipv6_sctp(self):
        self.rte_flow_process(vectors_ipv6_sctp)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv4_gtpu_eh(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv4_gtpu(self):
        self.rte_flow_process(vectors_ipv4_gtpu)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv6_gtpu_eh(self):
        self.rte_flow_process(vectors_ipv6_gtpu_eh)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv6_gtpu(self):
        self.rte_flow_process(vectors_ipv6_gtpu)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_l2tpv3(self):
        self.rte_flow_process(vectors_ipv4_l2tpv3)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv6_l2tpv3(self):
        self.rte_flow_process(vectors_ipv6_l2tpv3)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv4_esp(self):
        self.rte_flow_process(vectors_ipv4_esp)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv6_esp(self):
        self.rte_flow_process(vectors_ipv6_esp)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv4_ah(self):
        self.rte_flow_process(vectors_ipv4_ah)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv6_ah(self):
        self.rte_flow_process(vectors_ipv6_ah)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv4_nat_t_esp(self):
        self.rte_flow_process(vectors_ipv4_nat_t_esp)

    @skip_unsupported_pkg("os default")
    def test_mac_ipv6_nat_t_esp(self):
        self.rte_flow_process(vectors_ipv6_nat_t_esp)

    def test_mac_ipv4_tcp_without_input_set(self):
        self.rte_flow_process(vectors_ipv4_tcp_without_input_set)

    def test_mac_ipv4_udp_without_input_set(self):
        self.rte_flow_process(vectors_ipv4_udp_without_input_set)

    def test_mac_ipv6_tcp_without_input_set(self):
        self.rte_flow_process(vectors_ipv6_tcp_without_input_set)

    def test_mac_ipv6_udp_without_input_set(self):
        self.rte_flow_process(vectors_ipv6_udp_without_input_set)

    def test_mac_ipv4_protocol(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 1 / end actions queue index 1 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 17 / end actions passthru / mark id 3 / end",
        ]

        # validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        # create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # pkt1 and pkt2 in "match" match rule 0, pkt3-6 match rule 1.
        out1 = self.send_pkts_getouput(MAC_IPV4_PAY_protocol["match"][0:2])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=2,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=True,
        )

        out2 = self.send_pkts_getouput(MAC_IPV4_PAY_protocol["match"][2:6])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=4,
            check_param={"port_id": 0, "mark_id": 3, "passthru": 1},
            stats=True,
        )

        # send mismatched packets:
        out3 = self.send_pkts_getouput(MAC_IPV4_PAY_protocol["mismatch"])
        rfc.check_iavf_fdir_mark(
            out3, pkt_num=4, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

        # destroy the rules and check there is no rule listed.
        self.destroy_fdir_rule(rule_id=rule_li, port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)

        # send matched packet
        out4 = self.send_pkts_getouput(MAC_IPV4_PAY_protocol["match"])
        rfc.check_iavf_fdir_mark(
            out4, pkt_num=6, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

    def test_mac_ipv4_multicast_protocol(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 dst is 224.0.0.1 proto is 1 / end actions queue index 1 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 dst is 224.0.0.1 proto is 17 / end actions passthru / mark id 3 / end",
        ]

        # validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        # create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # pkt1 and pkt2 in "match" match rule 0, pkt3-6 match rule 1.
        out1 = self.send_pkts_getouput(MAC_IPV4_PAY_multicast_protocol["match"][0:2])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=2,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=True,
        )

        out2 = self.send_pkts_getouput(MAC_IPV4_PAY_multicast_protocol["match"][2:6])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=4,
            check_param={"port_id": 0, "mark_id": 3, "passthru": 1},
            stats=True,
        )

        # send mismatched packets:
        out3 = self.send_pkts_getouput(MAC_IPV4_PAY_multicast_protocol["mismatch"])
        rfc.check_iavf_fdir_mark(
            out3, pkt_num=4, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

        # destroy the rules and check there is no rule listed.
        self.destroy_fdir_rule(rule_id=rule_li, port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)

        # send matched packet
        out4 = self.send_pkts_getouput(MAC_IPV4_PAY_multicast_protocol["match"])
        rfc.check_iavf_fdir_mark(
            out4, pkt_num=6, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

    def test_mac_ipv6_protocol(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 17 / end actions rss queues 5 6 end / mark id 0 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 6 / end actions mark id 2 / rss / end",
        ]

        # validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        # create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # pkt1-4 in "match" match rule 0, pkt5-6 match rule 1.
        out1 = self.send_pkts_getouput(MAC_IPV6_PAY_protocol["match"][0:4])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=4,
            check_param={"port_id": 0, "mark_id": 0, "queue": [5, 6]},
            stats=True,
        )

        out2 = self.send_pkts_getouput(MAC_IPV6_PAY_protocol["match"][4:6])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=2,
            check_param={"port_id": 0, "mark_id": 2, "passthru": 1},
            stats=True,
        )

        # send mismatched packets:
        out3 = self.send_pkts_getouput(MAC_IPV6_PAY_protocol["mismatch"])
        rfc.check_iavf_fdir_mark(
            out3, pkt_num=3, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

        # destroy the rules and check there is no rule listed.
        self.destroy_fdir_rule(rule_id=rule_li, port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)

        # send matched packet
        out4 = self.send_pkts_getouput(MAC_IPV6_PAY_protocol["match"])
        rfc.check_iavf_fdir_mark(
            out4, pkt_num=6, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

    def test_mac_ipv6_multicast_protocol(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv6 dst is ff01::2 proto is 17 / end actions rss queues 5 6 end / mark id 0 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is ff01::2 proto is 6 / end actions mark id 2 / rss / end",
        ]

        # validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        # create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # pkt1-4 in "match" match rule 0, pkt5-6 match rule 1.
        out1 = self.send_pkts_getouput(MAC_IPV6_PAY_multicast_protocol["match"][0:4])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=4,
            check_param={"port_id": 0, "mark_id": 0, "queue": [5, 6]},
            stats=True,
        )

        out2 = self.send_pkts_getouput(MAC_IPV6_PAY_multicast_protocol["match"][4:6])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=2,
            check_param={"port_id": 0, "mark_id": 2, "passthru": 1},
            stats=True,
        )

        # send mismatched packets:
        out3 = self.send_pkts_getouput(MAC_IPV6_PAY_multicast_protocol["mismatch"])
        rfc.check_iavf_fdir_mark(
            out3, pkt_num=3, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

        # destroy the rules and check there is no rule listed.
        self.destroy_fdir_rule(rule_id=rule_li, port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)

        # send matched packet
        out4 = self.send_pkts_getouput(MAC_IPV6_PAY_multicast_protocol["match"])
        rfc.check_iavf_fdir_mark(
            out4, pkt_num=6, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

    @skip_unsupported_pkg("os default")
    def test_mac_ipv4_gtpu_eh_without_teid(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 3 / end",
        ]
        MAC_IPV4_GTPU_EH_WITHOUT_TEID = {
            "match": 'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/TCP()/Raw("x"*20)',
            "mismatch": 'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTPPDUSessionContainer(type=1,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)',
        }
        # validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        # create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # send matched packet
        out1 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_TEID["match"])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 1},
            stats=True,
        )

        # send mismatched packets:
        out2 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_TEID["mismatch"])
        rfc.check_iavf_fdir_mark(
            out2, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

        # destroy the rules and check there is no rule listed.
        self.destroy_fdir_rule(rule_id=rule_li, port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)

        open_rss_rule = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end"
        rule_li = self.create_fdir_rule(open_rss_rule, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # send matched packet
        out3 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_TEID["match"])
        rfc.check_iavf_fdir_mark(
            out3, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

    @skip_unsupported_pkg("os default")
    def test_mac_ipv4_gtpu_eh_without_qfi(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / end actions rss queues 2 3 end / mark id 1 / end",
        ]
        MAC_IPV4_GTPU_EH_WITHOUT_QFI = {
            "match": 'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1)/IP()/UDP()/Raw("x"*20)',
            "mismatch": 'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=1, P=1)/IP()/UDP()/Raw("x"*20)',
        }
        # validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        # create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # send matched packet
        out1 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_QFI["match"])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": [2, 3]},
            stats=True,
        )

        # send mismatched packets:
        out2 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_QFI["mismatch"])
        rfc.check_iavf_fdir_mark(
            out2, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

        # destroy the rules and check there is no rule listed.
        self.destroy_fdir_rule(rule_id=rule_li, port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)

        open_rss_rule = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end"
        rule_li = self.create_fdir_rule(open_rss_rule, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # send matched packet
        out3 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_QFI["match"])
        rfc.check_iavf_fdir_mark(
            out3, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=False
        )

    def run_coexist_outer_gtpu(self, rules, pkts):

        # validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        # create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # send matched packet, check action
        out0 = self.send_pkts_getouput(pkts["match"][0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": [1, 2]},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts["match"][1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": [3, 4, 5, 6]},
            stats=True,
        )
        out2 = self.send_pkts_getouput(pkts["match"][2])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 7},
            stats=True,
        )
        out3 = self.send_pkts_getouput(pkts["match"][3])
        rfc.check_iavf_fdir_mark(
            out3,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 4, "queue": 8},
            stats=True,
        )
        out4 = self.send_pkts_getouput(pkts["match"][4])
        rfc.check_iavf_fdir_mark(
            out4,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 5, "passthru": True},
            stats=True,
        )
        out5 = self.send_pkts_getouput(pkts["match"][5])
        rfc.check_iavf_fdir_mark(
            out5,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 6, "passthru": True},
            stats=True,
        )
        out6 = self.send_pkts_getouput(pkts["match"][6])
        rfc.check_iavf_fdir_mark(
            out6, pkt_num=1, check_param={"port_id": 0, "drop": True}, stats=True
        )
        out7 = self.send_pkts_getouput(pkts["match"][7])
        rfc.check_iavf_fdir_mark(
            out7, pkt_num=1, check_param={"port_id": 0, "drop": True}, stats=True
        )

        # send mismatched packet, check not do match action
        out0 = self.send_pkts_getouput(pkts["mismatch"][0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": [1, 2]},
            stats=False,
        )
        out1 = self.send_pkts_getouput(pkts["mismatch"][1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": [3, 4, 5, 6]},
            stats=False,
        )
        out2 = self.send_pkts_getouput(pkts["mismatch"][2])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 7},
            stats=False,
        )
        out3 = self.send_pkts_getouput(pkts["mismatch"][3])
        rfc.check_iavf_fdir_mark(
            out3,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 4, "queue": 8},
            stats=False,
        )
        out4 = self.send_pkts_getouput(pkts["mismatch"][4])
        rfc.check_iavf_fdir_mark(
            out4,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 5, "passthru": True},
            stats=False,
        )
        out5 = self.send_pkts_getouput(pkts["mismatch"][5])
        rfc.check_iavf_fdir_mark(
            out5,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 6, "passthru": True},
            stats=False,
        )
        out6 = self.send_pkts_getouput(pkts["mismatch"][6])
        rfc.check_iavf_fdir_mark(
            out6, pkt_num=1, check_param={"port_id": 0, "drop": True}, stats=False
        )
        out7 = self.send_pkts_getouput(pkts["mismatch"][7])
        rfc.check_iavf_fdir_mark(
            out7, pkt_num=1, check_param={"port_id": 0, "drop": True}, stats=False
        )

    @skip_unsupported_pkg("os default")
    def test_mac_outer_co_exist_gtpu_eh_dst(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.31 / udp / gtpu / gtp_psc / end actions rss queues 1 2 end / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is ::32 / udp / gtpu / gtp_psc / end actions rss queues 3 4 5 6 end / mark id 2 / end",
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.33 / udp / gtpu / gtp_psc / end actions queue index 7 / mark id 3 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is ::14 / udp / gtpu / gtp_psc / end actions queue index 8 / mark id 4 / end",
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.35 / udp / gtpu / gtp_psc / end actions passthru / mark id 5 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is ::36 / udp / gtpu / gtp_psc / end actions passthru / mark id 6 / end",
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.37 / udp / gtpu / gtp_psc / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv6 dst is ::38 / udp / gtpu / gtp_psc / end actions drop / end",
        ]
        MAC_GTPU_EH = {
            "match": [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/UDP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IP()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IP()/ICMP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
            ],
            "mismatch": [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/UDP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.34")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::15")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IP()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IP()/ICMP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::39")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
            ],
        }
        self.run_coexist_outer_gtpu(rules, MAC_GTPU_EH)

    @skip_unsupported_pkg("os default")
    def test_mac_outer_co_exist_gtpu_dst(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.31 / udp / gtpu / end actions rss queues 1 2 end / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is ::32 / udp / gtpu / end actions rss queues 3 4 5 6 end / mark id 2 / end",
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.33 / udp / gtpu / end actions queue index 7 / mark id 3 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is ::14 / udp / gtpu / end actions queue index 8 / mark id 4 / end",
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.35 / udp / gtpu / end actions passthru / mark id 5 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is ::36 / udp / gtpu / end actions passthru / mark id 6 / end",
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.37 / udp / gtpu / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv6 dst is ::38 / udp / gtpu / end actions drop / end",
        ]
        MAC_GTPU = {
            "match": [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/UDP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
            ],
            "mismatch": [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/UDP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.34")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::15")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::39")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
            ],
        }
        self.run_coexist_outer_gtpu(rules, MAC_GTPU)

    @skip_unsupported_pkg("os default")
    def test_mac_outer_co_exist_gtpu_eh_src(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.21 / udp / gtpu / gtp_psc / end actions rss queues 1 2 end / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv6 src is ::12 / udp / gtpu / gtp_psc / end actions rss queues 3 4 5 6 end / mark id 2 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.23 / udp / gtpu / gtp_psc / end actions queue index 7 / mark id 3 / end",
            "flow create 0 ingress pattern eth / ipv6 src is 2001::4 / udp / gtpu / gtp_psc / end actions queue index 8 / mark id 4 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.25 / udp / gtpu / gtp_psc / end actions passthru / mark id 5 / end",
            "flow create 0 ingress pattern eth / ipv6 src is ::16 / udp / gtpu / gtp_psc / end actions passthru / mark id 6 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.27 / udp / gtpu / gtp_psc / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv6 src is 2001::8 / udp / gtpu / gtp_psc / end actions drop / end",
        ]
        MAC_GTPU_EH = {
            "match": [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/UDP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IP()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IP()/ICMP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
            ],
            "mismatch": [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.22", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/UDP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::13", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.24", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::5", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IP()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.26", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::17", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IP()/ICMP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.28", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::9", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
            ],
        }
        self.run_coexist_outer_gtpu(rules, MAC_GTPU_EH)

    @skip_unsupported_pkg("os default")
    def test_mac_outer_co_exist_gtpu_src(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.21 / udp / gtpu / end actions rss queues 1 2 end / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv6 src is ::12 / udp / gtpu / end actions rss queues 3 4 5 6 end / mark id 2 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.23 / udp / gtpu / end actions queue index 7 / mark id 3 / end",
            "flow create 0 ingress pattern eth / ipv6 src is 2001::4 / udp / gtpu / end actions queue index 8 / mark id 4 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.25 / udp / gtpu / end actions passthru / mark id 5 / end",
            "flow create 0 ingress pattern eth / ipv6 src is ::16 / udp / gtpu / end actions passthru / mark id 6 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.27 / udp / gtpu / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv6 src is 2001::8 / udp / gtpu / end actions drop / end",
        ]
        MAC_GTPU = {
            "match": [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/UDP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
            ],
            "mismatch": [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.22", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/UDP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::13", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.24", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::5", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.26", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::17", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.28", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::9", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
            ],
        }
        self.run_coexist_outer_gtpu(rules, MAC_GTPU)

    @skip_unsupported_pkg("os default")
    def test_mac_outer_co_exist_gtpu_mix(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.21 dst is 192.168.0.31 / udp / gtpu / gtp_psc / end actions rss queues 1 2 end / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv6 src is ::12 dst is ::32 / udp / gtpu / gtp_psc / end actions rss queues 3 4 5 6 end / mark id 2 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.23 dst is 192.168.0.33 / udp / gtpu / gtp_psc / end actions queue index 7 / mark id 3 / end",
            "flow create 0 ingress pattern eth / ipv6 src is 2001::4 dst is ::14 / udp / gtpu / gtp_psc / end actions queue index 8 / mark id 4 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.25 dst is 192.168.0.35 / udp / gtpu / end actions passthru / mark id 5 / end",
            "flow create 0 ingress pattern eth / ipv6 src is ::16 dst is ::36 / udp / gtpu / end actions passthru / mark id 6 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.27 dst is 192.168.0.37 / udp / gtpu / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv6 src is 2001::8 dst is ::38 / udp / gtpu / end actions drop / end",
        ]
        MAC_GTPU_MIX = {
            "match": [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/UDP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IP()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
            ],
            "mismatch": [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.22", dst="192.168.0.32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IPv6()/UDP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::13", dst="::33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.24", dst="192.168.0.34")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=1, QFI=0x33)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::5", dst="::15")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTPPDUSessionContainer(type=0, QFI=0x33)/IP()/TCP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.26", dst="192.168.0.36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::17", dst="::37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.28", dst="192.168.0.38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::9", dst="::39")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
            ],
        }

        self.run_coexist_outer_gtpu(rules, MAC_GTPU_MIX)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_pfcp(self):
        # open the RSS function for PFCP session packet.
        out = self.pmd_output.execute_cmd(
            "flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end"
        )
        self.verify(
            "Flow rule #0 created" in out,
            "failed to enable RSS function for MAC_IPV4_PFCP session packet",
        )
        out = self.pmd_output.execute_cmd(
            "flow create 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end"
        )
        self.verify(
            "Flow rule #1 created" in out,
            "failed to enable RSS function for MAC_IPV6_PFCP session packet",
        )
        self.multirules_process(vectors_pfcp)

    @skip_unsupported_pkg("os default")
    def test_l2_ethertype(self):
        self.multirules_process(vectors_l2_ethertype)

    def test_negative_case(self):
        """
        negative cases
        """
        rules = {
            "invalid parameters of queue index": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 16 / end",
            "invalid parameters of rss queues": [
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 end / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues end / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 15 16 end / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 end / end",
            ],
            "invalid mark id": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / mark id 4294967296 / end",
            "invalid parameters of GTPU input set": [
                "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x100 / end actions queue index 1 / end",
                "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc qfi is 0x5 / end actions queue index 2 / end",
                "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / end actions queue index 1 / end",
            ],
            "unsupported type of L2 ethertype": [
                "flow create 0 ingress pattern eth type is 0x0800 / end actions queue index 1 / end",
                "flow create 0 ingress pattern eth type is 0x86dd / end actions queue index 1 / end",
            ],
            "conflicted actions": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / rss queues 2 3 end / end",
            "void action": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions end",
            "unsupported action": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions count / end",
            "unsupported input set field": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tc is 2 / end actions queue index 1 / end",
            "void input set value": "flow create 0 ingress pattern eth / ipv4 / end actions queue index 1 / end",
            "invalid port": "flow create 2 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end",
        }
        # all the rules failed to create and validate
        self.validate_fdir_rule(
            rules["invalid parameters of queue index"], check_stats=False
        )
        self.create_fdir_rule(
            rules["invalid parameters of queue index"], check_stats=False
        )
        self.validate_fdir_rule(
            rules["invalid parameters of rss queues"], check_stats=False
        )
        self.create_fdir_rule(
            rules["invalid parameters of rss queues"], check_stats=False
        )
        self.validate_fdir_rule(
            rules["invalid parameters of GTPU input set"], check_stats=False
        )
        self.create_fdir_rule(
            rules["invalid parameters of GTPU input set"], check_stats=False
        )
        self.validate_fdir_rule(
            rules["unsupported type of L2 ethertype"], check_stats=False
        )
        self.create_fdir_rule(
            rules["unsupported type of L2 ethertype"], check_stats=False
        )
        self.validate_fdir_rule(rules["conflicted actions"], check_stats=False)
        self.create_fdir_rule(rules["conflicted actions"], check_stats=False)
        self.validate_fdir_rule(rules["void action"], check_stats=False)
        self.create_fdir_rule(rules["void action"], check_stats=False)
        self.validate_fdir_rule(rules["unsupported input set field"], check_stats=False)
        self.create_fdir_rule(rules["unsupported input set field"], check_stats=False)
        self.validate_fdir_rule(rules["void input set value"], check_stats=False)
        self.create_fdir_rule(rules["void input set value"], check_stats=False)
        self.validate_fdir_rule(rules["invalid port"], check_stats=False)
        self.create_fdir_rule(rules["invalid port"], check_stats=False)

        # check there is no rule listed
        self.check_fdir_rule(port_id=0, stats=False)
        self.check_fdir_rule(port_id=1, stats=False)

        # duplicated rules
        rule = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end"
        self.create_fdir_rule(rule, check_stats=True)
        self.create_fdir_rule(rule, check_stats=False)
        self.pmd_output.execute_cmd("flow destroy 0 rule 0")

        # conflict rules
        rule = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end"
        self.create_fdir_rule(rule, check_stats=True)
        rule1 = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 2 / end"
        self.create_fdir_rule(rule1, check_stats=False)
        rule2 = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions drop / end"
        self.create_fdir_rule(rule2, check_stats=False)
        self.create_fdir_rule(rule2, check_stats=False)
        self.pmd_output.execute_cmd("flow destroy 0 rule 0", timeout=1)
        rule3 = "flow create 0 ingress pattern eth / ipv4 / tcp / end actions queue index 1 / end"
        self.create_fdir_rule(rule3, check_stats=True)
        rule4 = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp / end actions queue index 1 / end"
        self.create_fdir_rule(rule4, check_stats=False)
        self.pmd_output.execute_cmd("flow destroy 0 rule 0", timeout=1)

        # delete a non-existent rule
        out1 = self.pmd_output.execute_cmd("flow destroy 0 rule 0")
        self.verify("error" not in out1, "there shouldn't report error message")
        out2 = self.pmd_output.execute_cmd("flow destroy 2 rule 0")
        self.verify("Invalid port" in out2, "there should report error message")
        out3 = self.pmd_output.execute_cmd("flow flush 2")
        self.verify("Invalid port" in out3, "port 2 doesn't exist.")
        out4 = self.pmd_output.execute_cmd("flow list 2")
        self.verify("Invalid port" in out4, "port 2 doesn't exist.")

        self.check_fdir_rule(port_id=0, stats=False)
        self.check_fdir_rule(port_id=1, stats=False)

    @skip_unsupported_pkg(["comms", "wireless"])
    def test_unsupported_pattern_with_OS_package(self):
        """
        Create GTPU rule, PFCP rule, L2 Ethertype rule, l2tpv3 rule and esp rule with OS default package
        """
        rule = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions rss queues 1 2 end / mark id 6 / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / esp spi is 6 / end actions rss queues 1 2 end / mark id 6 / end",
        ]
        self.launch_testpmd()
        self.validate_fdir_rule(rule, check_stats=False)
        self.create_fdir_rule(rule, check_stats=False)
        self.check_fdir_rule(port_id=0, stats=False)

    def test_create_same_rule_on_pf_vf(self):
        """
        create same rules on pf and vf, no conflict
        """
        self.pmd_output.quit()
        self.session_secondary = self.dut.new_session()
        self.session_third = self.dut.new_session()

        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end",
        ]
        pkts = {
            "matched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
            ],
            "mismatched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
            ],
            "pf": [
                'Ether(dst="%s")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)'
                % self.pf0_mac,
                'Ether(dst="%s")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)'
                % self.pf1_mac,
            ],
        }
        out_pf0 = self.dut.send_expect(
            "ethtool -N %s flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1"
            % self.pf0_intf,
            "# ",
        )
        out_pf1 = self.dut.send_expect(
            "ethtool -N %s flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1"
            % self.pf1_intf,
            "# ",
        )
        p = re.compile(r"Added rule with ID (\d+)")
        m0 = p.search(out_pf0)
        m1 = p.search(out_pf1)

        eal_param = "-c 0xf -n 6 -a %s -a %s --file-prefix=pf0" % (
            self.sriov_vfs_pf0[0].pci,
            self.sriov_vfs_pf0[1].pci,
        )
        command = (
            self.path
            + eal_param
            + " -- -i --rxq=%s --txq=%s" % (self.q_num, self.q_num)
        )
        self.dut.send_expect(command, "testpmd> ", 300)
        self.config_testpmd()

        eal_param = "-c 0xf0 -n 6 -a %s -a %s --file-prefix=pf1" % (
            self.sriov_vfs_pf1[0].pci,
            self.sriov_vfs_pf1[1].pci,
        )
        command = (
            self.path
            + eal_param
            + " -- -i --rxq=%s --txq=%s" % (self.q_num, self.q_num)
        )
        self.session_secondary.send_expect(command, "testpmd> ", 300)
        # self.session_secondary.config_testpmd()
        self.session_secondary.send_expect("set fwd rxonly", "testpmd> ")
        self.session_secondary.send_expect("set verbose 1", "testpmd> ")
        # specify a fixed rss-hash-key for Intel® Ethernet 800 Series ether
        self.session_secondary.send_expect(
            "port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd",
            "testpmd> ",
        )
        self.session_secondary.send_expect(
            "port config 1 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd",
            "testpmd> ",
        )
        self.session_secondary.send_expect("start", "testpmd> ")

        self.create_fdir_rule(rules, check_stats=True)
        self.session_secondary.send_expect(
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end",
            "created",
        )
        self.session_secondary.send_expect(
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end",
            "created",
        )

        # confirm pf link is up
        self.session_third.send_expect("ifconfig %s up" % self.pf0_intf, "# ", 15)
        self.session_third.send_expect("ifconfig %s up" % self.pf1_intf, "# ", 15)
        time.sleep(1)

        # send matched packets
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0)
        )
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1)
        )
        self.tester.scapy_execute()
        time.sleep(1)
        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify(
            "rx_queue_1_packets: 1" in out_pf0,
            "the packet is not redirected to expected queue of pf0",
        )
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify(
            "rx_queue_1_packets: 1" in out_pf1,
            "the packet is not redirected to expected queue of pf1",
        )

        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(
            out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=True
        )
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(
            out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=True
        )

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf10, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=True
        )

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf11, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=True
        )

        # send mismatched packets
        out_vf00 = self.send_pkts_getouput(pkts["mismatched"][0])
        rfc.check_iavf_fdir_mark(
            out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=False
        )
        out_vf01 = self.send_pkts_getouput(pkts["mismatched"][1])
        rfc.check_iavf_fdir_mark(
            out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=False
        )

        self.send_packets(pkts["mismatched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf10, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=False
        )

        self.send_packets(pkts["mismatched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf11, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=False
        )

        # flush all the rules
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.dut.send_expect("flow flush 1", "testpmd> ")
        self.session_secondary.send_expect("flow flush 0", "testpmd> ")
        self.session_secondary.send_expect("flow flush 1", "testpmd> ")

        self.session_third.send_expect(
            "ethtool -N %s delete %d" % (self.pf0_intf, int(m0.group(1))), "# "
        )
        self.session_third.send_expect(
            "ethtool -N %s delete %d" % (self.pf1_intf, int(m1.group(1))), "# "
        )
        self.session_third.send_expect(
            "ethtool -n %s" % (self.pf0_intf), "Total 0 rules"
        )
        self.session_third.send_expect(
            "ethtool -n %s" % (self.pf1_intf), "Total 0 rules"
        )

        # send matched packets
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0)
        )
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1)
        )
        self.tester.scapy_execute()

        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify(
            "rx_queue_1_packets: 1" in out_pf0,
            "the packet is redirected to expected queue of pf0",
        )
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify(
            "rx_queue_1_packets: 1" in out_pf1,
            "the packet is redirected to expected queue of pf1",
        )

        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(
            out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=False
        )
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(
            out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=False
        )

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf10, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=False
        )

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf11, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=False
        )

        self.dut.close_session(self.session_secondary)
        self.dut.close_session(self.session_third)

    def test_create_same_input_diff_action_on_pf_vf(self):
        """
        create same input set but different action rules on pf and vf, no conflict.
        """
        self.pmd_output.quit()
        self.session_secondary = self.dut.new_session()
        self.session_third = self.dut.new_session()

        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 3 4 end / mark / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
        ]
        pkts = {
            "matched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
            ],
            "mismatched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
            ],
            "pf": [
                'Ether(dst="%s")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)'
                % self.pf0_mac,
                'Ether(dst="%s")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)'
                % self.pf1_mac,
            ],
        }
        out_pf0 = self.dut.send_expect(
            "ethtool -N %s flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1"
            % self.pf0_intf,
            "# ",
        )
        out_pf1 = self.dut.send_expect(
            "ethtool -N %s flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 2"
            % self.pf1_intf,
            "# ",
        )
        p = re.compile(r"Added rule with ID (\d+)")
        m0 = p.search(out_pf0)
        m1 = p.search(out_pf1)

        eal_param = "-c 0xf -n 6 -a %s -a %s --file-prefix=pf0" % (
            self.sriov_vfs_pf0[0].pci,
            self.sriov_vfs_pf0[1].pci,
        )
        command = (
            self.path
            + eal_param
            + " -- -i --rxq=%s --txq=%s" % (self.q_num, self.q_num)
        )
        self.dut.send_expect(command, "testpmd> ", 300)
        self.config_testpmd()

        eal_param = "-c 0xf0 -n 6 -a %s -a %s --file-prefix=pf1" % (
            self.sriov_vfs_pf1[0].pci,
            self.sriov_vfs_pf1[1].pci,
        )
        command = (
            self.path
            + eal_param
            + " -- -i --rxq=%s --txq=%s" % (self.q_num, self.q_num)
        )
        self.session_secondary.send_expect(command, "testpmd> ", 300)
        # self.session_secondary.config_testpmd()
        self.session_secondary.send_expect("set fwd rxonly", "testpmd> ")
        self.session_secondary.send_expect("set verbose 1", "testpmd> ")
        # specify a fixed rss-hash-key for Intel® Ethernet 800 Series ether
        self.session_secondary.send_expect(
            "port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd",
            "testpmd> ",
        )
        self.session_secondary.send_expect(
            "port config 1 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd",
            "testpmd> ",
        )
        self.session_secondary.send_expect("start", "testpmd> ")

        self.create_fdir_rule(rules[:2], check_stats=True)
        self.session_secondary.send_expect(rules[2], "created")
        self.session_secondary.send_expect(rules[3], "created")

        # confirm pf link is up
        self.session_third.send_expect("ifconfig %s up" % self.pf0_intf, "# ", 15)
        self.session_third.send_expect("ifconfig %s up" % self.pf1_intf, "# ", 15)
        time.sleep(1)

        # send matched packets
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0)
        )
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1)
        )
        self.tester.scapy_execute()
        time.sleep(1)
        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify(
            "rx_queue_1_packets: 1" in out_pf0,
            "the packet is not redirected to expected queue of pf0",
        )
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify(
            "rx_queue_2_packets: 1" in out_pf1,
            "the packet is not redirected to expected queue of pf1",
        )

        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(
            out_vf00,
            pkt_num=1,
            check_param={"port_id": 0, "queue": 1, "mark_id": 1},
            stats=True,
        )
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(
            out_vf01,
            pkt_num=1,
            check_param={"port_id": 1, "queue": [3, 4], "mark_id": 0},
            stats=True,
        )

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf10, pkt_num=1, check_param={"port_id": 0, "drop": 1}, stats=True
        )

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf11,
            pkt_num=1,
            check_param={"port_id": 1, "passthru": 1, "mark_id": 1},
            stats=True,
        )

        # send mismatched packets
        out_vf00 = self.send_pkts_getouput(pkts["mismatched"][0])
        rfc.check_iavf_fdir_mark(
            out_vf00,
            pkt_num=1,
            check_param={"port_id": 0, "queue": 1, "mark_id": 1},
            stats=False,
        )
        out_vf01 = self.send_pkts_getouput(pkts["mismatched"][1])
        rfc.check_iavf_fdir_mark(
            out_vf01,
            pkt_num=1,
            check_param={"port_id": 1, "queue": [3, 4], "mark_id": 0},
            stats=False,
        )

        self.send_packets(pkts["mismatched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf10, pkt_num=1, check_param={"port_id": 0, "drop": 1}, stats=False
        )

        self.send_packets(pkts["mismatched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf11,
            pkt_num=1,
            check_param={"port_id": 1, "passthru": 1, "mark_id": 1},
            stats=False,
        )

        # flush all the rules
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.dut.send_expect("flow flush 1", "testpmd> ")
        self.session_secondary.send_expect("flow flush 0", "testpmd> ")
        self.session_secondary.send_expect("flow flush 1", "testpmd> ")

        self.session_third.send_expect(
            "ethtool -N %s delete %d" % (self.pf0_intf, int(m0.group(1))), "# "
        )
        self.session_third.send_expect(
            "ethtool -N %s delete %d" % (self.pf1_intf, int(m1.group(1))), "# "
        )
        self.session_third.send_expect(
            "ethtool -n %s" % (self.pf0_intf), "Total 0 rules"
        )
        self.session_third.send_expect(
            "ethtool -n %s" % (self.pf1_intf), "Total 0 rules"
        )

        # send matched packets
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0)
        )
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1)
        )
        self.tester.scapy_execute()

        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify(
            "rx_queue_1_packets: 1" in out_pf0,
            "the packet is redirected to expected queue of pf0",
        )
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify(
            "rx_queue_2_packets: 1" in out_pf1,
            "the packet is redirected to expected queue of pf1",
        )

        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(
            out_vf00,
            pkt_num=1,
            check_param={"port_id": 0, "queue": 1, "mark_id": 1},
            stats=False,
        )
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(
            out_vf01,
            pkt_num=1,
            check_param={"port_id": 1, "queue": [3, 4], "mark_id": 0},
            stats=False,
        )

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf10, pkt_num=1, check_param={"port_id": 0, "drop": 1}, stats=False
        )

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf11,
            pkt_num=1,
            check_param={"port_id": 1, "passthru": 1, "mark_id": 1},
            stats=False,
        )

        self.dut.close_session(self.session_secondary)
        self.dut.close_session(self.session_third)

    def test_create_diff_input_diff_action_on_pf_vf(self):
        """
        create different rules on pf and vf
        """
        self.pmd_output.quit()
        self.session_secondary = self.dut.new_session()
        self.session_third = self.dut.new_session()

        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.22 dst is 192.168.0.23 / udp src is 22 dst is 23 / end actions queue index 6 / mark / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.22 dst is 192.168.0.23 / udp src is 22 dst is 23 / end actions queue index 6 / mark id 1 / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.22 dst is 192.168.0.23 tos is 4 / tcp src is 22 dst is 23 / end actions drop / end",
        ]
        pkts = {
            "matched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.22",dst="192.168.0.23")/UDP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.22",dst="192.168.0.23")/UDP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.22",dst="192.168.0.23",tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            ],
            "mismatched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
            ],
            "pf": [
                'Ether(dst="%s")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)'
                % self.pf0_mac,
                'Ether(dst="%s")/IP(src="192.168.0.22",dst="192.168.0.23")/UDP(sport=22,dport=23)/Raw("x" * 80)'
                % self.pf1_mac,
            ],
        }
        out_pf0 = self.dut.send_expect(
            "ethtool -N %s flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1"
            % self.pf0_intf,
            "# ",
        )
        out_pf1 = self.dut.send_expect(
            "ethtool -N %s flow-type udp4 src-ip 192.168.0.22 dst-ip 192.168.0.23 src-port 22 dst-port 23 action -1"
            % self.pf1_intf,
            "# ",
        )
        p = re.compile(r"Added rule with ID (\d+)")
        m0 = p.search(out_pf0)
        m1 = p.search(out_pf1)

        eal_param = "-c 0xf -n 6 -a %s -a %s --file-prefix=pf0" % (
            self.sriov_vfs_pf0[0].pci,
            self.sriov_vfs_pf0[1].pci,
        )
        command = (
            self.path
            + eal_param
            + " -- -i --rxq=%s --txq=%s" % (self.q_num, self.q_num)
        )
        self.dut.send_expect(command, "testpmd> ", 300)
        self.config_testpmd()

        eal_param = "-c 0xf0 -n 6 -a %s -a %s --file-prefix=pf1" % (
            self.sriov_vfs_pf1[0].pci,
            self.sriov_vfs_pf1[1].pci,
        )
        command = (
            self.path
            + eal_param
            + " -- -i --rxq=%s --txq=%s" % (self.q_num, self.q_num)
        )
        self.session_secondary.send_expect(command, "testpmd> ", 300)
        # self.session_secondary.config_testpmd()
        self.session_secondary.send_expect("set fwd rxonly", "testpmd> ")
        self.session_secondary.send_expect("set verbose 1", "testpmd> ")
        # specify a fixed rss-hash-key for Intel® Ethernet 800 Series ether
        self.session_secondary.send_expect(
            "port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd",
            "testpmd> ",
        )
        self.session_secondary.send_expect(
            "port config 1 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd",
            "testpmd> ",
        )
        self.session_secondary.send_expect("start", "testpmd> ")

        self.create_fdir_rule(rules[:2], check_stats=True)
        self.session_secondary.send_expect(rules[2], "created")
        self.session_secondary.send_expect(rules[3], "created")

        # confirm pf link is up
        self.session_third.send_expect("ifconfig %s up" % self.pf0_intf, "# ", 15)
        self.session_third.send_expect("ifconfig %s up" % self.pf1_intf, "# ", 15)
        time.sleep(1)

        # send matched packets
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0)
        )
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1)
        )
        self.tester.scapy_execute()
        time.sleep(1)

        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify(
            "rx_queue_1_packets: 1" in out_pf0,
            "the packet is not redirected to expected queue of pf0",
        )
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify("rx_dropped: 1" in out_pf1, "the packet is not dropped pf1")

        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(
            out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": [2, 3]}, stats=True
        )
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(
            out_vf01,
            pkt_num=1,
            check_param={"port_id": 1, "queue": 6, "mark_id": 0},
            stats=True,
        )

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf10,
            pkt_num=1,
            check_param={"port_id": 0, "queue": 6, "mark_id": 1},
            stats=True,
        )

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf11, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=True
        )

        # send mismatched packets
        out_vf00 = self.send_pkts_getouput(pkts["mismatched"][0])
        rfc.check_iavf_fdir_mark(
            out_vf00,
            pkt_num=1,
            check_param={"port_id": 0, "queue": [2, 3]},
            stats=False,
        )
        out_vf01 = self.send_pkts_getouput(pkts["mismatched"][1])
        rfc.check_iavf_fdir_mark(
            out_vf01,
            pkt_num=1,
            check_param={"port_id": 1, "queue": 6, "mark_id": 0},
            stats=False,
        )

        self.send_packets(pkts["mismatched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf10,
            pkt_num=1,
            check_param={"port_id": 0, "queue": 6, "mark_id": 1},
            stats=False,
        )

        self.send_packets(pkts["mismatched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf11, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=False
        )

        # flush all the rules
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.dut.send_expect("flow flush 1", "testpmd> ")
        self.session_secondary.send_expect("flow flush 0", "testpmd> ")
        self.session_secondary.send_expect("flow flush 1", "testpmd> ")

        self.session_third.send_expect(
            "ethtool -N %s delete %d" % (self.pf0_intf, int(m0.group(1))), "# "
        )
        self.session_third.send_expect(
            "ethtool -N %s delete %d" % (self.pf1_intf, int(m1.group(1))), "# "
        )
        self.session_third.send_expect(
            "ethtool -n %s" % (self.pf0_intf), "Total 0 rules"
        )
        self.session_third.send_expect(
            "ethtool -n %s" % (self.pf1_intf), "Total 0 rules"
        )

        # send matched packets
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0)
        )
        self.tester.scapy_append(
            'sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1)
        )
        self.tester.scapy_execute()

        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify("rx_queue_1_packets: 1" in out_pf0, "the rule is not destroyed")
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify("rx_dropped: 1" in out_pf1, "the packet is dropped by pf1")

        # send mismatched packets
        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(
            out_vf00,
            pkt_num=1,
            check_param={"port_id": 0, "queue": [2, 3]},
            stats=False,
        )
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(
            out_vf01,
            pkt_num=1,
            check_param={"port_id": 1, "queue": 6, "mark_id": 0},
            stats=False,
        )

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf10,
            pkt_num=1,
            check_param={"port_id": 0, "queue": 6, "mark_id": 1},
            stats=False,
        )

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(
            out_vf11, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=False
        )

        self.dut.close_session(self.session_secondary)
        self.dut.close_session(self.session_third)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_maxnum_128_profiles(self):
        """
        There are 128 profiles in total.
        each pf apply for 8 profiles when kernel driver init, 4 for non-tunnel packet, 4 for tunnel packet.
        profile 0 and profile 1 are default profile for specific packet.
        design case with 2*100G card, so only 110 profiles can be used for vf.
        """
        nex_cnt = 0
        self.destroy_env()
        self.setup_npf_nvf_env(pf_num=1, vf_num=16)

        if len(self.dut_ports) == 4:
            nex_cnt = 94 // 8
        elif len(self.dut_ports) == 2:
            nex_cnt = 110 // 8
            # check the card is chapman beach 100g*2 or not
            pf_pci = self.dut.ports_info[0]["pci"]
            out = self.dut.send_expect(
                'lspci -s {} -vvv |grep "Product Name"'.format(pf_pci), "#"
            )
            res = re.search(r"Network Adapter\s+(?P<product_name>E810-.*)", out)
            self.verify(res, "product name not found'")
            # if card is chapman beach 100g*2, one pf port equals a general 100g*2 card,so 118 profiles can be used for vf
            if "E810-2CQDA2" in res.group("product_name"):
                nex_cnt = 118 // 8

        else:
            self.verify(False, "The number of ports is not supported")

        self.dut.send_expect(
            "ip link set {} vf {} mac 00:11:22:33:44:55".format(self.pf0_intf, nex_cnt),
            "#",
        )
        command = self.path + " -c f -n 6 -- -i --rxq=16 --txq=16"
        self.dut.send_expect(command, "testpmd> ", 360)
        self.config_testpmd()

        for port_id in range(nex_cnt):
            # The number of rules created is affected by the profile and TCAM. The maximum profile is 128 and the maximum
            # TCAM is 512. In order to test the maximum profile, need to create rules that consume less TCAM to ensure
            # that the profile will reach the maximum before TCAM exhausted
            rules = [
                "flow create {} ingress pattern eth / ipv4 / l2tpv3oip session_id is 1 / end actions queue index 1 / mark / end",
                "flow create {} ingress pattern eth / ipv6 / l2tpv3oip session_id is 2 / end actions queue index 1 / mark / end",
                "flow create {} ingress pattern eth / ipv4 / tcp / end actions queue index 2 / mark / end",
                "flow create {} ingress pattern eth / ipv6 / tcp / end actions queue index 2 / mark / end",
                "flow create {} ingress pattern eth / ipv4 / esp spi is 1 / end actions queue index 3 / mark / end",
                "flow create {} ingress pattern eth / ipv6 / esp spi is 2 / end actions queue index 3 / mark / end",
                "flow create {} ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 4 / mark id 1 / end",
                "flow create {} ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / end",
            ]
            self.create_fdir_rule(
                [rule.format(port_id) for rule in rules], check_stats=True
            )

        rules = [
            "flow create {} ingress pattern eth / ipv4 / l2tpv3oip session_id is 1 / end actions queue index 1 / mark / end",
            "flow create {} ingress pattern eth / ipv6 / l2tpv3oip session_id is 2 / end actions queue index 1 / mark / end",
            "flow create {} ingress pattern eth / ipv4 / tcp / end actions queue index 2 / mark / end",
            "flow create {} ingress pattern eth / ipv6 / tcp / end actions queue index 2 / mark / end",
            "flow create {} ingress pattern eth / ipv4 / esp spi is 1 / end actions queue index 3 / mark / end",
            "flow create {} ingress pattern eth / ipv6 / esp spi is 2 / end actions queue index 3 / mark / end",
        ]
        self.create_fdir_rule(
            [rule.format(nex_cnt) for rule in rules], check_stats=True
        )

        rule = "flow create {} ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 4 / mark id 1 / end".format(
            nex_cnt
        )
        self.create_fdir_rule(rule, check_stats=False)
        pkt1 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP()/Raw("x" * 80)'
        out = self.send_pkts_getouput(pkts=pkt1)
        rfc.check_iavf_fdir_mark(
            out,
            pkt_num=1,
            check_param={"port_id": nex_cnt, "mark_id": 0, "queue": 2},
            stats=True,
        )
        pkt2 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(dport=8805)/PFCP(S=0)/Raw("x" * 80)'
        out = self.send_pkts_getouput(pkts=pkt2)
        rfc.check_iavf_fdir_mark(
            out,
            pkt_num=1,
            check_param={"port_id": nex_cnt, "mark_id": 1, "queue": 4},
            stats=False,
        )

        self.dut.send_expect("flow flush {}".format(nex_cnt), "testpmd> ")
        self.check_fdir_rule(port_id=(nex_cnt), stats=False)
        out = self.send_pkts_getouput(pkts=pkt1)
        rfc.check_iavf_fdir_mark(
            out,
            pkt_num=1,
            check_param={"port_id": nex_cnt, "mark_id": 0, "queue": 2},
            stats=False,
        )

        self.create_fdir_rule(rule, check_stats=True)
        out = self.send_pkts_getouput(pkts=pkt2)
        rfc.check_iavf_fdir_mark(
            out,
            pkt_num=1,
            check_param={"port_id": nex_cnt, "mark_id": 1, "queue": 4},
            stats=True,
        )

    def test_stress_port_stop_start(self):
        """
        Rules can take effect after port stop/start
        """
        rule = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark / end"
        pkt = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") / Raw("x" * 80)'
        self.create_fdir_rule(rule, check_stats=True)
        out = self.send_pkts_getouput(pkts=pkt)
        rfc.check_iavf_fdir_mark(
            out,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 1},
            stats=True,
        )
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        # show the rule list, there is no rule listed
        self.check_fdir_rule(port_id=0, stats=False)
        out = self.send_pkts_getouput(pkts=pkt)
        rfc.verify_iavf_fdir_directed_by_rss(out)
        rfc.check_iavf_fdir_mark(
            out,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 1},
            stats=False,
        )

    def test_stress_delete_rules(self):
        """
        delete 1st/2nd/last rule won't affect other rules
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 24 / end actions queue index 2 / mark id 2 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 25 / end actions queue index 3 / mark id 3 / end",
        ]
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=25)/Raw("x" * 80)',
        ]

        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)
        out_0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out_0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=True,
        )
        out_1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out_1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=True,
        )
        out_2 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(
            out_2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=True,
        )

        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ")
        out_0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out_0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=False,
        )
        out_1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out_1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=True,
        )
        out_2 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(
            out_2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=True,
        )
        self.dut.send_expect("flow flush 0", "testpmd> ")

        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)
        self.dut.send_expect("flow destroy 0 rule 1", "testpmd> ")
        out_0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out_0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=True,
        )
        out_1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out_1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=False,
        )
        out_2 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(
            out_2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=True,
        )
        self.dut.send_expect("flow flush 0", "testpmd> ")

        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)
        self.dut.send_expect("flow destroy 0 rule 2", "testpmd> ")
        out_0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out_0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=True,
        )
        out_1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out_1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=True,
        )
        out_2 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(
            out_2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=False,
        )
        self.dut.send_expect("flow flush 0", "testpmd> ")

        out_0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out_0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=False,
        )
        out_1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out_1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=False,
        )
        out_2 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(
            out_2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=False,
        )

    def test_stress_vf_port_reset_add_new_rule(self):
        """
        vf reset, the origin rule can't take effect,
        then add a new rule which can take effect.
        relaunch testpmd, create same rules, can take effect.
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end",
        ]
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        ]
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 1},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 1},
            stats=True,
        )
        # reset vf
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port reset 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        # check there is not rule listed on port 0, the rule of port 1 is still be listed.
        self.check_fdir_rule(port_id=0, stats=False)
        self.check_fdir_rule(port_id=1, rule_list=["0"])
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        # check the packet is distributed by RSS
        rfc.verify_iavf_fdir_directed_by_rss(out0)
        rfc.check_iavf_fdir_mark(
            out0, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=False
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 1},
            stats=True,
        )
        # create the rule again
        self.create_fdir_rule(rules[0], check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 1},
            stats=True,
        )
        # relaunch testpmd, and create the rules, check matched packets.
        self.dut.send_expect("quit", "# ")
        self.launch_testpmd()
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 1},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 1},
            stats=True,
        )

    def test_stress_vf_port_reset_delete_rule(self):
        """
        vf reset, the origin rule can't take effect,
        then delete the rule which can't take effect without core dump,
        relaunch testpmd, create same rules, can take effect.
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark / end",
        ]
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        ]
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 6},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 6},
            stats=True,
        )
        # reset vf
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 1", "testpmd> ")
        self.dut.send_expect("port reset 1", "testpmd> ")
        self.dut.send_expect("port start 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        # check the rule of port0 is still listed, check there is not rule listed on port 1.
        self.check_fdir_rule(port_id=0, rule_list=["0"])
        self.check_fdir_rule(port_id=1, stats=False)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 6},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        # check the packet is distributed by RSS
        rfc.verify_iavf_fdir_directed_by_rss(out1)
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 6},
            stats=False,
        )
        # delete the rules
        self.destroy_fdir_rule(rule_id="0", port_id=0)
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 6},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 6},
            stats=False,
        )
        # relaunch testpmd, and create the rules, check matched packets.
        self.dut.send_expect("quit", "# ")
        self.launch_testpmd()
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 6},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 6},
            stats=True,
        )

    def test_stress_pf_reset_vf_add_new_rule(self):
        """
        pf trigger vf reset, the origin rule can't take effect,
        then add a new rule which can take effect.
        relaunch testpmd, create same rules, can take effect.
        """
        self.session_secondary = self.dut.new_session()
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end",
        ]
        new_rule = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.1 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark id 1 / end"
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.0",dst="192.1.0.1", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        ]
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 1},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 1},
            stats=True,
        )

        self.session_secondary.send_expect(
            "ip link set %s vf 0 mac 00:11:22:33:44:56" % self.pf0_intf, "# "
        )
        out = self.dut.session.get_session_before(timeout=2)
        self.verify("Port 0: reset event" in out, "failed to reset vf0")
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port reset 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        # check there is not rule listed on vf0
        self.check_fdir_rule(0, stats=False)
        out0 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(
            out0, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=True
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 1},
            stats=True,
        )

        # create a new rule, the packet patch the rule can be redirected to queue 6 with mark ID 1.
        self.create_fdir_rule(new_rule, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[3])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 6},
            stats=True,
        )
        # relaunch testpmd, and create the rules, check matched packets.
        self.dut.send_expect("quit", "# ")
        self.launch_testpmd()
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 1},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 1},
            stats=True,
        )
        self.dut.send_expect("quit", "# ")
        self.session_secondary.send_expect(
            "ip link set %s vf 0 mac 00:11:22:33:44:55" % self.pf0_intf, "# "
        )
        self.dut.close_session(self.session_secondary)

    def test_stress_pf_reset_vf_delete_rule(self):
        """
        pf trigger vf reset, the origin rule can't take effect,
        then delete the rule which can't take effect without core dump,
        relaunch testpmd, create same rules, can take effect.
        """
        self.session_secondary = self.dut.new_session()
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark / end",
        ]
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
        ]
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 6},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 6},
            stats=True,
        )

        self.session_secondary.send_expect(
            "ip link set %s vf 1 mac 00:11:22:33:44:56" % self.pf0_intf, "# "
        )
        out = self.dut.session.get_session_before(timeout=2)
        self.verify("Port 1: reset event" in out, "failed to reset vf1")
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 1", "testpmd> ")
        self.dut.send_expect("port reset 1", "testpmd> ")
        self.dut.send_expect("port start 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        # check there is not rule listed on vf1
        self.check_fdir_rule(1, stats=False)
        out0 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(
            out0, pkt_num=1, check_param={"port_id": 1, "passthru": 1}, stats=True
        )
        out1 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 6},
            stats=True,
        )
        # delete the rules
        self.dut.send_expect("flow destroy 0 rule 0", "Flow rule #0 destroyed")
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 6},
            stats=False,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 6},
            stats=False,
        )

        # relaunch testpmd, and create the rules, check matched packets.
        self.dut.send_expect("quit", "# ")
        self.launch_testpmd()
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 0, "queue": 6},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 1, "mark_id": 0, "queue": 6},
            stats=True,
        )
        self.dut.send_expect("quit", "# ")
        self.session_secondary.send_expect(
            "ip link set %s vf 1 mac 00:11:22:33:44:66" % self.pf0_intf, "# "
        )
        self.dut.close_session(self.session_secondary)

    def checksum_enablehw(self, port, hw):
        """
        set checksum parameters
        """
        self.dut.send_expect("set fwd csum", "testpmd>")
        self.dut.send_expect("port stop all", "testpmd>")
        self.dut.send_expect("csum set ip %s %d" % (hw, port), "testpmd>")
        self.dut.send_expect("csum set udp %s %d" % (hw, port), "testpmd>")
        self.dut.send_expect("port start all", "testpmd>")
        self.dut.send_expect("set promisc 0 on", "testpmd>")
        self.dut.send_expect("csum mac-swap off 0", "testpmd>")
        self.dut.send_expect("start", "testpmd>")

    def get_chksum_values(self, packets_expected):
        """
        Validate the checksum flags.
        """
        checksum_pattern = re.compile("chksum.*=.*(0x[0-9a-z]+)")

        chksum = dict()

        self.tester.send_expect("scapy", ">>> ")
        self.tester.send_expect("import sys", ">>> ")
        self.tester.send_expect("sys.path.append('./dep')", ">>> ")
        self.tester.send_expect("from pfcp import PFCP", ">>> ")

        for packet_type in list(packets_expected.keys()):
            self.tester.send_expect("p = %s" % packets_expected[packet_type], ">>>")
            out = self.tester.send_command("p.show2()", timeout=1)
            chksums = checksum_pattern.findall(out)
            chksum[packet_type] = chksums

        self.tester.send_expect("exit()", "#")
        return chksum

    def checksum_validate(self, packets_sent, packets_expected):
        """
        Validate the checksum.
        """
        tx_interface = self.tester_iface0
        rx_interface = self.tester_iface0

        sniff_src = "52:00:00:00:00:00"
        result = dict()
        pkt = Packet()
        chksum = self.get_chksum_values(packets_expected)
        self.inst = self.tester.tcpdump_sniff_packets(
            intf=rx_interface,
            count=len(packets_sent),
            filters=[{"layer": "ether", "config": {"src": sniff_src}}],
        )
        for packet_type in list(packets_sent.keys()):
            pkt.append_pkt(packets_sent[packet_type])
        pkt.send_pkt(crb=self.tester, tx_port=tx_interface, count=1)

        p = self.tester.load_tcpdump_sniff_packets(self.inst)
        nr_packets = len(p)
        print(p)
        packets_received = [
            p[i].sprintf("%IP.chksum%;%TCP.chksum%;%UDP.chksum%;%SCTP.chksum%")
            for i in range(nr_packets)
        ]
        print(len(packets_sent), len(packets_received))
        self.verify(
            len(packets_sent) * 1 == len(packets_received), "Unexpected Packets Drop"
        )
        i = 0
        for packet_received in packets_received:
            (
                ip_checksum,
                tcp_checksum,
                udp_checksum,
                sctp_checksum,
            ) = packet_received.split(";")
            if udp_checksum != "??":
                packet_type = "UDP"
                l4_checksum = udp_checksum
            if i == 0 or i == 2:
                packet_type = packet_type + "/PFCP_NODE"
            else:
                packet_type = packet_type + "/PFCP_SESSION"

            if ip_checksum != "??":
                packet_type = "IP/" + packet_type
                if chksum[packet_type] != [ip_checksum, l4_checksum]:
                    result[packet_type] = packet_type + " checksum error"
            else:
                packet_type = "IPv6/" + packet_type
                if chksum[packet_type] != [l4_checksum]:
                    result[packet_type] = packet_type + " checksum error"
            i = i + 1
        return (result, p)

    def set_vlan(self, vlan, port, strip, rx_tx="rx"):
        """
        set rx_vlan and tx_vlan
        """
        self.dut.send_expect("vlan set filter on %d" % port, "testpmd> ", 20)
        self.dut.send_expect("vlan set strip %s %d" % (strip, port), "testpmd> ", 20)
        self.dut.send_expect("rx_vlan add %d %d" % (vlan, port), "testpmd> ", 20)
        self.dut.send_expect("set verbose 1", "testpmd> ", 20)

        if rx_tx == "tx":
            self.dut.send_expect("port stop %d" % port, "testpmd> ", 20)
            self.dut.send_expect("tx_vlan set %d %d" % (port, vlan), "testpmd> ", 20)
            self.dut.send_expect("port start %d" % port, "testpmd> ", 20)
            self.dut.send_expect("set fwd mac", "testpmd> ", 20)

    def get_tcpdump_package(self, pkts):
        """
        return vlan id of tcpdump packets
        """
        vlans = []
        for i in range(len(pkts)):
            vlan = pkts.strip_element_vlan("vlan", p_index=i)
            print("vlan is:", vlan)
            vlans.append(vlan)
        return vlans

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_pfcp_vlan_strip_on_hw_checksum(self):
        """
        Set PFCP FDIR rules
        Enable HW checksum offload.
        Enable vlan filter and receipt of VLAN packets with VLAN Tag Identifier 1 on port 0.
        Disable vlan strip.
        Send packet with incorrect checksum,
        can rx it and report the checksum error,
        verify forwarded packets have correct checksum.
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / mark id 2 / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / mark id 3 / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / mark id 4 / end",
        ]

        self.dut.send_expect("quit", "# ")
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param="--rxq={} --txq={} --enable-rx-cksum --port-topology=loop".format(
                self.q_num, self.q_num
            ),
            eal_param="-a %s" % self.sriov_vfs_pf0[0].pci,
            socket=self.ports_socket,
        )
        vlan = 51
        mac = "00:11:22:33:44:56"
        sndIP = "10.0.0.1"
        sndIPv6 = "::1"
        pkts_sent = {
            "IP/UDP/PFCP_NODE": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s", chksum=0xf)/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=0)/("X"*46)'
            % (mac, sndIP),
            "IP/UDP/PFCP_SESSION": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s", chksum=0xf)/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=1)/("X"*46)'
            % (mac, sndIP),
            "IPv6/UDP/PFCP_NODE": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=0)/("X"*46)'
            % (mac, sndIPv6),
            "IPv6/UDP/PFCP_SESSION": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=1)/("X"*46)'
            % (mac, sndIPv6),
        }

        expIP = sndIP
        expIPv6 = sndIPv6
        pkts_ref = {
            "IP/UDP/PFCP_NODE": 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)'
            % (mac, expIP),
            "IP/UDP/PFCP_SESSION": 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)'
            % (mac, expIP),
            "IPv6/UDP/PFCP_NODE": 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)'
            % (mac, expIPv6),
            "IPv6/UDP/PFCP_SESSION": 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)'
            % (mac, expIPv6),
        }

        self.checksum_enablehw(port=0, hw="hw")

        self.set_vlan(vlan=vlan, port=0, strip="on")
        out_info = self.dut.send_expect("show port info 0", "testpmd> ", 20)
        self.verify("strip on" in out_info, "Wrong strip:" + out_info)

        # send packets and check the checksum value
        result = self.checksum_validate(pkts_sent, pkts_ref)
        # validate vlan in the tcpdumped packets
        out_dump = self.get_tcpdump_package(result[1])
        self.verify(len(out_dump), "Forwarded vlan packet not received!!!")
        self.verify(vlan not in out_dump, "Wrong vlan:" + str(out_dump))

        # Validate checksum on the receive packet
        out_testpmd = self.dut.send_expect("stop", "testpmd> ")
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out_testpmd)
        bad_l4csum = self.pmd_output.get_pmd_value("Bad-l4csum:", out_testpmd)
        self.verify(bad_ipcsum == 2, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 4, "Bad-l4csum check error")
        self.dut.send_expect("start", "testpmd> ")

        # check fdir rule take effect
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=True,
        )
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=True,
        )
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out3,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 4, "queue": 4},
            stats=True,
        )

        # destroy the rules and check there is no rule listed.
        self.dut.send_expect("flow flush 0", "testpmd> ", 20)
        self.check_fdir_rule(port_id=0, stats=False)

        # check no rules existing
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=False,
        )
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=False,
        )
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=False,
        )
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out3,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 4, "queue": 4},
            stats=False,
        )

        # send packets and check the checksum value
        result = self.checksum_validate(pkts_sent, pkts_ref)
        # validate vlan in the tcpdumped packets
        out_dump = self.get_tcpdump_package(result[1])
        self.verify(len(out_dump), "Forwarded vlan packet not received!!!")
        self.verify(vlan not in out_dump, "Wrong vlan:" + str(out_dump))

        # Validate checksum on the receive packet
        out_testpmd = self.dut.send_expect("stop", "testpmd> ")
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out_testpmd)
        bad_l4csum = self.pmd_output.get_pmd_value("Bad-l4csum:", out_testpmd)
        self.verify(bad_ipcsum == 2, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 4, "Bad-l4csum check error")

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_pfcp_vlan_strip_off_sw_checksum(self):
        """
        Set PFCP FDIR rules
        Enable SW checksum offload.
        Enable vlan filter and receipt of VLAN packets with VLAN Tag Identifier 1 on port 0.
        Disable vlan strip.
        Send packet with incorrect checksum,
        can rx it and report the checksum error,
        verify forwarded packets have correct checksum.
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / mark id 2 / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / mark id 3 / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / mark id 4 / end",
        ]

        self.dut.send_expect("quit", "# ")
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param="--rxq={} --txq={} --enable-rx-cksum --port-topology=loop".format(
                self.q_num, self.q_num
            ),
            eal_param="-a %s" % self.sriov_vfs_pf0[0].pci,
            socket=self.ports_socket,
        )
        vlan = 51
        mac = "00:11:22:33:44:56"
        sndIP = "10.0.0.1"
        sndIPv6 = "::1"
        pkts_sent = {
            "IP/UDP/PFCP_NODE": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s", chksum=0xf)/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=0)/("X"*46)'
            % (mac, sndIP),
            "IP/UDP/PFCP_SESSION": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s", chksum=0xf)/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=1)/("X"*46)'
            % (mac, sndIP),
            "IPv6/UDP/PFCP_NODE": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=0)/("X"*46)'
            % (mac, sndIPv6),
            "IPv6/UDP/PFCP_SESSION": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=1)/("X"*46)'
            % (mac, sndIPv6),
        }

        expIP = sndIP
        expIPv6 = sndIPv6
        pkts_ref = {
            "IP/UDP/PFCP_NODE": 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)'
            % (mac, expIP),
            "IP/UDP/PFCP_SESSION": 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)'
            % (mac, expIP),
            "IPv6/UDP/PFCP_NODE": 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)'
            % (mac, expIPv6),
            "IPv6/UDP/PFCP_SESSION": 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)'
            % (mac, expIPv6),
        }

        self.checksum_enablehw(port=0, hw="sw")

        self.set_vlan(vlan=vlan, port=0, strip="off")
        out_info = self.dut.send_expect("show port info 0", "testpmd> ", 20)
        self.verify("strip off" in out_info, "Wrong strip:" + out_info)

        result = self.checksum_validate(pkts_sent, pkts_ref)

        out_dump = self.get_tcpdump_package(result[1])
        self.verify(len(out_dump), "Forwarded vlan packet not received!!!")
        self.verify(vlan in out_dump, "Wrong vlan:" + str(out_dump))

        # Validate checksum on the receive packet
        out_testpmd = self.dut.send_expect("stop", "testpmd> ")
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out_testpmd)
        bad_l4csum = self.pmd_output.get_pmd_value("Bad-l4csum:", out_testpmd)
        self.verify(bad_ipcsum == 2, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 4, "Bad-l4csum check error")
        self.dut.send_expect("start", "testpmd> ")

        # check fdir rule take effect
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=True,
        )
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=True,
        )
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out3,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 4, "queue": 4},
            stats=True,
        )

        # destroy the rules and check there is no rule listed.
        self.dut.send_expect("flow flush 0", "testpmd> ", 20)
        self.check_fdir_rule(port_id=0, stats=False)

        # check no rules existing
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=False,
        )
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=False,
        )
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=False,
        )
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out3,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 4, "queue": 4},
            stats=False,
        )

        result = self.checksum_validate(pkts_sent, pkts_ref)

        out_dump = self.get_tcpdump_package(result[1])
        self.verify(len(out_dump), "Forwarded vlan packet not received!!!")
        self.verify(vlan in out_dump, "Wrong vlan:" + str(out_dump))

        # Validate checksum on the receive packet
        out_testpmd = self.dut.send_expect("stop", "testpmd> ")
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out_testpmd)
        bad_l4csum = self.pmd_output.get_pmd_value("Bad-l4csum:", out_testpmd)
        self.verify(bad_ipcsum == 2, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 4, "Bad-l4csum check error")

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_pfcp_vlan_insert_on(self):
        """
        Set PFCP FDIR rules
        Enable vlan filter and insert VLAN Tag Identifier 1 to vlan packet sent from port 0
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / mark id 2 / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / mark id 3 / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / mark id 4 / end",
        ]

        self.dut.send_expect("quit", "# ")
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param="--rxq={} --txq={} --enable-rx-cksum --port-topology=loop".format(
                self.q_num, self.q_num
            ),
            eal_param="-a %s" % self.sriov_vfs_pf0[0].pci,
            socket=self.ports_socket,
        )
        vlan = 51
        mac = "00:11:22:33:44:55"
        sndIP = "10.0.0.1"
        sndIPv6 = "::1"
        pkt = Packet()
        pkts_sent = {
            "IP/UDP/PFCP_NODE": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)'
            % (mac, sndIP),
            "IP/UDP/PFCP_SESSION": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)'
            % (mac, sndIP),
            "IPv6/UDP/PFCP_NODE": 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)'
            % (mac, sndIPv6),
            "IPv6/UDP/PFCP_SESSION": 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)'
            % (mac, sndIPv6),
        }

        self.set_vlan(vlan=vlan, port=0, strip="off", rx_tx="tx")
        self.dut.send_expect("start", "testpmd> ")

        tx_interface = self.tester_iface0
        rx_interface = self.tester_iface0

        dmac = "00:11:22:33:44:55"
        smac = self.pf1_mac
        inst = self.tester.tcpdump_sniff_packets(rx_interface)

        for packet_type in list(pkts_sent.keys()):
            pkt.append_pkt(pkts_sent[packet_type])
        pkt.send_pkt(crb=self.tester, tx_port=tx_interface, count=1)

        p = self.tester.load_tcpdump_sniff_packets(inst)

        out = self.get_tcpdump_package(p)
        self.verify(vlan in out, "Vlan not found:" + str(out))
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        # check fdir rule take effect
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=True,
        )
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=True,
        )
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=True,
        )
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out3,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 4, "queue": 4},
            stats=True,
        )

        # destroy the rules and check there is no rule listed.
        self.dut.send_expect("flow flush 0", "testpmd> ", 20)
        self.check_fdir_rule(port_id=0, stats=False)

        # check no rules existing
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out0,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 1, "queue": 1},
            stats=False,
        )
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out1,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 2, "queue": 2},
            stats=False,
        )
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(
            out2,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 3, "queue": 3},
            stats=False,
        )
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(
            out3,
            pkt_num=1,
            check_param={"port_id": 0, "mark_id": 4, "queue": 4},
            stats=False,
        )

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect("tx_vlan reset 0", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("stop", "testpmd> ", 30)

    def test_check_profile_delete(self):
        pkt_ipv4_pay_ipv6_pay = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1, hlim=2)/("X"*480)',
        ]

        rule_ipv4_tcp_ipv6_udp = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 2 / mark id 2 / end",
        ]
        # create rules
        self.create_fdir_rule(rule_ipv4_tcp_ipv6_udp, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=True)
        out = self.send_pkts_getouput(pkt_ipv4_pay_ipv6_pay)
        rfc.verify_iavf_fdir_directed_by_rss(out, stats=True)

        self.pmd_output.execute_cmd("flow flush 0")
        rule_ipv4_other_ipv6_other = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 3 / mark id 3 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / end actions queue index 4 / mark id 4 / end",
        ]
        self.create_fdir_rule(rule_ipv4_other_ipv6_other, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=True)
        out = self.send_pkts_getouput(pkt_ipv4_pay_ipv6_pay)
        rfc.check_iavf_fdir_mark(
            out,
            pkt_num=2,
            check_param={"port_id": 0, "mark_id": [3, 4], "queue": [3, 4]},
            stats=True,
        )

        self.pmd_output.execute_cmd("flow flush 0")
        self.create_fdir_rule(rule_ipv4_tcp_ipv6_udp, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=True)
        out = self.send_pkts_getouput(pkt_ipv4_pay_ipv6_pay)
        rfc.verify_iavf_fdir_directed_by_rss(out, stats=True)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_ipv4(self):
        self.rte_flow_process(vectors_ipv4_gtpu_ipv4)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_ipv4_tcp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_ipv4_tcp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_ipv4_udp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_ipv4_udp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ipv4(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ipv4)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ipv4_tcp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ipv4_tcp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ipv4_udp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ipv4_udp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_dl_ipv4(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_dl_ipv4)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_dl_ipv4_tcp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_dl_ipv4_tcp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_dl_ipv4_udp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_dl_ipv4_udp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ul_ipv4(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ul_ipv4)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ul_ipv4_tcp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ul_ipv4_tcp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ul_ipv4_udp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ul_ipv4_udp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_ipv6(self):
        self.rte_flow_process(vectors_ipv4_gtpu_ipv6)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_ipv6_tcp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_ipv6_tcp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_ipv6_udp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_ipv6_udp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ipv6(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ipv6)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ipv6_tcp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ipv6_tcp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ipv6_udp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ipv6_udp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_dl_ipv6(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_dl_ipv6)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_dl_ipv6_tcp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_dl_ipv6_tcp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_dl_ipv6_udp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_dl_ipv6_udp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ul_ipv6(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ul_ipv6)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ul_ipv6_tcp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ul_ipv6_tcp)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_ipv4_gtpu_eh_ul_ipv6_udp(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh_ul_ipv6_udp)

    def _rte_conflict_rule(self, conflict_rule, rule, match_pkt, stats=True):
        check_param = {"port_id": 0, "mark_id": 1, "queue": 10}

        self.create_fdir_rule(conflict_rule, check_stats=False)
        rule_id = self.create_fdir_rule(rule, check_stats=True)
        out = self.send_pkts_getouput(pkts=match_pkt)
        pkt_num = len(match_pkt)
        rfc.check_iavf_fdir_mark(out, pkt_num=pkt_num, check_param=check_param)
        if int(rule_id[0]) > 1:
            rule_id = int(rule_id[0]) - 1
        else:
            rule_id = 0
        if stats:
            self.destroy_fdir_rule(rule_id)

    def _create_check_conflict_rule(self, rules, pkts):
        self.create_fdir_rule(rules[0], check_stats=True)
        pkt_list = [pkts[0], pkts[3]]
        self._rte_conflict_rule(rules[1:3], rules[3], pkt_list)

        pkt_list = [pkts[1], pkts[3]]
        self._rte_conflict_rule(rules[5:], rules[1], pkt_list)

        pkt_list = [pkts[1], pkts[4]]
        self._rte_conflict_rule(rules[0], rules[4], pkt_list)

        c_rules = [rules[3], rules[4], rules[7], rules[9], rules[10]]
        pkt_list = [pkts[4], pkts[5]]
        self._rte_conflict_rule(c_rules, rules[5], pkt_list)

        c_rules = [rules[3], rules[6], rules[8], rules[9], rules[11]]
        pkt_list = [pkts[5], pkts[7]]
        self._rte_conflict_rule(c_rules, rules[7], pkt_list)

        c_rules = [rules[3], rules[4], rules[6]]
        pkt_list = [pkts[7], pkts[8]]
        self._rte_conflict_rule(c_rules, rules[8], pkt_list)

        c_rules = [rules[3], rules[5], rules[6]]
        pkt_list = [pkts[8], pkts[9]]
        self._rte_conflict_rule(c_rules, rules[9], pkt_list)

        c_rules = [rules[3], rules[4], rules[5], rules[9], rules[10], rules[11]]
        pkt_list = [pkts[6], pkts[9]]
        self._rte_conflict_rule(c_rules, rules[6], pkt_list)

        c_rules = [rules[3], rules[4], rules[5], rules[7], rules[8]]
        pkt_list = [pkts[6], pkts[10]]
        self._rte_conflict_rule(c_rules, rules[10], pkt_list, stats=False)

        c_rules = [rules[3], rules[4], rules[5], rules[7], rules[8], rules[9]]
        pkt_list = [pkts[6], pkts[10], pkts[11]]
        self._rte_conflict_rule(c_rules, rules[11], pkt_list, stats=False)

        c_rules = [rules[3], rules[4], rules[5], rules[7], rules[8], rules[9]]
        pkt_list = [pkts[2], pkts[6], pkts[10], pkts[11]]
        self._rte_conflict_rule(c_rules, rules[2], pkt_list, stats=False)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_inner_ipv4_gtpu_conflict_rule(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
        ]

        pkts = [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x"*20)',
        ]

        self._create_check_conflict_rule(rules, pkts)

    @skip_unsupported_pkg(["os default", "wireless"])
    def test_mac_inner_ipv6_gtpu_conflict_rule(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end",
        ]

        pkts = [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw("x"*20)',
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw("x"*20)',
        ]

        self._create_check_conflict_rule(rules, pkts)

    def test_mac_ipv4_gre_ipv4(self):
        self.rte_flow_process(vectors_ipv4_gre_ipv4)

    def test_mac_ipv6_gre_ipv4(self):
        self.rte_flow_process(vectors_ipv6_gre_ipv4)

    def test_mac_ipv4_gre_ipv6(self):
        self.rte_flow_process(vectors_ipv4_gre_ipv6)

    def test_mac_ipv6_gre_ipv6(self):
        self.rte_flow_process(vectors_ipv6_gre_ipv6)

    def test_mac_ipv4_gre_ipv4_tcp(self):
        self.rte_flow_process(vectors_ipv4_gre_ipv4_tcp)

    def test_mac_ipv6_gre_ipv4_tcp(self):
        self.rte_flow_process(vectors_ipv6_gre_ipv4_tcp)

    def test_mac_ipv4_gre_ipv6_tcp(self):
        self.rte_flow_process(vectors_ipv4_gre_ipv6_tcp)

    def test_mac_ipv6_gre_ipv6_tcp(self):
        self.rte_flow_process(vectors_ipv6_gre_ipv6_tcp)

    def test_mac_ipv4_gre_ipv4_udp(self):
        self.rte_flow_process(vectors_ipv4_gre_ipv4_udp)

    def test_mac_ipv6_gre_ipv4_udp(self):
        self.rte_flow_process(vectors_ipv6_gre_ipv4_udp)

    def test_mac_ipv4_gre_ipv6_udp(self):
        self.rte_flow_process(vectors_ipv4_gre_ipv6_udp)

    def test_mac_ipv6_gre_ipv6_udp(self):
        self.rte_flow_process(vectors_ipv6_gre_ipv6_udp)

    def tear_down(self):
        # destroy all flow rule on port 0
        if self.running_case in [
            "test_mac_ipv4_pay_multicast",
            "test_mac_ipv4_multicast_protocol",
            "test_mac_ipv6_pay_multicast",
            "test_mac_ipv6_multicast_protocol",
        ]:
            self.pmd_output.execute_cmd("mcast_addr remove 0 11:22:33:44:55:66")
        self.destroy_env()
        self.dut.kill_all()
        if getattr(self, "session_secondary", None):
            self.dut.close_session(self.session_secondary)
        if getattr(self, "session_third", None):
            self.dut.close_session(self.session_third)

        if self.running_case in [
            "test_pfcp_vlan_strip_off_sw_checksum",
            "test_pfcp_vlan_strip_on_hw_checksum",
        ]:
            self.ip_link_set(
                host_intf=self.host_intf_0,
                cmd="vf",
                port=0,
                types="trust",
                value="off",
            )
            self.ip_link_set(
                host_intf=self.host_intf_0,
                cmd="vf",
                port=0,
                types="spoofchk",
                value="on",
            )
            self.ip_link_set(
                host_intf=self.host_intf_1,
                cmd="vf",
                port=0,
                types="trust",
                value="off",
            )
            self.ip_link_set(
                host_intf=self.host_intf_1,
                cmd="vf",
                port=0,
                types="spoofchk",
                value="on",
            )

    def tear_down_all(self):
        self.dut.kill_all()
        self.destroy_env()
