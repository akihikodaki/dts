# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re
import traceback

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, skip_unsupported_pkg
from framework.utils import GREEN, RED

from .rte_flow_common import RssProcessing

MAC_IPv4_UDP = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22,dport=23)/Raw("x" * 80)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.20",dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22")/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=21,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=24)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
    ],
}
# Test case 1: VF_RSS_MAC/IPv4/UDP
mac_ipv4_udp = {
    "sub_casename": "mac_ipv4_udp",
    "rule": "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500001C0000000000110000C0A80014C0A800150016001700080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF00000000 / end actions rss queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv4_UDP["basic"],
            "action": {"save_hash": "ipv4-udp"},
        },
        {
            "send_packet": MAC_IPv4_UDP["mismatch"],
            "action": {"check_hash_different": "ipv4-udp"},
        },
    ],
}

MAC_IPv6_TCP_sysmetric = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=23,dport=22)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:1010", src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:1010", src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=23,dport=22)/("X"*480)',
    ],
}
# Test case 2: VF_RSS_MAC/IPv6/TCP_sysmetric
mac_ipv6_tcp_sysmetric = {
    "sub_casename": "mac_ipv6_tcp_sysmetric",
    "rule": "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000140600CDCD910A222254988475111139001010CDCD910A2222549884751111390020200016001700000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions rss func symmetric_toeplitz queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv6_TCP_sysmetric["basic"],
            "action": {"save_hash": "ipv6-tcp"},
        },
        {
            "send_packet": MAC_IPv6_TCP_sysmetric["match"],
            "action": {"check_hash_same": "ipv6-tcp"},
        },
    ],
}

MAC_IPv4_UDP_VXLAN_MAC_IPv4_PAY = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)',
    ],
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=33)/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.10.20",dst="192.168.0.21")/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.10.21")/Raw("x" * 80)',
    ],
}
# Test case 3: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4/PAY
mac_ipv4_udp_vxlan_mac_ipv4_pay = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_pay",
    "rule": "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000003000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_PAY["basic"],
            "action": {"save_hash": "ipv4_udp_vxlan_ipv4_pay"},
        },
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_PAY["mismatch"],
            "action": {"check_hash_different": "ipv4_udp_vxlan_ipv4_pay"},
        },
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_PAY["match"],
            "action": {"check_hash_same": "ipv4_udp_vxlan_ipv4_pay"},
        },
    ],
}

MAC_IPv4_UDP_VXLAN_MAC_IPv4_UDP = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/("X"*480)',
    ],
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=33)/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.10.20",dst="192.168.0.21")/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.10.21")/UDP()/("X"*480)',
    ],
}
# Test case 4: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4/UDP
mac_ipv4_udp_vxlan_mac_ipv4_udp = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_udp",
    "rule": "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004E00000000001100000101010102020202000012B5003A0000080000000000000000000000000100000000000208004500001C0000000000110000C0A80014C0A800150000000000080000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions rss queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_UDP["basic"],
            "action": {"save_hash": "ipv4_udp_vxlan_ipv6_pay"},
        },
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_UDP["mismatch"],
            "action": {"check_hash_different": "ipv4_udp_vxlan_ipv6_pay"},
        },
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_UDP["match"],
            "action": {"check_hash_same": "ipv4_udp_vxlan_ipv6_pay"},
        },
    ],
}

MAC_IPv4_UDP_VXLAN_MAC_IPv4_sysmetric = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)',
    ],
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.21",dst="192.168.0.20")/Raw("x" * 80)',
    ],
}
# Test case 5: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4_sysmetric
mac_ipv4_udp_vxlan_mac_ipv4_sysmetric = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_sysmetric",
    "rule": "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss func symmetric_toeplitz queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_sysmetric["basic"],
            "action": {"save_hash": "ipv6_udp_vxlan_ipv4_pay"},
        },
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_sysmetric["match"],
            "action": {"check_hash_same": "ipv6_udp_vxlan_ipv4_pay"},
        },
    ],
}

