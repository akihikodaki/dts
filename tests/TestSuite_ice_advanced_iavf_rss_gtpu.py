# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

import random
import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, check_supported_nic, skip_unsupported_pkg

from .rte_flow_common import RssProcessing

mac_ipv4_gtpu_ipv4_basic = {
    "ipv4-nonfrag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
    "ipv4-frag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)',
    "ipv4-icmp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)',
    "ipv4-tcp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP()/("X"*480)',
    "ipv4-udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)',
}

mac_ipv4_gtpu_ipv4_l3src_changed_pkt = eval(
    str(mac_ipv4_gtpu_ipv4_basic).replace("192.168.0.2", "192.168.1.2")
)
mac_ipv4_gtpu_ipv4_l3dst_changed_pkt = eval(
    str(mac_ipv4_gtpu_ipv4_basic).replace("192.168.0.1", "192.168.1.1")
)

mac_ipv4_gtpu_ipv4_l3dst_only = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_l3dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3dst_changed_pkt["ipv4-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3src_changed_pkt["ipv4-nonfrag"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3dst_changed_pkt["ipv4-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3src_changed_pkt["ipv4-frag"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3dst_changed_pkt["ipv4-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3src_changed_pkt["ipv4-icmp"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-tcp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3dst_changed_pkt["ipv4-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3src_changed_pkt["ipv4-tcp"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3dst_changed_pkt["ipv4-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3src_changed_pkt["ipv4-udp"],
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv4_l3src_only = eval(
    str(mac_ipv4_gtpu_ipv4_l3dst_only)
    .replace("mac_ipv4_gtpu_ipv4_l3dst", "mac_ipv4_gtpu_ipv4_l3src")
    .replace("l3-dst-only", "l3-src-only")
    .replace("check_hash_same", "hash_check_different")
    .replace("check_hash_different", "check_hash_same")
    .replace("hash_check_different", "check_hash_different")
)
mac_ipv4_gtpu_ipv4_all = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_all",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3dst_changed_pkt["ipv4-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3src_changed_pkt["ipv4-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-nonfrag"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3dst_changed_pkt["ipv4-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3src_changed_pkt["ipv4-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-frag"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3dst_changed_pkt["ipv4-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3src_changed_pkt["ipv4-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-icmp"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-tcp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3dst_changed_pkt["ipv4-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3src_changed_pkt["ipv4-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-tcp"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3dst_changed_pkt["ipv4-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_l3src_changed_pkt["ipv4-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-udp"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_different",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv4_gtpu = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_gtpu",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types gtpu end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-nonfrag"].replace(
                "teid=0x123456", "teid=0x12345"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-nonfrag"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-frag"].replace(
                "teid=0x123456", "teid=0x12345"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-frag"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-icmp"].replace(
                "teid=0x123456", "teid=0x12345"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-icmp"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-udp"].replace(
                "teid=0x123456", "teid=0x12345"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_basic["ipv4-udp"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv4_toeplitz = [
    mac_ipv4_gtpu_ipv4_l3dst_only,
    mac_ipv4_gtpu_ipv4_l3src_only,
    mac_ipv4_gtpu_ipv4_all,
    mac_ipv4_gtpu_ipv4_gtpu,
]

mac_ipv4_gtpu_ipv4_symmetric = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            "action": {"save_hash": "ipv4-nonfrag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
            "action": {"save_hash": "ipv4-frag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
            "action": {"save_hash": "ipv4-icmp"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
            "action": {"save_hash": "ipv4-udp"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP()/("X"*480)',
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-nonfrag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-frag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-icmp"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP()/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-udp"},
        },
    ],
}

mac_ipv4_gtpu_ipv6_symmetric = eval(
    str(mac_ipv4_gtpu_ipv4_symmetric)
    .replace("IPv6", "IPv61")
    .replace(
        'IP(dst="192.168.0.1",src="192.168.0.2"',
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
    )
    .replace(
        'IP(dst="192.168.0.2",src="192.168.0.1"',
        'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
    )
    .replace(", frag=6)", ")/IPv6ExtHdrFragment()")
    .replace(
        'IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(dst="192.168.0.1",src="192.168.0.2")',
    )
    .replace(
        'IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(src="192.168.0.1",dst="192.168.0.2")',
    )
    .replace("gtpu / ipv4", "gtpu / ipv6")
    .replace("types ipv4", "types ipv6")
)

mac_ipv4_gtpu_ipv4_udp_symmetric = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            "action": {"save_hash": "basic_with_rule"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_no_hash_or_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            "action": "check_no_hash_or_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_no_hash_or_different",
        },
    ],
}

mac_ipv4_gtpu_ipv6_udp_symmetric = eval(
    str(mac_ipv4_gtpu_ipv4_udp_symmetric)
    .replace("IPv6", "IPv61")
    .replace(
        'IP(dst="192.168.0.1",src="192.168.0.2"',
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
    )
    .replace(
        'IP(dst="192.168.0.2",src="192.168.0.1"',
        'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
    )
    .replace(
        'IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(dst="192.168.0.1",src="192.168.0.2")',
    )
    .replace(
        'IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(src="192.168.0.1",dst="192.168.0.2")',
    )
    .replace("gtpu / ipv4", "gtpu / ipv6")
    .replace("types ipv4-udp", "types ipv6-udp")
)

mac_ipv4_gtpu_ipv4_tcp_symmetric = eval(
    str(mac_ipv4_gtpu_ipv4_udp_symmetric)
    .replace("TCP(", "TCP1(")
    .replace("UDP(sport", "TCP(sport")
    .replace("TCP1", "UDP")
    .replace("udp / end", "tcp / end ")
    .replace("ipv4-udp", "ipv4-tcp")
    .replace("udp_symmetric", "tcp_symmetric")
)

mac_ipv4_gtpu_ipv6_tcp_symmetric = eval(
    str(mac_ipv4_gtpu_ipv4_tcp_symmetric)
    .replace("IPv6", "IPv61")
    .replace(
        'IP(dst="192.168.0.1",src="192.168.0.2"',
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
    )
    .replace(
        'IP(dst="192.168.0.2",src="192.168.0.1"',
        'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
    )
    .replace(
        'IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(dst="192.168.0.1",src="192.168.0.2")',
    )
    .replace(
        'IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(src="192.168.0.1",dst="192.168.0.2")',
    )
    .replace("gtpu / ipv4", "gtpu / ipv6")
    .replace("types ipv4-tcp", "types ipv6-tcp")
)

mac_ipv4_gtpu_eh_dl_ipv4_symmetric = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            "action": {"save_hash": "ipv4-nonfrag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
            "action": {"save_hash": "ipv4-frag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
            "action": {"save_hash": "ipv4-icmp"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
            "action": {"save_hash": "ipv4-udp"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP()/("X"*480)',
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-nonfrag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-frag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-icmp"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP()/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-udp"},
        },
    ],
}
mac_ipv4_gtpu_eh_ul_ipv4_symmetric = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv4_symmetric)
    .replace("(type=1", "(type=2")
    .replace("(type=0", "(type=1")
    .replace("(type=2", "(type=0")
    .replace("eh_dl", "eh_ul")
    .replace("gtp_psc pdu_t is 0", "gtp_psc pdu_t is 1")
)

mac_ipv4_gtpu_eh_ipv4_symmetric = [
    mac_ipv4_gtpu_eh_dl_ipv4_symmetric,
    mac_ipv4_gtpu_eh_ul_ipv4_symmetric,
]

mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            "action": "save_hash",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_no_hash_or_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            "action": "check_no_hash_or_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_no_hash_or_different",
        },
    ],
}
mac_ipv4_gtpu_eh_ul_ipv4_udp_symmetric = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric)
    .replace("(type=1", "(type=2")
    .replace("(type=0", "(type=1")
    .replace("(type=2", "(type=0")
    .replace("gtp_psc pdu_t is 0", "gtp_psc pdu_t is 1")
    .replace("eh_dl", "eh_ul")
)
mac_ipv4_gtpu_eh_ipv4_udp_symmetric = [
    mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric,
    mac_ipv4_gtpu_eh_ul_ipv4_udp_symmetric,
]

mac_ipv4_gtpu_eh_ipv4_tcp_symmetric = [
    eval(
        str(element)
        .replace("TCP", "TCP1")
        .replace("udp", "tcp")
        .replace("UDP(sport", "TCP(sport")
        .replace("TCP1", "UDP")
        .replace("ipv4 / tcp / gtpu", "ipv4 / udp / gtpu")
    )
    for element in mac_ipv4_gtpu_eh_ipv4_udp_symmetric
]

mac_ipv4_gtpu_eh_ipv6_symmetric = eval(
    str(mac_ipv4_gtpu_eh_ipv4_symmetric)
    .replace("IPv6", "IPv61")
    .replace(
        'IP(dst="192.168.0.1",src="192.168.0.2"',
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
    )
    .replace(
        'IP(dst="192.168.0.2",src="192.168.0.1"',
        'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
    )
    .replace(", frag=6)", ")/IPv6ExtHdrFragment()")
    .replace(
        'IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(dst="192.168.0.1",src="192.168.0.2")',
    )
    .replace(
        'IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(src="192.168.0.1",dst="192.168.0.2")',
    )
    .replace("ipv4 / end", "ipv6 / end")
    .replace("types ipv4", "types ipv6")
    .replace("ipv4_symmetric", "ipv6_symmetric")
)

mac_ipv4_gtpu_eh_ipv6_udp_symmetric = eval(
    str(mac_ipv4_gtpu_eh_ipv4_udp_symmetric)
    .replace("IPv6", "IPv61")
    .replace(
        'IP(dst="192.168.0.1",src="192.168.0.2"',
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
    )
    .replace(
        'IP(dst="192.168.0.2",src="192.168.0.1"',
        'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
    )
    .replace(
        'IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(dst="192.168.0.1",src="192.168.0.2")',
    )
    .replace(
        'IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(src="192.168.0.1",dst="192.168.0.2")',
    )
    .replace("ipv4 / udp / end", "ipv6 / udp / end")
    .replace("types ipv4-udp", "types ipv6-udp")
    .replace("ipv4_udp_symmetric", "ipv6_udp_symmetric")
)


mac_ipv4_gtpu_eh_ipv6_tcp_symmetric = eval(
    str(mac_ipv4_gtpu_eh_ipv4_tcp_symmetric)
    .replace("IPv6", "IPv61")
    .replace(
        'IP(dst="192.168.0.1",src="192.168.0.2"',
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
    )
    .replace(
        'IP(dst="192.168.0.2",src="192.168.0.1"',
        'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
    )
    .replace(
        'IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(dst="192.168.0.1",src="192.168.0.2")',
    )
    .replace(
        'IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        'IP(src="192.168.0.1",dst="192.168.0.2")',
    )
    .replace("ipv4 / tcp / end", "ipv6 / tcp / end")
    .replace("types ipv4-tcp", "types ipv6-tcp")
    .replace("ipv4_tcp_symmetric", "ipv6_tcp_symmetric")
)

mac_ipv4_gtpu_ipv4_udp_basic = {
    "ipv4-udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
}

mac_ipv4_gtpu_ipv4_udp_l3dst = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_l3dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv4_udp_l3src = eval(
    str(mac_ipv4_gtpu_ipv4_udp_l3dst)
    .replace("mac_ipv4_gtpu_ipv4_udp_l3dst", "mac_ipv4_gtpu_ipv4_udp_l3src")
    .replace("l3-dst-only", "l3-src-only")
    .replace("check_hash_same", "hash_check_different")
    .replace("check_hash_different", "check_hash_same")
    .replace("hash_check_different", "check_hash_different")
)

mac_ipv4_gtpu_ipv4_udp_l3src_l4src = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_l3src_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "sport=22", "sport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"]
            .replace("dport=23", "dport=33")
            .replace("192.168.0.1", "192.168.1.1"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv4_udp_l3src_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_l3src_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"]
            .replace("sport=22", "sport=32")
            .replace("192.168.0.1", "192.168.1.1"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv4_udp_l3dst_l4src = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_l3dst_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "sport=22", "sport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"]
            .replace("dport=23", "dport=33")
            .replace("192.168.0.2", "192.168.1.2"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"]
            .replace("sport=22", "sport=32")
            .replace("192.168.0.2", "192.168.1.2"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}
mac_ipv4_gtpu_ipv4_udp_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"]
            .replace("sport=22", "sport=32")
            .replace("192.168.0", "192.168.1"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}
mac_ipv4_gtpu_ipv4_udp_l4src = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"]
            .replace("dport=23", "dport=32")
            .replace("192.168.0", "192.168.1"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv4_udp_all = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_all",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "teid=0x123456", "teid=0x12345"
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv4_udp_l3 = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_l3",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv4_udp_basic["ipv4-udp"].replace(
                "sport=22,dport=23", "sport=12,dport=13"
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv4_udp_toeplitz = [
    mac_ipv4_gtpu_ipv4_udp_l3dst,
    mac_ipv4_gtpu_ipv4_udp_l3src,
    mac_ipv4_gtpu_ipv4_udp_l3dst_l4src,
    mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst,
    mac_ipv4_gtpu_ipv4_udp_l3src_l4src,
    mac_ipv4_gtpu_ipv4_udp_l3src_l4dst,
    mac_ipv4_gtpu_ipv4_udp_l4src,
    mac_ipv4_gtpu_ipv4_udp_l4dst,
    mac_ipv4_gtpu_ipv4_udp_all,
    mac_ipv4_gtpu_ipv4_udp_l3,
]

mac_ipv4_gtpu_ipv4_tcp_toeplitz = [
    eval(
        str(element)
        .replace("TCP", "TCP1")
        .replace("udp", "tcp")
        .replace("UDP(sport", "TCP(sport")
        .replace("TCP1", "UDP")
        .replace("ipv4 / tcp / gtpu", "ipv4 / udp / gtpu")
    )
    for element in mac_ipv4_gtpu_ipv4_udp_toeplitz
]

mac_ipv4_gtpu_ipv6_basic = {
    "ipv6-nonfrag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    "ipv6-frag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
    "ipv6-icmp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
    "ipv6-tcp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6('
    'src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP()/("X"*480)',
    "ipv6-udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/("X"*480)',
}

mac_ipv4_gtpu_ipv6_l3src_changed_pkt = eval(
    str(mac_ipv4_gtpu_ipv6_basic).replace("ABAB", "1212")
)
mac_ipv4_gtpu_ipv6_l3dst_changed_pkt = eval(
    str(mac_ipv4_gtpu_ipv6_basic).replace("CDCD", "3434")
)

mac_ipv4_gtpu_ipv6_l3dst_only = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_l3dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-nonfrag"],
            "action": {"save_hash", "ipv6-nonfrag"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-nonfrag"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-frag"],
            "action": {"save_hash", "ipv6-frag"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-frag"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-icmp"],
            "action": {"save_hash", "ipv6-icmp"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-icmp"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-tcp"],
            "action": {"save_hash", "ipv6-tcp"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-tcp"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-udp"],
            "action": {"save_hash", "ipv6-udp"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-udp"],
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv6_l3src_only = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_l3src_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-nonfrag"],
            "action": {"save_hash", "ipv6-nonfrag"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-nonfrag"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-frag"],
            "action": {"save_hash", "ipv6-frag"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-frag"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-icmp"],
            "action": {"save_hash", "ipv6-icmp"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-icmp"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-tcp"],
            "action": {"save_hash", "ipv6-tcp"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-tcp"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-udp"],
            "action": {"save_hash", "ipv6-udp"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-udp"],
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv6_l3src_only = eval(
    str(mac_ipv4_gtpu_ipv6_l3dst_only)
    .replace("mac_ipv4_gtpu_ipv6_l3dst", "mac_ipv4_gtpu_ipv6_l3src")
    .replace("l3-dst-only", "l3-src-only")
    .replace("check_hash_same", "hash_check_different")
    .replace("check_hash_different", "check_hash_same")
    .replace("hash_check_different", "check_hash_different")
)
mac_ipv4_gtpu_ipv6_all = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_all",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-nonfrag"],
            "action": {"save_hash", "ipv6-nonfrag"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-nonfrag"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-frag"],
            "action": {"save_hash", "ipv6-frag"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-frag"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-icmp"],
            "action": {"save_hash", "ipv6-icmp"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-icmp"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-tcp"],
            "action": {"save_hash", "ipv6-tcp"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-tcp"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-udp"],
            "action": {"save_hash", "ipv6-udp"},
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3dst_changed_pkt["ipv6-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_l3src_changed_pkt["ipv6-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-udp"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_different",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv6_gtpu = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_gtpu",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types gtpu end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-nonfrag"].replace(
                "teid=0x123456", "teid=0x12345"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-nonfrag"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-frag"].replace(
                "teid=0x123456", "teid=0x12345"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-frag"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-icmp"].replace(
                "teid=0x123456", "teid=0x12345"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-icmp"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-udp"].replace(
                "teid=0x123456", "teid=0x12345"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_basic["ipv6-udp"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv6_toeplitz = [
    mac_ipv4_gtpu_ipv6_l3dst_only,
    mac_ipv4_gtpu_ipv6_l3src_only,
    mac_ipv4_gtpu_ipv6_all,
    mac_ipv4_gtpu_ipv6_gtpu,
]

mac_ipv4_gtpu_ipv6_udp_basic = {
    "ipv6-udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
}
mac_ipv4_gtpu_ipv6_udp_l3dst = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_udp_l3dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "CDCD", "3434"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "ABAB", "1212"
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv6_udp_l3src = eval(
    str(mac_ipv4_gtpu_ipv6_udp_l3dst)
    .replace("mac_ipv4_gtpu_ipv6_udp_l3dst", "mac_ipv4_gtpu_ipv6_udp_l3src")
    .replace("l3-dst-only", "l3-src-only")
    .replace("check_hash_same", "hash_check_different")
    .replace("check_hash_different", "check_hash_same")
    .replace("hash_check_different", "check_hash_different")
)

mac_ipv4_gtpu_ipv6_udp_l3src_l4src = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_udp_l3src_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "ABAB", "1212"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "sport=22", "sport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"]
            .replace("dport=23", "dport=33")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv6_udp_l3src_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_udp_l3src_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "ABAB", "1212"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"]
            .replace("sport=22", "sport=32")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv6_udp_l3dst_l4src = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_udp_l3dst_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "CDCD", "3434"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "sport=22", "sport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"]
            .replace("dport=23", "dport=33")
            .replace("ABAB", "1212"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv6_udp_l3dst_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_udp_l3dst_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "CDCD", "3434"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"]
            .replace("sport=22", "sport=32")
            .replace("ABAB", "1212"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}
mac_ipv4_gtpu_ipv6_udp_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_udp_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"]
            .replace("sport=22", "sport=32")
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}
mac_ipv4_gtpu_ipv6_udp_l4src = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_udp_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"]
            .replace("dport=23", "dport=32")
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv6_udp_all = {
    "sub_casename": "mac_ipv4_gtpu_ipv6_udp_all",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "CDCD", "3434"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "ABAB", "1212"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_ipv6_udp_basic["ipv6-udp"].replace(
                "teid=0x123456", "teid=0x12345"
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_ipv6_udp_toeplitz = [
    mac_ipv4_gtpu_ipv6_udp_l3dst,
    mac_ipv4_gtpu_ipv6_udp_l3src,
    mac_ipv4_gtpu_ipv6_udp_l3dst_l4src,
    mac_ipv4_gtpu_ipv6_udp_l3dst_l4dst,
    mac_ipv4_gtpu_ipv6_udp_l3src_l4src,
    mac_ipv4_gtpu_ipv6_udp_l3src_l4dst,
    mac_ipv4_gtpu_ipv6_udp_l4src,
    mac_ipv4_gtpu_ipv6_udp_l4dst,
    mac_ipv4_gtpu_ipv6_udp_all,
]

mac_ipv4_gtpu_ipv6_tcp_toeplitz = [
    eval(
        str(element)
        .replace("TCP", "TCP1")
        .replace("udp", "tcp")
        .replace("UDP(sport", "TCP(sport")
        .replace("TCP1", "UDP")
        .replace("ipv4 / tcp / gtpu", "ipv4 / udp / gtpu")
    )
    for element in mac_ipv4_gtpu_ipv6_udp_toeplitz
]

mac_ipv4_gtpu_eh_dl_ipv4_basic = {
    "ipv4-nonfrag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
    "ipv4-frag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
    "ipv4-icmp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
    "ipv4-udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
    "ipv4-tcp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP()/("X"*480)',
}

mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv4_basic).replace("192.168.0.2", "192.168.1.2")
)
mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv4_basic).replace("192.168.0.1", "192.168.1.1")
)

mac_ipv4_gtpu_eh_dl_ipv4_l3dst_only = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_l3dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt["ipv4-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt["ipv4-nonfrag"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt["ipv4-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt["ipv4-frag"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt["ipv4-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt["ipv4-icmp"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt["ipv4-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt["ipv4-udp"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-tcp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt["ipv4-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt["ipv4-tcp"],
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv4_l3src_only = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv4_l3dst_only)
    .replace("eh_dl_ipv4_l3dst", "eh_ul_ipv4_l3src")
    .replace("l3-dst-only", "l3-src-only")
    .replace("check_hash_same", "hash_check_different")
    .replace("check_hash_different", "check_hash_same")
    .replace("hash_check_different", "check_hash_different")
)
mac_ipv4_gtpu_eh_dl_ipv4_all = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_all",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt["ipv4-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt["ipv4-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-nonfrag"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt["ipv4-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt["ipv4-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-frag"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt["ipv4-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt["ipv4-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-icmp"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt["ipv4-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt["ipv4-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-udp"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-tcp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt["ipv4-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt["ipv4-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_basic["ipv4-tcp"].replace(
                "192.168.0.", "192.168.1."
            ),
            "action": "check_hash_different",
        },
    ],
    "post-test": [],
}


mac_ipv4_gtpu_eh_dl_ipv4 = [
    mac_ipv4_gtpu_eh_dl_ipv4_l3dst_only,
    mac_ipv4_gtpu_eh_dl_ipv4_l3src_only,
    mac_ipv4_gtpu_eh_dl_ipv4_all,
]

mac_ipv4_gtpu_eh_ul_ipv4 = [
    eval(
        str(element)
        .replace("(type=1", "(type=2")
        .replace("(type=0", "(type=1")
        .replace("(type=2", "(type=0")
        .replace("gtp_psc pdu_t is 0", "gtp_psc pdu_t is 1")
        .replace("eh_dl", "eh_ul")
    )
    for element in mac_ipv4_gtpu_eh_dl_ipv4
]

mac_ipv4_gtpu_eh_ipv4_toeplitz = mac_ipv4_gtpu_eh_dl_ipv4 + mac_ipv4_gtpu_eh_ul_ipv4

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic = {
    "ipv4-nonfrag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
    "ipv4-nonfrag_ul": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
    "ipv4-frag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
    "ipv4-icmp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
    "ipv4-udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt = eval(
    str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic).replace("192.168.0.2", "192.168.1.2")
)
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt = eval(
    str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic).replace("192.168.0.1", "192.168.1.1")
)

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_only = {
    "sub_casename": "mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt[
                "ipv4-nonfrag"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt[
                "ipv4-nonfrag"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-nonfrag_ul"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt[
                "ipv4-nonfrag_ul"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt[
                "ipv4-nonfrag_ul"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt[
                "ipv4-frag"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt[
                "ipv4-frag"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt[
                "ipv4-icmp"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt[
                "ipv4-icmp"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt[
                "ipv4-udp"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt[
                "ipv4-udp"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_only = eval(
    str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_only)
    .replace("ul_dl_ipv4_l3dst", "ul_dl_ipv4_l3src")
    .replace("l3-dst-only", "l3-src-only")
    .replace(
        'dst="192.168.0.1",src="192.168.1.2"', 'dst="192.168.0.1",src="192.168.1.3"'
    )
    .replace(
        'dst="192.168.1.1",src="192.168.0.2"', 'dst="192.168.0.1",src="192.168.1.2"'
    )
    .replace(
        'dst="192.168.0.1",src="192.168.1.3"', 'dst="192.168.1.1",src="192.168.0.2"'
    )
)
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_all = {
    "sub_casename": "mac_ipv4_gtpu_eh_without_ul_dl_ipv4_all",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt[
                "ipv4-nonfrag"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt[
                "ipv4-nonfrag"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-nonfrag"
            ].replace("192.168.0.", "192.168.1."),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-nonfrag"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-nonfrag_ul"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt[
                "ipv4-nonfrag_ul"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt[
                "ipv4-nonfrag_ul"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-nonfrag_ul"
            ].replace("192.168.0.", "192.168.1."),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-nonfrag_ul"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt[
                "ipv4-frag"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt[
                "ipv4-frag"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-frag"
            ].replace("192.168.0.", "192.168.1."),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-frag"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt[
                "ipv4-icmp"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt[
                "ipv4-icmp"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-icmp"
            ].replace("192.168.0.", "192.168.1."),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-icmp"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt[
                "ipv4-udp"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt[
                "ipv4-udp"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-udp"
            ].replace("192.168.0.", "192.168.1."),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-udp"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_gtpu = {
    "sub_casename": "mac_ipv4_gtpu_eh_without_ul_dl_ipv4_gtpu",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types gtpu end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-nonfrag"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-nonfrag"
            ].replace("192.168.0.", "192.168.1."),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-nonfrag_ul"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-nonfrag_ul"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-nonfrag_ul"
            ].replace("192.168.0.", "192.168.1."),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-frag"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-frag"
            ].replace("192.168.0.", "192.168.1."),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-icmp"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-icmp"
            ].replace("192.168.0.", "192.168.1."),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-udp"
            ].replace("0x123456", "0x12345"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic[
                "ipv4-udp"
            ].replace("192.168.0.", "192.168.1."),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz = [
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_all,
]

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic = {
    "dl": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
    "ul": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_only = {
    "sub_casename": "mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"]
            .replace("192.168.0.2", "192.168.1.2")
            .replace("sport=22, dport=23", "sport=32, dport=33"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"]
            .replace("192.168.0.2", "192.168.1.2")
            .replace("sport=22, dport=23", "sport=32, dport=33"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_only = eval(
    str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_only)
    .replace("ul_dl_ipv4_udp_l3dst", "ul_dl_ipv4_udp_l3src")
    .replace("l3-dst-only", "l3-src-only")
    .replace(
        'dst="192.168.0.1",src="192.168.1.2"', 'dst="192.168.0.1",src="192.168.1.3"'
    )
    .replace(
        'dst="192.168.1.1",src="192.168.0.2"', 'dst="192.168.0.1",src="192.168.1.2"'
    )
    .replace(
        'dst="192.168.0.1",src="192.168.1.3"', 'dst="192.168.1.1",src="192.168.0.2"'
    )
)
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src = {
    "sub_casename": "mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"]
            .replace("192.168.0.1", "192.168.1.1")
            .replace("dport=23", "dport=33")
            .replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"]
            .replace("192.168.0.1", "192.168.1.1")
            .replace("dport=23", "dport=33")
            .replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4dst = eval(
    str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src)
    .replace("udp_l3src_l4src", "udp_l3src_l4dst")
    .replace("l4-src-only", "l4-dst-only")
    .replace("sport=32, dport=23", "sport=22, dport=34")
    .replace("sport=22, dport=33", "sport=32, dport=23")
)
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4src = eval(
    str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src)
    .replace("udp_l3src_l4src", "udp_l3dst_l4src")
    .replace("l3-src-only", "l3-dst-only")
    .replace(
        'dst="192.168.0.1",src="192.168.1.2"', 'dst="192.168.0.1",src="192.168.1.3"'
    )
    .replace(
        'dst="192.168.1.1",src="192.168.0.2"', 'dst="192.168.0.1",src="192.168.1.2"'
    )
    .replace(
        'dst="192.168.0.1",src="192.168.1.3"', 'dst="192.168.1.1",src="192.168.0.2"'
    )
)
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4dst = eval(
    str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4src)
    .replace("udp_l3dst_l4src", "udp_l3dst_l4dst")
    .replace("l3-src-only", "l3-dst-only")
    .replace("l4-src-only", "l4-dst-only")
    .replace("sport=32, dport=23", "sport=22, dport=34")
    .replace("sport=22, dport=33", "sport=32, dport=23")
)
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only = {
    "sub_casename": "mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"]
            .replace("192.168.0", "192.168.1")
            .replace("dport=23", "dport=33")
            .replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"]
            .replace("192.168.0", "192.168.1")
            .replace("dport=23", "dport=33")
            .replace("0x123456", "0x12345"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4dst_only = eval(
    str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only)
    .replace("udp_l4src_only", "udp_l4dst_only")
    .replace("l4-src-only", "l4-dst-only")
    .replace("sport=32, dport=23", "sport=22, dport=34")
    .replace("sport=22, dport=33", "sport=32, dport=23")
)
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp = {
    "sub_casename": "mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"].replace(
                "0x123456", "0x12345"
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3 = {
    "sub_casename": "mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["dl"].replace(
                "sport=22, dport=23", "sport=12, dport=13"
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic["ul"].replace(
                "sport=22, dport=23", "sport=12, dport=13"
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz = [
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4dst,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4src,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4dst,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4dst_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3,
]

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz = [
    eval(
        str(element)
        .replace("TCP", "TCP1")
        .replace("udp", "tcp")
        .replace("UDP(sport", "TCP(sport")
        .replace("TCP1", "UDP")
        .replace("ipv4 / tcp / gtpu", "ipv4 / udp / gtpu")
    )
    for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz
]

mac_ipv4_gtpu_eh_without_ul_dl_ipv6_toeplitz = [
    eval(
        str(element)
        .replace("gtp_psc / ipv4", "gtp_psc / ipv6")
        .replace("types ipv4", "types ipv6")
        .replace("ul_dl_ipv4", "ul_dl_ipv6")
        .replace(", frag=6)", ")/IPv6ExtHdrFragment()")
        .replace(
            'IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
            'IP(dst="192.168.0.3", src="192.168.0.3"',
        )
        .replace(
            'IP(dst="192.168.0.1",src="192.168.0.2"',
            'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        )
        .replace(
            'IP(dst="192.168.1.1",src="192.168.0.2"',
            'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        )
        .replace(
            'IP(dst="192.168.0.1",src="192.168.1.2"',
            'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"',
        )
        .replace(
            'IP(dst="192.168.1.1",src="192.168.1.2"',
            'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"',
        )
        .replace(
            'IP(dst="192.168.0.3",src="192.168.0.3"',
            'IP(dst="192.168.0.1",src="192.168.0.2"',
        )
    )
    for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz
]

mac_ipv4_gtpu_eh_without_ul_dl_ipv6_udp_toeplitz = [
    eval(
        str(element)
        .replace("gtp_psc / ipv4", "gtp_psc / ipv6")
        .replace("ipv4-udp", "ipv6-udp")
        .replace("types ipv4", "types ipv6")
        .replace("ul_dl_ipv4_udp", "ul_dl_ipv6_udp")
        .replace(
            'IP(dst="192.168.0.1",src="192.168.0.2"',
            'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        )
        .replace(
            'IP(dst="192.168.1.1",src="192.168.0.2"',
            'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        )
        .replace(
            'IP(dst="192.168.0.1",src="192.168.1.2"',
            'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"',
        )
        .replace(
            'IP(dst="192.168.1.1",src="192.168.1.2"',
            'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"',
        )
    )
    for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz
]

mac_ipv4_gtpu_eh_without_ul_dl_ipv6_tcp_toeplitz = [
    eval(
        str(element)
        .replace("gtp_psc / ipv4", "gtp_psc / ipv6")
        .replace("ipv4 / tcp", "ipv6 / tcp")
        .replace("types ipv4", "types ipv6")
        .replace("ipv4-tcp", "ipv6-tcp")
        .replace("ul_dl_ipv4_tcp", "ul_dl_ipv6_tcp")
        .replace(
            'IP(dst="192.168.0.1",src="192.168.0.2"',
            'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        )
        .replace(
            'IP(dst="192.168.1.1",src="192.168.0.2"',
            'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        )
        .replace(
            'IP(dst="192.168.0.1",src="192.168.1.2"',
            'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"',
        )
        .replace(
            'IP(dst="192.168.1.1",src="192.168.1.2"',
            'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"',
        )
    )
    for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz
]

mac_ipv4_gtpu_eh_dl_ipv4_udp_basic = {
    "ipv4-udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
}
mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst)
    .replace("mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst", "mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src")
    .replace("l3-dst-only", "l3-src-only")
    .replace("check_hash_same", "hash_check_different")
    .replace("check_hash_different", "check_hash_same")
    .replace("hash_check_different", "check_hash_different")
)

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4src = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "sport=22", "sport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"]
            .replace("dport=23", "dport=33")
            .replace("192.168.0.1", "192.168.1.1"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"]
            .replace("sport=22", "sport=32")
            .replace("192.168.0.1", "192.168.1.1"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4src = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "sport=22", "sport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"]
            .replace("dport=23", "dport=33")
            .replace("192.168.0.2", "192.168.1.2"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"]
            .replace("sport=22", "sport=32")
            .replace("192.168.0.2", "192.168.1.2"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}
mac_ipv4_gtpu_eh_dl_ipv4_udp_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_udp_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"]
            .replace("sport=22", "sport=32")
            .replace("192.168.0", "192.168.1"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}
mac_ipv4_gtpu_eh_dl_ipv4_udp_l4src = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_udp_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"]
            .replace("dport=23", "dport=32")
            .replace("192.168.0", "192.168.1"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_all = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_udp_all",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3 = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv4_udp_l3",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.1", "192.168.1.1"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"].replace(
                "192.168.0.2", "192.168.1.2"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv4_udp_basic["ipv4-udp"]
            .replace("sport=22", "sport=12")
            .replace("dport=23", "dport=13"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_toeplitz = [
    mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst,
    mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src,
    mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4src,
    mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4dst,
    mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4src,
    mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4dst,
    mac_ipv4_gtpu_eh_dl_ipv4_udp_l4src,
    mac_ipv4_gtpu_eh_dl_ipv4_udp_l4dst,
    mac_ipv4_gtpu_eh_dl_ipv4_udp_all,
    mac_ipv4_gtpu_eh_dl_ipv4_udp_l3,
]

mac_ipv4_gtpu_eh_ul_ipv4_udp_toeplitz = [
    eval(
        str(element)
        .replace("(type=1", "(type=2")
        .replace("(type=0", "(type=1")
        .replace("(type=2", "(type=0")
        .replace("gtp_psc pdu_t is 0", "gtp_psc pdu_t is 1")
        .replace("eh_dl", "eh_ul")
    )
    for element in mac_ipv4_gtpu_eh_dl_ipv4_udp_toeplitz
]

mac_ipv4_gtpu_eh_ipv4_udp_toeplitz = (
    mac_ipv4_gtpu_eh_dl_ipv4_udp_toeplitz + mac_ipv4_gtpu_eh_ul_ipv4_udp_toeplitz
)

mac_ipv4_gtpu_eh_ipv4_tcp_toeplitz = [
    eval(
        str(element)
        .replace("TCP", "TCP1")
        .replace("udp", "tcp")
        .replace("UDP(sport", "TCP(sport")
        .replace("TCP1", "UDP")
        .replace("ipv4 / tcp / gtpu", "ipv4 / udp / gtpu")
    )
    for element in mac_ipv4_gtpu_eh_ipv4_udp_toeplitz
]

mac_ipv4_gtpu_eh_dl_ipv6_basic = {
    "ipv6-nonfrag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    "ipv6-frag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
    "ipv6-icmp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
    "ipv6-udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/("X"*480)',
    "ipv6-tcp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP()/("X"*480)',
}

mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv6_basic).replace("ABAB", "1212")
)
mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv6_basic).replace("CDCD", "3434")
)

mac_ipv4_gtpu_eh_dl_ipv6_l3dst_only = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv6_l3dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt["ipv6-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt["ipv6-nonfrag"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt["ipv6-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt["ipv6-frag"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt["ipv6-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt["ipv6-icmp"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt["ipv6-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt["ipv6-udp"],
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-tcp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt["ipv6-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt["ipv6-tcp"],
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv6_l3src_only = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv6_l3dst_only)
    .replace("mac_ipv4_gtpu_eh_dl_ipv6_l3dst", "mac_ipv4_gtpu_eh_dl_ipv6_l3src")
    .replace("l3-dst-only", "l3-src-only")
    .replace("check_hash_same", "hash_check_different")
    .replace("check_hash_different", "check_hash_same")
    .replace("hash_check_different", "check_hash_different")
)
mac_ipv4_gtpu_eh_dl_ipv6_all = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv6_all",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-nonfrag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt["ipv6-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt["ipv6-nonfrag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-nonfrag"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-frag"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt["ipv6-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt["ipv6-frag"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-frag"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-icmp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt["ipv6-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt["ipv6-icmp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-icmp"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt["ipv6-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt["ipv6-udp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-udp"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-tcp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt["ipv6-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt["ipv6-tcp"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_basic["ipv6-tcp"]
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_different",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv6_toeplitz = [
    mac_ipv4_gtpu_eh_dl_ipv6_l3dst_only,
    mac_ipv4_gtpu_eh_dl_ipv6_l3src_only,
    mac_ipv4_gtpu_eh_dl_ipv6_all,
]

mac_ipv4_gtpu_eh_ul_ipv6_toeplitz = [
    eval(
        str(element)
        .replace("(type=1", "(type=2")
        .replace("(type=0", "(type=1")
        .replace("(type=2", "(type=0")
        .replace("gtp_psc pdu_t is 0", "gtp_psc pdu_t is 1")
        .replace("eh_dl", "eh_ul")
    )
    for element in mac_ipv4_gtpu_eh_dl_ipv6_toeplitz
]

mac_ipv4_gtpu_eh_ipv6_toeplitz = (
    mac_ipv4_gtpu_eh_dl_ipv6_toeplitz + mac_ipv4_gtpu_eh_ul_ipv6_toeplitz
)

mac_ipv4_gtpu_eh_dl_ipv6_udp_basic = {
    "ipv6-udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
}
mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "CDCD", "3434"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "ABAB", "1212"
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst)
    .replace("mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst", "mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src")
    .replace("l3-dst-only", "l3-src-only")
    .replace("check_hash_same", "hash_check_different")
    .replace("check_hash_different", "check_hash_same")
    .replace("hash_check_different", "check_hash_different")
)

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4src = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "ABAB", "1212"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "sport=22", "sport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"]
            .replace("dport=23", "dport=33")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "ABAB", "1212"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"]
            .replace("sport=22", "sport=32")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4src = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "CDCD", "3434"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "sport=22", "sport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"]
            .replace("dport=23", "dport=33")
            .replace("ABAB", "1212"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "CDCD", "3434"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"]
            .replace("sport=22", "sport=32")
            .replace("ABAB", "1212"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}
mac_ipv4_gtpu_eh_dl_ipv6_udp_l4dst = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv6_udp_l4dst",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"]
            .replace("sport=22", "sport=32")
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}
mac_ipv4_gtpu_eh_dl_ipv6_udp_l4src = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv6_udp_l4src",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"]
            .replace("dport=23", "dport=32")
            .replace("ABAB", "1212")
            .replace("CDCD", "3434"),
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_all = {
    "sub_casename": "mac_ipv4_gtpu_eh_dl_ipv6_udp_all",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"],
            "action": "save_hash",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "sport=22", "sport=32"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "dport=23", "dport=33"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "CDCD", "3434"
            ),
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_eh_dl_ipv6_udp_basic["ipv6-udp"].replace(
                "ABAB", "1212"
            ),
            "action": "check_hash_different",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_toeplitz = [
    mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst,
    mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src,
    mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4src,
    mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4dst,
    mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4src,
    mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4dst,
    mac_ipv4_gtpu_eh_dl_ipv6_udp_l4src,
    mac_ipv4_gtpu_eh_dl_ipv6_udp_l4dst,
    mac_ipv4_gtpu_eh_dl_ipv6_udp_all,
]
mac_ipv4_gtpu_eh_ul_ipv6_udp_toeplitz = [
    eval(
        str(element)
        .replace("(type=1", "(type=2")
        .replace("(type=0", "(type=1")
        .replace("(type=2", "(type=0")
        .replace("gtp_psc pdu_t is 0", "gtp_psc pdu_t is 1")
        .replace("eh_dl", "eh_ul")
    )
    for element in mac_ipv4_gtpu_eh_dl_ipv6_udp_toeplitz
]
mac_ipv4_gtpu_eh_ipv6_udp_toeplitz = (
    mac_ipv4_gtpu_eh_dl_ipv6_udp_toeplitz + mac_ipv4_gtpu_eh_ul_ipv6_udp_toeplitz
)

mac_ipv4_gtpu_eh_ipv6_tcp_toeplitz = [
    eval(
        str(element)
        .replace("TCP", "TCP1")
        .replace("udp", "tcp")
        .replace("UDP(sport", "TCP(sport")
        .replace("TCP1", "UDP")
        .replace("ipv4 / tcp / gtpu", "ipv4 / udp / gtpu")
    )
    for element in mac_ipv4_gtpu_eh_ipv6_udp_toeplitz
]

inner_l4_mac_ipv4_gtpu_ipv4_udp_tcp = {
    "sub_casename": "mac_ipv4_gtpu_ipv4_udp_tcp",
    "port_id": 0,
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end",
    ],
    "test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            "action": "save_hash",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            "action": "check_hash_different",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            "action": "save_or_no_hash",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            "action": "check_hash_same_or_no_hash",
        },
    ],
}
inner_l4_mac_ipv6_gtpu_ipv4_udp_tcp = eval(
    str(inner_l4_mac_ipv4_gtpu_ipv4_udp_tcp)
    .replace("eth / ipv4", "eth / ipv6")
    .replace("gtpu / ipv4", "gtpu / gtp_psc / ipv4")
    .replace("IP()", "IPv6()")
    .replace(
        "teid=0x123456)", "teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)"
    )
    .replace("mac_ipv4", "mac_ipv6")
)
inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp = {
    "sub_casename": "inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp",
    "port_id": 0,
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end",
    ],
    "test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            "action": "save_hash",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            "action": "check_hash_different",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            "action": "save_or_no_hash",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            "action": "check_hash_same_or_no_hash",
        },
    ],
}
inner_l4_mac_ipv6_gtpu_eh_ipv6_udp_tcp = eval(
    str(inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp)
    .replace("eth / ipv4", "eth / ipv6")
    .replace("pdu_t is 0", "pdu_t is 1")
    .replace("(type=0", "(type=1")
    .replace("IP()", "IPv6()")
    .replace("mac_ipv4", "mac_ipv6")
)
inner_l4_protocal_hash = [
    inner_l4_mac_ipv4_gtpu_ipv4_udp_tcp,
    inner_l4_mac_ipv6_gtpu_ipv4_udp_tcp,
    inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp,
    inner_l4_mac_ipv6_gtpu_eh_ipv6_udp_tcp,
]

mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric = {
    "sub_casename": "mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            "action": {"save_hash": "ipv4-nonfrag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2",frag=6)/("X"*480)',
            "action": {"save_hash": "ipv4-frag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1",frag=6)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
            "action": {"save_hash": "ipv4-icmp"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            "action": {"save_hash": "ipv4-udp"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-nonfrag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1",frag=6)/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-frag"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            "action": {"check_no_hash_or_different": "ipv4-icmp"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            "action": {"check_no_hash_or_different", "ipv4-udp"},
        },
    ],
}

mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric = eval(
    str(mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric)
    .replace("gtp_psc / ipv4", "gtp_psc / ipv6")
    .replace("types ipv4", "types ipv6")
    .replace("gtpu_eh_ipv4", "gtpu_eh_ipv6")
    .replace(",frag=6)", ")/IPv6ExtHdrFragment()")
    .replace(
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        'IP(dst="192.168.1.1", src="192.168.1.2"',
    )
    .replace(
        'IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        'IP(src="192.168.1.1", dst="192.168.1.2"',
    )
    .replace(
        'IP(dst="192.168.0.1",src="192.168.0.2"',
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
    )
    .replace(
        'IP(dst="192.168.0.2",src="192.168.0.1"',
        'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
    )
)

mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric = {
    "sub_casename": "mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            "action": {"save_hash": "udp-dl"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            "action": {"save_hash": "udp-ul"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-dl"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-dl"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-dl"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-ul"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-ul"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-ul"},
        },
    ],
}
mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric = eval(
    str(mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric)
    .replace("gtp_psc / ipv4", "gtp_psc / ipv6")
    .replace("types ipv4", "types ipv6")
    .replace("gtpu_eh_ipv4", "gtpu_eh_ipv6")
    .replace(
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        'IP(dst="192.168.1.1", src="192.168.1.2"',
    )
    .replace(
        'IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        'IP(src="192.168.1.1", dst="192.168.1.2"',
    )
    .replace(
        'IP(dst="192.168.0.1",src="192.168.0.2"',
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
    )
    .replace(
        'IP(dst="192.168.0.2",src="192.168.0.1"',
        'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
    )
)

mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric = {
    "sub_casename": "mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            "action": {"save_hash": "udp-dl"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            "action": {"save_hash": "udp-ul"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            "action": "check_hash_same",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-dl"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-dl"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-dl"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-ul"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-ul"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            "action": {"check_no_hash_or_different", "udp-ul"},
        },
    ],
}

mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric = eval(
    str(mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric)
    .replace("gtp_psc / ipv4", "gtp_psc / ipv6")
    .replace("types ipv4", "types ipv6")
    .replace("gtpu_eh_ipv4", "gtpu_eh_ipv6")
    .replace(
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        'IP(dst="192.168.1.1", src="192.168.1.2"',
    )
    .replace(
        'IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
        'IP(src="192.168.1.1", dst="192.168.1.2"',
    )
    .replace(
        'IP(dst="192.168.0.1",src="192.168.0.2"',
        'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"',
    )
    .replace(
        'IP(dst="192.168.0.2",src="192.168.0.1"',
        'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
    )
)

# iavf rss gtpc gtpu
# matched basic pkt
mac_ipv4_gtpu_basic_pkt = {
    "ipv4-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "ipv4-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "ipv4-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv4-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()',
    ],
    "vlan-ipv4-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "vlan-ipv4-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "vlan-ipv4-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv4-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()',
    ],
}

mac_ipv6_gtpu_basic_pkt = {
    "ipv6-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "ipv6-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "ipv6-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv6-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "vlan-ipv6-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "vlan-ipv6-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "vlan-ipv6-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv6-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
}

mac_ipv4_gtpc_basic_pkt = {
    "ipv4-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv4-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "ipv4-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "ipv4-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "ipv4-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "ipv4-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "ipv4-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "ipv4-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "ipv4-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()',
    ],
    "ipv4-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
    "vlan-ipv4-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv4-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "vlan-ipv4-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "vlan-ipv4-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "vlan-ipv4-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "vlan-ipv4-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "vlan-ipv4-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "vlan-ipv4-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "vlan-ipv4-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
    ],
    "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
}

mac_ipv6_gtpc_basic_pkt = {
    "ipv6-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv6-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "ipv6-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "ipv6-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "ipv6-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "ipv6-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "ipv6-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "ipv6-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "ipv6-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
    ],
    "ipv6-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
    "vlan-ipv6-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv6-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "vlan-ipv6-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "vlan-ipv6-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "vlan-ipv6-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "vlan-ipv6-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "vlan-ipv6-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "vlan-ipv6-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "vlan-ipv6-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
    ],
    "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
}

# matched change pkt

mac_ipv4_gtpu_l3src_only_changed = {
    "ipv4-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "ipv4-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "ipv4-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv4-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()',
    ],
    "vlan-ipv4-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "vlan-ipv4-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "vlan-ipv4-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv4-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()',
    ],
}

mac_ipv4_gtpu_l3dst_only_changed = {
    "ipv4-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "ipv4-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "ipv4-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv4-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()',
    ],
    "vlan-ipv4-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "vlan-ipv4-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "vlan-ipv4-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv4-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoResponse()',
    ],
}

