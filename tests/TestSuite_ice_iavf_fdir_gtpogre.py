# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2021 Intel Corporation
#

import re
import time

from scapy.all import *

import tests.rte_flow_common as rfc
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.utils import GREEN, RED

LAUNCH_QUEUE = 16

mac_ipv4_gre_ipv4_gtpu_ipv4_pkt = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")',
    ],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()',
    ],
}

tv_mac_ipv4_gre_ipv4_gtpu_ipv4_queue_index = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ipv4_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 13 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": 3, "mark_id": 13},
}

tv_mac_ipv4_gre_ipv4_gtpu_ipv4_rss_queues = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ipv4_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions rss queues 4 5 end / mark id 23 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": [4, 5], "mark_id": 23},
}

tv_mac_ipv4_gre_ipv4_gtpu_ipv4_passthru = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ipv4_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions passthru / mark id 33 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 33},
}

tv_mac_ipv4_gre_ipv4_gtpu_ipv4_drop = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ipv4_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions drop / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "drop": True},
}

tv_mac_ipv4_gre_ipv4_gtpu_ipv4_mark_rss = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ipv4_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions mark / rss / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tvs_mac_ipv4_gre_ipv4_gtpu_ipv4 = [
    tv_mac_ipv4_gre_ipv4_gtpu_ipv4_queue_index,
    tv_mac_ipv4_gre_ipv4_gtpu_ipv4_rss_queues,
    tv_mac_ipv4_gre_ipv4_gtpu_ipv4_passthru,
    tv_mac_ipv4_gre_ipv4_gtpu_ipv4_drop,
    tv_mac_ipv4_gre_ipv4_gtpu_ipv4_mark_rss,
]

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
    ],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=14, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=24)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/UDP(sport=13, dport=23)',
    ],
}

tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_queue_index = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": 3, "mark_id": 13},
}

tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_rss_queues = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions rss queues 4 5 end / mark id 23 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": [4, 5], "mark_id": 23},
}

tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_passthru = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions passthru / mark id 33 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 33},
}

tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_drop = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions drop / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "drop": True},
}

tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_mark_rss = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions mark / rss / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_udp = [
    tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_queue_index,
    tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_rss_queues,
    tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_passthru,
    tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_drop,
    tv_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_mark_rss,
]

tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_tcp = [
    eval(
        str(element)
        .replace("UDP(sport", "UDP1(sport")
        .replace("TCP(sport", "TCP1(sport")
        .replace("UDP1(sport", "TCP(sport")
        .replace("TCP1(sport", "UDP(sport")
        .replace("_udp_", "_tcp_")
        .replace("udp src", "tcp src")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_udp
]

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")',
    ],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.14", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6()',
    ],
}

tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_queue_index = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 13 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": 3, "mark_id": 13},
}

tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_rss_queues = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions rss queues 4 5 end / mark id 23 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": [4, 5], "mark_id": 23},
}

tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_passthru = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions passthru / mark id 33 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 33},
}

tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_drop = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions drop / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "drop": True},
}

tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_mark_rss = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions mark / rss / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4 = [
    tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_queue_index,
    tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_rss_queues,
    tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_passthru,
    tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_drop,
    tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_mark_rss,
]

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
    ],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=14, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=24)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=14, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=24)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
    ],
}

tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_queue_index = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": 3, "mark_id": 13},
}

tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_rss_queues = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions rss queues 4 5 end / mark id 23 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": [4, 5], "mark_id": 23},
}

tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_passthru = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions passthru / mark id 33 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 33},
}

tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_drop = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions drop / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "drop": True},
}

tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_mark_rss = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions mark / rss / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp = [
    tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_queue_index,
    tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_rss_queues,
    tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_passthru,
    tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_drop,
    tv_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_mark_rss,
]

tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp = [
    eval(
        str(element)
        .replace("UDP(sport", "UDP1(sport")
        .replace("TCP(sport", "TCP1(sport")
        .replace("UDP1(sport", "TCP(sport")
        .replace("TCP1(sport", "UDP(sport")
        .replace("_udp_", "_tcp_")
        .replace("udp src", "tcp src")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp
]

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")',
    ],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")',
    ],
}

tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_queue_index = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 13 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": 3, "mark_id": 13},
}

tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_rss_queues = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions rss queues 4 5 end / mark id 23 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": [4, 5], "mark_id": 23},
}

tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_passthru = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions passthru / mark id 33 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 33},
}

tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_drop = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions drop / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "drop": True},
}

tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_mark_rss = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions mark / rss / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4 = [
    tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_queue_index,
    tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_rss_queues,
    tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_passthru,
    tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_drop,
    tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_mark_rss,
]

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
    ],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=14, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=24)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/TCP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6()/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
    ],
}

tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_queue_index = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": 3, "mark_id": 13},
}

tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_rss_queues = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions rss queues 4 5 end / mark id 23 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": [4, 5], "mark_id": 23},
}

tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_passthru = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions passthru / mark id 33 / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 33},
}

tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_drop = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions drop / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "drop": True},
}

tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_mark_rss = {
    "name": "tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions mark / rss / end",
    "scapy_str": {
        "matched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt["matched"],
        "unmatched": mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp = [
    tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_queue_index,
    tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_rss_queues,
    tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_passthru,
    tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_drop,
    tv_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_mark_rss,
]

tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp = [
    eval(
        str(element)
        .replace("UDP(sport", "UDP1(sport")
        .replace("TCP(sport", "TCP1(sport")
        .replace("UDP1(sport", "TCP(sport")
        .replace("TCP1(sport", "UDP(sport")
        .replace("_udp_", "_tcp_")
        .replace("udp src", "tcp src")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp
]

tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4 = [
    eval(
        str(element)
        .replace("_ul_", "_dl_")
        .replace("type=1", "type=11")
        .replace("type=0", "type=10")
        .replace("type=11", "type=0")
        .replace("type=10", "type=1")
        .replace("pdu_t is 1", "pdu_t is 0")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4
]

tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp = [
    eval(
        str(element)
        .replace("_ul_", "_dl_")
        .replace("type=1", "type=11")
        .replace("type=0", "type=10")
        .replace("type=11", "type=0")
        .replace("type=10", "type=1")
        .replace("pdu_t is 1", "pdu_t is 0")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp
]

tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp = [
    eval(
        str(element)
        .replace("_ul_", "_dl_")
        .replace("type=1", "type=11")
        .replace("type=0", "type=10")
        .replace("type=11", "type=0")
        .replace("type=10", "type=1")
        .replace("pdu_t is 1", "pdu_t is 0")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp
]

tvs_mac_ipv6_gre_ipv4_gtpu_ipv4 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv4
]

tvs_mac_ipv6_gre_ipv4_gtpu_ipv4_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_udp
]

tvs_mac_ipv6_gre_ipv4_gtpu_ipv4_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_tcp
]

tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv4 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4
]

tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv4_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp
]

tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv4_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp
]

tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv4 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4
]

tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv4_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp
]

tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv4_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp
]

tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv4 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4
]

tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv4_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp
]

tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv4_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp
]

tvs_mac_ipv4_gre_ipv6_gtpu_ipv4 = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv4
]

tvs_mac_ipv4_gre_ipv6_gtpu_ipv4_udp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_udp
]

tvs_mac_ipv4_gre_ipv6_gtpu_ipv4_tcp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_tcp
]

tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv4 = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4
]

tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_udp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp
]

tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_tcp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp
]

tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv4 = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4
]

tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_udp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp
]

tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_tcp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp
]

tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv4 = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4
]

tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_udp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp
]

tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_tcp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp
]

tvs_mac_ipv4_gre_ipv4_gtpu_ipv6 = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv4
]

tvs_mac_ipv4_gre_ipv4_gtpu_ipv6_udp = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_udp
]

tvs_mac_ipv4_gre_ipv4_gtpu_ipv6_tcp = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_tcp
]

tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6 = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4
]

tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp
]

tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp
]

tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6 = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4
]

tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp
]

tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp
]

tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6 = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4
]

tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp
]

tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp = [
    eval(
        str(element)
        .replace("gtpu_ipv4", "gtpu_ipv6")
        .replace("eh_ipv4", "eh_ipv6")
        .replace("ul_ipv4", "ul_ipv6")
        .replace("dl_ipv4", "dl_ipv6")
        .replace("GTP_U_Header()/IPv6", "GTP_U_Header()/IP")
        .replace("GTPPDUSessionContainer()/IPv6", "GTPPDUSessionContainer()/IP")
        .replace("QFI=0x34)/IPv6", "QFI=0x34)/IP")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp
]

tvs_mac_ipv6_gre_ipv6_gtpu_ipv4 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ipv4
]