MAC_IPv4_UDP_VXLAN_MAC_IPv4 = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)',
    ],
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.10.21")/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.10")/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=22)/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.10.20",dst="192.168.0.21")/("X"*480)',
    ],
}
# Test case 6: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4_inner-l3-src-only
mac_ipv4_udp_vxlan_mac_ipv4 = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4",
    "rule": "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFF00000000 / end actions rss queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4["basic"],
            "action": {"save_hash": "ipv4_udp_vxlan_ipv6_tcp"},
        },
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4["mismatch"],
            "action": {"check_hash_different": "ipv4_udp_vxlan_ipv6_tcp"},
        },
        {
            "send_packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4["match"],
            "action": {"check_hash_same": "ipv4_udp_vxlan_ipv6_tcp"},
        },
    ],
}

MAC_IPv4_UDP_GTPU_IPv4 = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw("x"*20)',
    ],
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x567)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.30", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.30", dst="192.168.10.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.31")/Raw("x"*20)',
    ],
}
# Test case 7: VF_RSS_MAC/IPv4/UDP/GTPU/IPv4
mac_ipv4_udp_gtpu_ipv4 = {
    "sub_casename": "mac_ipv4_udp_gtpu_ipv4",
    "rule": "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000380000000000110000C0A80014C0A80015000008680024000030FF001400000000450000140000000000000000C0A80A14C0A80A15 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv4_UDP_GTPU_IPv4["basic"],
            "action": {"save_hash": "ipv4_gtpu_ipv4"},
        },
        {
            "send_packet": MAC_IPv4_UDP_GTPU_IPv4["mismatch"],
            "action": {"check_hash_different": "ipv4_gtpu_ipv4"},
        },
        {
            "send_packet": MAC_IPv4_UDP_GTPU_IPv4["match"],
            "action": {"check_hash_same": "ipv4_gtpu_ipv4"},
        },
    ],
}

MAC_IPv4_UDP_GTPU_IPv6_UDP = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw("x"*20)',
    ],
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1011", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw("x"*20)',
    ],
}
# Test case 8: VF_RSS_MAC/IPv4/UDP/GTPU/IPv6/UDP_outer-l3
mac_ipv4_udp_gtpu_ipv6_udp = {
    "sub_casename": "mac_ipv4_udp_gtpu_ipv6_udp",
    "rule": "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000540000000000110000C0A80014C0A80015000008680040000030FF0030000000006000000000081100CDCD910A222254988475111139001010CDCD910A2222549884751111390020210000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 / end actions rss queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv4_UDP_GTPU_IPv6_UDP["basic"],
            "action": {"save_hash": "ipv4_gtpu_ipv6_udp"},
        },
        {
            "send_packet": MAC_IPv4_UDP_GTPU_IPv6_UDP["mismatch"],
            "action": {"check_hash_different": "ipv4_gtpu_ipv6_udp"},
        },
        {
            "send_packet": MAC_IPv4_UDP_GTPU_IPv6_UDP["match"],
            "action": {"check_hash_same": "ipv4_gtpu_ipv6_udp"},
        },
    ],
}

MAC_IPv4_UDP_GTPU_EH_IPv4_UDP_sysmetric = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/UDP()/Raw("x"*20)',
    ],
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.21", dst="192.168.1.20")/UDP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.20")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/UDP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.20")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.21", dst="192.168.1.20")/UDP()/Raw("x"*20)',
    ],
}
# Test case 9: VF_RSS_MAC/IPv4/UDP/GTPU/EH/IPv4/UDP_innersysmetric
mac_ipv4_udp_gtpu_eh_ipv4_udp_sysmetric = {
    "sub_casename": "mac_ipv4_udp_gtpu_eh_ipv4_udp_sysmetric ",
    "rule": "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000440000000000110000C0A80014C0A80014000008680030000034FF00240000000000000085010000004500001C0000000000110000C0A80114C0A801150000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions rss func symmetric_toeplitz queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv4_UDP_GTPU_EH_IPv4_UDP_sysmetric["basic"],
            "action": {"save_hash": "ipv6_gtpu_eh_ipv4_tcp"},
        },
        {
            "send_packet": MAC_IPv4_UDP_GTPU_EH_IPv4_UDP_sysmetric["match"],
            "action": {"check_hash_same": "ipv6_gtpu_eh_ipv4_tcp"},
        },
    ],
}

