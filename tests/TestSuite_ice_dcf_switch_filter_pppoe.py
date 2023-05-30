# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

import copy
import json
import os
import re
import time

import tests.rte_flow_common as rfc
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, check_supported_nic, skip_unsupported_pkg
from framework.utils import BLUE, GREEN, RED

tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id = {
    "name": "tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id",
    "rte_flow_pattern": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id = {
    "name": "tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id",
    "rte_flow_pattern": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv4_pay_session_id_proto_id = {
    "name": "tv_mac_pppoe_ipv4_pay_session_id_proto_id",
    "rte_flow_pattern": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv6_pay_session_id_proto_id = {
    "name": "tv_mac_pppoe_ipv6_pay_session_id_proto_id",
    "rte_flow_pattern": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv4_pay_ip_address = {
    "name": "tv_mac_pppoe_ipv4_pay_ip_address",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv4_udp_pay = {
    "name": "tv_mac_pppoe_ipv4_udp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port = {
    "name": "tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv4_tcp_pay = {
    "name": "tv_mac_pppoe_ipv4_tcp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port = {
    "name": "tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv6_pay_ip_address = {
    "name": "tv_mac_pppoe_ipv6_pay_ip_address",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv6_udp_pay = {
    "name": "tv_mac_pppoe_ipv6_udp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port = {
    "name": "tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv6_tcp_pay = {
    "name": "tv_mac_pppoe_ipv6_tcp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port = {
    "name": "tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv4_pay_ip_address = {
    "name": "tv_mac_vlan_pppoe_ipv4_pay_ip_address",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv4_udp_pay = {
    "name": "tv_mac_vlan_pppoe_ipv4_udp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port = {
    "name": "tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv4_tcp_pay = {
    "name": "tv_mac_vlan_pppoe_ipv4_tcp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port = {
    "name": "tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv6_pay_ip_address = {
    "name": "tv_mac_vlan_pppoe_ipv6_pay_ip_address",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv6_udp_pay = {
    "name": "tv_mac_vlan_pppoe_ipv6_udp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port = {
    "name": "tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv6_tcp_pay = {
    "name": "tv_mac_vlan_pppoe_ipv6_tcp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port = {
    "name": "tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_lcp_pay = {
    "name": "tv_mac_pppoe_lcp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_pppoe_ipcp_pay = {
    "name": "tv_mac_pppoe_ipcp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_lcp_pay = {
    "name": "tv_mac_vlan_pppoe_lcp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_vlan_pppoe_ipcp_pay = {
    "name": "tv_mac_vlan_pppoe_ipcp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions represented_port ethdev_port_id 1 / end",
    "matched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
            'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        ],
        "check_func": {
            "func": rfc.check_vf_rx_packets_number,
            "param": {"expect_port": 2, "expect_queues": "null"},
        },
        "expect_results": {"expect_pkts": 0},
    },
}


class TestICEDCFSwitchFilterPPPOE(TestCase):
    supported_nic = [
        "ICE_100G-E810C_QSFP",
        "ICE_25G-E810C_SFP",
        "ICE_25G-E810_XXV_SFP",
        "ICE_25G-E823C_QSFP",
    ]

    def bind_nics_driver(self, ports, driver=""):
        # modprobe vfio driver
        if driver == "vfio-pci":
            for port in ports:
                netdev = self.dut.ports_info[port]["port"]
                driver = netdev.get_nic_driver()
                if driver != "vfio-pci":
                    netdev.bind_driver(driver="vfio-pci")

        elif driver == "igb_uio":
            # igb_uio should insmod as default, no need to check
            for port in ports:
                netdev = self.dut.ports_info[port]["port"]
                driver = netdev.get_nic_driver()
                if driver != "igb_uio":
                    netdev.bind_driver(driver="igb_uio")
        else:
            for port in ports:
                netdev = self.dut.ports_info[port]["port"]
                driver_now = netdev.get_nic_driver()
                if driver == "":
                    driver = netdev.default_driver
                if driver != driver_now:
                    netdev.bind_driver(driver=driver)

    @check_supported_nic(supported_nic)
    @skip_unsupported_pkg(["os default", "wireless"])
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.used_dut_port_0 = self.dut_ports[0]
        self.pf0_intf = self.dut.ports_info[self.used_dut_port_0]["intf"]
        self.__tx_iface = self.tester.get_interface(localPort)
        self.pkt = Packet()
        self.testpmd_status = "close"
        # bind pf to kernel
        self.bind_nics_driver(self.dut_ports, driver="ice")

        # get priv-flags default stats
        self.flag = "vf-vlan-pruning"
        self.default_stats = self.dut.get_priv_flags_state(self.pf0_intf, self.flag)

        # set vf driver
        self.vf_driver = "vfio-pci"
        self.dut.send_expect("modprobe vfio-pci", "#")
        self.path = self.dut.apps_name["test-pmd"]

    def setup_1pf_vfs_env(self, pf_port=0, driver="default"):

        self.used_dut_port_0 = self.dut_ports[pf_port]
        # get PF interface name
        self.pf0_intf = self.dut.ports_info[self.used_dut_port_0]["intf"]
        out = self.dut.send_expect("ethtool -i %s" % self.pf0_intf, "#")
        if self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s off" % (self.pf0_intf, self.flag), "# "
            )
        # generate 4 VFs on PF
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 4, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        # set VF0 as trust
        self.dut.send_expect("ip link set %s vf 0 trust on" % self.pf0_intf, "#")
        # bind VFs to dpdk driver
        for port in self.sriov_vfs_port_0:
            port.bind_driver(self.vf_driver)
        time.sleep(5)

    def reload_ice(self):
        self.dut.send_expect("rmmod ice && modprobe ice", "# ", 60)

    def set_up(self):
        """
        Run before each test case.
        """
        self.reload_ice()

    def create_testpmd_command(self):
        """
        Create testpmd command
        """
        # Prepare testpmd EAL and parameters
        vf0_pci = self.sriov_vfs_port_0[0].pci
        vf1_pci = self.sriov_vfs_port_0[1].pci
        all_eal_param = self.dut.create_eal_parameters(
            cores="1S/4C/1T",
            ports=[vf0_pci, vf1_pci],
            port_options={vf0_pci: "cap=dcf,representor=[1]"},
        )
        command = self.path + all_eal_param + " -- -i"
        return command

    def launch_testpmd(self):
        """
        launch testpmd with the command
        """
        command = self.create_testpmd_command()
        out = self.dut.send_expect(command, "testpmd> ", 30)
        self.testpmd_status = "running"
        self.dut.send_expect("set portlist 2", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)

    def send_packets(self, dic, session_name="", tx_iface=""):
        """
        send packets.
        """
        if session_name == "":
            session_name = self.dut
        if tx_iface == "":
            tx_iface = self.__tx_iface
        session_name.send_expect("start", "testpmd> ", 15)
        time.sleep(2)
        # send packets
        self.pkt.update_pkt(dic["scapy_str"])
        self.pkt.send_pkt(self.tester, tx_port=tx_iface, count=1, timeout=370)
        time.sleep(3)
        out = session_name.send_expect("stop", "testpmd> ")
        return out

    def send_and_check_packets(self, dic, session_name="", tx_iface=""):
        """
        general packets processing workflow.
        """
        if session_name == "":
            session_name = self.dut
        if tx_iface == "":
            tx_iface = self.__tx_iface
        session_name.send_expect("start", "testpmd> ", 15)
        time.sleep(2)
        # send packets
        self.pkt.update_pkt(dic["scapy_str"])
        self.pkt.send_pkt(self.tester, tx_port=tx_iface, count=1, timeout=370)
        time.sleep(3)
        out = session_name.send_expect("stop", "testpmd> ", 15)
        dic["check_func"]["func"](
            out, dic["check_func"]["param"], dic["expect_results"]
        )

    def send_and_get_packets_bg(self, dic, session_name="", tx_iface=""):
        """
        general packets processing workflow.
        """
        if session_name == "":
            session_name = self.dut
        if tx_iface == "":
            tx_iface = self.__tx_iface
        session_name.send_expect("start", "testpmd> ", 15)
        time.sleep(2)
        # send packets
        pkt = Packet()
        pkt.update_pkt(dic["scapy_str"])
        pkt.send_pkt_bg(self.tester, tx_port=tx_iface, count=1, loop=0, timeout=370)
        time.sleep(3)
        out = session_name.send_expect("stop", "testpmd> ", 15)
        results = dic["check_func"]["func"](
            out, dic["check_func"]["param"], dic["expect_results"], False
        )
        return results

    def validate_switch_filter_rule(
        self, rte_flow_pattern, session_name="", check_stats=True
    ):
        """
        validate switch filter rules
        """
        if session_name == "":
            session_name = self.dut
        p = "Flow rule validated"
        rule_list = []
        if isinstance(rte_flow_pattern, list):
            for rule in rte_flow_pattern:
                length = len(rule)
                rule_rep = rule[0:5] + "validate" + rule[11:length]
                out = session_name.send_expect(rule_rep, "testpmd> ")  # validate a rule
                if (p in out) and ("Failed" not in out):
                    rule_list.append(True)
                else:
                    rule_list.append(False)
        elif isinstance(rte_flow_pattern, str):
            length = len(rte_flow_pattern)
            rule_rep = rte_flow_pattern[0:5] + "validate" + rte_flow_pattern[11:length]
            out = session_name.send_expect(rule_rep, "testpmd> ")  # validate a rule
            if (p in out) and ("Failed" not in out):
                rule_list.append(True)
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            self.verify(
                all(rule_list),
                "some rules not validated successfully, result %s, rule %s"
                % (rule_list, rte_flow_pattern),
            )
        else:
            self.verify(
                not any(rule_list),
                "all rules should not validate successfully, result %s, rule %s"
                % (rule_list, rte_flow_pattern),
            )

    def create_switch_filter_rule(
        self, rte_flow_pattern, session_name="", check_stats=True
    ):
        """
        create switch filter rules
        """
        if session_name == "":
            session_name = self.dut
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        if isinstance(rte_flow_pattern, list):
            for rule in rte_flow_pattern:
                out = session_name.send_expect(rule, "testpmd> ")  # create a rule
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        else:
            out = session_name.send_expect(
                rte_flow_pattern, "testpmd> "
            )  # create a rule
            m = p.search(out)
            if m:
                rule_list.append(m.group(1))
            else:
                rule_list.append(False)
        if check_stats:
            self.verify(
                all(rule_list),
                "some rules not created successfully, result %s, rule %s"
                % (rule_list, rte_flow_pattern),
            )
        else:
            self.verify(
                not any(rule_list),
                "all rules should create failed, result %s" % rule_list,
            )
        return rule_list

    def check_switch_filter_rule_list(
        self, port_id, rule_list, session_name="", need_verify=True
    ):
        """
        check the rules in list identical to ones in rule_list
        """
        if session_name == "":
            session_name = self.dut
        out = session_name.send_expect("flow list %d" % port_id, "testpmd> ", 15)
        p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
        m = p.search(out)
        if not m:
            result = []
        else:
            p_spec = re.compile("^(\d+)\s")
            out_lines = out.splitlines()
            res = filter(bool, map(p_spec.match, out_lines))
            result = [i.group(1) for i in res]
        if need_verify:
            self.verify(
                result == rule_list,
                "the rule list is not the same. expect %s, result %s"
                % (rule_list, result),
            )
        else:
            return result

    def destroy_switch_filter_rule(
        self, port_id, rule_list, session_name="", need_verify=True
    ):
        if session_name == "":
            session_name = self.dut
        p = re.compile(r"Flow rule #(\d+) destroyed")
        destroy_list = []
        if isinstance(rule_list, list):
            for i in rule_list:
                out = session_name.send_expect(
                    "flow destroy %s rule %s" % (port_id, i), "testpmd> ", 15
                )
                m = p.search(out)
                if m:
                    destroy_list.append(m.group(1))
                else:
                    destroy_list.append(False)
        else:
            out = session_name.send_expect(
                "flow destroy %s rule %s" % (port_id, rule_list), "testpmd> ", 15
            )
            m = p.search(out)
            if m:
                destroy_list.append(m.group(1))
            else:
                destroy_list.append(False)
            rule_list = [rule_list]
        if need_verify:
            self.verify(
                destroy_list == rule_list,
                "flow rule destroy failed, expect %s result %s"
                % (rule_list, destroy_list),
            )
        else:
            return destroy_list

    def get_kernel_vf_log(self, vf_intfs, session_name):
        """
        get the log of each kernel vf in list vf_intfs
        """
        out_vfs = []
        for intf in vf_intfs:
            out = session_name.send_expect("ifconfig %s" % intf, "#")
            out_vfs.append(out)
        return out_vfs

    def _rte_flow_validate_pattern(self, test_vector, launch_testpmd=True):

        if launch_testpmd:
            # launch testpmd
            self.launch_testpmd()
        # validate a rule
        self.validate_switch_filter_rule(test_vector["rte_flow_pattern"])
        # create a rule
        rule_list = self.create_switch_filter_rule(
            test_vector["rte_flow_pattern"]
        )  # create a rule
        self.check_switch_filter_rule_list(0, rule_list)
        # send matched packets and check
        matched_dic = test_vector["matched"]
        self.send_and_check_packets(matched_dic)
        # send mismatched packets and check
        mismatched_dic = test_vector["mismatched"]
        self.send_and_check_packets(mismatched_dic)
        # destroy rule and send matched packets
        self.destroy_switch_filter_rule(0, rule_list)
        self.check_switch_filter_rule_list(0, [])
        # send matched packets and check
        destroy_dict = copy.deepcopy(matched_dic)
        if isinstance(destroy_dict["expect_results"]["expect_pkts"], list):
            destroy_dict["expect_results"]["expect_pkts"] = [0] * len(
                destroy_dict["expect_results"]["expect_pkts"]
            )
        else:
            destroy_dict["expect_results"]["expect_pkts"] = 0
        self.send_and_check_packets(destroy_dict)

    def test_mac_vlan_pppoe_ipv4_pay_session_id_proto_id(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id)

    def test_mac_vlan_pppoe_ipv6_pay_session_id_proto_id(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id)

    def test_mac_pppoe_ipv4_pay_session_id_proto_id(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_pay_session_id_proto_id)

    def test_mac_pppoe_ipv6_pay_session_id_proto_id(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_pay_session_id_proto_id)

    def test_mac_pppoe_ipv4_pay_ip_address(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_pay_ip_address)

    def test_mac_pppoe_ipv4_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_udp_pay)

    def test_mac_pppoe_ipv4_udp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port)

    def test_mac_pppoe_ipv4_tcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_tcp_pay)

    def test_mac_pppoe_ipv4_tcp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port)

    def test_mac_pppoe_ipv6_pay_ip_address(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_pay_ip_address)

    def test_mac_pppoe_ipv6_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_udp_pay)

    def test_mac_pppoe_ipv6_udp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port)

    def test_mac_pppoe_ipv6_tcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_tcp_pay)

    def test_mac_pppoe_ipv6_tcp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port)

    def test_mac_vlan_pppoe_ipv4_pay_ip_address(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_pay_ip_address)

    def test_mac_vlan_pppoe_ipv4_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_udp_pay)

    def test_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port)

    def test_mac_vlan_pppoe_ipv4_tcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_tcp_pay)

    def test_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port)

    def test_mac_vlan_pppoe_ipv6_pay_ip_address(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_pay_ip_address)

    def test_mac_vlan_pppoe_ipv6_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_udp_pay)

    def test_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port)

    def test_mac_vlan_pppoe_ipv6_tcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_tcp_pay)

    def test_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port)

    def test_mac_pppoe_lcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_lcp_pay)

    def test_mac_pppoe_ipcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipcp_pay)

    def test_mac_vlan_pppoe_lcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_lcp_pay)

    def test_mac_vlan_pppoe_ipcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipcp_pay)

    def tear_down(self):
        """
        Run after each test case.
        """
        if self.testpmd_status != "close":
            # destroy all flow rules on DCF
            self.dut.send_expect("flow flush 0", "testpmd> ", 15)
            self.dut.send_expect("clear port stats all", "testpmd> ", 15)
            self.dut.send_expect("quit", "#", 15)
            # destroy vfs
            for port_id in self.dut_ports:
                self.dut.destroy_sriov_vfs_by_port(port_id)
            self.testpmd_status = "close"
        if getattr(self, "session_secondary", None):
            self.dut.close_session(self.session_secondary)
        # kill all DPDK application
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        if self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s %s"
                % (self.pf0_intf, self.flag, self.default_stats),
                "# ",
            )