mac_ipv6_gtpu_l3src_only_changed = {
    "ipv6-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "ipv6-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "ipv6-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv6-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "vlan-ipv6-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "vlan-ipv6-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "vlan-ipv6-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv6-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
}

mac_ipv6_gtpu_l3dst_only_changed = {
    "ipv6-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "ipv6-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "ipv6-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv6-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "vlan-ipv6-gtpu-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
    ],
    "vlan-ipv6-gtpu-eh-pay": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
    ],
    "vlan-ipv6-gtpu-echo-request": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv6-gtpu-echo-reponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
}

mac_ipv4_gtpc_l3src_only_changed = {
    "ipv4-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv4-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "ipv4-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "ipv4-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "ipv4-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "ipv4-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "ipv4-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "ipv4-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "ipv4-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=27)/GTPPDUNotificationRequest()',
    ],
    "ipv4-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
    "vlan-ipv4-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv4-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "vlan-ipv4-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "vlan-ipv4-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "vlan-ipv4-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "vlan-ipv4-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "vlan-ipv4-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "vlan-ipv4-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "vlan-ipv4-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
    ],
    "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
}

mac_ipv4_gtpc_l3dst_only_changed = {
    "ipv4-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv4-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "ipv4-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "ipv4-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "ipv4-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "ipv4-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "ipv4-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "ipv4-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "ipv4-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
    ],
    "ipv4-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
    "vlan-ipv4-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv4-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "vlan-ipv4-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "vlan-ipv4-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "vlan-ipv4-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "vlan-ipv4-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "vlan-ipv4-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "vlan-ipv4-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "vlan-ipv4-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
    ],
    "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
}