tvs_mac_ipv6_gre_ipv6_gtpu_ipv4_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ipv4_udp
]

tvs_mac_ipv6_gre_ipv6_gtpu_ipv4_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ipv4_tcp
]

tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv4 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv4
]

tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv4_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_udp
]

tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv4_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_tcp
]

tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv4 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv4
]

tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv4_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_udp
]

tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv4_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_tcp
]

tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv4 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv4
]

tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv4_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_udp
]

tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv4_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_tcp
]

tvs_mac_ipv4_gre_ipv6_gtpu_ipv6 = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv6
]

tvs_mac_ipv4_gre_ipv6_gtpu_ipv6_udp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv6_udp
]

tvs_mac_ipv4_gre_ipv6_gtpu_ipv6_tcp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv6_tcp
]

tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv6 = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6
]

tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_udp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp
]

tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_tcp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp
]

tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv6 = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6
]

tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_udp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp
]

tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_tcp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp
]

tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv6 = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6
]

tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_udp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp
]

tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_tcp = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp
]

tvs_mac_ipv6_gre_ipv4_gtpu_ipv6 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv6
]

tvs_mac_ipv6_gre_ipv4_gtpu_ipv6_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv6_udp
]

tvs_mac_ipv6_gre_ipv4_gtpu_ipv6_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ipv6_tcp
]

tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv6 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6
]

tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv6_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp
]

tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv6_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp
]

tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv6 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6
]

tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv6_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp
]

tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv6_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp
]

tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv6 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6
]

tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv6_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp
]

tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv6_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp
]

tvs_mac_ipv6_gre_ipv6_gtpu_ipv6 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ipv6
]

tvs_mac_ipv6_gre_ipv6_gtpu_ipv6_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ipv6_udp
]

tvs_mac_ipv6_gre_ipv6_gtpu_ipv6_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ipv6_tcp
]

tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv6 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv6
]

tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv6_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_udp
]

tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv6_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_tcp
]

tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv6 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv6
]

tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv6_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_udp
]

tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv6_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_tcp
]

tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv6 = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv6
]

tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv6_udp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_udp
]

tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv6_tcp = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace("IP()/GRE", "IP1()/GRE")
        .replace("IPv6()/GRE", "IPv66()/GRE")
        .replace("IP1()/GRE", "IPv6()/GRE")
        .replace("IPv66()/GRE", "IP()/GRE")
        .replace("ipv4 / gre", "ipv6 / gre")
    )
    for element in tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_tcp
]

outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IP()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IP()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IPv6()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IPv6()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IP()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IP()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IPv6()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IPv6()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IP()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IP()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IPv6()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IPv6()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IP()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IP()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IPv6()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IPv6()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()/TCP()',
    ],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.14", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.15")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x11)/GTPPDUSessionContainer(QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x13)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.14", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IPv6()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.15")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IPv6()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x11)/GTPPDUSessionContainer(QFI=0x3)/IPv6()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x13)/IPv6()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.14", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.15")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x11)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x13)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.14", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.15")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x11)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x13)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/IP()',
    ],
}

tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_queue_index = {
    "name": "tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc qfi is 0x3 / end actions queue index 3 / mark id 13 / end",
    "scapy_str": {
        "matched": outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt["matched"],
        "unmatched": outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": 3, "mark_id": 13},
}

tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_rss_queues = {
    "name": "tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc qfi is 0x3 / end actions rss queues 4 5 end / mark id 23 / end",
    "scapy_str": {
        "matched": outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt["matched"],
        "unmatched": outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": [4, 5], "mark_id": 23},
}

tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_passthru = {
    "name": "tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc qfi is 0x3 / end actions passthru / mark id 33 / end",
    "scapy_str": {
        "matched": outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt["matched"],
        "unmatched": outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 33},
}

tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_drop = {
    "name": "tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc qfi is 0x3 / end actions drop / end",
    "scapy_str": {
        "matched": outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt["matched"],
        "unmatched": outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "drop": True},
}

tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_mark_rss = {
    "name": "tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc qfi is 0x3 / end actions mark / rss / end",
    "scapy_str": {
        "matched": outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt["matched"],
        "unmatched": outer_mac_ipv4_gre_ipv4_gtpu_eh_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tvs_outer_mac_ipv4_gre_ipv4_gtpu_eh = [
    tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_queue_index,
    tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_rss_queues,
    tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_passthru,
    tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_drop,
    tv_outer_mac_ipv4_gre_ipv4_gtpu_eh_mark_rss,
]


outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()/TCP()',
    ],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.14", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.15")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x11)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x13)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.14", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.15")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x11)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x13)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IPv6()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.14", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.15")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IP()/UDP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x11)/GTPPDUSessionContainer(type=1, P=1, QFI=0x3)/IPv6()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=1, P=1, QFI=0x13)/IP()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(type=0, P=1, QFI=0x3)/IP()/TCP()',
        'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.4", dst="1.1.2.5")/GRE()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0x12)/IP()',
    ],
}

tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_queue_index = {
    "name": "tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc pdu_t is 1 qfi is 0x3 / end actions queue index 3 / mark id 13 / end",
    "scapy_str": {
        "matched": outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt["matched"],
        "unmatched": outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": 3, "mark_id": 13},
}

tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_rss_queues = {
    "name": "tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc pdu_t is 1 qfi is 0x3 / end actions rss queues 4 5 end / mark id 23 / end",
    "scapy_str": {
        "matched": outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt["matched"],
        "unmatched": outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "queue": [4, 5], "mark_id": 23},
}

tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_passthru = {
    "name": "tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc pdu_t is 1 qfi is 0x3 / end actions passthru / mark id 33 / end",
    "scapy_str": {
        "matched": outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt["matched"],
        "unmatched": outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 33},
}

tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_drop = {
    "name": "tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc pdu_t is 1 qfi is 0x3 / end actions drop / end",
    "scapy_str": {
        "matched": outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt["matched"],
        "unmatched": outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "drop": True},
}

tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_mark_rss = {
    "name": "tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc pdu_t is 1 qfi is 0x3 / end actions mark / rss / end",
    "scapy_str": {
        "matched": outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt["matched"],
        "unmatched": outer_mac_ipv4_gre_ipv4_gtpu_ul_pkt["unmatched"],
    },
    "check_param": {"port_id": 0, "rxq": LAUNCH_QUEUE, "mark_id": 0, "rss": True},
}

tvs_outer_mac_ipv4_gre_ipv4_gtpu_ul = [
    tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_queue_index,
    tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_rss_queues,
    tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_passthru,
    tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_drop,
    tv_outer_mac_ipv4_gre_ipv4_gtpu_ul_mark_rss,
]

tvs_outer_mac_ipv4_gre_ipv4_gtpu_dl = [
    eval(
        str(element)
        .replace("_ul", "_dl")
        .replace("type=1", "type=11")
        .replace("type=0", "type=10")
        .replace("type=11", "type=0")
        .replace("type=10", "type=1")
        .replace("pdu_t is 1", "pdu_t is 0")
    )
    for element in tvs_outer_mac_ipv4_gre_ipv4_gtpu_ul
]

tvs_outer_mac_ipv4_gre_ipv6_gtpu_eh = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_outer_mac_ipv4_gre_ipv4_gtpu_eh
]

tvs_outer_mac_ipv4_gre_ipv6_gtpu_ul = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_outer_mac_ipv4_gre_ipv4_gtpu_ul
]

tvs_outer_mac_ipv4_gre_ipv6_gtpu_dl = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_outer_mac_ipv4_gre_ipv4_gtpu_dl
]

tvs_outer_mac_ipv6_gre_ipv4_gtpu_eh = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_outer_mac_ipv4_gre_ipv4_gtpu_eh
]

tvs_outer_mac_ipv6_gre_ipv4_gtpu_ul = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_outer_mac_ipv4_gre_ipv4_gtpu_ul
]

tvs_outer_mac_ipv6_gre_ipv4_gtpu_dl = [
    eval(
        str(element)
        .replace("mac_ipv4", "mac_ipv6")
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            'IP(src="1.1.2.4", dst="1.1.2.15")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")',
        )
        .replace(
            'IP(src="1.1.2.14", dst="1.1.2.5")',
            'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        )
        .replace(
            "ipv4 src is 1.1.2.4 dst is 1.1.2.5",
            "ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020",
        )
    )
    for element in tvs_outer_mac_ipv4_gre_ipv4_gtpu_dl
]

