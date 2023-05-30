# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import random
import re
import time
from multiprocessing import Manager, Process

import framework.utils as utils
import tests.rte_flow_common as rfc
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.utils import GREEN, RED

from .rte_flow_common import TXQ_RXQ_NUMBER

tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_control = {
    "name": "l2tpv2_seession_id_mac_ipv4_l2tpv2_control",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type control session_id is 0x1111 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_eth_l2_src_only_mac_ipv4_l2tpv2_control = {
    "name": "eth_l2_src_only_mac_ipv4_l2tpv2_control",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type control / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv4_l2tpv2_control = [
    tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_control,
    tv_eth_l2_src_only_mac_ipv4_l2tpv2_control,
]

tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_control = {
    "name": "l2tpv2_seession_id_mac_ipv6_l2tpv2_control",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type control session_id is 0x1111 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_eth_l2_src_only_mac_ipv6_l2tpv2_control = {
    "name": "eth_l2_src_only_mac_ipv6_l2tpv2_control",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type control / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv6_l2tpv2_control = [
    tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_control,
    tv_eth_l2_src_only_mac_ipv6_l2tpv2_control,
]

tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_data = {
    "name": "l2tpv2_seession_id_mac_ipv4_l2tpv2_data",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data session_id is 0x1111 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_eth_l2_src_only_mac_ipv4_l2tpv2_data = {
    "name": "eth_l2_src_only_mac_ipv4_l2tpv2_data",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type data / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_data_l = {
    "name": "l2tpv2_seession_id_mac_ipv4_l2tpv2_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l session_id is 0x1111 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_eth_l2_src_only_mac_ipv4_l2tpv2_data_l = {
    "name": "eth_l2_src_only_mac_ipv4_l2tpv2_data_l",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type data_l / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_data_s = {
    "name": "l2tpv2_seession_id_mac_ipv4_l2tpv2_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s session_id is 0x1111 / end actions passthru / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "passthru": 1},
}

tv_eth_l2_src_only_mac_ipv4_l2tpv2_data_s = {
    "name": "eth_l2_src_only_mac_ipv4_l2tpv2_data_s",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type data_s / end actions queue index 6 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 6},
}

tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_data_o = {
    "name": "l2tpv2_seession_id_mac_ipv4_l2tpv2_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o session_id is 0x1111 offset_size is 6 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

tv_eth_l2_src_only_mac_ipv4_l2tpv2_data_o = {
    "name": "eth_l2_src_only_mac_ipv4_l2tpv2_data_o",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type data_o offset_size is 6 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_data_l_s = {
    "name": "l2tpv2_seession_id_mac_ipv4_l2tpv2_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s session_id is 0x1111 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_eth_l2_src_only_mac_ipv4_l2tpv2_data_l_s = {
    "name": "eth_l2_src_only_mac_ipv4_l2tpv2_data_l_s",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type data_l_s / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

vectors_mac_ipv4_l2tpv2 = [
    tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_data,
    tv_eth_l2_src_only_mac_ipv4_l2tpv2_data,
    tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_data_l,
    tv_eth_l2_src_only_mac_ipv4_l2tpv2_data_l,
    tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_data_s,
    tv_eth_l2_src_only_mac_ipv4_l2tpv2_data_s,
    tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_data_o,
    tv_eth_l2_src_only_mac_ipv4_l2tpv2_data_o,
    tv_l2tpv2_seession_id_mac_ipv4_l2tpv2_data_l_s,
    tv_eth_l2_src_only_mac_ipv4_l2tpv2_data_l_s,
]

tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_data = {
    "name": "l2tpv2_seession_id_mac_ipv6_l2tpv2_data",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data session_id is 0x1111 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_eth_l2_src_only_mac_ipv6_l2tpv2_data = {
    "name": "eth_l2_src_only_mac_ipv6_l2tpv2_data",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type data / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_data_l = {
    "name": "l2tpv2_seession_id_mac_ipv6_l2tpv2_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l session_id is 0x1111 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_eth_l2_src_only_mac_ipv6_l2tpv2_data_l = {
    "name": "eth_l2_src_only_mac_ipv6_l2tpv2_data_l",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type data_l / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_data_s = {
    "name": "l2tpv2_seession_id_mac_ipv6_l2tpv2_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s session_id is 0x1111 / end actions mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1},
}

tv_eth_l2_src_only_mac_ipv6_l2tpv2_data_s = {
    "name": "eth_l2_src_only_mac_ipv6_l2tpv2_data_s",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type data_s / end actions queue index 6 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 6},
}

tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_data_o = {
    "name": "l2tpv2_seession_id_mac_ipv6_l2tpv2_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o session_id is 0x1111 offset_size is 6 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

tv_eth_l2_src_only_mac_ipv6_l2tpv2_data_o = {
    "name": "eth_l2_src_only_mac_ipv6_l2tpv2_data_o",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type data_o offset_size is 6 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_data_l_s = {
    "name": "l2tpv2_seession_id_mac_ipv6_l2tpv2_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s session_id is 0x1111 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_eth_l2_src_only_mac_ipv6_l2tpv2_data_l_s = {
    "name": "eth_l2_src_only_mac_ipv6_l2tpv2_data_l_s",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type data_l_s / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

vectors_mac_ipv6_l2tpv2 = [
    tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_data,
    tv_eth_l2_src_only_mac_ipv6_l2tpv2_data,
    tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_data_l,
    tv_eth_l2_src_only_mac_ipv6_l2tpv2_data_l,
    tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_data_s,
    tv_eth_l2_src_only_mac_ipv6_l2tpv2_data_s,
    tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_data_o,
    tv_eth_l2_src_only_mac_ipv6_l2tpv2_data_o,
    tv_l2tpv2_seession_id_mac_ipv6_l2tpv2_data_l_s,
    tv_eth_l2_src_only_mac_ipv6_l2tpv2_data_l_s,
]

tv_l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data = {
    "name": "l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data session_id is 0x1111 / ppp / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_eth_l2_src_only_mac_ipv4_pppol2tpv2_data = {
    "name": "eth_l2_src_only_mac_ipv4_pppol2tpv2_data",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type data / ppp / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_l = {
    "name": "l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l session_id is 0x1111 / ppp / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_eth_l2_src_only_mac_ipv4_pppol2tpv2_data_l = {
    "name": "eth_l2_src_only_mac_ipv4_pppol2tpv2_data_l",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type data_l / ppp / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_s = {
    "name": "l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s session_id is 0x1111 / ppp / end actions passthru / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "passthru": 1},
}

tv_eth_l2_src_only_mac_ipv4_pppol2tpv2_data_s = {
    "name": "eth_l2_src_only_mac_ipv4_pppol2tpv2_data_s",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type data_s / ppp / end actions queue index 6 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 6},
}

tv_l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_o = {
    "name": "l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o session_id is 0x1111 offset_size is 6 / ppp / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

tv_eth_l2_src_only_mac_ipv4_pppol2tpv2_data_o = {
    "name": "eth_l2_src_only_mac_ipv4_pppol2tpv2_data_o",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type data_o offset_size is 6 / ppp / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_l_s = {
    "name": "l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s session_id is 0x1111 / ppp / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_eth_l2_src_only_mac_ipv4_pppol2tpv2_data_l_s = {
    "name": "eth_l2_src_only_mac_ipv4_pppol2tpv2_data_l_s",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv4 / udp / l2tpv2 type data_l_s / ppp / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

vectors_mac_ipv4_pppol2tpv2 = [
    tv_l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data,
    tv_eth_l2_src_only_mac_ipv4_pppol2tpv2_data,
    tv_l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_l,
    tv_eth_l2_src_only_mac_ipv4_pppol2tpv2_data_l,
    tv_l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_s,
    tv_eth_l2_src_only_mac_ipv4_pppol2tpv2_data_s,
    tv_l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_o,
    tv_eth_l2_src_only_mac_ipv4_pppol2tpv2_data_o,
    tv_l2tpv2_seession_id_mac_ipv4_pppol2tpv2_data_l_s,
    tv_eth_l2_src_only_mac_ipv4_pppol2tpv2_data_l_s,
]

tv_l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data = {
    "name": "l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data session_id is 0x1111 / ppp / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_eth_l2_src_only_mac_ipv6_pppol2tpv2_data = {
    "name": "eth_l2_src_only_mac_ipv6_pppol2tpv2_data",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type data / ppp / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_l = {
    "name": "l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l session_id is 0x1111 / ppp / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_eth_l2_src_only_mac_ipv6_pppol2tpv2_data_l = {
    "name": "eth_l2_src_only_mac_ipv6_pppol2tpv2_data_l",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type data_l / ppp / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_s = {
    "name": "l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s session_id is 0x1111 / ppp / end actions mark id 1 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "mark_id": 1},
}

tv_eth_l2_src_only_mac_ipv6_pppol2tpv2_data_s = {
    "name": "eth_l2_src_only_mac_ipv6_pppol2tpv2_data_s",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type data_s / ppp / end actions queue index 6 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 6},
}

tv_l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_o = {
    "name": "l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o session_id is 0x1111 offset_size is 6 / ppp / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

tv_eth_l2_src_only_mac_ipv6_pppol2tpv2_data_o = {
    "name": "eth_l2_src_only_mac_ipv6_pppol2tpv2_data_o",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type data_o offset_size is 6 / ppp / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_l_s = {
    "name": "l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s session_id is 0x1111 / ppp / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_eth_l2_src_only_mac_ipv6_pppol2tpv2_data_l_s = {
    "name": "eth_l2_src_only_mac_ipv6_pppol2tpv2_data_l_s",
    "rule": "flow create 0 ingress pattern eth src is 00:00:00:00:00:01 / ipv6 / udp / l2tpv2 type data_l_s / ppp / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)/HDLC()/Raw(b"\\x00\\x00")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)/HDLC()/Raw(b"\\x00\\x00")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

vectors_mac_ipv6_pppol2tpv2 = [
    tv_l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data,
    tv_eth_l2_src_only_mac_ipv6_pppol2tpv2_data,
    tv_l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_l,
    tv_eth_l2_src_only_mac_ipv6_pppol2tpv2_data_l,
    tv_l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_s,
    tv_eth_l2_src_only_mac_ipv6_pppol2tpv2_data_s,
    tv_l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_o,
    tv_eth_l2_src_only_mac_ipv6_pppol2tpv2_data_o,
    tv_l2tpv2_seession_id_mac_ipv6_pppol2tpv2_data_l_s,
    tv_eth_l2_src_only_mac_ipv6_pppol2tpv2_data_l_s,
]

tv_ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data = {
    "name": "ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv4 src is 10.0.0.11 dst is 10.0.0.22 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10",dst="10.0.0.22")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.20")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_l = {
    "name": "ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv4 src is 10.0.0.11 dst is 10.0.0.22 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10",dst="10.0.0.22")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.20")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_s = {
    "name": "ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv4 src is 10.0.0.11 dst is 10.0.0.22 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10",dst="10.0.0.22")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.20")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_o = {
    "name": "ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv4 src is 10.0.0.11 dst is 10.0.0.22 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10",dst="10.0.0.22")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.20")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_l_s = {
    "name": "ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv4 src is 10.0.0.11 dst is 10.0.0.22 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10",dst="10.0.0.22")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.20")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv4_pppol2tpv2_ipv4_pay = [
    tv_ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data,
    tv_ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_l,
    tv_ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_s,
    tv_ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_o,
    tv_ipv4_mac_ipv4_pppol2tpv2_ipv4_pay_data_l_s,
]

tv_ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data = {
    "name": "ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv4 src is 10.0.0.11 / udp src is 11 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10")/UDP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_l = {
    "name": "ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv4 src is 10.0.0.11 / udp dst is 22 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_s = {
    "name": "ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv4 dst is 10.0.0.22 / udp src is 11 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.20")/UDP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_o = {
    "name": "ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv4 dst is 10.0.0.22 / udp dst is 22 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.20")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_l_s = {
    "name": "ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv4 src is 10.0.0.11 / udp dst is 22 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv4_pppol2tpv2_ipv4_udp_pay = [
    tv_ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data,
    tv_ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_l,
    tv_ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_s,
    tv_ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_o,
    tv_ipv4_udp_mac_ipv4_pppol2tpv2_ipv4_udp_pay_data_l_s,
]

tv_ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data = {
    "name": "ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv4 src is 10.0.0.11 / tcp src is 11 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10")/TCP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_l = {
    "name": "ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv4 src is 10.0.0.11 / tcp dst is 22 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10")/TCP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_s = {
    "name": "ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv4 dst is 10.0.0.22 / tcp src is 11 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.20")/TCP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_o = {
    "name": "ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv4 dst is 10.0.0.22 / tcp dst is 22 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.20")/TCP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_l_s = {
    "name": "ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv4 src is 10.0.0.11 / tcp dst is 22 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10")/TCP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv4_pppol2tpv2_ipv4_tcp = [
    tv_ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data,
    tv_ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_l,
    tv_ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_s,
    tv_ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_o,
    tv_ipv4_tcp_mac_ipv4_pppol2tpv2_ipv4_tcp_data_l_s,
]

tv_ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data = {
    "name": "ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_l = {
    "name": "ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_s = {
    "name": "ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_o = {
    "name": "ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_l_s = {
    "name": "ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv4_pppol2tpv2_ipv6_pay = [
    tv_ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data,
    tv_ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_l,
    tv_ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_s,
    tv_ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_o,
    tv_ipv6_mac_ipv4_pppol2tpv2_ipv6_pay_data_l_s,
]

tv_ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data = {
    "name": "ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 11 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_l = {
    "name": "ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 / udp dst is 22 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_s = {
    "name": "ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 11 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_o = {
    "name": "ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 / udp dst is 22 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_l_s = {
    "name": "ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp dst is 22 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv4_pppol2tpv2_ipv6_udp_pay = [
    tv_ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data,
    tv_ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_l,
    tv_ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_s,
    tv_ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_o,
    tv_ipv6_udp_mac_ipv4_pppol2tpv2_ipv6_udp_pay_data_l_s,
]

tv_ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data = {
    "name": "ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data / ppp / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 11 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_l = {
    "name": "ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 / tcp dst is 22 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920")/TCP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_s = {
    "name": "ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 11 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_o = {
    "name": "ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 / tcp dst is 22 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920")/TCP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_l_s = {
    "name": "ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 / tcp src is 11 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920")/TCP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv4_pppol2tpv2_ipv6_tcp = [
    tv_ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data,
    tv_ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_l,
    tv_ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_s,
    tv_ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_o,
    tv_ipv6_tcp_mac_ipv4_pppol2tpv2_ipv6_tcp_data_l_s,
]

tv_ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data = {
    "name": "ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv4 src is 10.0.0.11 dst is 10.0.0.22 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10",dst="10.0.0.22")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.20")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_l = {
    "name": "ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv4 src is 10.0.0.11 dst is 10.0.0.22 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10",dst="10.0.0.22")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.20")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=32)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_s = {
    "name": "ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv4 src is 10.0.0.11 dst is 10.0.0.22 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10",dst="10.0.0.22")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.20")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_o = {
    "name": "ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv4 src is 10.0.0.11 dst is 10.0.0.22 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10",dst="10.0.0.22")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.20")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_l_s = {
    "name": "ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv4 src is 10.0.0.11 dst is 10.0.0.22 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10",dst="10.0.0.22")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.20")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=36)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11",dst="10.0.0.22")',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv6_pppol2tpv2_ipv4_pay = [
    tv_ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data,
    tv_ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_l,
    tv_ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_s,
    tv_ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_o,
    tv_ipv4_mac_ipv6_pppol2tpv2_ipv4_pay_data_l_s,
]

tv_ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data = {
    "name": "ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv4 src is 10.0.0.11 / udp dst is 22 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_l = {
    "name": "ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv4 dst is 10.0.0.22 / udp src is 11 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.20")/UDP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=40)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_s = {
    "name": "ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv4 src is 10.0.0.11 / udp dst is 22 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_o = {
    "name": "ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv4 dst is 10.0.0.22 / udp src is 11 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.20")/UDP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_l_s = {
    "name": "ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv4 dst is 10.0.0.22 / udp dst is 22 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.20")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=44)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv6_pppol2tpv2_ipv4_udp_pay = [
    tv_ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data,
    tv_ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_l,
    tv_ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_s,
    tv_ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_o,
    tv_ipv4_udp_mac_ipv6_pppol2tpv2_ipv4_udp_pay_data_l_s,
]

tv_ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data = {
    "name": "ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv4 src is 10.0.0.11 / tcp dst is 22 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10")/TCP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_l = {
    "name": "ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv4 dst is 10.0.0.22 / tcp src is 11 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.20")/TCP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_s = {
    "name": "ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv4 src is 10.0.0.11 / tcp dst is 22 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.10")/TCP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x21")/IP(src="10.0.0.11")/TCP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_o = {
    "name": "ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv4 dst is 10.0.0.22 / tcp src is 11 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.20")/TCP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_l_s = {
    "name": "ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv4 dst is 10.0.0.22 / tcp dst is 22 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.20")/TCP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x21")/IP(dst="10.0.0.22")/TCP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv6_pppol2tpv2_ipv4_tcp = [
    tv_ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data,
    tv_ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_l,
    tv_ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_s,
    tv_ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_o,
    tv_ipv4_tcp_mac_ipv6_pppol2tpv2_ipv4_tcp_data_l_s,
]

tv_ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data = {
    "name": "ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_l = {
    "name": "ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=52)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_s = {
    "name": "ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_o = {
    "name": "ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_l_s = {
    "name": "ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=56)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv6_pppol2tpv2_ipv6_pay = [
    tv_ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data,
    tv_ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_l,
    tv_ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_s,
    tv_ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_o,
    tv_ipv6_mac_ipv6_pppol2tpv2_ipv6_pay_data_l_s,
]

tv_ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data = {
    "name": "ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 11 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_l = {
    "name": "ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 / udp dst is 22 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_s = {
    "name": "ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 11 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_o = {
    "name": "ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 / udp dst is 22 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_l_s = {
    "name": "ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp dst is 22 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=64)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv6_pppol2tpv2_ipv6_udp_pay = [
    tv_ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data,
    tv_ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_l,
    tv_ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_s,
    tv_ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_o,
    tv_ipv6_udp_mac_ipv6_pppol2tpv2_ipv6_udp_pay_data_l_s,
]

tv_ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data = {
    "name": "ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data / ppp / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 11 / end actions queue index 3 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x000)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 3},
}

tv_ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_l = {
    "name": "ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_l",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 / tcp dst is 22 / end actions queue index 5 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920")/TCP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=60)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 5},
}

tv_ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_s = {
    "name": "ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 11 / end actions rss queues 2 3 end / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x080)/HDLC()/Raw(b"\\x00\\x57")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "queue": [2, 3]},
}

tv_ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_o = {
    "name": "ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_o",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o offset_size is 6 / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 / tcp dst is 22 / end actions queue index 2 / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=20)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920")/TCP(dport=22)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x020,offset=6)/Raw(b"\\x00\\x00\\x00\\x00")/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(dport=22)',
        ],
    },
    "check_param": {"port_id": 0, "queue": 2},
}

tv_ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_l_s = {
    "name": "ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_l_s",
    "rule": "flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / ipv6 src is ABAB:910B:6666:3457:8295:3333:1800:2929 / tcp src is 11 / end actions drop / end",
    "scapy_str": {
        "match": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=11)',
            'Ether(src="00:00:00:00:00:01")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=11)',
        ],
        "mismatch": [
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=10)',
            'Ether(src="11:22:33:44:55:77")/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2920")/TCP(sport=11)',
            'Ether(src="11:22:33:44:55:77")/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=76)/HDLC()/Raw(b"\\x00\\x57")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=11)',
        ],
    },
    "check_param": {"port_id": 0, "drop": 1},
}

vectors_mac_ipv6_pppol2tpv2_ipv6_tcp = [
    tv_ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data,
    tv_ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_l,
    tv_ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_s,
    tv_ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_o,
    tv_ipv6_tcp_mac_ipv6_pppol2tpv2_ipv6_tcp_data_l_s,
]


class TestICEIavfFDIRPPPoL2TPv2oUDP(TestCase):
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
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.pci0 = self.dut.ports_info[self.dut_ports[0]]["pci"]
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
        self.rxq = 16

    def set_up(self):
        """
        Run before each test case.
        """
        self.pmd_output.execute_cmd("start")

    def launch_testpmd(self, symmetric=False):
        param = "--rxq=16 --txq=16"
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

    def send_packets(self, packets, pf_id=0, count=1):
        self.pkt.update_pkt(packets)
        tx_port = self.tester_iface0
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
                all(rule_list),
                "some rules validate failed, result %s" % rule_list,
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
                all(rule_list),
                "some rules create failed, result %s" % rule_list,
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

    def destroy_vf(self):
        self.dut.send_expect("quit", "# ", 60)
        time.sleep(2)
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])

    def test_mac_ipv4_l2tpv2_control(self):
        self.rte_flow_process(vectors_mac_ipv4_l2tpv2_control)

    def test_mac_ipv6_l2tpv2_control(self):
        self.rte_flow_process(vectors_mac_ipv6_l2tpv2_control)

    def test_mac_ipv4_l2tpv2(self):
        self.rte_flow_process(vectors_mac_ipv4_l2tpv2)

    def test_mac_ipv6_l2tpv2(self):
        self.rte_flow_process(vectors_mac_ipv6_l2tpv2)

    def test_mac_ipv4_pppol2tpv2(self):
        self.rte_flow_process(vectors_mac_ipv4_pppol2tpv2)

    def test_mac_ipv6_pppol2tpv2(self):
        self.rte_flow_process(vectors_mac_ipv6_pppol2tpv2)

    def test_mac_ipv4_pppol2tpv2_ipv4_pay(self):
        self.rte_flow_process(vectors_mac_ipv4_pppol2tpv2_ipv4_pay)

    def test_mac_ipv4_pppol2tpv2_ipv4_udp_pay(self):
        self.rte_flow_process(vectors_mac_ipv4_pppol2tpv2_ipv4_udp_pay)

    def test_mac_ipv4_pppol2tpv2_ipv4_tcp(self):
        self.rte_flow_process(vectors_mac_ipv4_pppol2tpv2_ipv4_tcp)

    def test_mac_ipv4_pppol2tpv2_ipv6_pay(self):
        self.rte_flow_process(vectors_mac_ipv4_pppol2tpv2_ipv6_pay)

    def test_mac_ipv4_pppol2tpv2_ipv6_udp_pay(self):
        self.rte_flow_process(vectors_mac_ipv4_pppol2tpv2_ipv6_udp_pay)

    def test_mac_ipv4_pppol2tpv2_ipv6_tcp(self):
        self.rte_flow_process(vectors_mac_ipv4_pppol2tpv2_ipv6_tcp)

    def test_mac_ipv6_pppol2tpv2_ipv4_pay(self):
        self.rte_flow_process(vectors_mac_ipv6_pppol2tpv2_ipv4_pay)

    def test_mac_ipv6_pppol2tpv2_ipv4_udp_pay(self):
        self.rte_flow_process(vectors_mac_ipv6_pppol2tpv2_ipv4_udp_pay)

    def test_mac_ipv6_pppol2tpv2_ipv4_tcp(self):
        self.rte_flow_process(vectors_mac_ipv6_pppol2tpv2_ipv4_tcp)

    def test_mac_ipv6_pppol2tpv2_ipv6_pay(self):
        self.rte_flow_process(vectors_mac_ipv6_pppol2tpv2_ipv6_pay)

    def test_mac_ipv6_pppol2tpv2_ipv6_udp_pay(self):
        self.rte_flow_process(vectors_mac_ipv6_pppol2tpv2_ipv6_udp_pay)

    def test_mac_ipv6_pppol2tpv2_ipv6_tcp(self):
        self.rte_flow_process(vectors_mac_ipv6_pppol2tpv2_ipv6_tcp)

    def tear_down(self):
        # destroy all flow rule on port 0
        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")

    def tear_down_all(self):
        self.destroy_vf()
        self.dut.kill_all()
