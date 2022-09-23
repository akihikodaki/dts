# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#


import copy
import re
import traceback
from collections import OrderedDict

from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, skip_unsupported_pkg
from framework.utils import GREEN, RED

from .rte_flow_common import FdirProcessing

MAC_IPv4_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw("x" * 80)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.20",dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22")/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=21,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=24)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
    ],
}

mac_ipv4_udp_queue = {
    "sub_casename": "mac_ipv4_udp_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500001C0000000000110000C0A80014C0A800150016001700080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF00000000 / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv4_UDP,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv4_udp_rss = {
    "sub_casename": "mac_ipv4_udp_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500001C0000000000110000C0A80014C0A800150016001700080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF00000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv4_UDP,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv4_udp_passthru = {
    "sub_casename": "mac_ipv4_udp_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500001C0000000000110000C0A80014C0A800150016001700080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF00000000 / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv4_UDP,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv4_udp_drop = {
    "sub_casename": "mac_ipv4_udp_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500001C0000000000110000C0A80014C0A800150016001700080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF00000000 / end actions drop / end",
    ],
    "packet": MAC_IPv4_UDP,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 1: VF_FDIR_MAC/IPv4/UDP
mac_ipv4_udp = [
    mac_ipv4_udp_queue,
    mac_ipv4_udp_rss,
    mac_ipv4_udp_passthru,
    mac_ipv4_udp_drop,
]

MAC_IPv6_TCP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1011")/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/TCP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="CDCD:910A:2222:5498:8475:1111:3900:1010")/UDP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv6_tcp_queue = {
    "sub_casename": "mac_ipv6_tcp_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000140600CDCD910A222254988475111139001010CDCD910A2222549884751111390020200016001700000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv6_TCP,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv6_tcp_rss = {
    "sub_casename": "mac_ipv6_tcp_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000140600CDCD910A222254988475111139001010CDCD910A2222549884751111390020200016001700000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv6_TCP,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv6_tcp_passthru = {
    "sub_casename": "mac_ipv6_tcp_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000140600CDCD910A222254988475111139001010CDCD910A2222549884751111390020200016001700000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv6_TCP,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv6_tcp_drop = {
    "sub_casename": "mac_ipv6_tcp_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000140600CDCD910A222254988475111139001010CDCD910A2222549884751111390020200016001700000000000000005000000000000000 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000 / end actions drop / end",
    ],
    "packet": MAC_IPv6_TCP,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 2: VF_FDIR_MAC/IPv6/TCP
mac_ipv6_tcp = [
    mac_ipv6_tcp_queue,
    mac_ipv6_tcp_rss,
    mac_ipv6_tcp_passthru,
    mac_ipv6_tcp_drop,
]

MAC_IPv4_UDP_VXLAN_MAC_IPv4_PAY = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.1.21")/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.1.20",dst="192.168.0.21")/Raw("x" * 80)',
    ],
}

mac_ipv4_udp_vxlan_mac_ipv4_pay_queue = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_pay_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000460000000000110000C0A80014C0A80015000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_PAY,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv4_udp_vxlan_mac_ipv4_pay_rss = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_pay_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000460000000000110000C0A80014C0A80015000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_PAY,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv4_udp_vxlan_mac_ipv4_pay_passthru = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_pay_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000460000000000110000C0A80014C0A80015000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_PAY,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv4_udp_vxlan_mac_ipv4_pay_drop = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_pay_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000460000000000110000C0A80014C0A80015000012B50032000008000000000000000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions drop / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_PAY,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 3: VF_FDIR_MAC/IPv4/UDP/VXLAN/MAC/IPv4/PAY
mac_ipv4_udp_vxlan_mac_ipv4_pay = [
    mac_ipv4_udp_vxlan_mac_ipv4_pay_queue,
    mac_ipv4_udp_vxlan_mac_ipv4_pay_rss,
    mac_ipv4_udp_vxlan_mac_ipv4_pay_passthru,
    mac_ipv4_udp_vxlan_mac_ipv4_pay_drop,
]

MAC_IPv4_UDP_VXLAN_MAC_IPv4_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.10.20",dst="192.168.0.21")/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.10.21")/UDP()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/TCP()/("X"*480)',
    ],
}

mac_ipv4_udp_vxlan_mac_ipv4_udp_queue = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_udp_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004E00000000001100000101010102020202000012B5003A0000080000000000000000000000000100000000000208004500001C0000000000110000C0A80014C0A800150000000000080000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_UDP,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv4_udp_vxlan_mac_ipv4_udp_rss = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_udp_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004E00000000001100000101010102020202000012B5003A0000080000000000000000000000000100000000000208004500001C0000000000110000C0A80014C0A800150000000000080000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_UDP,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv4_udp_vxlan_mac_ipv4_udp_passthru = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_udp_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004E00000000001100000101010102020202000012B5003A0000080000000000000000000000000100000000000208004500001C0000000000110000C0A80014C0A800150000000000080000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_UDP,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv4_udp_vxlan_mac_ipv4_udp_drop = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_udp_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004E00000000001100000101010102020202000012B5003A0000080000000000000000000000000100000000000208004500001C0000000000110000C0A80014C0A800150000000000080000 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions drop / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_UDP,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 4: VF_FDIR_MAC/IPv4/UDP/VXLAN/MAC/IPv4/UDP
mac_ipv4_udp_vxlan_mac_ipv4_udp = [
    mac_ipv4_udp_vxlan_mac_ipv4_udp_queue,
    mac_ipv4_udp_vxlan_mac_ipv4_udp_rss,
    mac_ipv4_udp_vxlan_mac_ipv4_udp_passthru,
    mac_ipv4_udp_vxlan_mac_ipv4_udp_drop,
]

