# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2021-2022 Intel Corporation
#

import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, check_supported_nic, skip_unsupported_pkg
from framework.utils import GREEN, RED

from .rte_flow_common import FdirProcessing

mac_qinq_ipv4_pay_src_ip = {
    "name": "mac_qinq_ipv4_pay_src_ip",
    "rule": "flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv4 src is 196.222.232.221 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.222")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_ipv4_pay_dst_ip = {
    "name": "mac_qinq_ipv4_pay_dst_ip",
    "rule": "flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv4 dst is 196.222.232.221 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.222")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_ipv4_pay_dest_mac = {
    "name": "mac_qinq_ipv4_pay_dest_mac",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv4 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/("X"*480)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/("X"*480)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP()/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_ipv4_pay = [
    mac_qinq_ipv4_pay_src_ip,
    mac_qinq_ipv4_pay_dst_ip,
    mac_qinq_ipv4_pay_dest_mac,
]

mac_qinq_ipv6_pay_src_ip = {
    "name": "mac_qinq_ipv6_pay_src_ip",
    "rule": "flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv6 src is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:9999")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_ipv6_pay_dst_ip = {
    "name": "mac_qinq_ipv6_pay_dst_ip",
    "rule": "flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_ipv6_pay_dest_mac = {
    "name": "mac_qinq_ipv6_pay_dest_mac",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv6 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6()/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6()/("X"*480)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6()/("X"*480)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6()/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_ipv6_pay = [
    mac_qinq_ipv6_pay_src_ip,
    mac_qinq_ipv6_pay_dst_ip,
    mac_qinq_ipv6_pay_dest_mac,
]

mac_qinq_pppoe_pay = [
    {
        "name": "mac_qinq_pppoe_pay",
        "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / end actions represented_port ethdev_port_id 1 / end",
        "scapy_str": {
            "matched": [
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)',
            ],
            "mismatched": [
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)',
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)',
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)',
                'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)',
            ],
        },
        "check_param": {"port_id": 2},
    }
]

mac_qinq_pppoe_proto = [
    {
        "name": "mac_qinq_pppoe_proto",
        "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / pppoe_proto_id is 0x0057 / end actions represented_port ethdev_port_id 1 / end",
        "scapy_str": {
            "matched": [
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)'
            ],
            "mismatched": [
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)',
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
            ],
        },
        "check_param": {"port_id": 2},
    }
]

mac_qinq_pppoe_ipv4_src_ip = {
    "name": "mac_qinq_pppoe_ipv4_src_ip",
    "rule": "flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 src is 196.222.232.221 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.222")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_pppoe_ipv4_dst_ip = {
    "name": "mac_qinq_pppoe_ipv4_dst_ip",
    "rule": "flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 dst is 196.222.232.221 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.222")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_pppoe_ipv4_dest_mac = {
    "name": "mac_qinq_pppoe_ipv4_dest_mac",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_pppoe_ipv4 = [
    mac_qinq_pppoe_ipv4_src_ip,
    mac_qinq_pppoe_ipv4_dst_ip,
    mac_qinq_pppoe_ipv4_dest_mac,
]

mac_qinq_pppoe_ipv6_src_ip = {
    "name": "mac_qinq_pppoe_ipv6_src_ip",
    "rule": "flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 src is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:9999")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_pppoe_ipv6_dst_ip = {
    "name": "mac_qinq_pppoe_ipv6_dst_ip",
    "rule": "flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_pppoe_ipv6_dest_mac = {
    "name": "mac_qinq_pppoe_ipv6_dest_mac",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)',
        ],
    },
    "check_param": {"port_id": 2},
}

mac_qinq_pppoe_ipv6 = [
    mac_qinq_pppoe_ipv6_src_ip,
    mac_qinq_pppoe_ipv6_dst_ip,
    mac_qinq_pppoe_ipv6_dest_mac,
]

# Non-pipeline mode
tv_mac_qinq_ipv4 = {
    "name": "tv_mac_qinq_ipv4",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/("X"*80)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.2")/("X"*80)',
        ],
    },
    "check_param": {"port_id": 2},
}