MAC_IPv4_UDP_GTPU_UL_IPv4 = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw("x"*20)',
    ],
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.11.20", dst="192.168.1.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.11.21")/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.10.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw("x"*20)',
    ],
}
# Test case 10: VF_RSS_MAC/IPv4/UDP/GTPU/UL/IPv4_inner-l3-dst-only
mac_ipv4_udp_gtpu_ul_ipv4 = {
    "sub_casename": "mac_ipv4_udp_gtpu_ul_ipv4",
    "rule": "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500003C0000000000110000C0A80014C0A80015000008680028000034FF001C000000000000008501100000450000140000000000000000C0A80114C0A80115 pattern mask 000000000000000000000000000000000000000000000000000000000000FFFFFFFF000000000000000000000000000000000000000000F000000000000000000000000000000000000000000000 / end actions rss queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv4_UDP_GTPU_UL_IPv4["basic"],
            "action": {"save_hash": "ipv4_gtpu_ul_ipv4"},
        },
        {
            "send_packet": MAC_IPv4_UDP_GTPU_UL_IPv4["mismatch"],
            "action": {"check_hash_different": "ipv4_gtpu_ul_ipv4"},
        },
        {
            "send_packet": MAC_IPv4_UDP_GTPU_UL_IPv4["match"],
            "action": {"check_hash_same": "ipv4_gtpu_ul_ipv4"},
        },
    ],
}

MAC_IPv4_UDP_GTPU_DL_IPv4_TCP = {
    "basic": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw("x"*20)',
    ],
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.10.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.11.20", dst="192.168.1.21")/TCP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.21", dst="192.168.1.21")/TCP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.22")/TCP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.22")/TCP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.22")/TCP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="191.168.1.20", dst="192.168.1.21")/TCP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.161.1.20", dst="192.168.1.21")/TCP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw("x"*20)',
    ],
}
# Test case 11: VF_RSS_MAC/IPv4/UDP/GTPU/DL/IPv4/TCP_un-word-aligned key
mac_ipv4_udp_gtpu_dl_ipv4_tcp = {
    "sub_casename": "mac_ipv4_udp_gtpu_dl_ipv4_tcp",
    "rule": "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF0030000000000000008501000000450000280000000000060000C0A80114C0A801150000000000000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F00000000000000000000000000000FFFF0000000000000000000000000000000000000000000000000000 / end actions rss queues end / end",
    "test": [
        {
            "send_packet": MAC_IPv4_UDP_GTPU_DL_IPv4_TCP["basic"],
            "action": {"save_hash": "ipv4_gtpu_dl_ipv4_tcp"},
        },
        {
            "send_packet": MAC_IPv4_UDP_GTPU_DL_IPv4_TCP["mismatch"],
            "action": {"check_hash_different": "ipv4_gtpu_dl_ipv4_tcp"},
        },
        {
            "send_packet": MAC_IPv4_UDP_GTPU_DL_IPv4_TCP["match"],
            "action": {"check_hash_same": "ipv4_gtpu_dl_ipv4_tcp"},
        },
    ],
}

vf1_mac = "00:11:22:33:44:55"
# tester send pcaket port
tPort = 0
# dut receive packet port
dPort = 1
port_topology = {"port_id": dPort, "tport_id": tPort}