MAC_IPv4_UDP_VXLAN_MAC_IPv4_vni = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.10.20",dst="192.168.0.21")/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.20",dst="192.168.10.21")/("X"*480)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=13)/Ether()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)',
    ],
}

mac_ipv4_udp_vxlan_mac_ipv4_vni_queue = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_vni_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000003000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F0000000000000000000000000000000000000000000000000000000000000000000000 / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_vni,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv4_udp_vxlan_mac_ipv4_vni_rss = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_vni_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000003000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F0000000000000000000000000000000000000000000000000000000000000000000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_vni,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv4_udp_vxlan_mac_ipv4_vni_passthru = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_vni_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000003000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F0000000000000000000000000000000000000000000000000000000000000000000000 / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_vni,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv4_udp_vxlan_mac_ipv4_vni_drop = {
    "sub_casename": "mac_ipv4_udp_vxlan_mac_ipv4_vni_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500004600000000001100000101010102020202000012B50032000008000000000003000000000000010000000000020800450000140000000000000000C0A80014C0A80015 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F0000000000000000000000000000000000000000000000000000000000000000000000 / end actions drop / end",
    ],
    "packet": MAC_IPv4_UDP_VXLAN_MAC_IPv4_vni,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 5: VF_FDIR_MAC/IPv4/UDP/VXLAN/MAC/IPv4_vni
mac_ipv4_udp_vxlan_mac_ipv4_vni = [
    mac_ipv4_udp_vxlan_mac_ipv4_vni_queue,
    mac_ipv4_udp_vxlan_mac_ipv4_vni_rss,
    mac_ipv4_udp_vxlan_mac_ipv4_vni_passthru,
    mac_ipv4_udp_vxlan_mac_ipv4_vni_drop,
]

MAC_IPv4_UDP_GTPU_IPv4 = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.30", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.30", dst="192.168.10.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.10.20", dst="192.168.10.31")/Raw("x"*20)',
    ],
}

mac_ipv4_udp_gtpu_ipv4_queue = {
    "sub_casename": "mac_ipv4_udp_gtpu_ipv4_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000380000000000110000C0A80014C0A80015000008680024000030FF001400000000450000140000000000000000C0A80A14C0A80A15 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_IPv4,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv4_udp_gtpu_ipv4_rss = {
    "sub_casename": "mac_ipv4_udp_gtpu_ipv4_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000380000000000110000C0A80014C0A80015000008680024000030FF001400000000450000140000000000000000C0A80A14C0A80A15 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_IPv4,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv4_udp_gtpu_ipv4_passthru = {
    "sub_casename": "mac_ipv4_udp_gtpu_ipv4_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000380000000000110000C0A80014C0A80015000008680024000030FF001400000000450000140000000000000000C0A80A14C0A80A15 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_IPv4,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv4_udp_gtpu_ipv4_drop = {
    "sub_casename": "mac_ipv4_udp_gtpu_ipv4_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000380000000000110000C0A80014C0A80015000008680024000030FF001400000000450000140000000000000000C0A80A14C0A80A15 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF00000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions drop / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_IPv4,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 6: VF_FDIR_MAC/IPv4/UDP/GTPU/IPv4
mac_ipv4_udp_gtpu_ipv4 = [
    mac_ipv4_udp_gtpu_ipv4_queue,
    mac_ipv4_udp_gtpu_ipv4_rss,
    mac_ipv4_udp_gtpu_ipv4_passthru,
    mac_ipv4_udp_gtpu_ipv4_drop,
]

MAC_IPv4_UDP_GTPU_IPv6_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.10.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1011", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP()/Raw("x"*20)',
    ],
}