tv_mac_qinq_ipv6 = {
    "name": "tv_mac_qinq_ipv6",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*80)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/("X"*80)',
        ],
    },
    "check_param": {"port_id": 2},
}

tv_mac_qinq_ipv4_udp = {
    "name": "tv_mac_qinq_ipv4_udp",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv4 / udp src is 50 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/UDP(sport=50,dport=23)/("X"*80)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/UDP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/UDP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP()/UDP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/UDP(sport=50,dport=22)/("X"*80)',
        ],
    },
    "check_param": {"port_id": 2},
}

tv_mac_qinq_ipv4_tcp = {
    "name": "tv_mac_qinq_ipv4_tcp",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv4 / tcp src is 50 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/TCP(sport=50,dport=23)/("X"*80)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/TCP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/TCP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP()/TCP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/TCP(sport=50,dport=22)/("X"*80)',
        ],
    },
    "check_param": {"port_id": 2},
}

tvs_mac_l4_qinq_dcf_non_pipeline_mode = [
    tv_mac_qinq_ipv4,
    tv_mac_qinq_ipv6,
    tv_mac_qinq_ipv4_udp,
    tv_mac_qinq_ipv4_tcp,
]

# Pipeline mode
tv_mac_qinq_ipv6_udp = {
    "name": "tv_mac_qinq_ipv6_udp",
    "rule": "flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 50 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=50,dport=23)/("X"*80)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=50,dport=22)/("X"*80)',
        ],
    },
    "check_param": {"port_id": 2},
}

tv_mac_qinq_ipv6_tcp = {
    "name": "tv_mac_qinq_ipv6_tcp",
    "rule": "flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 50 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "scapy_str": {
        "matched": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=50,dport=23)/("X"*80)'
        ],
        "mismatched": [
            'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=50,dport=23)/("X"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=50,dport=22)/("X"*80)',
        ],
    },
    "check_param": {"port_id": 2},
}

tvs_mac_l4_qinq_dcf_pipeline_mode = [tv_mac_qinq_ipv6_udp, tv_mac_qinq_ipv6_tcp]


