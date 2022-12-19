# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re
import traceback

import tests.rte_flow_common as rfc
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.utils import GREEN, RED

from .rte_flow_common import FdirProcessing

MAC_IPV4_UDP_VXLAN = {
    "matched": [
        'Ether(dst="{}")/IP()/UDP(dport=4789)/Raw("x"*80)',  # {} is pf mac
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Ether()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Ether()/IP()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Ether()/IP()/TCP()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Ether()/IP()/UDP()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Ether()/IP()/ICMP()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Ether()/IPv6()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Ether()/IPv6()/TCP()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Ether()/IPv6()/UDP()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Ether()/IPv6()/ICMP()/Raw("x"*80)',
    ],
    "mismatched": [
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Ether()/IP()/Raw("x" * 80)',
        'Ether(dst="{}")/IP()/UDP(dport=1)/Raw("x" * 80)',
        'Ether(dst="{}")/IP()/UDP(dport=1)/VXLAN()/Ether()/IP()/Raw("x" * 80)',
        'Ether(dst="{}")/IP()/TCP()/VXLAN()/Ether()/IP()/Raw("x" * 80)',
        'Ether(dst="{}")/IP()/ICMP()/VXLAN()/Ether()/IP()/Raw("x" * 80)',
    ],
}

mac_ipv4_udp_vxlan = {
    "sub_casename": "mac_ipv4_udp_vxlan",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp dst is 4789 / end actions port_representor port_id 0 / end",
    "matched": {
        "packet": MAC_IPV4_UDP_VXLAN["matched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [11, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV4_UDP_VXLAN["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_IPV6_UDP_VXLAN = {
    "matched": [
        'Ether(dst="{}")/IPv6()/UDP(dport=4789)/Raw("x"*80)',  # {} is pf mac
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Ether()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Ether()/IP()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Ether()/IP()/TCP()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Ether()/IP()/UDP()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Ether()/IP()/ICMP()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Ether()/IPv6()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Ether()/IPv6()/TCP()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Ether()/IPv6()/UDP()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP()/VXLAN()/Ether()/IPv6()/ICMP()/Raw("x"*80)',
    ],
    "mismatched": [
        'Ether(dst="{}")/IP()/UDP()/VXLAN()/Ether()/IP()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP(dport=1)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP(dport=1)/VXLAN()/Ether()/IP()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/TCP()/VXLAN()/Ether()/IP()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/ICMP()/VXLAN()/Ether()/IP()/Raw("x"*80)',
    ],
}

mac_ipv6_udp_vxlan = {
    "sub_casename": "mac_ipv6_udp_vxlan",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp dst is 4789 / end actions port_representor port_id 0 / end",
    "matched": {
        "packet": MAC_IPV6_UDP_VXLAN["matched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [11, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV6_UDP_VXLAN["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_VLAN_IPV4 = {
    "matched": [
        'Ether(dst="{}")/Dot1Q(vlan=1)/IP(dst="192.168.0.1")/Raw("x"*80)',  # {} is pf mac
        'Ether(dst="{}")/Dot1Q(vlan=1)/IP(dst="192.168.0.1")/UDP()/Raw("x"*80)',
        'Ether(dst="{}")/Dot1Q(vlan=1)/IP(dst="192.168.0.1")/TCP()/Raw("x"*80)',
    ],
    "mismatched": [
        'Ether(dst="{}")/Dot1Q(vlan=1)/Raw("x"*80)',
        'Ether(dst="{}")/IP(dst="192.168.0.1")/Raw("x"*80)',
        'Ether(dst="{}")/Dot1Q(vlan=1)/IP(dst="192.168.0.2")/Raw("x"*80)',
        'Ether(dst="{}")/Dot1Q(vlan=2)/IP(dst="192.168.0.1")/Raw("x"*80)',
    ],
}

mac_vlan_ipv4 = {
    "sub_casename": "mac_vlan_ipv4",
    "rule": "flow create 0 ingress pattern eth / vlan tci is 1 / ipv4 dst is 192.168.0.1 / end actions port_representor port_id 0 / end",
    "matched": {
        "packet": MAC_VLAN_IPV4["matched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [3, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_VLAN_IPV4["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_IPV4_ICMP = {
    "matched": [
        'Ether(dst="{}")/IP(proto=1)/Raw("x"*80)',  # {} is pf mac
        'Ether(dst="{}")/IP()/ICMP()/Raw("x"*80)',
    ],
    "mismatched": [
        'Ether(dst="{}")/IP(proto=2)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/ICMP()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/TCP()/Raw("x"*80)',
    ],
}

mac_ipv4_icmp = {
    "sub_casename": "mac_ipv4_icmp",
    "rule": "flow create 0 ingress pattern eth / ipv4 proto is 0x1 / end actions port_representor port_id 0 / end",
    "matched": {
        "packet": MAC_IPV4_ICMP["matched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [2, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV4_ICMP["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_IPV4_SRC_DST_MASK = {
    "matched": [
        'Ether(dst="{}")/IP(src="224.255.255.255",dst="224.255.255.255")/Raw("x"*80)',  # {} is pf mac
        'Ether(dst="{}")/IP(src="224.255.255.255",dst="224.0.0.0")/UDP(sport=22)/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="224.0.0.0",dst="224.255.255.255")/TCP(sport=22)/Raw("x"*80)',
    ],
    "mismatched": [
        'Ether(dst="{}")/IP(src="225.0.0.0",dst="225.0.0.0")/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="225.0.0.0",dst="224.0.0.0")/UDP(sport=22)/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="224.0.0.0",dst="225.0.0.0")/TCP(sport=22)/Raw("x"*80)',
    ],
}

mac_ipv4_src_dst_mask = {
    "sub_casename": "mac_ipv4_src_dst_mask",
    "rule": "flow create 0 ingress pattern eth / ipv4 src spec 224.0.0.0 src mask 255.0.0.0 dst spec 224.0.0.0 dst mask 255.0.0.0 / end actions port_representor port_id 0 / end",
    "matched": {
        "packet": MAC_IPV4_SRC_DST_MASK["matched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [3, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV4_SRC_DST_MASK["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_IPV6_SRC_DST_MASK = {
    "matched": [
        'Ether(dst="{}")/IPv6(dst="CDCD:910A:2222:5498:0000:0000:0000:0000",src="CDCD:910A:2222:5498:0000:0000:0000:0000")/Raw("x"*80)',  # {} is pf mac
        'Ether(dst="{}")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="CDCD:910A:2222:5498:0000:0000:0000:0000")/UDP(sport=22)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(dst="CDCD:910A:2222:5498:0000:0000:0000:0000",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22)/Raw("x"*80)',
    ],
    "mismatched": [
        'Ether(dst="{}")/IPv6(dst="CDCD:910A:2222:5499:8475:1111:3900:2020",src="CDCD:910A:2222:5499:8475:1111:3900:2020")/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(dst="CDCD:910A:2222:5498:0000:0000:0000:0000",src="CDCD:910A:2222:5499:8475:1111:3900:2020")/UDP(sport=22)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(dst="CDCD:910A:2222:5499:8475:1111:3900:2020",src="CDCD:910A:2222:5498:0000:0000:0000:0000")/TCP(sport=22)/Raw("x"*80)',
    ],
}

mac_ipv6_src_dst_mask = {
    "sub_casename": "mac_ipv6_src_dst_mask",
    "rule": "flow create 0 ingress pattern eth / ipv6 src spec CDCD:910A:2222:5498:8475:1111:3900:2020 src mask ffff:ffff:ffff:ffff:0000:0000:0000:0000 dst spec CDCD:910A:2222:5498:8475:1111:3900:2020 dst mask ffff:ffff:ffff:ffff:0000:0000:0000:0000 / end actions port_representor port_id 0 / end",
    "matched": {
        "packet": MAC_IPV6_SRC_DST_MASK["matched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [3, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV6_SRC_DST_MASK["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

l3_mask = [mac_ipv4_src_dst_mask, mac_ipv6_src_dst_mask]

MAC_IPV4_UDP_SRC_DST_MASK = {
    "matched": [
        'Ether(dst="{}")/IP()/UDP(sport=2048,dport=1)/Raw("x"*80)',  # {} is pf mac
    ],
    "mismatched": [
        'Ether(dst="{}")/IP()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP(sport=104,dport=1281)/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP(sport=2152,dport=1280)/Raw("x"*80)',
        'Ether(dst="{}")/IP()/TCP(sport=2152,dport=1281)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP(sport=2152,dport=1281)/Raw("x"*80)',
    ],
}

mac_ipv4_udp_src_dst_mask = {
    "sub_casename": "mac_ipv4_udp_src_dst_mask",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp src spec 2152 src mask 0xff00 dst spec 1281 dst mask 0x00ff / end actions port_representor port_id 0 / end",
    "matched": {
        "packet": MAC_IPV4_UDP_SRC_DST_MASK["matched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [1, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV4_UDP_SRC_DST_MASK["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_IPV4_TCP_SRC_DST_MASK = {
    "matched": [
        'Ether(dst="{}")/IP()/TCP(sport=2048,dport=1)/Raw("x"*80)',  # {} is pf mac
    ],
    "mismatched": [
        'Ether(dst="{}")/IP()/Raw("x"*80)',
        'Ether(dst="{}")/IP()/TCP(sport=104,dport=1281)/Raw("x"*80)',
        'Ether(dst="{}")/IP()/TCP(sport=2152,dport=1280)/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP(sport=2152,dport=1281)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/TCP(sport=2152,dport=1281)/Raw("x"*80)',
    ],
}

mac_ipv4_tcp_src_dst_mask = {
    "sub_casename": "mac_ipv4_tcp_src_dst_mask",
    "rule": "flow create 0 ingress pattern eth / ipv4 / tcp src spec 2152 src mask 0xff00 dst spec 1281 dst mask 0x00ff / end actions port_representor port_id 0 / end",
    "matched": {
        "packet": MAC_IPV4_TCP_SRC_DST_MASK["matched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [1, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV4_TCP_SRC_DST_MASK["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_IPV6_UDP_SRC_DST_MASK = {
    "matched": [
        'Ether(dst="{}")/IPv6()/UDP(sport=2048,dport=1)/Raw("x"*80)',  # {} is pf mac
    ],
    "mismatched": [
        'Ether(dst="{}")/IPv6()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP(sport=104,dport=1281)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP(sport=2152,dport=1280)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/TCP(sport=2152,dport=1281)/Raw("x"*80)',
        'Ether(dst="{}")/IP()/UDP(sport=2152,dport=1281)/Raw("x"*80)',
    ],
}

mac_ipv6_udp_src_dst_mask = {
    "sub_casename": "mac_ipv6_udp_src_dst_mask",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp src spec 2152 src mask 0xff00 dst spec 1281 dst mask 0x00ff / end actions port_representor port_id 0 / end",
    "matched": {
        "packet": MAC_IPV6_UDP_SRC_DST_MASK["matched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [1, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV6_UDP_SRC_DST_MASK["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_IPV4_TCP_SRC_DST_MASK = {
    "matched": [
        'Ether(dst="{}")/IPv6()/TCP(sport=2048,dport=1)/Raw("x"*80)',  # {} is pf mac
    ],
    "mismatched": [
        'Ether(dst="{}")/IPv6()/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/TCP(sport=104,dport=1281)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/TCP(sport=2152,dport=1280)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6()/UDP(sport=2152,dport=1281)/Raw("x"*80)',
        'Ether(dst="{}")/IP()/TCP(sport=2152,dport=1281)/Raw("x"*80)',
    ],
}

mac_ipv6_tcp_src_dst_mask = {
    "sub_casename": "mac_ipv6_tcp_src_dst_mask",
    "rule": "flow create 0 ingress pattern eth / ipv6 / tcp src spec 2152 src mask 0xff00 dst spec 1281 dst mask 0x00ff / end actions port_representor port_id 0 / end",
    "matched": {
        "packet": MAC_IPV4_TCP_SRC_DST_MASK["matched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [1, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV4_TCP_SRC_DST_MASK["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

l4_mask = [
    mac_ipv4_udp_src_dst_mask,
    mac_ipv4_tcp_src_dst_mask,
    mac_ipv6_udp_src_dst_mask,
    mac_ipv6_tcp_src_dst_mask,
]

MAC_IPV4_UDP_PAYLOAD = {
    "matched": [
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.1")/UDP(sport=2048,dport=2022)/Raw("x"*80)',  # {} is pf mac
    ],
    "mismatched": [
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.1")/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="192.168.0.21",dst="192.168.0.1")/UDP(sport=2048,dport=2022)/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.2")/UDP(sport=2048,dport=2022)/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.1")/UDP(sport=2047,dport=2022)/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.1")/UDP(sport=2048,dport=2023)/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.1")/TCP(sport=2048,dport=2022)/Raw("x"*80)',
    ],
}

mac_ipv4_udp_payload_priority = {
    "sub_casename": "mac_ipv4_udp_payload_priority",
    "rule": [
        "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / udp src is 2048 dst is 2022 / end actions port_representor port_id 0 / rss queues 4 5 end / end",
        "flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / udp src is 2048 dst is 2022 / end actions port_representor port_id 0 / rss queues 6 7 end / end",
    ],
    "matched": {
        "packet": MAC_IPV4_UDP_PAYLOAD["matched"],
        "check_param": {
            "expect_port": [0, 1, 2, 3],
            "queue": {"priority_0": [4, 5], "priority_1": [6, 7]},
        },
        "expect_pkts": [1, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV4_UDP_PAYLOAD["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_IPV4_TCP_PAYLOAD = {
    "matched": [
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.1")/TCP(sport=2048,dport=2022)/Raw("x"*80)',  # {} is pf mac
    ],
    "mismatched": [
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.1")/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="192.168.0.21",dst="192.168.0.1")/TCP(sport=2048,dport=2022)/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="192.168.0.21",dst="192.168.0.1")/TCP(sport=2048,dport=2022)/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.1")/TCP(sport=2047,dport=2022)/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.1")/TCP(sport=2048,dport=2023)/Raw("x"*80)',
        'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.1")/UDP(sport=2048,dport=2022)/Raw("x"*80)',
    ],
}

mac_ipv4_tcp_payload_priority = {
    "sub_casename": "mac_ipv4_udp_payload_priority",
    "rule": [
        "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / tcp src is 2048 dst is 2022 / end actions port_representor port_id 0 / queue index 2 / end",
        "flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / tcp src is 2048 dst is 2022 / end actions port_representor port_id 0 / queue index 3 / end",
    ],
    "matched": {
        "packet": MAC_IPV4_TCP_PAYLOAD["matched"],
        "check_param": {
            "expect_port": [0, 1, 2, 3],
            "queue": {"priority_0": 2, "priority_1": 3},
        },
        "expect_pkts": [1, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV4_TCP_PAYLOAD["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_IPV6_UDP_PAYLOAD = {
    "matched": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=2048,dport=2022)/Raw("x"*80)',  # {} is pf mac
    ],
    "mismatched": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=2048,dport=2022)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=2048,dport=2023)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=2047,dport=2022)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=2048,dport=2022)/Raw("x"*80)',
    ],
}

mac_ipv6_udp_payload_priority = {
    "sub_casename": "mac_ipv6_udp_payload_priority",
    "rule": [
        "flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 2048 dst is 2022 / end actions port_representor port_id 0 / rss queues 4 5 end / end",
        "flow create 0 priority 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 2048 dst is 2022 / end actions port_representor port_id 0 / rss queues 6 7 end / end",
    ],
    "matched": {
        "packet": MAC_IPV6_UDP_PAYLOAD["matched"],
        "check_param": {
            "expect_port": [0, 1, 2, 3],
            "queue": {"priority_0": [4, 5], "priority_1": [6, 7]},
        },
        "expect_pkts": [1, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV6_UDP_PAYLOAD["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}

MAC_IPV6_TCP_PAYLOAD = {
    "matched": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=2048,dport=2022)/Raw("x"*80)',  # {} is pf mac
    ],
    "mismatched": [
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=2048,dport=2022)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=2047,dport=2023)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=2048,dport=2023)/Raw("x"*80)',
        'Ether(dst="{}")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=2048,dport=2022)/Raw("x"*80)',
    ],
}

mac_ipv6_tcp_payload_priority = {
    "sub_casename": "mac_ipv6_udp_payload_priority",
    "rule": [
        "flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 / tcp src is 2048 dst is 2022 / end actions port_representor port_id 0 / queue index 2 / end",
        "flow create 0 priority 1 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 / tcp src is 2048 dst is 2022 / end actions port_representor port_id 0 / queue index 3 / end",
    ],
    "matched": {
        "packet": MAC_IPV6_TCP_PAYLOAD["matched"],
        "check_param": {
            "expect_port": [0, 1, 2, 3],
            "queue": {"priority_0": 2, "priority_1": 3},
        },
        "expect_pkts": [1, 0, 0, 0],
    },
    "mismatched": {
        "packet": MAC_IPV6_TCP_PAYLOAD["mismatched"],
        "check_param": {"expect_port": [0, 1, 2, 3]},
        "expect_pkts": [0, 0, 0, 0],
    },
}


class TestICEIavfFlowSubscribe(TestCase):
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
        localPort0 = self.tester.get_local_port(self.dut_ports[0])
        localPort1 = self.tester.get_local_port(self.dut_ports[1])
        self.tport_iface0 = self.tester.get_interface(localPort0)
        self.tport_iface1 = self.tester.get_interface(localPort1)
        self.used_dport_0 = self.dut_ports[0]
        self.used_dport_1 = self.dut_ports[1]
        self.pf0_intf = self.dut.ports_info[self.used_dport_0]["intf"]
        self.pf1_intf = self.dut.ports_info[self.used_dport_1]["intf"]
        self.pf0_pci = self.dut.ports_info[self.used_dport_0]["pci"]
        self.pf1_pci = self.dut.ports_info[self.used_dport_1]["pci"]
        self.pf0_mac = self.dut.get_mac_address(0)
        self.pf1_mac = self.dut.get_mac_address(1)
        self.other_mac = "00:12:23:34:45:89"

        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)

        self.rxq = 16
        self.fdirpro = FdirProcessing(
            self, self.pmd_output, [self.tport_iface0, self.tport_iface1], self.rxq
        )
        self.logfmt = "*" * 20

    def set_up(self):
        """

        Run before each test case.
        """
        self.reload_kdriver()

    def reload_kdriver(self):
        self.dut.send_expect("rmmod ice && modprobe ice", "# ", timeout=60)

    def setup_npf_nvf_env(self, pf_num=1, vf_num=4):
        try:
            self.pf0_vfs_pci = list()
            self.pf1_vfs_pci = list()
            # generate vf on pf
            if pf_num == 1:
                self.dut.generate_sriov_vfs_by_port(
                    self.used_dport_0, vf_num, driver=self.kdriver
                )
                self.sriov_vfs_pf0 = self.dut.ports_info[self.used_dport_0]["vfs_port"]
                # bind VF0 and VF1 to dpdk driver
                for vf_port in self.sriov_vfs_pf0:
                    vf_port.bind_driver(self.drivername)
                    self.pf0_vfs_pci.append(vf_port.pci)
            else:
                self.dut.generate_sriov_vfs_by_port(
                    self.used_dport_0, vf_num, driver=self.kdriver
                )
                self.dut.generate_sriov_vfs_by_port(
                    self.used_dport_1, vf_num, driver=self.kdriver
                )
                self.sriov_vfs_pf0 = self.dut.ports_info[self.used_dport_0]["vfs_port"]
                self.sriov_vfs_pf1 = self.dut.ports_info[self.used_dport_1]["vfs_port"]
                for vf_port in self.sriov_vfs_pf0:
                    vf_port.bind_driver(self.drivername)
                    self.pf0_vfs_pci.append(vf_port.pci)
                for vf_port in self.sriov_vfs_pf1:
                    vf_port.bind_driver(self.drivername)
                    self.pf1_vfs_pci.append(vf_port.pci)

        except Exception as e:
            self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])
            self.dut.destroy_sriov_vfs_by_port(self.dut_ports[1])
            raise Exception(e)
        out = self.dut.send_expect("./usertools/dpdk-devbind.py -s", "# ")
        self.dut.logger.info(out)

    def setup_vf(self, pf_intf, trust_vf, vf_mac=None, reset_mac=False):
        trust_vf_list = trust_vf if isinstance(trust_vf, list) else [trust_vf]
        # set vf port trust on
        for vf in trust_vf_list:
            self.dut.send_expect(
                "ip link set {0} vf {1} trust on".format(pf_intf, vf), "# "
            )
            if reset_mac:
                vf_mac = vf_mac if vf_mac else "00:11:22:33:44:55"
                self.dut.send_expect(
                    "ip link set dev {0} address {1}".format(pf_intf, vf_mac), "# "
                )

    def destroy_env(self):
        """

        This is to stop testpmd and destroy npf and nvf environment.
        """
        self.pmd_output.quit()
        if getattr(self, "session1", None):
            self.pmd_output1.quit()
            self.dut.close_session(self.session1)
            del self.session1
        self.dut.kill_all()
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[1])
        if self.running_case == "test_2_pf_4_vfs":
            # restore pf mac
            self.dut.send_expect(
                "ip link set dev {0} address {1}".format(self.pf0_intf, self.pf0_mac),
                "# ",
            )
            self.dut.send_expect(
                "ip link set dev {0} address {1}".format(self.pf1_intf, self.pf1_mac),
                "# ",
            )

    def config_testpmd(self, pmd_output=None):
        pmd_output = pmd_output if pmd_output else self.pmd_output
        pmd_output.execute_cmd("set verbose 1")
        pmd_output.execute_cmd("set fwd rxonly")
        pmd_output.execute_cmd("set promisc all off")
        res = pmd_output.wait_link_status_up("all", timeout=30)
        self.verify(res is True, "some ports link status is down")
        pmd_output.execute_cmd("start")

    def launch_testpmd(self, port_list, pmd_output=None, **kwargs):
        pmd_output = pmd_output if pmd_output else self.pmd_output
        pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param="--rxq={0} --txq={0}".format(self.rxq),
            ports=port_list,
            **kwargs,
        )
        self.config_testpmd(pmd_output)

    def get_vfs_mac(self, pmd_output):
        out = pmd_output.execute_cmd("show port info all")
        mac_pattern = r"MAC address: (.*?)\s"
        mac_list = re.findall(mac_pattern, out)
        return mac_list

    def send_packets_and_get_output(self, dic, pmd_output=None, tx_iface=""):
        """
        general packets processing workflow.
        """
        pmd_output = pmd_output if pmd_output else self.pmd_output
        tx_iface = self.tport_iface0 if tx_iface == "" else tx_iface
        pmd_output.execute_cmd("start")
        pmd_output.execute_cmd("clear port stats all")
        # send packets
        self.pkt.update_pkt(dic["packet"])
        self.pkt.send_pkt(self.tester, tx_port=tx_iface, count=1)
        out1 = pmd_output.get_output(timeout=1)
        out2 = pmd_output.execute_cmd("stop")
        out3 = pmd_output.get_output(timeout=1)
        out = out1 + out2 + out3
        return out

    def check_vf_rx_packets(self, out, check_param, expect_pkts, check_stats=True):
        """
        check the vf receives the correct number packets
        """
        queue = check_param.get("queue") if check_param.get("queue") else "null"
        expect_port = check_param["expect_port"]
        expect_port = expect_port if isinstance(expect_port, list) else [expect_port]
        results = []
        for i in range(len(expect_port)):
            pkt_num = rfc.get_port_rx_packets_number(out, expect_port[i])
            results.append(pkt_num)
        if check_stats:
            # check packets number
            self.verify(
                results == expect_pkts,
                "failed: packets number not correct. expect %s, result %s"
                % (expect_pkts, results),
            )

            if queue == "null":
                self.dut.logger.info(
                    GREEN(
                        "{0} not get except queue, so not need to check queue {0}".format(
                            self.logfmt
                        )
                    )
                )
                return
            check_port_info = list()
            uncheck_port = list()
            # check queue
            for i in range(len(expect_pkts)):
                if expect_pkts[i] > 0:
                    check_info = dict()
                    check_info["expect_pkts"] = expect_pkts[i]
                    check_info["check_param"] = {
                        "port_id": expect_port[i],
                        "queue": queue,
                    }
                    check_port_info.append((expect_port[i], check_info))
                else:
                    uncheck_port.append(expect_port[i])
            self.dut.logger.info(
                GREEN(
                    "{0} port {1} not need check queue {0}".format(
                        self.logfmt, uncheck_port
                    )
                )
            )
            for check_port, check_info in check_port_info:
                self.dut.logger.info(
                    GREEN(
                        "{0} start check queue for port {1} {0}".format(
                            self.logfmt, check_port
                        )
                    )
                )
                expect_pkts = check_info["expect_pkts"]
                check_param = check_info["check_param"]
                check_param["rxq"] = self.rxq
                rfc.check_queue(out, expect_pkts, check_param, stats=check_stats)
        else:
            # check_stats=False, all vf can not receive packets, "expect_pkts": [0,0,0,0]
            expect_pkts = [0 for _ in range(len(expect_port))]
            self.verify(
                results == expect_pkts,
                "failed: packets number not correct. expect %s, result %s"
                % (expect_pkts, results),
            )

    def rte_flow(self, case_list, func_name, reset_env=True, **kwargs):
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
        if reset_env:
            # prepare the test environment
            self.setup_npf_nvf_env(pf_num=1, vf_num=4)
            self.setup_vf(self.pf0_intf, trust_vf=0)
            # launch testpmd
            self.launch_testpmd(self.pf0_vfs_pci, self.pmd_output)

        if not isinstance(case_list, list):
            case_list = [case_list]
        test_results = dict()
        for case in case_list:
            case_name = case.get("sub_casename")
            test_results[case_name] = {}
            try:
                self.dut.logger.info(
                    GREEN("{0} case_name:{1} {0}".format(self.logfmt, case_name))
                )
                case.update(kwargs)
                func_name(case)
            except Exception:
                test_results[case_name]["result"] = "failed"
                test_results[case_name]["err"] = re.sub(
                    r"['\r\n]", "", str(traceback.format_exc(limit=1))
                ).replace("\\\\", "\\")
                self.dut.logger.info(
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
                self.dut.logger.info((GREEN("case passed: {}".format(case_name))))
            finally:
                self.pmd_output.execute_cmd("flow flush 0")
        pass_rate = (
            round(
                sum(1 for k in test_results if "passed" in test_results[k]["result"])
                / len(test_results),
                4,
            )
            * 100
        )
        self.dut.logger.info(
            GREEN(
                [
                    "{}:{}".format(sub_name, test_results[sub_name]["result"])
                    for sub_name in test_results
                ]
            )
        )
        self.dut.logger.info(GREEN("pass rate is: {}".format(pass_rate)))
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

    def flow_subscribe_operate(self, case):
        """
        test steps of flow rule case:
            1. validate rules.
            2. create rules and check rules list for vf.
            3. send matched packets, check the packets are received by vf and queue.
            4. send mismatched packets, check the packets are not received by vf
            5. destroy rule, list rules.
            6. send matched packets, check the packtet can not received by vf.

        :param case: case dict info, eg:
            mac_ipv4_udp_vxlan = {
                "sub_casename": "mac_ipv4_udp_vxlan",
                "rule": "flow create 0 ingress pattern eth / ipv4 / udp dst is 4789 / end actions port_representor port_id 0 / end",

                "matched": {
                    "packet": MAC_IPV4_UDP_VXLAN['matched'],
                    "check_param": {"expect_port": [0, 1, 2, 3]},
                    "expect_pkts": [1, 0, 0, 0],
                },
                "mismatched": {
                    "packet": MAC_IPV4_UDP_VXLAN['mismatched'],
                    "check_param": {"expect_port": [0, 1, 2, 3]},
                    "expect_pkts": [0, 0, 0, 0],
                },
            }
        :return: None
        """
        # get tx_iface
        tx_iface = case.get("tx_iface")
        tx_iface = tx_iface if tx_iface else self.tport_iface0
        rule = case["rule"]
        extend_rule = case.get("extend_rule")
        if extend_rule:
            self.fdirpro.create_rule(extend_rule)
        # validate rules
        self.fdirpro.validate_rule(rule)
        # create rules and check rules list for vf.
        rule_li = self.fdirpro.create_rule(rule)
        self.fdirpro.check_rule(port_id=0, rule_list=rule_li)

        # set the dst mac of the packet by with mac
        case["matched"]["packet"] = [
            packet.format(self.pf0_mac) for packet in case["matched"]["packet"]
        ]
        case["mismatched"]["packet"] = [
            packet.format(self.pf0_mac) for packet in case["mismatched"]["packet"]
        ]

        # send matched packets, check the packets are received by vf and queue.
        matched_dic = case["matched"]
        self.dut.logger.info(
            GREEN("{0} send and check match packets {0}".format(self.logfmt))
        )
        out = self.send_packets_and_get_output(
            matched_dic, self.pmd_output, tx_iface=tx_iface
        )
        self.check_vf_rx_packets(
            out,
            check_param=matched_dic["check_param"],
            expect_pkts=matched_dic["expect_pkts"],
            check_stats=True,
        )

        # send mismatched packets, check the packets are not received by vf
        mismatched_dic = case["mismatched"]

        self.dut.logger.info(
            GREEN("{0} send and check mismatch packets {0}".format(self.logfmt))
        )
        out = self.send_packets_and_get_output(
            mismatched_dic, self.pmd_output, tx_iface=tx_iface
        )
        self.check_vf_rx_packets(
            out,
            check_param=mismatched_dic["check_param"],
            expect_pkts=mismatched_dic["expect_pkts"],
            check_stats=True,
        )
        # destroy rule, list rules.
        self.dut.logger.info(GREEN("{0} list and destroy rule {0}".format(self.logfmt)))
        self.fdirpro.destroy_rule(port_id=0, rule_id=rule_li)
        self.fdirpro.check_rule(port_id=0, rule_list=rule_li, stats=False)
        # send matched packets, check the packtet can not received by vf.
        self.dut.logger.info(
            GREEN(
                "{0} send and check match packets after destroy rule {0}".format(
                    self.logfmt
                )
            )
        )
        out = self.send_packets_and_get_output(
            matched_dic, self.pmd_output, tx_iface=tx_iface
        )
        self.check_vf_rx_packets(
            out,
            check_param=matched_dic["check_param"],
            expect_pkts=matched_dic["expect_pkts"],
            check_stats=False,
        )

    def flow_subscribe_priority_operate(self, case):
        """
        test steps of flow rule case:
            1. validate rules: two rules have same pattern, input set but different priority and action(priority 0 -> to queue 5, priority 1 -> to queue 6).
            2. create rules and list rules for vf.
            3. send matched packets, check vf receive the packets for hiting the priority 0.
            4. send mismatched packets, check the packets are not received by vf.
            5. destroy rule with priority 0, list rules.
            6. send matched packets, check vf receive the packets for hiting the priority 1.
            7. create rule 0 and send match packet, check vf receive the packets for hiting the priority 0.

        :param case: case dict info, eg:
            mac_ipv4_udp_payload_priority = {
                "sub_casename": "mac_ipv4_udp_payload_priority",
                "rule": [
                "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / udp src is 2048 dst is 2022 / end actions port_representor port_id 0 / rss queues 4 5 end / end",
                "flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.1 / udp src is 2048 dst is 2022 / end actions port_representor port_id 0 / rss queues 6 7 end / end",
                ],

                "matched": {
                    "packet": MAC_IPV4_UDP_PAYLOAD['matched'],
                    "check_param": {"expect_port": [0, 1, 2, 3], "queue": {"priority_0": [4, 5], "priority_1": [6,7]}},
                    "expect_pkts": [1, 0, 0, 0],
                },
                "mismatched": {
                    "packet": MAC_IPV4_UDP_PAYLOAD['mismatched'],
                    "check_param": {"expect_port": [0, 1, 2, 3]},
                    "expect_pkts": [0, 0, 0, 0],
                },
            }
        :return: None
        """
        # get tx_iface
        tx_iface = case.get("tx_iface")
        tx_iface = tx_iface if tx_iface else self.tport_iface0
        # validate and create rule
        rule = case["rule"]
        extend_rule = case.get("extend_rule")
        if extend_rule:
            self.fdirpro.create_rule(extend_rule)
        self.fdirpro.validate_rule(rule)
        rule_li = self.fdirpro.create_rule(rule)
        self.fdirpro.check_rule(port_id=0, rule_list=rule_li, stats=True)

        # set the dst mac of the packet by with mac
        case["matched"]["packet"] = [
            packet.format(self.pf0_mac) for packet in case["matched"]["packet"]
        ]
        case["mismatched"]["packet"] = [
            packet.format(self.pf0_mac) for packet in case["mismatched"]["packet"]
        ]

        priority_0_check_queue = case["matched"]["check_param"]["queue"]["priority_0"]
        priority_1_check_queue = case["matched"]["check_param"]["queue"]["priority_1"]

        # send matched packets, check vf receive the packets for hiting the priority 0
        # set check queue is hiting the priority 0
        case["matched"]["check_param"]["queue"] = priority_0_check_queue
        matched_dic = case["matched"]
        self.dut.logger.info(
            GREEN(
                "{0} send matched packets, check vf receive the packets for hiting the priority 0 {0}".format(
                    self.logfmt
                )
            )
        )
        out = self.send_packets_and_get_output(
            matched_dic, self.pmd_output, tx_iface=tx_iface
        )
        self.check_vf_rx_packets(
            out,
            check_param=matched_dic["check_param"],
            expect_pkts=matched_dic["expect_pkts"],
            check_stats=True,
        )

        # send mismatched packets, check the packets are not received by vf.
        mismatched_dic = case["mismatched"]

        self.dut.logger.info(
            GREEN(
                "{0} send mismatched packets, check the packets are not received by vf {0}".format(
                    self.logfmt
                )
            )
        )
        out = self.send_packets_and_get_output(
            mismatched_dic, self.pmd_output, tx_iface=tx_iface
        )
        self.check_vf_rx_packets(
            out,
            check_param=mismatched_dic["check_param"],
            expect_pkts=mismatched_dic["expect_pkts"],
            check_stats=True,
        )
        # destroy rule with priority 0, list rules.
        self.dut.logger.info(
            GREEN(
                "{0} destroy rule with priority 0, list rules {0}".format(self.logfmt)
            )
        )
        self.fdirpro.destroy_rule(port_id=0, rule_id=rule_li[0])
        self.fdirpro.check_rule(port_id=0, rule_list=rule_li[0], stats=False)
        self.fdirpro.check_rule(port_id=0, rule_list=rule_li[1], stats=True)
        # send matched packets, check vf receive the packets for hiting the priority 1.
        case["matched"]["check_param"]["queue"] = priority_1_check_queue
        self.dut.logger.info(
            GREEN(
                "{0} send matched packets, check vf receive the packets for hiting the priority 1 {0}".format(
                    self.logfmt
                )
            )
        )
        out = self.send_packets_and_get_output(
            matched_dic, self.pmd_output, tx_iface=tx_iface
        )
        self.check_vf_rx_packets(
            out,
            check_param=matched_dic["check_param"],
            expect_pkts=matched_dic["expect_pkts"],
            check_stats=True,
        )
        # recreate rule 0 and send match packet, check vf receive the packets for hiting the priority 0
        self.dut.logger.info(
            GREEN(
                "{0} recreate rule 0 and send match packet, check vf receive the packets for hiting the priority 0 {0}".format(
                    self.logfmt
                )
            )
        )
        case["matched"]["check_param"]["queue"] = priority_0_check_queue
        rule_li1 = self.fdirpro.create_rule(rule[0])
        self.fdirpro.check_rule(0, rule_list=rule_li1, stats=True)
        self.fdirpro.check_rule(0, rule_list=rule_li[1], stats=True)
        out = self.send_packets_and_get_output(
            matched_dic, self.pmd_output, tx_iface=tx_iface
        )
        self.check_vf_rx_packets(
            out,
            check_param=matched_dic["check_param"],
            expect_pkts=matched_dic["expect_pkts"],
            check_stats=True,
        )

    # The following are flow subscription smoke tests
    def test_1_pf_4_vfs(self):
        """

        Subcase 1: 1 PF 4 VFs
        """
        rules = [
            "flow create 0 ingress pattern eth dst is {} / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end".format(
                self.pf0_mac
            ),
            "flow create 1 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 1 / end",
            "flow create 2 ingress pattern eth dst is {} / ipv4 / udp src is 22 / end actions port_representor port_id 2 / end".format(
                self.pf0_mac
            ),
            "flow create 3 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 3 / end",
        ]

        matched = {
            "packet": [
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80)'.format(
                    self.pf0_mac
                ),
            ],
            "check_param": {"expect_port": [0, 1, 2, 3]},
            "expect_pkts": [1, 1, 1, 1],
        }

        mismatched = {
            "packet": [
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80)'.format(
                    self.other_mac
                ),
                'Ether(dst="{}")/IPv6()/UDP(sport=22)/Raw("x" * 80)'.format(
                    self.pf0_mac
                ),
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/Raw("x" * 80)'.format(
                    self.pf0_mac
                ),
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22)/Raw("x" * 80)'.format(
                    self.pf0_mac
                ),
            ],
            "check_param": {"expect_port": [0, 1, 2, 3]},
            "expect_pkts": [0, 0, 0, 0],
        }

        # prepare the test environment
        self.setup_npf_nvf_env(pf_num=1, vf_num=4)
        self.setup_vf(self.pf0_intf, trust_vf=[0, 1, 2, 3])
        self.launch_testpmd(port_list=self.pf0_vfs_pci)
        self.fdirpro.validate_rule(rules, check_stats=True)
        rule_list = self.fdirpro.create_rule(rules, check_stats=True)
        for i in range(len(rules)):
            self.fdirpro.check_rule(port_id=i, rule_list=rule_list[i], stats=True)
        self.dut.logger.info(
            GREEN("{0} rule exists and check match packets {0}".format(self.logfmt))
        )
        # send matched packets, check the packets are received by vf
        out = self.send_packets_and_get_output(matched, tx_iface=self.tport_iface0)
        self.check_vf_rx_packets(
            out,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=True,
        )

        self.dut.logger.info(
            GREEN("{0} rule exists and check mismatch packets {0}".format(self.logfmt))
        )
        # send mismatched packets, check the packets are not received by vf
        out = self.send_packets_and_get_output(mismatched, tx_iface=self.tport_iface0)
        self.check_vf_rx_packets(
            out,
            check_param=mismatched["check_param"],
            expect_pkts=mismatched["expect_pkts"],
            check_stats=True,
        )
        # reset vf
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop all")
        self.pmd_output.execute_cmd("port reset all")
        self.pmd_output.execute_cmd("port start all")
        self.pmd_output.execute_cmd("start")
        # check that all rules are cleared
        for i in range(len(rules)):
            self.fdirpro.check_rule(port_id=i, rule_list=rule_list[i], stats=False)
        self.dut.logger.info(
            GREEN("{0} rule non-exist and check match packets {0}".format(self.logfmt))
        )
        # send matched packets, check the packets are not received by vf
        out = self.send_packets_and_get_output(matched, tx_iface=self.tport_iface0)
        self.check_vf_rx_packets(
            out,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=False,
        )

    def test_2_pf_4_vfs(self):
        """

        Subcase 2:  2 PF 4 VFs
        """
        pf0_new_mac = "00:11:22:33:44:55"
        pf1_new_mac = "00:11:22:33:44:66"

        rules = [
            "flow create 0 ingress pattern eth dst is {} / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end",
        ]

        normal = {
            "packet": [
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80)',  # vf mac
                'Ether(dst="{}")/IPv6(src="::22",dst="::11")/TCP(sport=22)/Raw("x" * 80)',  # vf mac
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)',  # vf mac
                'Ether(dst="{}")/IPv6(src="::22",dst="::11")/Raw("x" * 80)',  # vf mac
            ],
            "check_param": {"expect_port": [0, 1]},
            "expect_pkts": [4, 4],
        }

        matched = {
            "packet": [
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80)'.format(
                    pf0_new_mac
                ),
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80)'.format(
                    pf1_new_mac
                ),
            ],
            "check_param": {"expect_port": [0, 1]},
            "expect_pkts": [1, 0],
        }

        mismatched = {
            "packet": [
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80)'.format(
                    self.pf0_mac
                ),
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22)/Raw("x" * 80)'.format(
                    self.pf1_mac
                ),
                'Ether(dst="{}")/IPv6()/UDP(sport=22)/Raw("x" * 80)'.format(
                    pf0_new_mac
                ),
                'Ether(src="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP()/Raw("x" * 80)'.format(
                    pf1_new_mac
                ),
                'Ether(dst="{}")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP()/Raw("x" * 80)'.format(
                    pf0_new_mac
                ),
            ],
            "check_param": {"expect_port": [0, 1]},
            "expect_pkts": [0, 0],
        }

        # prepare the test environment
        self.session1 = self.dut.new_session()
        self.pmd_output1 = PmdOutput(self.dut, session=self.session1)
        self.setup_npf_nvf_env(pf_num=2, vf_num=2)
        self.setup_vf(self.pf0_intf, trust_vf=0, vf_mac=pf0_new_mac, reset_mac=True)
        self.setup_vf(self.pf1_intf, trust_vf=0, vf_mac=pf1_new_mac, reset_mac=True)

        self.fdirpro1 = FdirProcessing(
            self, self.pmd_output1, [self.tport_iface0, self.tport_iface1], self.rxq
        )
        self.launch_testpmd(
            self.pf0_vfs_pci,
            pmd_output=self.pmd_output,
            eal_param="--file-prefix=pf0_vf",
        )
        self.launch_testpmd(
            self.pf1_vfs_pci,
            pmd_output=self.pmd_output1,
            eal_param="--file-prefix=pf1_vf",
        )
        # rule create failed that use old pf mac
        self.fdirpro.create_rule(rules[0].format(self.pf0_mac), check_stats=False)
        self.fdirpro1.create_rule(rules[0].format(self.pf1_mac), check_stats=False)
        # rule create successful that use new pf mac
        rule_list = self.fdirpro.create_rule(
            rules[0].format(pf0_new_mac), check_stats=True
        )
        self.fdirpro.check_rule(port_id=0, rule_list=rule_list, stats=True)
        rule_list1 = self.fdirpro1.create_rule(
            rules[0].format(pf1_new_mac), check_stats=True
        )
        self.fdirpro1.check_rule(port_id=0, rule_list=rule_list1, stats=True)

        pf0_vf_mac_list = self.get_vfs_mac(self.pmd_output)
        pf1_vf_mac_list = self.get_vfs_mac(self.pmd_output1)
        all_vf_mac_list = pf0_vf_mac_list + pf1_vf_mac_list
        normal_packets = list()
        for vf_mac in all_vf_mac_list:
            for packet in normal["packet"]:
                normal_packets.append(packet.format(vf_mac))
        normal["packet"] = normal_packets
        self.dut.logger.info(
            GREEN("{0} rule exists and check normal packets {0}".format(self.logfmt))
        )
        # send all normal packets in pf0 and pf1, check that the vf can only receive packets whose dst MAC is itself
        out = self.send_packets_and_get_output(
            normal, pmd_output=self.pmd_output, tx_iface=self.tport_iface0
        )
        out1 = self.send_packets_and_get_output(
            normal, pmd_output=self.pmd_output1, tx_iface=self.tport_iface1
        )
        self.check_vf_rx_packets(
            out,
            check_param=normal["check_param"],
            expect_pkts=normal["expect_pkts"],
            check_stats=True,
        )
        self.check_vf_rx_packets(
            out1,
            check_param=normal["check_param"],
            expect_pkts=normal["expect_pkts"],
            check_stats=True,
        )
        self.dut.logger.info(
            GREEN("{0} rule exists and check match packets {0}".format(self.logfmt))
        )
        # send all match packets from port 0 and 1 of the tester,
        # and check that each VF can only receive match rule packet.
        out = self.send_packets_and_get_output(
            matched, pmd_output=self.pmd_output, tx_iface=self.tport_iface0
        )
        out1 = self.send_packets_and_get_output(
            matched, pmd_output=self.pmd_output1, tx_iface=self.tport_iface1
        )
        self.check_vf_rx_packets(
            out,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=True,
        )
        self.check_vf_rx_packets(
            out1,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=True,
        )
        self.dut.logger.info(
            GREEN("{0} rule exists and check mismatch packets {0}".format(self.logfmt))
        )
        # send all mismatched packets from port 0 and port 1 of the tester,
        # and check that all vfs can not received these packets.
        out = self.send_packets_and_get_output(
            mismatched, pmd_output=self.pmd_output, tx_iface=self.tport_iface0
        )
        out1 = self.send_packets_and_get_output(
            mismatched, pmd_output=self.pmd_output1, tx_iface=self.tport_iface1
        )
        self.check_vf_rx_packets(
            out,
            check_param=mismatched["check_param"],
            expect_pkts=mismatched["expect_pkts"],
            check_stats=True,
        )
        self.check_vf_rx_packets(
            out1,
            check_param=mismatched["check_param"],
            expect_pkts=mismatched["expect_pkts"],
            check_stats=True,
        )
        # destory all rule
        for id in rule_list:
            self.pmd_output.execute_cmd("flow destroy 0 rule {}".format(id))
        self.fdirpro.check_rule(port_id=0, rule_list=rule_list, stats=False)
        for id in rule_list:
            self.pmd_output1.execute_cmd("flow destroy 0 rule {}".format(id))
        self.fdirpro1.check_rule(port_id=0, rule_list=rule_list1, stats=False)
        self.dut.logger.info(
            GREEN("{0} rule non-exist and check normal packets {0}".format(self.logfmt))
        )
        # send all normal packets in pf0 and pf1, check that the vf can only receive packets whose dst MAC is itself
        out = self.send_packets_and_get_output(
            normal, pmd_output=self.pmd_output, tx_iface=self.tport_iface0
        )
        out1 = self.send_packets_and_get_output(
            normal, pmd_output=self.pmd_output1, tx_iface=self.tport_iface1
        )
        self.check_vf_rx_packets(
            out,
            check_param=normal["check_param"],
            expect_pkts=normal["expect_pkts"],
            check_stats=True,
        )
        self.check_vf_rx_packets(
            out1,
            check_param=normal["check_param"],
            expect_pkts=normal["expect_pkts"],
            check_stats=True,
        )
        self.dut.logger.info(
            GREEN("{0} rule non-exist and check match packets {0}".format(self.logfmt))
        )
        # send the match rule packets and all vf can not received packet.
        out = self.send_packets_and_get_output(
            matched, pmd_output=self.pmd_output, tx_iface=self.tport_iface0
        )
        out1 = self.send_packets_and_get_output(
            matched, pmd_output=self.pmd_output1, tx_iface=self.tport_iface1
        )
        self.check_vf_rx_packets(
            out,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=False,
        )

        self.check_vf_rx_packets(
            out1,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=False,
        )

    def test_exclusive_rule(self):
        """

        Subcase 3: exclusive rule
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end",
            "flow create 2 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 2 / queue index 3 / end",
            "flow create 3 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 3 / queue index 4 / end",
        ]

        self.setup_npf_nvf_env(pf_num=1, vf_num=4)
        self.setup_vf(self.pf0_intf, trust_vf=[0, 1, 2, 3])
        self.launch_testpmd(port_list=self.pf0_vfs_pci)
        self.fdirpro.validate_rule(rules, check_stats=True)
        # same flow subscribe rule only can create once
        rule_list = self.fdirpro.create_rule(rules[0], check_stats=True)
        self.fdirpro.check_rule(port_id=0, stats=True, rule_list=rule_list)
        self.fdirpro.create_rule(rules[0], check_stats=False)
        self.fdirpro.destroy_rule(0, rule_list)
        self.fdirpro.check_rule(port_id=0, stats=False, rule_list=rule_list)
        # the same rule to queue only can create in 1 vf
        rule_list = self.fdirpro.create_rule(rules[1], check_stats=True)
        self.fdirpro.check_rule(port_id=2, stats=True, rule_list=rule_list)
        self.fdirpro.create_rule(rules[2], check_stats=False)
        # destory rule 0 and recreate rule::
        self.fdirpro.destroy_rule(2, rule_list)
        self.fdirpro.create_rule(rules[2], check_stats=True)
        self.fdirpro.check_rule(port_id=3, stats=True, rule_list=rule_list)
        self.fdirpro.create_rule(rules[1], check_stats=False)

    def test_negative_rule(self):
        """
        Subcase 4: negative rule

        """
        self.setup_npf_nvf_env(pf_num=1, vf_num=4)
        self.setup_vf(self.pf0_intf, trust_vf=[0, 1, 2])
        self.launch_testpmd(port_list=self.pf0_vfs_pci)
        vf_mac = self.get_vfs_mac(self.pmd_output)[0]

        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 1 / end",
            "flow create 1 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end",
            "flow create 0 ingress pattern eth dst is {} / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end".format(
                vf_mac
            ),
            "flow create 1 ingress pattern eth dst is {} / ipv4 / udp src is 22 / end actions port_representor port_id 1 / end".format(
                self.pf1_mac
            ),
            "flow create 2 ingress pattern eth src is {} / ipv4 / udp src is 22 / end actions port_representor port_id 2 / end".format(
                self.pf0_mac
            ),
            "flow create 3 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 3 / end",
        ]

        # all rule create failed
        check_msg = "iavf_flow_create(): Failed to create flow"
        self.fdirpro.create_rule(rules, check_stats=False, msg=check_msg)

    def test_pf_reset(self):
        """

        Subcase 5: pf reset
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 0 / end",
            "flow create 1 ingress pattern eth / ipv4 / udp src is 22 / end actions port_representor port_id 1 / end",
        ]
        matched = {
            "packet": [
                'Ether(dst="{}")/IP()/UDP(sport=22)/Raw("x"*80)'.format(self.pf0_mac),
                'Ether(dst="{}")/IP()/UDP(sport=22)/Raw("x"*80)'.format(self.pf1_mac),
            ],
            "check_param": {"expect_port": [0, 1]},
            "expect_pkts": [1, 1],
        }

        # prepare the test environment
        self.session1 = self.dut.new_session()
        self.pmd_output1 = PmdOutput(self.dut, session=self.session1)
        self.setup_npf_nvf_env(pf_num=2, vf_num=2)
        self.setup_vf(self.pf0_intf, trust_vf=[0, 1])
        self.setup_vf(self.pf1_intf, trust_vf=[0, 1])

        self.fdirpro1 = FdirProcessing(
            self, self.pmd_output1, [self.tport_iface0, self.tport_iface1], self.rxq
        )
        self.launch_testpmd(
            self.pf0_vfs_pci,
            pmd_output=self.pmd_output,
            eal_param="--file-prefix=pf0_vf",
        )
        self.launch_testpmd(
            self.pf1_vfs_pci,
            pmd_output=self.pmd_output1,
            eal_param="--file-prefix=pf1_vf",
        )
        # create rule and check rule list
        rule_list = self.fdirpro.create_rule(rules, check_stats=True)
        self.fdirpro.check_rule(port_id=0, rule_list=rule_list, stats=True)
        rule_list1 = self.fdirpro1.create_rule(rules, check_stats=True)
        self.fdirpro1.check_rule(port_id=0, rule_list=rule_list1, stats=True)

        self.dut.logger.info(
            GREEN("{0} rule exists and check match packets {0}".format(self.logfmt))
        )
        # send match and check pf0 and pf1 vfs can receive packet
        out = self.send_packets_and_get_output(
            matched, pmd_output=self.pmd_output, tx_iface=self.tport_iface0
        )
        out1 = self.send_packets_and_get_output(
            matched, pmd_output=self.pmd_output1, tx_iface=self.tport_iface1
        )
        self.check_vf_rx_packets(
            out,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=True,
        )
        self.check_vf_rx_packets(
            out1,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=True,
        )
        # reset pf0
        self.dut.logger.info(GREEN("{0} reset pf0 {0}".format(self.logfmt)))
        self.dut.logger.info(
            "echo 1 > /sys/bus/pci/devices/{}/reset".format(
                self.pf0_pci.replace(":", "\:")
            )
        )
        self.dut.send_expect(
            "echo 1 > /sys/bus/pci/devices/{}/reset".format(
                self.pf0_pci.replace(":", "\:")
            ),
            "# ",
            alt_session=True,
        )
        # send match and check pf0 vfs can not receive packet and pf1 vfs can receive packet
        out = self.send_packets_and_get_output(
            matched, pmd_output=self.pmd_output, tx_iface=self.tport_iface0
        )
        out1 = self.send_packets_and_get_output(
            matched, pmd_output=self.pmd_output1, tx_iface=self.tport_iface1
        )
        self.check_vf_rx_packets(
            out,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=False,
        )
        self.check_vf_rx_packets(
            out1,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=True,
        )

        # reset pf1
        self.dut.logger.info(GREEN("{0} reset pf1 {0}".format(self.logfmt)))
        self.dut.logger.info(
            "echo 1 > /sys/bus/pci/devices/{}/reset".format(
                self.pf1_pci.replace(":", "\:")
            )
        )
        self.dut.send_expect(
            "echo 1 > /sys/bus/pci/devices/{}/reset".format(
                self.pf1_pci.replace(":", "\:")
            ),
            "# ",
            alt_session=True,
        )
        # send match and check pf0 vfs can not receive packet and pf1 vfs can receive packet
        out = self.send_packets_and_get_output(
            matched, pmd_output=self.pmd_output, tx_iface=self.tport_iface0
        )
        out1 = self.send_packets_and_get_output(
            matched, pmd_output=self.pmd_output1, tx_iface=self.tport_iface1
        )
        self.check_vf_rx_packets(
            out,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=False,
        )
        self.check_vf_rx_packets(
            out1,
            check_param=matched["check_param"],
            expect_pkts=matched["expect_pkts"],
            check_stats=False,
        )

    # The following are flow subscription pattern and input set tests
    def test_mac_ipv4_udp_vxlan(self):
        """

        case: MAC_IPV4_UDP_VXLAN
        """
        func_name = self.flow_subscribe_operate
        self.rte_flow(mac_ipv4_udp_vxlan, func_name)

    def test_mac_ipv6_udp_vxlan(self):
        """

        case: MAC_IPV6_UDP_VXLAN
        """
        func_name = self.flow_subscribe_operate
        self.rte_flow(mac_ipv6_udp_vxlan, func_name)

    def test_mac_vlan_ipv4(self):
        """

        case: MAC_VLAN_IPV4
        """
        func_name = self.flow_subscribe_operate
        self.rte_flow(mac_vlan_ipv4, func_name)

    def test_mac_ipv4_icmp(self):
        """

        case: MAC_IPV4_ICMP
        """
        func_name = self.flow_subscribe_operate
        self.rte_flow(mac_ipv4_icmp, func_name)

    def test_l3_mask(self):
        """

        case: l3 mask
        """
        func_name = self.flow_subscribe_operate
        self.rte_flow(l3_mask, func_name)

    def test_l4_mask(self):
        """

        case : l4 mask
        """
        func_name = self.flow_subscribe_operate
        self.rte_flow(l4_mask, func_name)

    def test_mac_ipv4_udp_payload_priority(self):
        """

        case: MAC_IPV4_UDP_PAYLOAD_priority
        """
        func_name = self.flow_subscribe_priority_operate
        self.rte_flow(mac_ipv4_udp_payload_priority, func_name)

    def test_mac_ipv4_tcp_payload_priority(self):
        """

        case: MAC_IPV4_TCP_PAYLOAD_priority
        """
        func_name = self.flow_subscribe_priority_operate
        self.rte_flow(mac_ipv4_tcp_payload_priority, func_name)

    def test_mac_ipv6_udp_payload_priority(self):
        """

        case: MAC_IPV6_UDP_PAYLOAD_priority
        """
        func_name = self.flow_subscribe_priority_operate
        self.rte_flow(mac_ipv6_udp_payload_priority, func_name)

    def test_mac_ipv6_tcp_payload_priority(self):
        """

        case: MAC_IPV6_TCP_PAYLOAD_priority
        """
        func_name = self.flow_subscribe_priority_operate
        self.rte_flow(mac_ipv6_tcp_payload_priority, func_name)

    def tear_down(self):
        self.destroy_env()

    def tear_down_all(self):
        self.dut.kill_all()