mac_ipv6_gtpc_l3src_only_changed = {
    "ipv6-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv6-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "ipv6-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "ipv6-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "ipv6-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "ipv6-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "ipv6-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "ipv6-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "ipv6-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
    ],
    "ipv6-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
    "vlan-ipv6-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv6-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "vlan-ipv6-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "vlan-ipv6-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "vlan-ipv6-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "vlan-ipv6-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "vlan-ipv6-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "vlan-ipv6-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "vlan-ipv6-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
    ],
    "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
}

mac_ipv6_gtpc_l3dst_only_changed = {
    "ipv6-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "ipv6-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "ipv6-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "ipv6-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "ipv6-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "ipv6-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "ipv6-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "ipv6-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "ipv6-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
    ],
    "ipv6-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
    "vlan-ipv6-gtpc-EchoRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
    ],
    "vlan-ipv6-gtpc-EchoEesponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
    ],
    "vlan-ipv6-gtpc-CreatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
    ],
    "vlan-ipv6-gtpc-CreatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
    ],
    "vlan-ipv6-gtpc-UpdatePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
    ],
    "vlan-ipv6-gtpc-UpdatePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
    ],
    "vlan-ipv6-gtpc-DeletePDPContextRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
    ],
    "vlan-ipv6-gtpc-DeletePDPContextResponse": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
    ],
    "vlan-ipv6-gtpc-PDUNotificationRequest": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
    ],
    "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification": [
        'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
    ],
}