class TestICEDcfDualVlan(TestCase):
    @check_supported_nic(
        [
            "ICE_25G-E810C_SFP",
            "ICE_100G-E810C_QSFP",
            "ICE_25G-E810_XXV_SFP",
            "ICE_25G-E823C_QSFP",
        ]
    )
    def set_up_all(self):
        """
        Run at the start of each test suite.
        prerequisites.
        """
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        # Verify that enough threads are available
        cores = self.dut.get_core_list("1S/4C/1T")
        self.verify(cores is not None, "Insufficient cores for speed testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.tester_iface1 = self.tester.get_interface(self.tester_port1)

        self.used_dut_port = self.dut_ports[0]
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]["intf"]
        port = self.dut.ports_info[0]["port"]
        port.bind_driver()
        # get priv-flags default stats
        self.flag = "vf-vlan-pruning"
        self.default_stats = self.dut.get_priv_flags_state(self.pf_interface, self.flag)

        self.vf_flag = False
        self.vf0_mac = ""
        self.vf1_mac = "00:11:22:33:44:11"
        self.vf2_mac = "00:11:22:33:44:22"
        self.vf3_mac = "00:11:22:33:44:33"
        self.path = self.dut.apps_name["test-pmd"]
        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.fdirprocess = FdirProcessing(
            self, self.pmd_output, [self.tester_iface0], rxq=8
        )

    def reload_ice(self):
        self.dut.send_expect("rmmod ice && modprobe ice", "# ")

    def set_up(self):
        """
        Run before each test case.
        """
        self.reload_ice()
        self.pci_list = []
        if self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s %s"
                % (self.pf_interface, self.flag, self.default_stats),
                "# ",
            )

    def setup_1pf_4vfs_env(self):
        if self.vf_flag is False:
            self.dut.generate_sriov_vfs_by_port(
                self.used_dut_port, 4, driver=self.kdriver
            )
            self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]["vfs_port"]
            self.vf_flag = True
            self.dut.send_expect(
                "ip link set %s vf 0 trust on" % (self.pf_interface), "# "
            )
            self.dut.send_expect(
                "ip link set %s vf 1 mac %s" % (self.pf_interface, self.vf1_mac),
                "# ",
            )
            self.dut.send_expect(
                "ip link set %s vf 2 mac %s" % (self.pf_interface, self.vf2_mac),
                "# ",
            )
            self.dut.send_expect(
                "ip link set %s vf 3 mac %s" % (self.pf_interface, self.vf3_mac),
                "# ",
            )

            try:
                for port in self.sriov_vfs_port:
                    port.bind_driver(self.drivername)
                    self.pci_list.append(port.pci)

                self.vf0_prop = {"opt_host": self.sriov_vfs_port[0].pci}
                self.dut.send_expect("ifconfig %s up" % self.pf_interface, "# ")
                self.dut.send_expect(
                    "ip link set dev %s vf 0 spoofchk off" % self.pf_interface, "# "
                )
                self.dut.send_expect(
                    "ip link set dev %s vf 1 spoofchk off" % self.pf_interface, "# "
                )
                self.dut.send_expect(
                    "ip link set dev %s vf 2 spoofchk off" % self.pf_interface, "# "
                )
                self.dut.send_expect(
                    "ip link set dev %s vf 3 spoofchk off" % self.pf_interface, "# "
                )
            except Exception as e:
                self.destroy_iavf()
                raise Exception(e)

    def destroy_iavf(self):
        if self.vf_flag is True:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.vf_flag = False

    def launch_testpmd(self, pipline_mode=False):
        if pipline_mode:
            port_options = {
                self.pci_list[0]: "cap=dcf,representor=[1],pipeline-mode-support=1"
            }
        else:
            port_options = {self.pci_list[0]: "cap=dcf,representor=[1]"}
        param = " "
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param=param,
            ports=self.pci_list,
            socket=self.ports_socket,
            port_options=port_options,
        )
        self.confing_testpmd()

    def confing_testpmd(self):
        driver_type = "Device name.*?%s.*?\n(.*)" % self.sriov_vfs_port[0].pci
        output = self.pmd_output.execute_cmd("show port info all")
        out = re.findall(driver_type, output)
        self.verify(len(out) == 2, "port0 and port1 driver not is net_ice_dcf")
        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")

    def reset_vf(self):
        self.pmd_output.execute_cmd("port stop 2")
        self.pmd_output.execute_cmd("port reset 2")
        self.pmd_output.execute_cmd("port start 2")
        self.pmd_output.execute_cmd("start")

    def tcpdump_send_packet_get_output(self, pkt):
        self.tester.send_expect("rm -rf getPackageByTcpdump.pcap", "# ")
        self.tester.send_expect(
            "tcpdump -A -nn -e -vv -w getPackageByTcpdump.pcap -i %s 2> /dev/null& "
            % (self.tester_iface0),
            "#",
        )
        time.sleep(2)
        out1 = self.fdirprocess.send_pkt_get_out(pkt)
        out2 = self.pmd_output.execute_cmd("show port stats 0")
        out = out1 + out2
        self.tester.send_expect("killall tcpdump", "# ")
        tcpdump_out = self.tester.send_expect(
            "tcpdump -A -nn -vv -er getPackageByTcpdump.pcap", "# "
        )

        return (out, tcpdump_out)

    def check_packets(self, out, port_id, pkt_num=1, check_stats=True):
        p = "port (\d+)/queue.*"
        result_list = re.findall(p, out)
        self.verify(
            len(result_list) == pkt_num, "received packets mismatch".format(port_id)
        )
        for res in result_list:
            if check_stats:
                self.verify(
                    int(res) == port_id,
                    "port {} did not received the packets".format(port_id),
                )
            else:
                self.verify(
                    int(res) != port_id,
                    "port {} should not received a packets".format(port_id),
                )

    def _rte_flow_validate_pattern(self, test_vector):
        test_results = {}
        for test in test_vector:
            self.logger.info((GREEN("========test subcase: %s========" % test["name"])))
            try:
                port_id = test["check_param"]["port_id"]
                self.fdirprocess.validate_rule(test["rule"], check_stats=True)
                rule_list = self.fdirprocess.create_rule(test["rule"], check_stats=True)
                self.fdirprocess.check_rule(0, stats=True, rule_list=rule_list)
                # send matched packets and check
                matched_packets = test["scapy_str"]["matched"]
                out = self.fdirprocess.send_pkt_get_out(matched_packets)
                self.check_packets(out, port_id, len(matched_packets))
                # send mismatched packets and check
                mismatched_packets = test["scapy_str"]["mismatched"]
                out = self.fdirprocess.send_pkt_get_out(mismatched_packets)
                self.check_packets(
                    out, port_id, len(mismatched_packets), check_stats=False
                )
                self.fdirprocess.destroy_rule(0, rule_list)
                self.fdirprocess.check_rule(0, stats=False, rule_list=rule_list)
                out = self.fdirprocess.send_pkt_get_out(matched_packets)
                self.check_packets(
                    out, port_id, len(matched_packets), check_stats=False
                )
                test_results[test["name"]] = True
                self.logger.info((GREEN("subcase passed: %s" % test["name"])))
            except Exception as e:
                self.logger.warning((RED(e)))
                self.dut.send_command("flow flush 0")
                self.dut.send_command("flow flush 1")
                test_results[test["name"]] = False
                self.logger.info((RED("subcase failed: %s" % test["name"])))
                continue
        failed_cases = []
        for k, v in list(test_results.items()):
            if not v:
                failed_cases.append(k)
        self.verify(all(test_results.values()), "{} failed.".format(failed_cases))

    def test_dcf_mac_qinq_ipv4_pay(self):
        """
        Test case 01: DCF switch for MAC_QINQ_IPV4_PAY
        """
        self.setup_1pf_4vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_ipv4_pay)

    def test_dcf_mac_qinq_ipv6_pay(self):
        """
        Test case 02: DCF switch for MAC_QINQ_IPV6_PAY
        """
        self.setup_1pf_4vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_ipv6_pay)

    @skip_unsupported_pkg("os default")
    def test_dcf_mac_qinq_pppoe_pay(self):
        """
        Test case 03: DCF switch for MAC_QINQ_PPPOE_PAY
        """
        self.setup_1pf_4vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_pppoe_pay)

    @skip_unsupported_pkg("os default")
    def test_dcf_mac_qinq_pppoe_pay_proto(self):
        """
        Test case 04: DCF switch for MAC_QINQ_PPPOE_PAY_Proto
        """
        self.setup_1pf_4vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_pppoe_proto)

    @skip_unsupported_pkg("os default")
    def test_dcf_mac_qinq_pppoe_ipv4(self):
        """
        Test case 05: DCF switch for MAC_QINQ_PPPOE_IPV4
        """
        self.setup_1pf_4vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_pppoe_ipv4)

    @skip_unsupported_pkg("os default")
    def test_dcf_mac_qinq_pppoe_ipv6(self):
        """
        Test case 06: DCF switch for MAC_QINQ_PPPOE_IPV6
        """
        self.setup_1pf_4vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_pppoe_ipv6)

    def test_dcf_mac_l4_qinq_non_pipeline_mode(self):
        """
        Test case 07: DCF switch for MAC_L4_QINQ
        """
        self.setup_1pf_4vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(tvs_mac_l4_qinq_dcf_non_pipeline_mode)

    def test_dcf_mac_l4_qinq_pipeline_mode(self):
        """
        Test case 08: DCF switch for MAC_L4_QINQ_IPV6
        """
        self.setup_1pf_4vfs_env()
        self.launch_testpmd(pipline_mode=True)
        self._rte_flow_validate_pattern(tvs_mac_l4_qinq_dcf_pipeline_mode)

    def send_packet_check_vlan_strip(self, pkts, outer=False, inner=False):
        for pkt in pkts:
            pkt_index = pkts.index(pkt)
            out, tcpdump_out = self.tcpdump_send_packet_get_output(pkt)
            self.check_packets(out, port_id=2, pkt_num=1)
            vlan_list = re.findall("vlan\s+\d+", tcpdump_out)
            if pkt_index == 1:
                vlan_num = 2
                if outer or inner:
                    vlan_num -= 1
                self.verify(len(vlan_list) == vlan_num, "received outer vlan packet!!!")
            else:
                vlan_num = 4
                if inner and outer:
                    vlan_num -= 2
                elif outer:
                    vlan_num -= 1
                self.verify(
                    len(vlan_list) == vlan_num, "received outer vlan packet error!!!"
                )

    def test_dcf_vlan_strip_in_pvid_enable(self):
        """
        Test case 09: DCF vlan strip when pvid enable
        """
        pkts = [
            'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)'
            % self.vf1_mac,
            'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=21,type=0x0800)/IP(src="196.222.232.221")/("X"*480)'
            % self.vf1_mac,
        ]
        self.setup_1pf_4vfs_env()
        self.launch_testpmd()
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set strip on 1")
        self.reset_vf()
        self.send_packet_check_vlan_strip(pkts, outer=True)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set strip off 1")
        self.reset_vf()
        self.send_packet_check_vlan_strip(pkts)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set strip on 1")
        self.reset_vf()
        self.pmd_output.execute_cmd("vlan set strip on 2")
        self.send_packet_check_vlan_strip(pkts, outer=True, inner=True)
        self.pmd_output.execute_cmd("quit", "#")
        self.launch_testpmd()
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set strip on 2")
        self.pmd_output.execute_cmd("vlan set strip on 1")
        self.reset_vf()
        self.send_packet_check_vlan_strip(pkts, outer=True, inner=True)

    def send_packet_check_vlan_inter(
        self, pkts, out_vlan, port_id=3, vlan_header=None, iner_vlan=None
    ):
        for pkt in pkts:
            pkt_index = pkts.index(pkt)
            out, tcpdump_out = self.tcpdump_send_packet_get_output(pkt)
            self.check_packets(out, port_id)
            p = "vlan\s+(\d+)"
            vlan_list = re.findall(p, tcpdump_out)
            if vlan_header:
                header = re.findall(vlan_header, tcpdump_out)
            if pkt_index == 0:
                if out_vlan == 1:
                    self.verify(
                        len(vlan_list) == 1,
                        "received packet outer vlan not is %s" % out_vlan,
                    )
                elif out_vlan == 0:
                    self.verify(
                        len(vlan_list) == 0,
                        "received packet outer vlan not is %s" % out_vlan,
                    )
                else:
                    self.verify(
                        int(vlan_list[0]) == out_vlan,
                        "received packet outer vlan not is %s" % out_vlan,
                    )
                if iner_vlan:
                    self.verify(
                        int(vlan_list[1]) == iner_vlan,
                        "received packet outer vlan not is %s" % iner_vlan,
                    )
            else:
                if out_vlan == 1:
                    self.verify(
                        len(vlan_list) == 3 and int(vlan_list[1]) == out_vlan,
                        "received packet outer vlan not is %s" % out_vlan,
                    )
                elif out_vlan == 0:
                    self.verify(
                        len(vlan_list) == 2,
                        "received packet outer vlan not is %s" % out_vlan,
                    )
                else:
                    self.verify(
                        int(vlan_list[1]) == out_vlan,
                        "received packet outer vlan not is %s" % out_vlan,
                    )
                if iner_vlan:
                    self.verify(
                        int(vlan_list[2]) == iner_vlan,
                        "received packet outer vlan not is %s" % iner_vlan,
                    )
            if vlan_header == "0x8100":
                self.verify(
                    vlan_header in tcpdump_out,
                    "vlan header not matched, expect: %s." % vlan_header,
                )
            elif vlan_header is None:
                pass
            else:
                self.verify(
                    len(header) == 1,
                    "vlan header not matched, expect: %s." % vlan_header,
                )

    def test_dcf_vlan_insert_in_pvid_enable(self):
        """
        Test case 10: DCF vlan insertion when pvid enable
        """
        out_vlan = 24
        iner_vlan = 11
        header = "0x8100"
        pkt_list = [
            'Ether(dst="%s",type=0x0800)/IP(src="196.222.232.221")/("X"*480)'
            % self.vf2_mac,
            'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)'
            % self.vf2_mac,
        ]
        self.setup_1pf_4vfs_env()
        self.launch_testpmd()
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("tx_vlan set pvid 1 %d on" % out_vlan)
        self.reset_vf()
        self.send_packet_check_vlan_inter(pkt_list, out_vlan, vlan_header=header)
        header = "0x88a8"
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set outer tpid %s 1" % header)
        self.reset_vf()
        self.send_packet_check_vlan_inter(pkt_list, out_vlan, vlan_header=header)
        header = "0x9100"
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set outer tpid %s 1" % header)
        self.reset_vf()
        self.send_packet_check_vlan_inter(pkt_list, out_vlan, vlan_header=header)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop 2")
        self.pmd_output.execute_cmd("tx_vlan set 2 %d" % iner_vlan)
        self.pmd_output.execute_cmd("port start 2")
        self.pmd_output.execute_cmd("start")
        self.send_packet_check_vlan_inter(
            pkt_list, out_vlan, vlan_header=header, iner_vlan=iner_vlan
        )
        self.pmd_output.execute_cmd("quit", "# ")
        self.launch_testpmd()
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop 2")
        self.pmd_output.execute_cmd("tx_vlan set 2 %d" % iner_vlan)
        self.pmd_output.execute_cmd("port start 2")
        self.pmd_output.execute_cmd("tx_vlan set pvid 1 %d on" % out_vlan)
        self.reset_vf()
        self.send_packet_check_vlan_inter(
            pkt_list, out_vlan, port_id=3, vlan_header=header, iner_vlan=iner_vlan
        )

    def test_dcf_vlan_filter_in_pvid_enable(self):
        """
        Test case 11: DCF vlan filter when pvid enable
        """
        pkt_list1 = [
            'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=11,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)'
            % self.vf1_mac,
            'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=11,type=0x0800)/IP(src="196.222.232.221")/("X"*480)'
            % self.vf1_mac,
        ]
        pkt_list2 = [
            'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=21,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)'
            % self.vf1_mac,
            'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=21,type=0x0800)/IP(src="196.222.232.221")/("X"*480)'
            % self.vf1_mac,
        ]
        if self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s on" % (self.pf_interface, self.flag),
                "# ",
            )
        self.setup_1pf_4vfs_env()
        self.launch_testpmd()
        self.pmd_output.execute_cmd("vlan set filter on 1")
        out = self.pmd_output.execute_cmd("rx_vlan add 11 1")
        self.verify("failed" in out, "add rx_vlan successfully for VF1 by representor")
        self.pmd_output.execute_cmd("vlan set filter on 2")
        self.pmd_output.execute_cmd("rx_vlan add 11 2")
        for pkt in pkt_list1:
            out = self.fdirprocess.send_pkt_get_out(pkt)
            self.check_packets(out, 2)
        for pkt in pkt_list2:
            out = self.fdirprocess.send_pkt_get_out(pkt)
            self.check_packets(out, 2, pkt_num=0, check_stats=False)
        self.pmd_output.execute_cmd("rx_vlan rm 11 2")
        for pkt in pkt_list1:
            out = self.fdirprocess.send_pkt_get_out(pkt)
            self.check_packets(out, 2, pkt_num=0, check_stats=False)

    def tear_down(self):
        self.pmd_output.quit()
        self.dut.kill_all()
        self.destroy_iavf()

    def tear_down_all(self):
        if self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s %s"
                % (self.pf_interface, self.flag, self.default_stats),
                "# ",
            )