mac_ipv4_udp_gtpu_ipv6_udp_queue = {
    "sub_casename": "mac_ipv4_udp_gtpu_ipv6_udp_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000540000000000110000C0A80014C0A80015000008680040000030FF0030000000006000000000081100CDCD910A222254988475111139001010CDCD910A2222549884751111390020210000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000000000000000 / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_IPv6_UDP,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv4_udp_gtpu_ipv6_udp_rss = {
    "sub_casename": "mac_ipv4_udp_gtpu_ipv6_udp_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000540000000000110000C0A80014C0A80015000008680040000030FF0030000000006000000000081100CDCD910A222254988475111139001010CDCD910A2222549884751111390020210000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000000000000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_IPv6_UDP,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv4_udp_gtpu_ipv6_udp_passthru = {
    "sub_casename": "mac_ipv4_udp_gtpu_ipv6_udp_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000540000000000110000C0A80014C0A80015000008680040000030FF0030000000006000000000081100CDCD910A222254988475111139001010CDCD910A2222549884751111390020210000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000000000000000 / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_IPv6_UDP,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv4_udp_gtpu_ipv6_udp_drop = {
    "sub_casename": "mac_ipv4_udp_gtpu_ipv6_udp_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000540000000000110000C0A80014C0A80015000008680040000030FF0030000000006000000000081100CDCD910A222254988475111139001010CDCD910A2222549884751111390020210000000000080000 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000000000000000 / end actions drop / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_IPv6_UDP,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 7: VF_FDIR_MAC/IPv4/UDP/GTPU/IPv6/UDP
mac_ipv4_udp_gtpu_ipv6_udp = [
    mac_ipv4_udp_gtpu_ipv6_udp_queue,
    mac_ipv4_udp_gtpu_ipv6_udp_rss,
    mac_ipv4_udp_gtpu_ipv6_udp_passthru,
    mac_ipv4_udp_gtpu_ipv6_udp_drop,
]

MAC_IPv6_UDP_GTPU_DL_IPv4 = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1011", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.20", dst="192.168.0.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.20", dst="192.168.10.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1010", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x"*20)',
    ],
}

mac_ipv6_udp_gtpu_dl_ipv4_queue = {
    "sub_casename": "mac_ipv6_udp_gtpu_dl_ipv4_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000281100CDCD910A222254988475111139001010CDCD910A222254988475111139002021000008680028000034FF001C000000000000008501000000450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv6_UDP_GTPU_DL_IPv4,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv6_udp_gtpu_dl_ipv4_rss = {
    "sub_casename": "mac_ipv6_udp_gtpu_dl_ipv4_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000281100CDCD910A222254988475111139001010CDCD910A222254988475111139002021000008680028000034FF001C000000000000008501000000450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv6_UDP_GTPU_DL_IPv4,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv6_udp_gtpu_dl_ipv4_passthru = {
    "sub_casename": "mac_ipv6_udp_gtpu_dl_ipv4_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000281100CDCD910A222254988475111139001010CDCD910A222254988475111139002021000008680028000034FF001C000000000000008501000000450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv6_UDP_GTPU_DL_IPv4,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv6_udp_gtpu_dl_ipv4_drop = {
    "sub_casename": "mac_ipv6_udp_gtpu_dl_ipv4_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000281100CDCD910A222254988475111139001010CDCD910A222254988475111139002021000008680028000034FF001C000000000000008501000000450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions drop / end",
    ],
    "packet": MAC_IPv6_UDP_GTPU_DL_IPv4,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 8: VF_FDIR_MAC/IPv6/UDP/GTPU/DL/IPv4
mac_ipv6_udp_gtpu_dl_ipv4 = [
    mac_ipv6_udp_gtpu_dl_ipv4_queue,
    mac_ipv6_udp_gtpu_dl_ipv4_rss,
    mac_ipv6_udp_gtpu_dl_ipv4_passthru,
    mac_ipv6_udp_gtpu_dl_ipv4_drop,
]

MAC_IPv4_GTPU_UL_IPv4 = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.10.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.11.20", dst="192.168.1.21")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.11.21")/Raw("x"*20)',
    ],
}

mac_ipv4_gtpu_ul_ipv4_queue = {
    "sub_casename": "mac_ipv4_gtpu_ul_ipv4_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500003C0000000000110000C0A80014C0A80015000008680028000034FF001C000000000000008501100000450000140000000000000000C0A80114C0A80115 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F00000000000000000000000000000FFFFFFFFFFFFFFFF / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv4_GTPU_UL_IPv4,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv4_gtpu_ul_ipv4_rss = {
    "sub_casename": "mac_ipv4_gtpu_ul_ipv4_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500003C0000000000110000C0A80014C0A80015000008680028000034FF001C000000000000008501100000450000140000000000000000C0A80114C0A80115 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F00000000000000000000000000000FFFFFFFFFFFFFFFF / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv4_GTPU_UL_IPv4,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv4_gtpu_ul_ipv4_passthru = {
    "sub_casename": "mac_ipv4_gtpu_ul_ipv4_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500003C0000000000110000C0A80014C0A80015000008680028000034FF001C000000000000008501100000450000140000000000000000C0A80114C0A80115 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F00000000000000000000000000000FFFFFFFFFFFFFFFF / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv4_GTPU_UL_IPv4,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv4_gtpu_ul_ipv4_drop = {
    "sub_casename": "mac_ipv4_gtpu_ul_ipv4_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 00112233445500000000000208004500003C0000000000110000C0A80014C0A80015000008680028000034FF001C000000000000008501100000450000140000000000000000C0A80114C0A80115 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F00000000000000000000000000000FFFFFFFFFFFFFFFF / end actions drop / end",
    ],
    "packet": MAC_IPv4_GTPU_UL_IPv4,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 9: VF_FDIR_MAC/IPv4/UDP/GTPU/UL/IPv4