class TestIavfRssProtocolAgnosticFlow(TestCase):
    """
    E810 enable Protocol agnostic flow offloading
    """

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.skip_case("ICE" in self.nic, "%s nic not support this suite" % self.nic)
        self.dports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dports) >= 1, "Insufficient ports")
        self.pf_interface = self.dut.ports_info[self.dports[0]]["intf"]
        self.pmd_output = PmdOutput(self.dut)
        self.tester_ifaces = [
            self.tester.get_interface(self.dut.ports_map[port]) for port in self.dports
        ]
        self.rxq = 16
        self.pkt = Packet()
        self.rsspro = RssProcessing(
            self, self.pmd_output, self.tester_ifaces, rxq=self.rxq
        )
        self.create_iavf()

    @skip_unsupported_pkg("os default")
    def set_up(self):
        """
        Run before each test case.
        """
        self.launch_testpmd()

    def create_iavf(self):
        self.dut.restore_interfaces()
        self.dut.generate_sriov_vfs_by_port(self.dports[0], 2)
        # set VF0 as trust
        self.dut.send_expect("ip link set %s vf 0 trust on" % self.pf_interface, "#")
        self.sriov_vfs_port = self.dut.ports_info[self.dports[0]]["vfs_port"]
        self.vf_pci0 = self.sriov_vfs_port[0].pci
        self.vf_pci1 = self.sriov_vfs_port[1].pci
        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.drivername)
            self.dut.send_expect("ifconfig %s up" % self.pf_interface, "# ")
            self.dut.send_expect(
                "ip link set %s vf 1 mac %s" % (self.pf_interface, vf1_mac), "# "
            )
        except Exception as e:
            self.destroy_iavf()
            raise Exception(e)

    def launch_testpmd(self):
        """
        launch testpmd with the command
        """
        params = "--rxq={0} --txq={0} --disable-rss --txd=384 --rxd=384".format(
            self.rxq
        )
        eal_params = '-a {},cap=dcf -a {} --log-level="ice,7"'.format(
            self.vf_pci0, self.vf_pci1
        )
        self.pmd_output.start_testpmd(param=params, eal_param=eal_params)
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add vxlan 0x12b5")
        self.pmd_output.execute_cmd("start")
        self.pmd_output.wait_link_status_up(0)

    def destroy_iavf(self):
        self.dut.destroy_sriov_vfs_by_port(self.dports[0])
        self.dut.bind_interfaces_linux(self.drivername)

    def send_pkt_get_output(self, pkts, port_id=0, tport_id=0, count=1, interval=0):
        tx_port = self.tester_ifaces[tport_id] if tport_id else self.tester_ifaces[0]
        self.logger.info("----------send packet-------------")
        self.logger.info("{}".format(pkts))
        self.pkt.update_pkt(pkts)
        self.pkt.send_pkt(
            crb=self.tester,
            tx_port=tx_port,
            count=count,
            interval=interval,
        )
        out = self.pmd_output.get_output(timeout=1)
        pkt_pattern = (
            "port\s%d/queue\s\d+:\sreceived\s(\d+)\spackets.+?\n.*length=\d{2,}\s"
            % port_id
        )
        reveived_data = re.findall(pkt_pattern, out)
        reveived_pkts = sum(map(int, [i[0] for i in reveived_data]))
        if isinstance(pkts, list):
            self.verify(
                reveived_pkts == len(pkts) * count,
                "expect received %d pkts, but get %d instead"
                % (len(pkts) * count, reveived_pkts),
            )
        else:
            self.verify(
                reveived_pkts == 1 * count,
                "expect received %d pkts, but get %d instead"
                % (1 * count, reveived_pkts),
            )
        return out

    def handle_tests(self, tests, port_id=0, tport_id=0):
        out = ""
        for test in tests:
            if "send_packet" in test:
                out = self.send_pkt_get_output(
                    test["send_packet"], port_id=port_id, tport_id=tport_id
                )
            if "action" in test:
                self.rsspro.handle_actions(out, test["action"], port_id)

    def handle_rss_case(self, case_info):
        # clear hash_records before each sub case
        self.hash_records = {}
        self.error_msgs = []
        self.current_saved_hash = ""
        sub_case_name = case_info.get("sub_casename")
        self.logger.info(
            "===================Test sub case: {}================".format(sub_case_name)
        )
        # received packet port id
        port_id = case_info.get("port_id") if case_info.get("port_id") else 0
        # send packet port id
        tport_id = case_info.get("tport_id") if case_info.get("tport_id") else 0
        rules = case_info.get("rule") if case_info.get("rule") else []
        rule_ids = []
        if "pre-test" in case_info:
            self.logger.info("------------handle pre-test--------------")
            self.handle_tests(case_info["pre-test"], port_id=port_id, tport_id=tport_id)

        # handle tests
        tests = case_info["test"]
        self.logger.info("------------handle test--------------")
        # validate rule
        if rules:
            self.rsspro.validate_rule(rule=rules, check_stats=True)
            rule_ids = self.rsspro.create_rule(rule=case_info["rule"], check_stats=True)
            self.rsspro.check_rule(port_id=port_id, rule_list=rule_ids)
        self.handle_tests(tests, port_id=port_id, tport_id=tport_id)

        # handle post-test
        if "post-test" in case_info:
            self.logger.info("------------handle post-test--------------")
            self.rsspro.destroy_rule(port_id=port_id, rule_id=rule_ids)
            self.rsspro.check_rule(port_id=port_id, stats=False)
            self.rsspro.handle_tests(case_info["post-test"], port_id=port_id)
        if self.error_msgs:
            self.verify(
                False,
                " ".join([errs.replace("'", " ") for errs in self.error_msgs[:500]]),
            )

    def rte_flow(self, case_list, func_name, **kwargs):
        """
        main flow of case:
            1. iterate the case list and do the below steps:
                a. get the subcase name and init dict to save result
                b. call method by func name to execute case step
                c. record case result and err msg if case failed
                d. clear flow rule
            2. calculate the case passing rate according to the result dict
            3. record case result and pass rate in the case log file
            4. verify whether the case pass rate is equal to 100, if not, mark the case as failed and raise the err msg
        :param case_list: case list, each item is a subcase of case
        :param func_name: hadle case method name, eg:
                        'flow_rule_operate': a method of 'FlowRuleProcessing' class,
                        used to handle flow rule related suites,such as fdir and switch_filter
                        'handle_rss_distribute_cases': a method of 'RssProcessing' class,
                        used to handle rss related suites
        :return:
        usage:
        for flow rule related:
            rte_flow(caselist, flow_rule_operate)
        for rss related:
            rte_flow(caselist, handle_rss_distribute_cases)
        """
        if not isinstance(case_list, list):
            case_list = [case_list]
        test_results = dict()
        for case in case_list:
            case_name = case.get("sub_casename")
            test_results[case_name] = {}
            try:
                self.logger.info("{0} case_name:{1} {0}".format("*" * 20, case_name))
                case.update(kwargs)
                func_name(case)
            except Exception:
                test_results[case_name]["result"] = "failed"
                test_results[case_name]["err"] = re.sub(
                    r"['\r\n]", "", str(traceback.format_exc(limit=1))
                ).replace("\\\\", "\\")
                self.logger.info(
                    (
                        RED(
                            "case failed:{}, err:{}".format(
                                case_name, traceback.format_exc()
                            )
                        )
                    )
                )
            else:
                test_results[case_name]["result"] = "passed"
                self.logger.info((GREEN("case passed: {}".format(case_name))))
            finally:
                check_param = case.get("check_param")
                if check_param:
                    port_id = check_param.get("port_id")
                else:
                    port_id = case.get("port_id") if case.get("port_id") else 0
                self.pmd_output.execute_cmd("flow flush %s" % port_id)
        pass_rate = (
            round(
                sum(1 for k in test_results if "passed" in test_results[k]["result"])
                / len(test_results),
                4,
            )
            * 100
        )
        self.logger.info(
            [
                "{}:{}".format(sub_name, test_results[sub_name]["result"])
                for sub_name in test_results
            ]
        )
        self.logger.info("pass rate is: {}".format(pass_rate))
        msg = [
            "subcase_name:{}:{},err:{}".format(
                name, test_results[name].get("result"), test_results[name].get("err")
            )
            for name in test_results.keys()
            if "failed" in test_results[name]["result"]
        ]
        self.verify(
            int(pass_rate) == 100,
            "some subcases failed, detail as below:{}".format(msg),
        )

    def test_multi_rules_mac_ipv4_udp_vxlan_ipv6(self):
        """
        Test case 12: VF_RSS_multi-rules_MAC/IPv4/UDP/VXLAN/IPv6
        """
        rules = [
            "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004C00000000001100000101010102020202000012B50038000008000000000000006000000000000000CDCD910A222254988475111139001010CDCD910A222254988475111139002021 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF / end actions rss queues end / end",
            "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004C00000000001100000101010102020202000012B50038000008000000000000006000000000000000CDCD910A222254988475111139001010CDCD910A222254988475111139002021 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions rss queues end / end",
        ]
        MAC_IPv4_UDP_VXLAN_IPv6 = {
            "basic": [
                'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)',
            ],
            "match": [
                'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/("X"*480)',
            ],
            "mismatch": [
                'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1011", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)',
            ],
        }
        tests = [
            {
                "send_packet": MAC_IPv4_UDP_VXLAN_IPv6["basic"],
                "action": {"save_hash": "ipv4_udp_vxlan_ipv6"},
            },
            {
                "send_packet": MAC_IPv4_UDP_VXLAN_IPv6["mismatch"],
                "action": {"check_hash_different": "ipv4_udp_vxlan_ipv6"},
            },
            {
                "send_packet": MAC_IPv4_UDP_VXLAN_IPv6["match"],
                "action": {"check_hash_same": "ipv4_udp_vxlan_ipv6"},
            },
        ]
        # create rule
        self.rsspro.create_rule(rules, check_stats=True)
        self.rsspro.error_msgs = []
        self.rsspro.error_msgs = []
        self.handle_tests(tests, port_id=dPort, tport_id=tPort)
        if self.rsspro.error_msgs:
            self.verify(
                False,
                " ".join(
                    [errs.replace("'", " ") for errs in self.rsspro.error_msgs[:500]]
                ),
            )

    def test_mac_ipv4_udp_gtpu_dl_ipv4_tcp(self):
        """
        Test case 11: VF_RSS_MAC/IPv4/UDP/GTPU/DL/IPv4/TCP_un-word-aligned key
        """
        func_name = self.handle_rss_case
        self.rte_flow(mac_ipv4_udp_gtpu_dl_ipv4_tcp, func_name, **port_topology)

    def test_mac_ipv4_udp_gtpu_ul_ipv4(self):
        """
        Test case 10: VF_RSS_MAC/IPv4/UDP/GTPU/UL/IPv4_inner-l3-dst-only
        """
        func_name = self.handle_rss_case
        self.rte_flow(mac_ipv4_udp_gtpu_ul_ipv4, func_name, **port_topology)

    def test_mac_ipv4_udp_gtpu_eh_ipv4_udp_sysmetric(self):
        """
        Test case 9: VF_RSS_MAC/IPv4/GTPU/EH/IPv4/DUP_innersysmetric
        """
        func_name = self.handle_rss_case
        self.rte_flow(
            mac_ipv4_udp_gtpu_eh_ipv4_udp_sysmetric, func_name, **port_topology
        )

    def test_mac_ipv4_udp_gtpu_ipv6_udp(self):
        """
        # Test case 8: VF_RSS_MAC/IPv4/UDP/GTPU/IPv6/UDP_outer-l3
        """
        func_name = self.handle_rss_case
        self.rte_flow(mac_ipv4_udp_gtpu_ipv6_udp, func_name, **port_topology)

    def test_mac_ipv4_udp_gtpu_ipv4(self):
        """
        Test case 7: VF_RSS_MAC/IPv4/UDP/GTPU/IPv4
        """
        func_name = self.handle_rss_case
        self.rte_flow(mac_ipv4_udp_gtpu_ipv4, func_name, **port_topology)

    def test_mac_ipv4_udp_vxlan_mac_ipv4(self):
        """
        Test case 6: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4_inner-l3-src-only
        """
        func_name = self.handle_rss_case
        self.rte_flow(mac_ipv4_udp_vxlan_mac_ipv4, func_name, **port_topology)

    def test_mac_ipv4_udp_vxlan_mac_ipv4_sysmetric(self):
        """
        Test case 5: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4_sysmetric
        """
        func_name = self.handle_rss_case
        self.rte_flow(mac_ipv4_udp_vxlan_mac_ipv4_sysmetric, func_name, **port_topology)

    def test_mac_ipv4_udp_vxlan_mac_ipv4_udp(self):
        """
        Test case 4: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4/UDP
        """
        func_name = self.handle_rss_case
        self.rte_flow(mac_ipv4_udp_vxlan_mac_ipv4_udp, func_name, **port_topology)

    def test_mac_ipv4_udp_vxlan_mac_ipv4_pay(self):
        """
        Test case 3: VF_RSS_MAC/IPv4/UDP/VXLAN/MAC/IPv4/PAY
        """
        func_name = self.handle_rss_case
        self.rte_flow(mac_ipv4_udp_vxlan_mac_ipv4_pay, func_name, **port_topology)

    def test_mac_ipv6_tcp_sysmetric(self):
        """
        Test case 2: VF_RSS_MAC/IPv6/TCP_sysmetric
        """
        func_name = self.handle_rss_case
        self.rte_flow(mac_ipv6_tcp_sysmetric, func_name, **port_topology)

    def test_mac_ipv4_udp(self):
        """
        Test case 1: VF_RSS_MAC/IPv4/UDP
        """
        func_name = self.handle_rss_case
        self.rte_flow(mac_ipv4_udp, func_name, **port_topology)

    def tear_down(self):
        """
        Run after each test case.
        """
        try:
            self.pmd_output.quit()
        except:
            self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.destroy_iavf()