tvs_outer_mac_ipv6_gre_ipv6_gtpu_eh = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_outer_mac_ipv6_gre_ipv4_gtpu_eh
]

tvs_outer_mac_ipv6_gre_ipv6_gtpu_ul = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_outer_mac_ipv6_gre_ipv4_gtpu_ul
]

tvs_outer_mac_ipv6_gre_ipv6_gtpu_dl = [
    eval(
        str(element)
        .replace("gre_ipv4", "gre_ipv6")
        .replace("GRE()/IP()", "GRE()/IP2()")
        .replace("GRE()/IPv6()", "GRE()/IPv62()")
        .replace("GRE()/IP2()", "GRE()/IPv6()")
        .replace("GRE()/IPv62()", "GRE()/IP()")
        .replace("gre / ipv4", "gre / ipv6")
    )
    for element in tvs_outer_mac_ipv6_gre_ipv4_gtpu_dl
]


class TestICEIavfFDIRGTPoGRE(TestCase):
    def set_up_all(self):
        self.ports = self.dut.get_ports(self.nic)

        # init pkt
        self.pkt = Packet()
        # set default app parameter
        self.pmd_out = PmdOutput(self.dut)
        self.tester_mac = self.tester.get_mac(0)
        self.tester_port0 = self.tester.get_local_port(self.ports[0])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)

        self.tester.send_expect("ifconfig {} up".format(self.tester_iface0), "# ")
        self.param = "--rxq={} --txq={} --disable-rss --txd=384 --rxd=384".format(
            LAUNCH_QUEUE, LAUNCH_QUEUE
        )
        self.param_fdir = "--rxq={} --txq={}".format(LAUNCH_QUEUE, LAUNCH_QUEUE)
        self.vf_flag = False
        self.cores = self.dut.get_core_list("1S/4C/1T")
        self.setup_1pf_vfs_env()

        self.ports_pci = [self.dut.ports_info[self.ports[0]]["pci"]]
        self.rxq = 16
        self.fdirprocess = rfc.FdirProcessing(
            self, self.pmd_out, [self.tester_iface0], LAUNCH_QUEUE, ipfrag_flag=False
        )
        self.rssprocess = rfc.RssProcessing(
            self, self.pmd_out, [self.tester_iface0], self.rxq
        )

    def set_up(self):
        pass

    def setup_1pf_vfs_env(self):
        """
        create vf and set vf mac
        """
        self.vf_flag = True
        self.dut.bind_interfaces_linux("ice")
        self.pf_interface = self.dut.ports_info[0]["intf"]
        self.dut.send_expect("ifconfig {} up".format(self.pf_interface), "# ")
        self.dut.generate_sriov_vfs_by_port(self.ports[0], 1, driver=self.kdriver)
        self.dut.send_expect(
            "ip link set {} vf 0 mac 00:11:22:33:44:55".format(self.pf_interface), "# "
        )
        self.vf_port = self.dut.ports_info[0]["vfs_port"]
        self.verify(len(self.vf_port) != 0, "VF create failed")
        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_assign_method = "vfio-pci"
        self.vf_port[0].bind_driver(self.vf_driver)

        self.vf_ports_pci = [self.vf_port[0].pci]

    def launch_testpmd(self, param_fdir=False):
        """
        start testpmd with fdir or rss param, and pf or vf

        :param param_fdir: True: Fdir param/False: rss param
        """
        if param_fdir == True:
            self.pmd_out.start_testpmd(
                cores=self.cores, ports=self.vf_ports_pci, param=self.param_fdir
            )
        else:
            self.pmd_out.start_testpmd(
                cores=self.cores, ports=self.vf_ports_pci, param=self.param
            )
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

    def destroy_testpmd_and_vf(self):
        """
        quit testpmd
        if vf testpmd, destroy the vfs and set vf_flag = false
        """
        for port_id in self.ports:
            self.dut.destroy_sriov_vfs_by_port(port_id)

    def tear_down(self):
        self.dut.send_expect("quit", "# ")
        self.dut.kill_all()

    def tear_down_all(self):
        self.destroy_testpmd_and_vf()
        self.dut.kill_all()

    def test_mac_ipv4_gre_ipv4_gtpu_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ipv4)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_udp)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ipv4_tcp)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ipv4)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ipv4_udp)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ipv4_tcp)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv4)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv4_udp)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv4_tcp)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv4)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv4_udp)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv4_tcp)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv4)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv4_udp)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv4_tcp)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ipv4)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ipv4_udp)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ipv4_tcp)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv4)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_udp)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_tcp)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv4)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_udp)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_tcp)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv4)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_udp)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_tcp)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ipv6)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ipv6_udp)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ipv6_tcp)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ipv4)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ipv4_udp)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ipv4_tcp)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv4)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv4_udp)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv4_tcp)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv4)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv4_udp)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv4_tcp)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv4(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv4)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv4_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv4_udp)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv4_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv4_tcp)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ipv6)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ipv6_udp)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ipv6_tcp)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv6)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_udp)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_tcp)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv6)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_udp)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_tcp)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv6)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_udp)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_tcp)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ipv6)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ipv6_udp)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ipv6_tcp)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv6)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv6_udp)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_eh_ipv6_tcp)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv6)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv6_udp)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_ul_ipv6_tcp)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv6)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv6_udp)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv4_gtpu_dl_ipv6_tcp)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ipv6)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ipv6_udp)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ipv6_tcp)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv6)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv6_udp)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_eh_ipv6_tcp)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv6)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv6_udp)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_ul_ipv6_tcp)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv6(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv6)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv6_udp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv6_udp)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv6_tcp(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_mac_ipv6_gre_ipv6_gtpu_dl_ipv6_tcp)

    def test_outer_mac_ipv4_gre_ipv4_gtpu_eh(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv4_gre_ipv4_gtpu_eh)

    def test_outer_mac_ipv4_gre_ipv4_gtpu_ul(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv4_gre_ipv4_gtpu_ul)

    def test_outer_mac_ipv4_gre_ipv4_gtpu_dl(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv4_gre_ipv4_gtpu_dl)

    def test_outer_mac_ipv4_gre_ipv6_gtpu_eh(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv4_gre_ipv6_gtpu_eh)

    def test_outer_mac_ipv4_gre_ipv6_gtpu_ul(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv4_gre_ipv6_gtpu_ul)

    def test_outer_mac_ipv4_gre_ipv6_gtpu_dl(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv4_gre_ipv6_gtpu_dl)

    def test_outer_mac_ipv6_gre_ipv4_gtpu_eh(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv6_gre_ipv4_gtpu_eh)

    def test_outer_mac_ipv6_gre_ipv4_gtpu_ul(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv6_gre_ipv4_gtpu_ul)

    def test_outer_mac_ipv6_gre_ipv4_gtpu_dl(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv6_gre_ipv4_gtpu_dl)

    def test_outer_mac_ipv6_gre_ipv6_gtpu_eh(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv6_gre_ipv6_gtpu_eh)

    def test_outer_mac_ipv6_gre_ipv6_gtpu_ul(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv6_gre_ipv6_gtpu_ul)

    def test_outer_mac_ipv6_gre_ipv6_gtpu_dl(self):
        self.launch_testpmd(param_fdir=True)
        self.fdirprocess.flow_director_validate(tvs_outer_mac_ipv6_gre_ipv6_gtpu_dl)

    def test_negative_cases(self):
        negative_rules = [
            "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp dst is 13 / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 33 / mark id 13 / end",
            "flow create 0 ingress pattern eth / ipv6 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is a/ ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions mark / rss / end",
            "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc pdu_t is 2 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / tcp src is 13 dst is 23 / end actions queue index 3 / mark id 13 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / gre / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc pdu_t is 1 qfi is 0x3 / end actions drop / end",
        ]
        self.launch_testpmd(param_fdir=True)
        self.rssprocess.create_rule(negative_rules, check_stats=False)

    def test_exclusive_cases(self):
        result_list = []

        self.logger.info("Subcase 1: inner rule and outer rule")
        result = True
        rule_list = [
            "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 13 / mark id 13 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 1.1.2.14 dst is 1.1.2.15 / gre / ipv4 / udp / gtpu teid is 0x12 / gtp_psc qfi is 0x3 / end actions queue index 14 / mark id 14 / end",
        ]
        pkt = 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.14", dst="1.1.2.15")/GRE()/IP()/UDP()/GTP_U_Header(teid=0x12)/GTPPDUSessionContainer(QFI=0x3)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)'

        self.launch_testpmd(param_fdir=True)
        try:
            self.rssprocess.create_rule(rule_list)
        except Exception as e:
            self.logger.warning("Subcase 1 failed: %s" % e)
            result = False
        hashes, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt)
        for queue in queues:
            if "0xe" != queue:
                result = False
                self.logger.error("Error: queue index {} != 14".format(queue))
                continue
        self.dut.send_expect("flow destroy 0 rule 1", "testpmd>")
        hashes, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt)
        for queue in queues:
            if "0xd" != queue:
                result = False
                self.logger.error("Error: queue index {} != 13".format(queue))
                continue
        result_list.append(result)
        self.dut.send_expect("quit", "# ")
        self.logger.info("*********subcase test result %s" % result_list)

        self.logger.info("Subcase 2: rule with eh and rule without eh")
        result = True
        rule_list = [
            "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 13 / mark id 13 / end",
            "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 3 / mark id 3 / end",
        ]
        pkt = [
            'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
            'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        ]

        self.launch_testpmd(param_fdir=True)
        try:
            self.rssprocess.create_rule(rule_list)
        except Exception as e:
            self.logger.warning("Subcase 2 failed: %s" % e)
            result = False
        hashes, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt[0])
        for queue in queues:
            if "0xd" != queue:
                result = False
                self.logger.error("Error: queue index {} != 13".format(queue))
                continue

        hashes, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt[1])
        for queue in queues:
            if "0x3" != queue:
                result = False
                self.logger.error("Error: queue index {} != 3".format(queue))
                continue
        result_list.append(result)
        self.dut.send_expect("quit", "# ")
        self.logger.info("*********subcase test result %s" % result_list)

        self.logger.info("Subcase 3: rule with l4 and rule without l4")
        result = True
        rule_list = [
            "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 13 / mark id 13 / end",
            "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / udp src is 13 dst is 23 / end actions queue index 3 / mark id 3 / end",
        ]
        pkt = [
            'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")',
            'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP(sport=13, dport=23)',
        ]

        self.launch_testpmd(param_fdir=True)
        try:
            self.rssprocess.create_rule(rule_list)
        except Exception as e:
            self.logger.warning("Subcase 3 failed: %s" % e)
            result = False
        hashes, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt[0])
        for queue in queues:
            if "0xd" != queue:
                result = False
                self.logger.error("Error: queue index {} != 13".format(queue))
                continue

        hashes, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt[1])
        for queue in queues:
            if "0x3" != queue:
                result = False
                self.logger.error("Error: queue index {} != 3".format(queue))
                continue
        result_list.append(result)
        self.dut.send_expect("quit", "# ")
        self.logger.info("*********subcase test result %s" % result_list)

        self.logger.info("Subcase 4: rule with ul and rule without ul/dl")
        result = True
        rule_list = [
            "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 13 / mark id 13 / end",
            "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 3 / end",
        ]
        pkt = 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")'

        self.launch_testpmd(param_fdir=True)
        try:
            self.rssprocess.create_rule(rule_list)
        except Exception as e:
            self.logger.warning("Subcase 4 failed: %s" % e)
            result = False
        hashes, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt)
        for queue in queues:
            if "0x3" != queue:
                result = False
                self.logger.error("Error: queue index {} != 3".format(queue))
                continue
        self.dut.send_expect("flow destroy 0 rule 1", "testpmd>")
        hashes, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkt)
        for queue in queues:
            if "0xd" != queue:
                result = False
                self.logger.error("Error: queue index {} != 13".format(queue))
                continue
        result_list.append(result)
        self.dut.send_expect("quit", "# ")
        self.logger.info("*********subcase test result %s" % result_list)

        self.logger.info("Subcase 5: ipv4/ipv4/ipv4 rule and ipv4/ipv6/ipv4 rule")
        result = True
        rule1 = "flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 13 / mark id 13 / end"
        rule2 = "flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 3 / end"
        self.launch_testpmd(param_fdir=True)
        try:
            self.rssprocess.create_rule(rule1, check_stats=True)
            self.rssprocess.create_rule(rule2, check_stats=False)
        except Exception as e:
            self.logger.warning("Subcase 5 failed: %s" % e)
            result = False
        result_list.append(result)
        self.dut.send_expect("quit", "# ")
        self.logger.info("*********subcase test result %s" % result_list)
        for i in result_list:
            self.verify(i is True, "some subcase fail")