mac_ipv4_gtpu_ul_ipv4 = [
    mac_ipv4_gtpu_ul_ipv4_queue,
    mac_ipv4_gtpu_ul_ipv4_rss,
    mac_ipv4_gtpu_ul_ipv4_passthru,
    mac_ipv4_gtpu_ul_ipv4_drop,
]

MAC_IPv4_UDP_GTPU_DL_IPv6 = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1010", dst="CDCD:910A:2222:5498:8475:1111:4000:2021")/Raw("x"*20)'
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1010", dst="CDCD:910A:2222:5498:8475:1111:4000:2021")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1010", dst="CDCD:910A:2222:5498:8475:1111:4000:2021")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.10.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1010", dst="CDCD:910A:2222:5498:8475:1111:4000:2021")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1011", dst="CDCD:910A:2222:5498:8475:1111:4000:2021")/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="CDCD:910A:2222:5498:8475:1111:4000:1010", dst="CDCD:910A:2222:5498:8475:1111:4000:2022")/Raw("x"*20)',
    ],
}

mac_ipv4_udp_gtpu_dl_ipv6_queue = {
    "sub_casename": "mac_ipv4_udp_gtpu_dl_ipv6_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF00300000000000000085010000006000000000000000CDCD910A222254988475111140001010CDCD910A222254988475111140002021 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_DL_IPv6,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv4_udp_gtpu_dl_ipv6_rss = {
    "sub_casename": "mac_ipv4_udp_gtpu_dl_ipv6_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF00300000000000000085010000006000000000000000CDCD910A222254988475111140001010CDCD910A222254988475111140002021 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_DL_IPv6,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv4_udp_gtpu_dl_ipv6_passthru = {
    "sub_casename": "mac_ipv4_udp_gtpu_dl_ipv6_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF00300000000000000085010000006000000000000000CDCD910A222254988475111140001010CDCD910A222254988475111140002021 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_DL_IPv6,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv4_udp_gtpu_dl_ipv6_drop = {
    "sub_casename": "mac_ipv4_udp_gtpu_dl_ipv6_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF00300000000000000085010000006000000000000000CDCD910A222254988475111140001010CDCD910A222254988475111140002021 pattern mask 0000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF000000000000000000000000000000000000000000F000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF / end actions drop / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_DL_IPv6,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 10: VF_FDIR_MAC/IPv4/UDP/GTPU/DL/IPv6
mac_ipv4_udp_gtpu_dl_ipv6 = [
    mac_ipv4_udp_gtpu_dl_ipv6_queue,
    mac_ipv4_udp_gtpu_dl_ipv6_rss,
    mac_ipv4_udp_gtpu_dl_ipv6_passthru,
    mac_ipv4_udp_gtpu_dl_ipv6_drop,
]

MAC_IPv4_UDP_GTPU_UL_IPv4_TCP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw("x"*20)',
    ],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.16.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.10.21")/TCP()/Raw("x"*20)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.20", dst="192.168.1.21")/TCP()/Raw("x"*20)',
    ],
}

mac_ipv4_udp_gtpu_ul_ipv4_tcp_queue = {
    "sub_casename": "mac_ipv4_udp_gtpu_ul_ipv4_tcp_queue",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF0030000000000000008501100000450000280000000000060000C0A80114C0A801150000000000000000000000005000000000000000 pattern mask 000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000 / end actions queue index 1 / mark id 10 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_UL_IPv4_TCP,
    "check_param": {"port_id": 1, "mark_id": 10, "queue": 1},
}

mac_ipv4_udp_gtpu_ul_ipv4_tcp_rss = {
    "sub_casename": "mac_ipv4_udp_gtpu_ul_ipv4_tcp_rss",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF0030000000000000008501100000450000280000000000060000C0A80114C0A801150000000000000000000000005000000000000000 pattern mask 000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000 / end actions rss queues 0 1 2 3 end / mark id 4 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_UL_IPv4_TCP,
    "check_param": {"port_id": 1, "mark_id": 4, "queue": [0, 1, 2, 3]},
}

mac_ipv4_udp_gtpu_ul_ipv4_tcp_passthru = {
    "sub_casename": "mac_ipv4_udp_gtpu_ul_ipv4_tcp_passthru",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF0030000000000000008501100000450000280000000000060000C0A80114C0A801150000000000000000000000005000000000000000 pattern mask 000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000 / end actions passthru / mark id 1 / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_UL_IPv4_TCP,
    "check_param": {"port_id": 1, "mark_id": 1, "rss": True},
}

mac_ipv4_udp_gtpu_ul_ipv4_tcp_drop = {
    "sub_casename": "mac_ipv4_udp_gtpu_ul_ipv4_tcp_drop",
    "rule": [
        "flow create 1 ingress pattern raw pattern spec 0011223344550000000000020800450000500000000000110000C0A80014C0A8001500000868003C000034FF0030000000000000008501100000450000280000000000060000C0A80114C0A801150000000000000000000000005000000000000000 pattern mask 000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FF000000000000000000000000000000000000000000 / end actions drop / end",
    ],
    "packet": MAC_IPv4_UDP_GTPU_UL_IPv4_TCP,
    "check_param": {"port_id": 1, "drop": True},
}