# subcase

mac_ipv4_gtpu_l3src_only = {
    "sub_casename": "mac_ipv4_gtpu_l3src_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / end actions rss types ipv4 l3-src-only end "
    "key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-pay"],
            "action": {"save_hash": "ipv4-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["ipv4-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.5")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-eh-pay"],
            "action": {"save_hash": "ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["ipv4-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.5")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-request"],
            "action": {"save_hash": "ipv4-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["ipv4-gtpu-echo-request"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.5")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-reponse"],
            "action": {"save_hash": "ipv4-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["ipv4-gtpu-echo-reponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.5")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-pay"],
            "action": {"save_hash": "vlan-ipv4-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["vlan-ipv4-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.1", dst="192.168.1.5")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-eh-pay"],
            "action": {"save_hash": "vlan-ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["vlan-ipv4-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.1", dst="192.168.1.5")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-request"],
            "action": {"save_hash": "vlan-ipv4-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed[
                "vlan-ipv4-gtpu-echo-request"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.1", dst="192.168.1.5")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-reponse"],
            "action": {"save_hash": "vlan-ipv4-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed[
                "vlan-ipv4-gtpu-echo-reponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.1", dst="192.168.1.5")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_l3dst_only = {
    "sub_casename": "mac_ipv4_gtpu_l3dst_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / end actions rss types ipv4 l3-dst-only end "
    "key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-pay"],
            "action": {"save_hash": "ipv4-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["ipv4-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-eh-pay"],
            "action": {"save_hash": "ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["ipv4-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPPDUSessionContainer(type=1, P=1, QFI=0x55)/Raw("x"*96)',
            "action": {"check_hash_same": "ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-request"],
            "action": {"save_hash": "ipv4-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["ipv4-gtpu-echo-request"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-reponse"],
            "action": {"save_hash": "ipv4-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["ipv4-gtpu-echo-reponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=27,dport=2152)/GTP_U_Header(teid=0x12345685,gtp_type=0x01)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-pay"],
            "action": {"save_hash": "vlan-ipv4-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["vlan-ipv4-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-eh-pay"],
            "action": {"save_hash": "vlan-ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["vlan-ipv4-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPPDUSessionContainer(type=1, P=1, QFI=0x55)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-request"],
            "action": {"save_hash": "vlan-ipv4-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed[
                "vlan-ipv4-gtpu-echo-request"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-reponse"],
            "action": {"save_hash": "vlan-ipv4-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed[
                "vlan-ipv4-gtpu-echo-reponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpu_l3_src_only_l3_dst_only = {
    "sub_casename": "mac_ipv4_gtpu_l3_src_only_l3_dst_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / end actions rss types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-pay"],
            "action": {"save_hash": "ipv4-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["ipv4-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["ipv4-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-eh-pay"],
            "action": {"save_hash": "ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["ipv4-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["ipv4-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
            "action": {"check_hash_different": "ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345691,gtp_type=0x01)/GTPPDUSessionContainer(type=1, P=1, QFI=0x55)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-request"],
            "action": {"save_hash": "ipv4-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["ipv4-gtpu-echo-request"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["ipv4-gtpu-echo-request"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345691,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-reponse"],
            "action": {"save_hash": "ipv4-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["ipv4-gtpu-echo-reponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["ipv4-gtpu-echo-reponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-pay"],
            "action": {"save_hash": "vlan-ipv4-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["vlan-ipv4-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["vlan-ipv4-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-eh-pay"],
            "action": {"save_hash": "vlan-ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed["vlan-ipv4-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed["vlan-ipv4-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPPDUSessionContainer(type=1, P=1, QFI=0x55)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-request"],
            "action": {"save_hash": "vlan-ipv4-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed[
                "vlan-ipv4-gtpu-echo-request"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed[
                "vlan-ipv4-gtpu-echo-request"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=21,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-reponse"],
            "action": {"save_hash": "vlan-ipv4-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv4_gtpu_l3dst_only_changed[
                "vlan-ipv4-gtpu-echo-reponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpu_l3src_only_changed[
                "vlan-ipv4-gtpu-echo-reponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
    ],
    # not support 20.11
    "post-test": [],
}

mac_ipv6_gtpu_l3src_only = {
    "sub_casename": "mac_ipv6_gtpu_l3src_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-pay"],
            "action": {"save_hash": "ipv6-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["ipv6-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345691,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-eh-pay"],
            "action": {"save_hash": "ipv6-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["ipv6-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPPDUSessionContainer(type=1, P=1, QFI=0x55)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-echo-request"],
            "action": {"save_hash": "ipv6-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["ipv6-gtpu-echo-request"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-echo-reponse"],
            "action": {"save_hash": "ipv6-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["ipv6-gtpu-echo-reponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-pay"],
            "action": {"save_hash": "vlan-ipv6-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["vlan-ipv6-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-eh-pay"],
            "action": {"save_hash": "vlan-ipv6-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["vlan-ipv6-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPPDUSessionContainer(type=1, P=1, QFI=0x44)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-echo-request"],
            "action": {"save_hash": "vlan-ipv6-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed[
                "vlan-ipv6-gtpu-echo-request"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-echo-reponse"],
            "action": {"save_hash": "vlan-ipv6-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed[
                "vlan-ipv6-gtpu-echo-reponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv6_gtpu_l3dst_only = {
    "sub_casename": "mac_ipv6_gtpu_l3dst_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-pay"],
            "action": {"save_hash": "ipv6-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["ipv6-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-eh-pay"],
            "action": {"save_hash": "ipv6-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["ipv6-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPPDUSessionContainer(type=1, P=1, QFI=0x55)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-echo-request"],
            "action": {"save_hash": "ipv6-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["ipv6-gtpu-echo-request"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-echo-reponse"],
            "action": {"save_hash": "ipv6-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["ipv6-gtpu-echo-reponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345691,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-pay"],
            "action": {"save_hash": "vlan-ipv6-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["vlan-ipv6-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=7)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-eh-pay"],
            "action": {"save_hash": "vlan-ipv6-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["vlan-ipv6-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPPDUSessionContainer(type=1, P=1, QFI=0x55)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-echo-request"],
            "action": {"save_hash": "vlan-ipv6-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed[
                "vlan-ipv6-gtpu-echo-request"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-echo-reponse"],
            "action": {"save_hash": "vlan-ipv6-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed[
                "vlan-ipv6-gtpu-echo-reponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv6_gtpu_l3_src_only_l3_dst_only = {
    "sub_casename": "mac_ipv6_gtpu_l3_src_only_l3_dst_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / end actions rss types ipv6 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-pay"],
            "action": {"save_hash": "ipv6-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["ipv6-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["ipv6-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-eh-pay"],
            "action": {"save_hash": "ipv6-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["ipv6-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["ipv6-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
            "action": "heck_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=27,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/GTPPDUSessionContainer(type=1, P=1, QFI=0x55)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-echo-request"],
            "action": {"save_hash": "ipv6-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["ipv6-gtpu-echo-request"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["ipv6-gtpu-echo-request"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-echo-reponse"],
            "action": {"save_hash": "ipv6-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["ipv6-gtpu-echo-reponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["ipv6-gtpu-echo-reponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-pay"],
            "action": {"save_hash": "vlan-ipv6-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["vlan-ipv6-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["vlan-ipv6-gtpu-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345683,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-eh-pay"],
            "action": {"save_hash": "vlan-ipv6-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed["vlan-ipv6-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed["vlan-ipv6-gtpu-eh-pay"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPPDUSessionContainer(type=1, P=1, QFI=0x55)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-echo-request"],
            "action": {"save_hash": "vlan-ipv6-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed[
                "vlan-ipv6-gtpu-echo-request"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed[
                "vlan-ipv6-gtpu-echo-request"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-echo-reponse"],
            "action": {"save_hash": "vlan-ipv6-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv6_gtpu_l3dst_only_changed[
                "vlan-ipv6-gtpu-echo-reponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpu_l3src_only_changed[
                "vlan-ipv6-gtpu-echo-reponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2152)/GTP_U_Header(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        # mismatched pkt
        # not support 20.11
        {
            # 'send_packet': mac_ipv6_gtpu_mismatched_pkt['ipv6-gtpu-eh-ipv4'],
            # 'action': 'check_no_hash',
        },
        {
            # 'send_packet': mac_ipv6_gtpu_mismatched_pkt['ipv6-gtpu-ipv4'],
            # 'action': 'check_no_hash',
        },
        {
            # 'send_packet': mac_ipv6_gtpu_mismatched_pkt['ipv6-gtpu-eh-ipv6'],
            # 'action': 'check_no_hash',
        },
        {
            # 'send_packet': mac_ipv6_gtpu_mismatched_pkt['ipv6-gtpu-ipv6'],
            # 'action': 'check_no_hash',
        },
        {
            # 'send_packet': mac_ipv6_gtpu_mismatched_pkt['ipv4-gtpu-pay'],
            # 'action': 'check_no_hash',
        },
        {
            # 'send_packet': mac_ipv6_gtpu_mismatched_pkt['ipv4-gtpu-eh-pay'],
            # 'action': 'check_no_hash',
        },
        {
            # 'send_packet': mac_ipv6_gtpu_mismatched_pkt['ipv6-gtpc-EchoRequest'],
            # 'action': 'check_no_hash',
        },
    ],
    # not support 20.11
    "post-test": [],
}

mac_ipv4_gtpc_l3src_only = {
    "sub_casename": "mac_ipv4_gtpc_l3src_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpc / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoRequest"],
            "action": {"save_hash": "ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed["ipv4-gtpc-EchoRequest"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoEesponse"],
            "action": {"save_hash": "ipv4-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed["ipv4-gtpc-EchoEesponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-CreatePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-UpdatePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-DeletePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-PDUNotificationRequest"],
            "action": {"save_hash": "ipv4-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x27)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {"save_hash": "ipv4-gtpc-SupportedExtensionHeadersNotification"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoRequest"],
            "action": {"save_hash": "vlan-ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-EchoRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoEesponse"],
            "action": {"save_hash": "vlan-ipv4-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-EchoEesponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {
                "save_hash": "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpc_l3dst_only = {
    "sub_casename": "mac_ipv4_gtpc_l3dst_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpc / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end ",
    "test": [
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoRequest"],
            "action": {"save_hash": "ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed["ipv4-gtpc-EchoRequest"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoEesponse"],
            "action": {"save_hash": "ipv4-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed["ipv4-gtpc-EchoEesponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-CreatePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-UpdatePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-DeletePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-PDUNotificationRequest"],
            "action": {"save_hash": "ipv4-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {"save_hash": "ipv4-gtpc-SupportedExtensionHeadersNotification"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoRequest"],
            "action": {"save_hash": "vlan-ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-EchoRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoEesponse"],
            "action": {"save_hash": "vlan-ipv4-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-EchoEesponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.3", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {
                "save_hash": "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv4_gtpc_l3_src_only_l3_dst_only = {
    "sub_casename": "mac_ipv4_gtpc_l3_src_only_l3_dst_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpc / end actions rss types ipv4 end key_len 0 queues end / end ",
    "test": [
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoRequest"],
            "action": {"save_hash": "ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed["ipv4-gtpc-EchoRequest"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed["ipv4-gtpc-EchoRequest"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoEesponse"],
            "action": {"save_hash": "ipv4-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed["ipv4-gtpc-EchoEesponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed["ipv4-gtpc-EchoEesponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-CreatePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-UpdatePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-DeletePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-PDUNotificationRequest"],
            "action": {"save_hash": "ipv4-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {"save_hash": "ipv4-gtpc-SupportedExtensionHeadersNotification"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoRequest"],
            "action": {"save_hash": "vlan-ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-EchoRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-EchoRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoEesponse"],
            "action": {"save_hash": "vlan-ipv4-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-EchoEesponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-EchoEesponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {
                "save_hash": "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_l3dst_only_changed[
                "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv4_gtpc_l3src_only_changed[
                "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(src="192.168.1.5", dst="192.168.1.7")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
    ],
    # not support 20.11
    "post-test": [],
}

mac_ipv6_gtpc_l3src_only = {
    "sub_casename": "mac_ipv4_gtpc_l3src_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / gtpc / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end ",
    "test": [
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-EchoRequest"],
            "action": {"save_hash": "ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed["ipv6-gtpc-EchoRequest"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-EchoEesponse"],
            "action": {"save_hash": "ipv6-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed["ipv6-gtpc-EchoEesponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-CreatePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-UpdatePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-DeletePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-PDUNotificationRequest"],
            "action": {"save_hash": "ipv6-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {"save_hash": "ipv6-gtpc-SupportedExtensionHeadersNotification"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["vlan-ipv6-gtpc-EchoRequest"],
            "action": {"save_hash": "vlan-ipv6-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-EchoRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["vlan-ipv6-gtpc-EchoEesponse"],
            "action": {"save_hash": "vlan-ipv6-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-EchoEesponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {
                "save_hash": "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            },
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv6_gtpc_l3dst_only = {
    "sub_casename": "mac_ipv6_gtpc_l3dst_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / gtpc / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end ",
    "test": [
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-EchoRequest"],
            "action": {"save_hash": "ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed["ipv6-gtpc-EchoRequest"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-EchoEesponse"],
            "action": {"save_hash": "ipv6-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed["ipv6-gtpc-EchoEesponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-CreatePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-UpdatePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-DeletePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-PDUNotificationRequest"],
            "action": {"save_hash": "ipv6-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {"save_hash": "ipv6-gtpc-SupportedExtensionHeadersNotification"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["vlan-ipv6-gtpc-EchoRequest"],
            "action": {"save_hash": "vlan-ipv6-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-EchoRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["vlan-ipv6-gtpc-EchoEesponse"],
            "action": {"save_hash": "vlan-ipv6-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-EchoEesponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {
                "save_hash": "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            },
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=3)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
    ],
    "post-test": [],
}

mac_ipv6_gtpc_l3_src_only_l3_dst_only = {
    "sub_casename": "mac_ipv6_gtpc_l3_src_only_l3_dst_only",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / gtpc / end actions rss types ipv6 end key_len 0 queues end / end ",
    "test": [
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-EchoRequest"],
            "action": {"save_hash": "ipv6-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed["ipv6-gtpc-EchoRequest"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed["ipv6-gtpc-EchoRequest"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345683,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-EchoEesponse"],
            "action": {"save_hash": "ipv6-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed["ipv6-gtpc-EchoEesponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed["ipv6-gtpc-EchoEesponse"],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-CreatePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-UpdatePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-DeletePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-PDUNotificationRequest"],
            "action": {"save_hash": "ipv6-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {"save_hash": "ipv6-gtpc-SupportedExtensionHeadersNotification"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["vlan-ipv6-gtpc-EchoRequest"],
            "action": {"save_hash": "vlan-ipv6-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-EchoRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-EchoRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["vlan-ipv6-gtpc-EchoEesponse"],
            "action": {"save_hash": "vlan-ipv6-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-EchoEesponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-EchoEesponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {
                "save_hash": "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            },
        },
        {
            "send_packet": mac_ipv6_gtpc_l3dst_only_changed[
                "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": mac_ipv6_gtpc_l3src_only_changed[
                "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_different",
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=5)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=23,dport=2123)/GTPHeader(teid=0x12345682,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
        # mismatched pkt
        # not support 20.11
        {
            # 'send_packet': mac_ipv6_gtpc_mismatched_pkt['ipv6-gtpu-pay'],
            # 'action': 'check_no_hash',
        },
        {
            # 'send_packet': mac_ipv6_gtpc_mismatched_pkt['ipv6-gtpu-eh-pay'],
            # 'action': 'check_no_hash',
        },
        {
            # 'send_packet': mac_ipv6_gtpc_mismatched_pkt['ipv6-gtpu-ipv4'],
            # 'action': 'check_no_hash',
        },
        {
            # 'send_packet': mac_ipv6_gtpc_mismatched_pkt['ipv6-gtpu-ipv6'],
            # 'action': 'check_no_hash',
        },
        {
            # 'send_packet': mac_ipv6_gtpc_mismatched_pkt['ipv4-gtpc-EchoRequest'],
            # 'action': 'check_no_hash',
        },
    ],
    # not support 20.11
    "post-test": [],
}

mac_ipv4_gtpu_symmetric = {
    "sub_casename": "mac_ipv4_gtpu_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-pay"],
            "action": {"save_hash": "ipv4-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-pay"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-eh-pay"],
            "action": {"save_hash": "ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-eh-pay"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-request"],
            "action": {"save_hash": "ipv4-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-request"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-reponse"],
            "action": {"save_hash": "ipv4-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-reponse"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-pay"],
            "action": {"save_hash": "vlan-ipv4-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-pay"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-eh-pay"],
            "action": {"save_hash": "vlan-ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-eh-pay"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-request"],
            "action": {"save_hash": "vlan-ipv4-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-request"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-reponse"],
            "action": {"save_hash": "vlan-ipv4-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-reponse"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-pay"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": {"check_no_hash_or_different": "ipv4-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-eh-pay"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": {"check_no_hash_or_different": "ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-request"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": {"check_no_hash_or_different": "ipv4-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["ipv4-gtpu-echo-reponse"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": {"check_no_hash_or_different": "ipv4-gtpu-echo-reponse"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-pay"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": {"check_no_hash_or_different": "vlan-ipv4-gtpu-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-eh-pay"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": {"check_no_hash_or_different": "vlan-ipv4-gtpu-eh-pay"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-request"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": {"check_no_hash_or_different": "vlan-ipv4-gtpu-echo-request"},
        },
        {
            "send_packet": mac_ipv4_gtpu_basic_pkt["vlan-ipv4-gtpu-echo-reponse"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3',
                'src="192.168.1.3", dst="192.168.1.1',
            ),
            "action": {"check_no_hash_or_different": "vlan-ipv4-gtpu-echo-reponse"},
        },
    ],
}

mac_ipv6_gtpu_symmetric = {
    "sub_casename": "mac_ipv6_gtpu_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-pay"],
            "action": {"save_hash": "ipv6-gtpu-pay"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-eh-pay"],
            "action": {"save_hash": "ipv6-gtpu-eh-pay"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-echo-request"],
            "action": {"save_hash": "ipv6-gtpu-echo-request"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["ipv6-gtpu-echo-reponse"],
            "action": {"save_hash": "ipv6-gtpu-echo-reponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-pay"],
            "action": {"save_hash": "vlan-ipv6-gtpu-pay"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-eh-pay"],
            "action": {"save_hash": "vlan-ipv6-gtpu-eh-pay"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-echo-request"],
            "action": {"save_hash": "vlan-ipv6-gtpu-echo-request"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpu_basic_pkt["vlan-ipv6-gtpu-echo-reponse"],
            "action": {"save_hash": "vlan-ipv6-gtpu-echo-reponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
            "action": {"check_no_hash_or_different": "ipv6-gtpu-pay"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
            "action": {"check_no_hash_or_different": "ipv6-gtpu-eh-pay"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": {"check_no_hash_or_different": "ipv6-gtpu-echo-request"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": {"check_no_hash_or_different": "ipv6-gtpu-echo-reponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/Raw("x"*96)',
            "action": {"check_no_hash_or_different": "vlan-ipv6-gtpu-pay"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*96)',
            "action": {"check_no_hash_or_different": "vlan-ipv6-gtpu-eh-pay"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": {"check_no_hash_or_different": "vlan-ipv6-gtpu-echo-request"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2152)/GTP_U_Header(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": {"check_no_hash_or_different": "vlan-ipv6-gtpu-echo-reponse"},
        },
    ],
}

mac_ipv4_gtpc_symmetric = {
    "sub_casename": "mac_ipv4_gtpc_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpc / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoRequest"],
            "action": {"save_hash": "ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoRequest"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoEesponse"],
            "action": {"save_hash": "ipv4-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoEesponse"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-CreatePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-CreatePDPContextRequest"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-CreatePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-UpdatePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-UpdatePDPContextRequest"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-UpdatePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-DeletePDPContextRequest"],
            "action": {"save_hash": "ipv4-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-DeletePDPContextRequest"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "ipv4-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-DeletePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-PDUNotificationRequest"],
            "action": {"save_hash": "ipv4-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-PDUNotificationRequest"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {"save_hash": "ipv4-gtpc-SupportedExtensionHeadersNotification"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-SupportedExtensionHeadersNotification"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoRequest"],
            "action": {"save_hash": "vlan-ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoRequest"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoEesponse"],
            "action": {"save_hash": "vlan-ipv4-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoEesponse"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextRequest"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextRequest"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-PDUNotificationRequest"
            ],
            "action": {"save_hash": "vlan-ipv4-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-PDUNotificationRequest"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {
                "save_hash": "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoRequest"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {"check_no_hash_or_different": "ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-EchoEesponse"][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {"check_no_hash_or_different": "ipv4-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-CreatePDPContextRequest"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "ipv4-gtpc-CreatePDPContextRequest"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-CreatePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "ipv4-gtpc-CreatePDPContextResponse"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-UpdatePDPContextRequest"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "ipv4-gtpc-UpdatePDPContextRequest"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-UpdatePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "ipv4-gtpc-UpdatePDPContextResponse"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-DeletePDPContextRequest"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "ipv4-gtpc-DeletePDPContextRequest"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-DeletePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "ipv4-gtpc-DeletePDPContextResponse"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["ipv4-gtpc-PDUNotificationRequest"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "ipv4-gtpc-PDUNotificationRequest"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "ipv4-gtpc-SupportedExtensionHeadersNotification"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "ipv4-gtpc-SupportedExtensionHeadersNotification"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoRequest"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {"check_no_hash_or_different": "vlan-ipv4-gtpc-EchoRequest"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt["vlan-ipv4-gtpc-EchoEesponse"][
                0
            ].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {"check_no_hash_or_different": "vlan-ipv4-gtpc-EchoEesponse"},
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextRequest"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "vlan-ipv4-gtpc-CreatePDPContextRequest"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-CreatePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "vlan-ipv4-gtpc-CreatePDPContextResponse"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "vlan-ipv4-gtpc-UpdatePDPContextRequest"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "vlan-ipv4-gtpc-UpdatePDPContextResponse"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextRequest"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "vlan-ipv4-gtpc-DeletePDPContextRequest"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-DeletePDPContextResponse"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "vlan-ipv4-gtpc-DeletePDPContextResponse"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-PDUNotificationRequest"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "vlan-ipv4-gtpc-PDUNotificationRequest"
            },
        },
        {
            "send_packet": mac_ipv4_gtpc_basic_pkt[
                "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            ][0].replace(
                'src="192.168.1.1", dst="192.168.1.3"',
                'src="192.168.1.3", dst="192.168.1.1"',
            ),
            "action": {
                "check_no_hash_or_different": "vlan-ipv4-gtpc-SupportedExtensionHeadersNotification"
            },
        },
    ],
}

mac_ipv6_gtpc_symmetric = {
    "sub_casename": "mac_ipv6_gtpc_symmetric",
    "port_id": 0,
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / gtpc / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end",
    "test": [
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-EchoRequest"],
            "action": {"save_hash": "ipv6-gtpc-EchoRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-EchoEesponse"],
            "action": {"save_hash": "ipv6-gtpc-EchoEesponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-CreatePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-UpdatePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-DeletePDPContextRequest"],
            "action": {"save_hash": "ipv6-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "ipv6-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["ipv6-gtpc-PDUNotificationRequest"],
            "action": {"save_hash": "ipv6-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {"save_hash": "ipv6-gtpc-SupportedExtensionHeadersNotification"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["vlan-ipv6-gtpc-EchoRequest"],
            "action": {"save_hash": "vlan-ipv6-gtpc-EchoRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt["vlan-ipv6-gtpc-EchoEesponse"],
            "action": {"save_hash": "vlan-ipv6-gtpc-EchoEesponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-CreatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-CreatePDPContextRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-CreatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-CreatePDPContextResponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-UpdatePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-UpdatePDPContextRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-UpdatePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-UpdatePDPContextResponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-DeletePDPContextRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-DeletePDPContextRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-DeletePDPContextResponse"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-DeletePDPContextResponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-PDUNotificationRequest"
            ],
            "action": {"save_hash": "vlan-ipv6-gtpc-PDUNotificationRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": "check_hash_same",
        },
        {
            "send_packet": mac_ipv6_gtpc_basic_pkt[
                "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            ],
            "action": {
                "save_hash": "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": "check_hash_same",
        },
    ],
    "post-test": [
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": {"check_no_hash_or_different": "ipv6-gtpc-EchoRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": {"check_no_hash_or_different": "ipv6-gtpc-EchoEesponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": {
                "check_no_hash_or_different": "ipv6-gtpc-CreatePDPContextRequest"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": {
                "check_no_hash_or_different": "ipv6-gtpc-CreatePDPContextResponse"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": {
                "check_no_hash_or_different": "ipv6-gtpc-UpdatePDPContextRequest"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": {
                "check_no_hash_or_different": "ipv6-gtpc-UpdatePDPContextResponse"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": {
                "check_no_hash_or_different": "ipv6-gtpc-DeletePDPContextRequest"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": {
                "check_no_hash_or_different": "ipv6-gtpc-DeletePDPContextResponse"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": {
                "check_no_hash_or_different": "ipv6-gtpc-PDUNotificationRequest"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": {
                "check_no_hash_or_different": "ipv6-gtpc-SupportedExtensionHeadersNotification"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x01)/GTPEchoRequest()',
            "action": {"check_no_hash_or_different": "vlan-ipv6-gtpc-EchoRequest"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x02)/GTPEchoResponse()',
            "action": {"check_no_hash_or_different": "vlan-ipv6-gtpc-EchoEesponse"},
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x10)/GTPCreatePDPContextRequest()',
            "action": {
                "check_no_hash_or_different": "vlan-ipv6-gtpc-CreatePDPContextRequest"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x11)/GTPCreatePDPContextResponse()',
            "action": {
                "check_no_hash_or_different": "vlan-ipv6-gtpc-CreatePDPContextResponse"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x12)/GTPUpdatePDPContextRequest()',
            "action": {
                "check_no_hash_or_different": "vlan-ipv6-gtpc-UpdatePDPContextRequest"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x13)/GTPUpdatePDPContextResponse()',
            "action": {
                "check_no_hash_or_different": "vlan-ipv6-gtpc-UpdatePDPContextResponse"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x14)/GTPDeletePDPContextRequest()',
            "action": {
                "check_no_hash_or_different": "vlan-ipv6-gtpc-DeletePDPContextRequest"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x15)/GTPDeletePDPContextResponse()',
            "action": {
                "check_no_hash_or_different": "vlan-ipv6-gtpc-DeletePDPContextResponse"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1B)/GTPPDUNotificationRequest()',
            "action": {
                "check_no_hash_or_different": "vlan-ipv6-gtpc-PDUNotificationRequest"
            },
        },
        {
            "send_packet": 'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=20,dport=2123)/GTPHeader(teid=0x12345678,gtp_type=0x1F)/GTPSupportedExtensionHeadersNotification()',
            "action": {
                "check_no_hash_or_different": "vlan-ipv6-gtpc-SupportedExtensionHeadersNotification"
            },
        },
    ],
}

mac_ipv4_gtpu_toeplitz = [
    mac_ipv4_gtpu_l3src_only,
    mac_ipv4_gtpu_l3dst_only,
    mac_ipv4_gtpu_l3_src_only_l3_dst_only,
]
mac_ipv6_gtpu_toeplitz = [
    mac_ipv6_gtpu_l3src_only,
    mac_ipv6_gtpu_l3dst_only,
    mac_ipv6_gtpu_l3_src_only_l3_dst_only,
]
mac_ipv4_gtpc_toeplitz = [
    mac_ipv4_gtpc_l3src_only,
    mac_ipv4_gtpc_l3dst_only,
    mac_ipv4_gtpc_l3_src_only_l3_dst_only,
]
mac_ipv6_gtpc_toeplitz = [
    mac_ipv6_gtpc_l3src_only,
    mac_ipv6_gtpc_l3dst_only,
    mac_ipv6_gtpc_l3_src_only_l3_dst_only,
]
mac_ipv4_gtpu_symmetric_toeplitz = [mac_ipv4_gtpu_symmetric]
mac_ipv6_gtpu_symmetric_toeplitz = [mac_ipv6_gtpu_symmetric]
mac_ipv4_gtpc_symmetric_toeplitz = [mac_ipv4_gtpc_symmetric]
mac_ipv6_gtpc_symmetric_toeplitz = [mac_ipv6_gtpc_symmetric]


class TestICEAdvancedIavfRSSGTPU(TestCase):
    supported_nic = [
        "ICE_100G-E810C_QSFP",
        "ICE_25G-E810C_SFP",
        "ICE_25G-E810_XXV_SFP",
        "ICE_25G-E823C_QSFP",
    ]

    @check_supported_nic(supported_nic)
    @skip_unsupported_pkg("os default")
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
        if symmetric:
            param = "--rxq=16 --txq=16"
        else:
            # if support add --disable-rss
            param = "--rxq=16 --txq=16"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param=param,
            eal_param=f"-a {self.vf0_pci}",
            socket=self.ports_socket,
        )
        """
        self.symmetric = symmetric
        if symmetric:
            # Need config rss in setup
            self.pmd_output.execute_cmd("port config all rss all")
        """
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        res = self.pmd_output.wait_link_status_up("all", timeout=15)
        self.verify(res is True, "there have port link is down")

    def switch_testpmd(self, symmetric=True):
        if symmetric != self.symmetric:
            self.pmd_output.quit()
            self.launch_testpmd(symmetric=symmetric)
            self.pmd_output.execute_cmd("start")

    def set_vlan_filter(self, state="on", port_id=0):
        """
        :param state: on/off
        """
        self.pmd_output.execute_cmd("vlan set filter {} {}".format(state, port_id))

    def vlan_action(self, action, vlan_id, port_id=0):
        """
        :param action: add/rm
        :param vlan_id: support int and list
        """
        if not isinstance(vlan_id, list):
            vlan_id = [vlan_id]
        [
            self.pmd_output.execute_cmd("rx_vlan {} {} {}".format(action, id, port_id))
            for id in vlan_id
        ]

    def handle_vlan_case(self, cases_info, vlan_id, port_id):
        try:
            self.set_vlan_filter("on", port_id)
            self.vlan_action("add", vlan_id, port_id)
            self.rssprocess.handle_rss_distribute_cases(cases_info=cases_info)
        finally:
            self.vlan_action("rm", vlan_id, port_id)
            self.set_vlan_filter("off", port_id)

    def test_mac_ipv4_gtpu_ipv4(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv4_toeplitz
        )

    def test_mac_ipv4_gtpu_ipv4_udp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv4_udp_toeplitz
        )

    def test_mac_ipv4_gtpu_ipv4_tcp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv4_tcp_toeplitz
        )

    def test_mac_ipv4_gtpu_ipv6(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv6_toeplitz
        )

    def test_mac_ipv4_gtpu_ipv6_udp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv6_udp_toeplitz
        )

    def test_mac_ipv4_gtpu_ipv6_tcp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv6_tcp_toeplitz
        )

    def test_mac_ipv6_gtpu_ipv4(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv4_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv4_udp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv4_udp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv4_tcp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv4_tcp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv6_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6_udp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv6_udp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6_tcp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv6_tcp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpu_eh_ipv4(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv4_toeplitz
        )

    def test_mac_ipv4_gtpu_eh_ipv4_udp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv4_udp_toeplitz
        )

    def test_mac_ipv4_gtpu_eh_ipv4_tcp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv4_tcp_toeplitz
        )

    def test_mac_ipv4_gtpu_eh_ipv6(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv6_toeplitz
        )

    def test_mac_ipv4_gtpu_eh_ipv6_udp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv6_udp_toeplitz
        )

    def test_mac_ipv4_gtpu_eh_ipv6_tcp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv6_tcp_toeplitz
        )

    def test_mac_ipv6_gtpu_eh_ipv4(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv4_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_udp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv4_udp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_tcp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv4_tcp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv6_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_udp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv6_udp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_tcp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv6_tcp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpu_eh_ipv4_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz
        )

    def test_mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz
        )

    def test_mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz
        )

    def test_mac_ipv4_gtpu_eh_ipv6_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv6_toeplitz
        )

    def test_mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv6_udp_toeplitz
        )

    def test_mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv6_tcp_toeplitz
        )

    def test_mac_ipv6_gtpu_eh_ipv4_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_udp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_tcp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_without_ul_dl_ipv6_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_udp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_without_ul_dl_ipv6_udp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_tcp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_without_ul_dl_ipv6_tcp_toeplitz
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpu_ipv4_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv4_symmetric
        )

    def test_mac_ipv4_gtpu_ipv4_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv4_udp_symmetric
        )

    def test_mac_ipv4_gtpu_ipv4_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv4_tcp_symmetric
        )

    def test_mac_ipv4_gtpu_ipv6_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv6_symmetric
        )

    def test_mac_ipv4_gtpu_ipv6_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv6_udp_symmetric
        )

    def test_mac_ipv4_gtpu_ipv6_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_ipv6_tcp_symmetric
        )

    def test_mac_ipv6_gtpu_ipv4_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv4_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv4_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv4_udp_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv4_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv4_tcp_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv6_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv6_udp_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_ipv6_tcp_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpu_eh_ipv4_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv4_symmetric
        )

    def test_mac_ipv4_gtpu_eh_ipv4_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv4_udp_symmetric
        )

    def test_mac_ipv4_gtpu_eh_ipv4_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv4_tcp_symmetric
        )

    def test_mac_ipv4_gtpu_eh_ipv6_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv6_symmetric
        )

    def test_mac_ipv4_gtpu_eh_ipv6_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv6_udp_symmetric
        )

    def test_mac_ipv4_gtpu_eh_ipv6_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv6_tcp_symmetric
        )

    def test_mac_ipv6_gtpu_eh_ipv4_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv4_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv4_tcp_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv4_tcp_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv6_symmetric
        )
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv6_tcp_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_tcp_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv6_tcp_symmetric
        )
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric
        )

    def test_mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric
        )

    def test_mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric
        )

    def test_mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric
        )

    def test_mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric
        )

    def test_mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(
            cases_info=mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric
        )

    def test_mac_ipv6_gtpu_eh_ipv4_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_udp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_udp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(
            mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric
        )
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_inner_l4_protocal_hash(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=inner_l4_protocal_hash)

    def test_negative_cases(self):
        negative_rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end",
        ]
        self.rssprocess.create_rule(
            rule=negative_rules,
            check_stats=False,
            msg="Failed to create parser engine.: Invalid argument",
        )

    def test_symmetric_negative_cases(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end",
        ]
        self.rssprocess.create_rule(rule=rules, check_stats=False)

    def test_stress_cases(self):
        # Subcase: add/delete IPV4_GTPU_UL_IPV4_TCP rules
        self.switch_testpmd()
        rule1 = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end"
        for _ in range(100):
            self.pmd_output.execute_cmd(rule1)
            self.pmd_output.execute_cmd("flow destroy 0 rule 0")
        rule_li = self.rssprocess.create_rule(rule=rule1)
        out = self.pmd_output.execute_cmd("flow list 0")
        p = re.compile("^(\d+)\s")
        li = out.splitlines()
        res = list(filter(bool, list(map(p.match, li))))
        result = [i.group(1) for i in res]
        self.verify(result == rule_li, "should only rule 0 existed")
        pkts1 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=32, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.1.2")/TCP(sport=22, dport=33)/("X"*480)',
        ]
        output = self.rssprocess.send_pkt_get_output(pkts=pkts1)
        hash_values1, rss_distribute = self.rssprocess.get_hash_verify_rss_distribute(
            output
        )
        self.verify(
            hash_values1[1] != hash_values1[0]
            and hash_values1[2] != hash_values1[0]
            and hash_values1[3] == hash_values1[0],
            "packet 2 and packet 3 should have different hash value with packet 1, packet 4 should has same hash value with packet 1.",
        )
        self.pmd_output.execute_cmd("flow flush 0")
        # Subcase: add/delete IPV4_GTPU_DL_IPV4 rules
        rule2 = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end"
        for _ in range(100):
            self.pmd_output.execute_cmd(rule2)
            self.pmd_output.execute_cmd("flow destroy 0 rule 0")
        rule_li = self.rssprocess.create_rule(rule=rule2)
        out = self.pmd_output.execute_cmd("flow list 0")
        p = re.compile("^(\d+)\s")
        li = out.splitlines()
        res = list(filter(bool, list(map(p.match, li))))
        result = [i.group(1) for i in res]
        self.verify(result == rule_li, "should only rule 0 existed")
        pkts2 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)',
        ]
        output = self.rssprocess.send_pkt_get_output(pkts=pkts2)
        hash_values2, rss_distribute = self.rssprocess.get_hash_verify_rss_distribute(
            output
        )
        self.verify(
            hash_values2[1] != hash_values2[0] and hash_values2[2] == hash_values2[0],
            "packet 2 should has different hash value with packet 1, packet 3 should has same hash value with packet 1.",
        )

    def test_multirules(self):
        self.switch_testpmd()
        self.logger.info("Subcase: IPV4_GTPU_IPV4/IPV4_GTPU_EH_IPV4")
        self.logger.info("Subcase: IPV4_GTPU_EH_IPV4 with/without UL/DL")
        self.logger.info("Subcase: IPV4_GTPU_EH_IPV4 without/with UL/DL")
        self.logger.info("Subcase: IPV4_GTPU_EH_IPV4 and IPV4_GTPU_EH_IPV4_UDP")
        self.logger.info("Subcase: IPV6_GTPU_EH_IPV6 and IPV6_GTPU_EH_IPV6_TCP")
        self.logger.info(
            "Subcase: IPV4_GTPU_EH_IPV6 and IPV4_GTPU_EH_IPV6_UDP without UL/DL"
        )
        self.logger.info("Subcase: IPV6_GTPU_IPV4 and IPV6_GTPU_IPV4_TCP")

    def test_ipv4_gtpu_ipv4_ipv4_gtpu_eh_ipv4(self):
        self.switch_testpmd()
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
        ]
        pkts1 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
        ]
        pkts2 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
        ]
        pkts3 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
        ]
        rule_li1 = self.rssprocess.create_rule(rule=rules[0])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        rule_li2 = self.rssprocess.create_rule(rule=rules[1])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts3)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3rd and different with 2nd",
        )

    def test_ipv4_gtpu_eh_ipv4_with_without_ul_dl(self):
        self.switch_testpmd(True)
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
        ]
        pkts1 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
        ]

        pkts2 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
        ]

        pkts3 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
        ]
        rule_li1 = self.rssprocess.create_rule(rule=rules[0])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        rule_li2 = self.rssprocess.create_rule(rule=rules[1])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts3)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

    def test_ipv4_gtpu_eh_ipv4_without_with_ul_dl(self):
        self.switch_testpmd()
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
        ]
        pkts1 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
        ]
        pkts2 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
        ]
        pkts3 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
        ]
        rule1 = self.rssprocess.create_rule(rules[0])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        rule2 = self.rssprocess.create_rule(rules[1])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts3)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

    def test_ipv4_gtpu_eh_ipv4_and_ipv4_gtpu_eh_ipv4_udp(self):
        self.switch_testpmd()
        pkts1 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=13)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.10.2")/UDP(sport=12, dport=23)/("X"*480)',
        ]
        pkts2 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
        ]
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
        ]

        rule_li1 = self.rssprocess.create_rule(rule=rules[0])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        rule_li2 = self.rssprocess.create_rule(rule=rules[1])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

    def test_ipv6_gtpu_eh_ipv6_and_ipv6_gtpu_eh_ipv6_tcp(self):
        self.switch_testpmd()
        pkts1 = [
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=13)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=23)/("X"*480)',
        ]
        pkts2 = [
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:1111")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)',
        ]

        rules = [
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end",
        ]

        rule_li1 = self.rssprocess.create_rule(rule=rules[0])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        rule_li2 = self.rssprocess.create_rule(rule=rules[1])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and 2rd",
        )

        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[1] and hash_value[1] == hash_value[2],
            "except all hash same hash",
        )

    def test_ipv4_gtpu_eh_ipv6_and_ipv4_gtpu_eh_ipv6_udp_without_ul_dl(self):
        self.switch_testpmd()
        pkts1 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/UDP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/UDP(sport=22, dport=13)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:1111")/UDP(sport=12, dport=23)/("X"*480)',
        ]
        pkts2 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:1111")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)',
        ]
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end",
        ]

        rule_li1 = self.rssprocess.create_rule(rule=rules[0])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        rule_li2 = self.rssprocess.create_rule(rule=rules[1])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[1] and hash_value[0] != hash_value[2],
            "got wrong hash, expect 1st hash equal to 2nd and different with 3rd",
        )

    def test_ipv6_gtpu_ipv4_and_ipv6_gtpu_ipv4_tcp(self):
        self.switch_testpmd()
        pkts1 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:1111")/TCP(sport=22, dport=13)/("X"*480)',
        ]
        pkts2 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:1111")/("X"*480)',
        ]
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end",
        ]

        rule_li1 = self.rssprocess.create_rule(rule=rules[0])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        rule_li2 = self.rssprocess.create_rule(rule=rules[1])
        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2)
        self.verify(
            hash_value[0] == hash_value[2] and hash_value[0] != hash_value[1],
            "got wrong hash, expect 1st hash equal to 3nd and different with 2rd",
        )

        hash_value, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(
            hash_value[0] != hash_value[2] and hash_value[0] == hash_value[1],
            "got wrong hash, expect 1st hash equal to 2nd and different with 3rd",
        )

    def test_toeplitz_symmetric_combination(self):
        self.switch_testpmd()
        self.logger.info("Subcase: toeplitz/symmetric with same pattern")
        # step 1
        rule_toeplitz = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end"
        rule_id_toeplitz = self.rssprocess.create_rule(rule=rule_toeplitz)
        self.rssprocess.check_rule(rule_list=rule_id_toeplitz)
        pkts_toeplitz = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
        ]
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(
            hash_value[1] != hash_value[0],
            "second packet should hash value different from the first packet",
        )
        self.verify(
            hash_value[2] == hash_value[0],
            "third packet should hash value same with the first packet",
        )
        # step 2
        rule_symmetric = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end"
        rule_id_symmetric = self.rssprocess.create_rule(rule=rule_symmetric)
        pkts_symmetric = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.3",dst="192.168.0.8",frag=6)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.8",dst="192.168.0.3",frag=6)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/ICMP()/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/ICMP()/("X"*480)',
        ]
        self.rssprocess.check_rule(rule_list=rule_id_symmetric)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_symmetric)
        self.verify(
            hash_value[0] == hash_value[1], "expect hash_value[0] == hash_value[1]"
        )
        self.verify(
            hash_value[2] == hash_value[3], "expect hash_value[2] == hash_value[3]"
        )
        self.verify(
            hash_value[4] == hash_value[5], "expect hash_value[4] == hash_value[5]"
        )
        # step 3
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        for temp in range(len(hash_value)):
            self.verify(
                len(hash_value[temp]) != 0,
                "all the toeplitz packet should have hash value",
            )
        self.pmd_output.execute_cmd("flow flush 0")

        self.logger.info("Subcase: toeplitz/symmetric with same ptype different UL/DL")
        # step 1
        rule_toeplitz = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end"
        pkts_toeplitz = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)',
        ]
        rule_symmetric = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end"
        pkts_symmetric = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.3",dst="192.168.0.8",frag=6)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.8",dst="192.168.0.3",frag=6)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.10",dst="192.168.0.20")/ICMP()/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.20",dst="192.168.0.10")/ICMP()/("X"*480)',
        ]
        rule_id_toeplitz = self.rssprocess.create_rule(rule=rule_toeplitz)
        self.rssprocess.check_rule(rule_list=rule_id_toeplitz)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(
            hash_value[1] != hash_value[0],
            "second packet should hash value different from the first packet",
        )
        self.verify(
            hash_value[2] == hash_value[0],
            "third packet should hash value same with the first packet",
        )
        rule_id_symmetric = self.rssprocess.create_rule(rule=rule_symmetric)
        self.rssprocess.check_rule(rule_list=rule_id_symmetric)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_symmetric)
        self.verify(
            hash_value[0] == hash_value[1], "expect hash_value[0] == hash_value[1]"
        )
        self.verify(
            hash_value[2] == hash_value[3], "expect hash_value[2] == hash_value[3]"
        )
        self.verify(
            hash_value[4] == hash_value[5], "expect hash_value[4] == hash_value[5]"
        )
        # step 2
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(
            hash_value[1] != hash_value[0],
            "second packet should hash value different from the first packet",
        )
        self.verify(
            hash_value[2] == hash_value[0],
            "third packet should hash value same with the first packet",
        )
        self.pmd_output.execute_cmd("flow flush 0")

        self.logger.info("Subcase: toeplitz/symmetric with different pattern")
        # step 1
        rule_toeplitz = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end"
        pkts_toeplitz = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=12, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/UDP(sport=22, dport=13)/("X"*480)',
        ]
        rule_symmetric = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end"
        pkts_symmetric = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="2222:3333:4444:5555:6666:7777:8888:9999",dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:ABCD",dst="1111:2222:3333:4444:5555:6666:7777:1234")/IPv6ExtHdrFragment()/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1234",dst="1111:2222:3333:4444:5555:6666:7777:ABCD")/IPv6ExtHdrFragment()/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1888",dst="2222:3333:4444:5555:6666:7777:8888:1999")/ICMP()/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="2222:3333:4444:5555:6666:7777:8888:1999",dst="1111:2222:3333:4444:5555:6666:7777:1888")/ICMP()/("X"*480)',
        ]
        rule_id_toeplitz = self.rssprocess.create_rule(rule=rule_toeplitz)
        self.rssprocess.check_rule(rule_list=rule_id_toeplitz)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(
            hash_value[1] != hash_value[0],
            "hash_value[1] should hash value different from hash_value[0]",
        )
        self.verify(
            hash_value[2] != hash_value[0],
            "hash_value[2] should hash value different with hash_value[0]",
        )
        self.verify(
            hash_value[3] == hash_value[0],
            "hash_value[3] should hash value same with hash_value[0]",
        )
        rule_id_symmetric = self.rssprocess.create_rule(rule=rule_symmetric)
        self.rssprocess.check_rule(rule_list=rule_id_symmetric)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_symmetric)
        self.verify(
            hash_value[0] == hash_value[1], "expect hash_value[0] == hash_value[1]"
        )
        self.verify(
            hash_value[2] == hash_value[3], "expect hash_value[2] == hash_value[3]"
        )
        self.verify(
            hash_value[4] == hash_value[5], "expect hash_value[4] == hash_value[5]"
        )
        # step 2
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(
            hash_value[1] != hash_value[0],
            "hash_value[1] should hash value different from hash_value[0]",
        )
        self.verify(
            hash_value[2] != hash_value[0],
            "hash_value[2] should hash value different with hash_value[0]",
        )
        self.verify(
            hash_value[3] == hash_value[0],
            "hash_value[3] should hash value same with hash_value[0]",
        )
        self.pmd_output.execute_cmd("flow flush 0")

        self.logger.info(
            "Subcase: toeplitz/symmetric with different pattern (with/without UL/DL)"
        )
        # step 1
        rule_toeplitz = "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end"
        pkts_toeplitz = [
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:1111")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=13)/("X"*480)',
        ]
        rule_symmetric = "flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end"
        pkts_symmetric = [
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:1111")/TCP(sport=22, dport=13)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:1111")/TCP(sport=22, dport=13)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", dst="2222:3333:4444:5555:6666:7777:8888:9999")/TCP(sport=12, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:1111", dst="2222:3333:4444:5555:6666:7777:8888:1111")/TCP(sport=22, dport=13)/("X"*480)',
        ]
        rule_id_toeplitz = self.rssprocess.create_rule(rule=rule_toeplitz)
        self.rssprocess.check_rule(rule_list=rule_id_toeplitz)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(
            hash_value[1] != hash_value[0],
            "hash_value[1] should hash value different from hash_value[0]",
        )
        self.verify(
            hash_value[2] == hash_value[0],
            "hash_value[2] should hash value same with hash_value[0]",
        )
        rule_id_symmetric = self.rssprocess.create_rule(rule=rule_symmetric)
        self.rssprocess.check_rule(rule_list=rule_id_symmetric)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_symmetric)
        self.verify(
            hash_value[1] != hash_value[0] and hash_value[2] == hash_value[0],
            "hash_value[0] should hash value different from hash_value[1] and equal to hash_value[2]",
        )
        self.verify(
            hash_value[4] != hash_value[3] and hash_value[5] == hash_value[3],
            "hash_value[3] should hash value different from hash_value[4] and equal to hash_value[5]",
        )
        self.verify(
            hash_value[6] != hash_value[7] and hash_value[6] == hash_value[8],
            "hash_value[6] should hash value different from hash_value[7] and equal to hash_value[8]",
        )
        # step 2
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(
            hash_value[1] == hash_value[0], "rule with UL/DL should can not work"
        )
        self.verify(
            hash_value[2] != hash_value[0], "rule with UL/DL should can not work"
        )
        self.pmd_output.execute_cmd("flow flush 0")

    def test_rss_function_when_disable_rss(self):
        self.pmd_output.quit()
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param="--rxq=16 --txq=16 --disable-rss --rxd=384 --txd=384",
            eal_param=f"-a {self.vf0_pci}",
            socket=self.ports_socket,
        )
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")
        res = self.pmd_output.wait_link_status_up("all", timeout=15)
        self.verify(res is True, "there have port link is down")
        rule = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end"
        self.rssprocess.create_rule(rule=rule)
        pkt = 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst=RandIP(),src=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)'
        output = self.rssprocess.send_pkt_get_output(pkts=pkt, count=1280)
        _, queues = self.rssprocess.get_hash_and_queues(output)
        hashes, rss_distribute = self.rssprocess.get_hash_verify_rss_distribute(output)
        self.verify(
            len(hashes) == 1280,
            "all the packets should have hash value and distributed to all queues by RSS.",
        )
        self.verify(
            len(set(queues)) == 16, "all the packets have distributed to all queues"
        )
        self.verify(rss_distribute, "the packet do not distribute by rss")

    # vf rss gtpc gtpu
    def test_mac_ipv4_gtpu(self):
        self.switch_testpmd(symmetric=False)
        self.handle_vlan_case(mac_ipv4_gtpu_toeplitz, [1, 3, 5], 0)

    def test_mac_ipv6_gtpu(self):
        self.switch_testpmd(symmetric=False)
        self.handle_vlan_case(mac_ipv6_gtpu_toeplitz, [1, 5, 7], 0)

    def test_mac_ipv4_gtpc(self):
        self.switch_testpmd(symmetric=False)
        self.handle_vlan_case(mac_ipv4_gtpc_toeplitz, [1, 3, 5], 0)

    def test_mac_ipv6_gtpc(self):
        self.switch_testpmd(symmetric=False)
        self.handle_vlan_case(mac_ipv6_gtpc_toeplitz, [1, 3, 5], 0)

    def test_mac_ipv4_gtpu_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.handle_vlan_case(mac_ipv4_gtpu_symmetric_toeplitz, 1, 0)

    def test_mac_ipv6_gtpu_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.handle_vlan_case(mac_ipv6_gtpu_symmetric_toeplitz, 1, 0)

    def test_mac_ipv4_gtpc_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.handle_vlan_case(mac_ipv4_gtpc_symmetric_toeplitz, 1, 0)

    def test_mac_ipv6_gtpc_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.handle_vlan_case(mac_ipv6_gtpc_symmetric_toeplitz, 1, 0)

    def tear_down(self):
        # destroy all flow rule on port 0
        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")

    def tear_down_all(self):
        self.destroy_vf()
        self.dut.kill_all()