# Test case 11: VF_FDIR_MAC/IPv4/UDP/GTPU/UL/IPv4/TCP_un-word-aligned key
mac_ipv4_udp_gtpu_ul_ipv4_tcp = [
    mac_ipv4_udp_gtpu_ul_ipv4_tcp_queue,
    mac_ipv4_udp_gtpu_ul_ipv4_tcp_rss,
    mac_ipv4_udp_gtpu_ul_ipv4_tcp_passthru,
    mac_ipv4_udp_gtpu_ul_ipv4_tcp_drop,
]

vf1_mac = "00:11:22:33:44:55"


class TestIavfFdirProtocolAgnosticFlow(TestCase):
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
        self.pmd_output = PmdOutput(self.dut)
        self.tester_ifaces = [
            self.tester.get_interface(self.dut.ports_map[port]) for port in self.dports
        ]
        self.pf_interface0 = self.dut.ports_info[self.dports[0]]["intf"]
        self.create_iavf()
        self.rxq = 16
        self.pkt = Packet()
        self.fdirpro = FdirProcessing(
            self, self.pmd_output, self.tester_ifaces, self.rxq
        )
        self.logfmt = "*" * 20

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
        self.dut.send_expect("ip link set %s vf 0 trust on" % self.pf_interface0, "#")
        self.sriov_vfs_port = self.dut.ports_info[self.dports[0]]["vfs_port"]
        self.vf_pci0 = self.sriov_vfs_port[0].pci
        self.vf_pci1 = self.sriov_vfs_port[1].pci
        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.drivername)
            self.dut.send_expect("ifconfig %s up" % self.pf_interface0, "# ")
            self.dut.send_expect(
                "ip link set %s vf 1 mac %s" % (self.pf_interface0, vf1_mac), "# "
            )
        except Exception as e:
            self.destroy_iavf()
            raise Exception(e)

    def launch_testpmd(self):
        """
        launch testpmd with the command
        """
        params = "--rxq={0} --txq={0}".format(self.rxq)
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

    def get_pkt_statistic(self, out, **kwargs):
        """
        :param out: information received by testpmd after sending packets and port statistics
        :return: rx statistic dict, eg: {'rx-packets':1, 'rx-dropped':0, 'rx-total':1}
        """
        p = re.compile(
            r"Forward\sstatistics\s+for\s+port\s+{}\s+.*\n.*RX-packets:\s(\d+)\s+RX-dropped:\s(\d+)\s+RX-total:\s(\d+)\s".format(
                kwargs.get("port_id")
            )
        )
        item_name = ["rx-packets", "rx-dropped", "rx-total"]
        statistic = p.findall(out)
        if statistic:
            static_dict = {
                k: v for k, v in zip(item_name, list(map(int, list(statistic[0]))))
            }
            return static_dict
        else:
            raise Exception(
                "got wrong output, not match pattern {}".format(p.pattern).replace(
                    "\\\\", "\\"
                )
            )

    def check_pkt_num(self, out, **kwargs):
        """
        check number of received packets matches the expected value
        :param out: information received by testpmd after sending packets and port statistics
        :param kwargs: some specified parameters, such as: pkt_num, port_id
        :return: rx statistic dict
        """
        self.logger.info(
            "{0} check pkt num for port:{1} {0}".format(
                self.logfmt, kwargs.get("port_id")
            )
        )
        pkt_num = kwargs.get("pkt_num")
        res = self.get_pkt_statistic(out, **kwargs)
        res_num = res["rx-total"]
        self.verify(
            res_num == pkt_num,
            "fail: got wrong number of packets, expect pakcet number {}, got {}".format(
                pkt_num, res_num
            ),
        )
        self.logger.info(
            (GREEN("pass: pkt num is {} same as expected".format(pkt_num)))
        )
        return res

    def check_queue(self, out, check_param, **kwargs):
        """
        verify that queue value matches the expected value
        :param out: information received by testpmd after sending packets and port statistics
        :param check_param: check item name and value, eg
                            "check_param": {"port_id": 0, "queue": 2}
        :param kwargs: some specified parameters, such as: pkt_num, port_id, stats
        :return:
        """
        self.logger.info("{0} check queue {0}".format(self.logfmt))
        queue = check_param["queue"]
        if isinstance(check_param["queue"], int):
            queue = [queue]
        patt = re.compile(
            r"port\s+{}/queue(.+?):\s+received\s+(\d+)\s+packets".format(
                kwargs.get("port_id")
            )
        )
        res = patt.findall(out)
        if res:
            pkt_queue = set([int(i[0]) for i in res])
            if kwargs.get("stats"):
                self.verify(
                    all(q in queue for q in pkt_queue),
                    "fail: queue id not matched, expect queue {}, got {}".format(
                        queue, pkt_queue
                    ),
                )
                self.logger.info((GREEN("pass: queue id {} matched".format(pkt_queue))))
            else:
                try:
                    self.verify(
                        not any(q in queue for q in pkt_queue),
                        "fail: queue id should not matched, {} should not in {}".format(
                            pkt_queue, queue
                        ),
                    )
                    self.logger.info(
                        (GREEN("pass: queue id {} not matched".format(pkt_queue)))
                    )
                except VerifyFailure:
                    self.logger.info(
                        "queue id {} contains the queue {} specified in rule, so need to check"
                        " whether the packet directed by rss or not".format(
                            pkt_queue, queue
                        )
                    )
                    # for mismatch packet the 'stats' parameter is False, need to change to True
                    kwargs["stats"] = True
                    self.check_rss(out, **kwargs)

        else:
            raise Exception("got wrong output, not match pattern")

    def check_mark_id(self, out, check_param, **kwargs):
        """
        verify that the mark ID matches the expected value
        :param out: information received by testpmd after sending packets
        :param check_param: check item name and value, eg
                            "check_param": {"port_id": 0, "mark_id": 1}
        :param kwargs: some specified parameters,eg: stats
        :return: None
        usage:
            check_mark_id(out, check_param, stats=stats)
        """
        self.logger.info("{0} check mark id {0}".format(self.logfmt))
        fdir_scanner = re.compile("FDIR matched ID=(0x\w+)")
        all_mark = fdir_scanner.findall(out)
        stats = kwargs.get("stats")
        if stats:
            mark_list = set(int(i, 16) for i in all_mark)
            self.verify(
                all([i == check_param["mark_id"] for i in mark_list]) and mark_list,
                "failed: some packet mark id of {} not match expect {}".format(
                    mark_list, check_param["mark_id"]
                ),
            )
            self.logger.info((GREEN("pass: all packets mark id are matched ")))
        else:
            # for mismatch packet,verify no mark id in output of received packet
            self.verify(
                not all_mark, "mark id {} in output, expect no mark id".format(all_mark)
            )
            self.logger.info((GREEN("pass: no mark id in output")))

    def check_rss(self, out, **kwargs):
        """
        check whether the packet directed by rss or not according to the specified parameters
        :param out: information received by testpmd after sending packets and port statistics
        :param kwargs: some specified parameters, such as: rxq, stats
        :return: queue value list
        usage:
            check_rss(out, rxq=rxq, stats=stats)
        """
        self.logger.info("{0} check rss {0}".format(self.logfmt))
        rxq = kwargs.get("rxq")
        p = re.compile("RSS\shash=(\w+)\s-\sRSS\squeue=(\w+)")
        pkt_info = p.findall(out)
        self.verify(
            pkt_info,
            "no information matching the pattern was found,pattern:{}".format(
                p.pattern
            ),
        )
        pkt_queue = set([int(i[1], 16) for i in pkt_info])
        if kwargs.get("stats"):
            self.verify(
                all([int(i[0], 16) % rxq == int(i[1], 16) for i in pkt_info]),
                "some pkt not directed by rss.",
            )
            self.logger.info((GREEN("pass: all pkts directed by rss")))
        else:
            self.verify(
                not any([int(i[0], 16) % rxq == int(i[1], 16) for i in pkt_info]),
                "some pkt directed by rss, expect not directed by rss",
            )
            self.logger.info((GREEN("pass: no pkt directed by rss")))
        return pkt_queue

    def check_drop(self, out, **kwargs):
        """
        check the drop number of packets according to the specified parameters
        :param out: information received by testpmd after sending packets and port statistics
        :param kwargs: some specified parameters, such as: pkt_num, port_id, stats
        :return: None
        usage:
            chek_drop(out, pkt_num=pkt_num, port_id=portid, stats=stats)
        """
        self.logger.info("{0} check drop {0}".format(self.logfmt))
        pkt_num = kwargs.get("pkt_num")
        stats = kwargs.get("stats")
        if "switch" in self.__class__.__name__.lower() and stats:
            pkt_num = 0
        res = self.get_pkt_statistic(out, **kwargs)
        self.verify(
            pkt_num == res["rx-total"],
            "failed: get wrong amount of packet {}, expected {}".format(
                res["rx-total"], pkt_num
            ),
        )
        drop_packet_num = res["rx-dropped"]
        if stats:
            self.verify(
                drop_packet_num == pkt_num,
                "failed: {} packet dropped,expect {} dropped".format(
                    drop_packet_num, pkt_num
                ),
            )
            self.logger.info(
                (
                    GREEN(
                        "pass: drop packet number {} is matched".format(drop_packet_num)
                    )
                )
            )
        else:
            self.verify(
                drop_packet_num == 0 and res["rx-packets"] == pkt_num,
                "failed: {} packet dropped, expect 0 packet dropped".format(
                    drop_packet_num
                ),
            )
            self.logger.info(
                (
                    GREEN(
                        "pass: drop packet number {} is matched".format(drop_packet_num)
                    )
                )
            )

    def check_with_param(self, out, pkt_num, check_param, stats=True):
        """
        according to the key and value of the check parameter,
        perform the corresponding verification in the out information
        :param out: information received by testpmd after sending packets and port statistics
        :param pkt_num: number of packets sent
        :param check_param: check item name and value, eg:
                            "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
                            "check_param": {"port_id": 0, "drop": 1}
        :param stats: effective status of rule, True or False, default is True
        :return:
        usage:
            check_with_param(out, pkt_num, check_param, stats)
            check_with_param(out, pkt_num, check_param=check_param)
        """
        rxq = self.rxq
        port_id = (
            check_param["port_id"] if check_param.get("port_id") is not None else 0
        )
        match_flag = True
        """
        check_dict shows the supported check items,the key is item name and value represent the check priority,
        the smaller the value, the higher the priority, priority default value is 999. if need to add new check item,
        please add it to the dict and implement the corresponding method and named as 'check_itemname',eg: check_queue
        """
        default_pri = 999
        check_dict = {
            "queue": default_pri,
            "drop": default_pri,
            "mark_id": 1,
            "rss": default_pri,
        }
        params = {"port_id": port_id, "rxq": rxq, "pkt_num": pkt_num, "stats": stats}
        # sort check_param order by priority, from high to low, set priority as 999 if key not in check_dict
        check_param = OrderedDict(
            sorted(
                check_param.items(),
                key=lambda item: check_dict.get(item[0], params["pkt_num"]),
            )
        )
        if not check_param.get("drop"):
            self.check_pkt_num(out, **params)
        for k in check_param:
            parameter = copy.deepcopy(params)
            if k not in check_dict:
                continue
            func_name = "check_{}".format(k)
            try:
                func = getattr(self, func_name)
            except AttributeError:
                emsg = "{},this func is not implemented, please check!".format(
                    traceback.format_exc()
                )
                raise Exception(emsg)
            else:
                # for mismatch packet, if the check item is 'rss',should also verify the packets are distributed by rss
                if k == "rss" and not stats:
                    parameter["stats"] = True
                    match_flag = False
                res = func(out=out, check_param=check_param, **parameter)
                if k == "rss" and match_flag:
                    self.matched_queue.append(res)

    def send_pkt_get_output_flow(
        self, pkts, port_id=0, count=1, interval=0, get_stats=False
    ):
        self.pmd_output.execute_cmd("clear port stats all")
        tx_port = self.tester_ifaces[port_id] if port_id else self.tester_ifaces[0]
        self.logger.info("----------send packet-------------")
        self.logger.info("{}".format(pkts))
        if not isinstance(pkts, list):
            pkts = [pkts]
        self.pkt.update_pkt(pkts)
        self.pkt.send_pkt(
            crb=self.tester,
            tx_port=tx_port,
            count=count,
            interval=interval,
        )
        out1 = self.pmd_output.get_output(timeout=3)
        if get_stats:
            out2 = self.pmd_output.execute_cmd("show port stats all")
            self.pmd_output.execute_cmd("stop")
        else:
            out2 = self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("start")
        return "".join([out1, out2])

    def flow_rule_operate(self, case):
        """
        test steps of flow rule case:
            1. create rule
            2. send and check match packets
            3. send and check mismatch packets
            4. list and destroy rule
            5. send and check match packet are distributed by rss
        :param case: case dict info, eg:
            mac_ipv4_pay_queue_index = {
                "sub_casename": "mac_ipv4_pay_queue_index",
                "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / end actions queue index 1 / end",
                "packet": MAC_IPV4_PAY,
                "check_param": {"port_id": 0, "queue": 1}
            }
        :return: None
        """
        check_param = case.get("check_param")
        port_id = check_param.get("port_id") if check_param.get("port_id") else 0
        tport_id = check_param.get("tport_id") if check_param.get("tport_id") else 0
        # validate and create rule
        rule = case.get("rule")
        extend_rule = case.get("extend_rule")
        if extend_rule:
            self.fdirpro.create_rule(extend_rule)
        self.fdirpro.validate_rule(rule)
        rule_li = self.fdirpro.create_rule(rule)
        # send and check match packets
        self.logger.info("{0} send and check match packets {0}".format(self.logfmt))
        match_pkts = case.get("packet").get("match")
        self.verify(match_pkts, "no match packets in case info")
        out1 = self.send_pkt_get_output_flow(pkts=match_pkts, port_id=tport_id)
        self.matched_queue = []
        self.check_with_param(
            out1,
            pkt_num=len(match_pkts),
            check_param=check_param,
        )
        # send and check mismatch packets
        self.logger.info("{0} send and check mismatch packets {0}".format(self.logfmt))
        mismatch_pkts = case.get("packet").get("mismatch")
        self.verify(mismatch_pkts, "no mismatch packets in case info")
        out2 = self.send_pkt_get_output_flow(pkts=mismatch_pkts)
        self.check_with_param(
            out2,
            pkt_num=len(mismatch_pkts),
            check_param=check_param,
            stats=False,
        )
        # list and destroy rule
        self.logger.info("{0} list and destroy rule {0}".format(self.logfmt))
        self.fdirpro.check_rule(port_id=port_id, rule_list=rule_li)
        self.fdirpro.destroy_rule(port_id=port_id, rule_id=rule_li)
        # send match packet
        self.logger.info(
            "{0} send and check match packets after destroy rule {0}".format(
                self.logfmt
            )
        )
        out3 = self.send_pkt_get_output_flow(pkts=match_pkts)
        self.check_with_param(
            out3,
            pkt_num=len(match_pkts),
            check_param=check_param,
            stats=False,
        )
        if check_param.get("rss"):
            self.verify(
                self.matched_queue
                and self.matched_queue[0 : len(match_pkts)]
                == self.matched_queue[-len(match_pkts) :],
                "send twice match packet, received in different queues",
            )
        # check not rule exists
        self.fdirpro.check_rule(port_id=port_id, stats=False, rule_list=rule_li)

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

    def test_multi_rules_mac_ipv6_udp_vxlan_ipv4(self):
        """
        Test case 12: VF_FDIR_multi-rules_MAC/IPv6/UDP/VXLAN/IPv4
        """
        rules = [
            "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000241100CDCD910A222254988475111139001010CDCD910A222254988475111139002020000012B5002400000800000000000000450000140000000000000000C0A80014C0A80015 pattern mask 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF / end actions queue index 4 / mark id 11 / end",
            "flow create 1 ingress pattern raw pattern spec 00112233445500000000000286DD6000000000241100CDCD910A222254988475111139001010CDCD910A222254988475111139002020000012B5002400000800000000000000450000140000000000000000C0A80014C0A80015 pattern mask 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFFFFFFFFFFFFFFF0000000000000000 / end actions queue index 1 / mark id 1 / end",
        ]
        packet = [
            'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP()/VXLAN()/IP(src="192.168.0.20",dst="192.168.0.21")/("X"*480)',
        ]
        check_param = {"port_id": 1, "mark_id": 11, "queue": 4}
        # check rule
        self.fdirpro.create_rule(rules, check_stats=True)
        out = self.send_pkt_get_output_flow(packet, port_id=0)
        # match rule 1
        self.check_with_param(out, len(packet), check_param)

    def test_mac_ipv4_udp_gtpu_ul_ipv4_tcp(self):
        """
        Test case 11: VF_FDIR_MAC/IPv4/UDP/GTPU/UL/IPv4/TCP_un-word-aligned key
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv4_udp_gtpu_ul_ipv4_tcp, func_name)

    def test_mac_ipv4_udp_gtpu_dl_ipv6(self):
        """
        Test case 10: VF_FDIR_MAC/IPv4/UDP/GTPU/DL/IPv6
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv4_udp_gtpu_dl_ipv6, func_name)

    def test_mac_ipv4_gtpu_ul_ipv4(self):
        """
        Test case 9: VF_FDIR_MAC/IPv4/UDP/GTPU/UL/IPv4
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv4_gtpu_ul_ipv4, func_name)

    def test_mac_ipv6_udp_gtpu_dl_ipv4(self):
        """
        Test case 8: VF_FDIR_MAC/IPv6/UDP/GTPU/DL/IPv4
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv6_udp_gtpu_dl_ipv4, func_name)

    def test_mac_ipv4_udp_gtpu_ipv6_udp(self):
        """
        Test case 7: VF_FDIR_MAC/IPv4/UDP/GTPU/IPv6/UDP
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv4_udp_gtpu_ipv6_udp, func_name)

    def test_mac_ipv4_udp_gtpu_ipv4(self):
        """
        Test case 6: VF_FDIR_MAC/IPv4/GTPU/IPv4
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv4_udp_gtpu_ipv4, func_name)

    def test_mac_ipv4_udp_vxlan_mac_ipv4_vni(self):
        """
        # Test case 5: VF_FDIR_MAC/IPv4/UDP/VXLAN/MAC/IPv4_vni
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv4_udp_vxlan_mac_ipv4_vni, func_name)

    def test_mac_ipv4_udp_vxlan_mac_ipv4_udp(self):
        """
        Test case 4: VF_FDIR_MAC/IPv4/UDP/VXLAN/MAC/IPv4/UDP
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv4_udp_vxlan_mac_ipv4_udp, func_name)

    def test_mac_ipv4_udp_vxlan_mac_ipv4_pay(self):
        """
        Test case 3: VF_FDIR_MAC/IPv4/UDP/VXLAN/MAC/IPv4/PAY
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv4_udp_vxlan_mac_ipv4_pay, func_name)

    def test_mac_ipv6_tcp(self):
        """
        Test case 2: VF_FDIR_MAC/IPv6/TCP
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv6_tcp, func_name)

    def test_mac_ipv4_udp(self):
        """
        Test case 1: VF_FDIR_MAC/IPv4/UDP
        """
        func_name = self.flow_rule_operate
        self.rte_flow(mac_ipv4_udp, func_name)

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
