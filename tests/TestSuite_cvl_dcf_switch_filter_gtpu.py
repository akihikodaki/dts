# BSD LICENSE
#
# Copyright(c) 2021 Intel Corporation. All rights reserved.
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

mac_ipv4_gtpu_basic = {
    "ipv4_gtpu": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/Raw("x" *20)',
    "ipv4_gtpu_eh_ipv4_nonfrag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/("X" *20)',
    "ipv4_gtpu_eh_ipv4_frag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(frag=6)/("X" *20)',
    "ipv4_gtpu_eh_ipv4_udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP()/("X" *20)',
    "ipv4_gtpu_eh_ipv4_tcp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP()/("X" *20)',
    "ipv4_gtpu_ipv4_nonfrag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/("X" *20)',
    "ipv4_gtpu_ipv4_frag": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP(frag=6)/("X" *20)',
    "ipv4_gtpu_ipv4_udp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP()/("X" *20)',
    "ipv4_gtpu_ipv4_tcp": 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/TCP()/("X" *20)',
}

tv_mac_ipv4_gtpu_teid_with_mask = {
    "name": "tv_mac_ipv4_gtpu_teid_with_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345677)"
            )
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_teid_without_mask = {
    "name": "tv_mac_ipv4_gtpu_teid_without_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"
            )
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_dst = {
    "name": "tv_mac_ipv4_gtpu_dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.1.2 / udp / gtpu / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace("IP()", 'IP(dst="192.168.1.2")')
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace("IP()", 'IP(dst="192.168.1.22")')
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_src = {
    "name": "tv_mac_ipv4_gtpu_src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 / udp / gtpu / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace("IP()", 'IP(src="192.168.1.1")')
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace("IP()", 'IP(src="192.168.1.11")')
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_src_dst = {
    "name": "tv_mac_ipv4_gtpu_src_dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / gtpu / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace(
                "IP()", 'IP(src="192.168.1.1", dst="192.168.1.2")'
            )
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace(
                "IP()", 'IP(src="192.168.1.11", dst="192.168.1.2")'
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace(
                "IP()", 'IP(src="192.168.1.1", dst="192.168.1.22")'
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu"].replace(
                "IP()", 'IP(src="192.168.1.11", dst="192.168.1.22")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_teid_dst = {
    "name": "tv_mac_ipv4_gtpu_teid_dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.1.2 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(dst="192.168.1.2")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345678)")
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(dst="192.168.1.22")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(dst="192.168.1.2")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(dst="192.168.1.22")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345677)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_teid_src = {
    "name": "tv_mac_ipv4_gtpu_teid_src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(src="192.168.1.1")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345678)")
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(src="192.168.1.11")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(src="192.168.1.1")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(src="192.168.1.11")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_all = {
    "name": "tv_mac_ipv4_gtpu_all",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(src="192.168.1.1", dst="192.168.1.2")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345678)")
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(src="192.168.1.11", dst="192.168.1.2")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(src="192.168.1.1", dst="192.168.1.22")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(src="192.168.1.11", dst="192.168.1.22")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu"]
            .replace("IP()", 'IP(src="192.168.1.11", dst="192.168.1.22")')
            .replace("GTP_U_Header()", "GTP_U_Header(teid=0x12345677)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

sv_mac_ipv4_gtpu = [
    tv_mac_ipv4_gtpu_teid_with_mask,
    tv_mac_ipv4_gtpu_teid_without_mask,
    tv_mac_ipv4_gtpu_dst,
    tv_mac_ipv4_gtpu_src,
    tv_mac_ipv4_gtpu_teid_dst,
    tv_mac_ipv4_gtpu_teid_src,
    tv_mac_ipv4_gtpu_all,
]

# the maximum input set is 32bytes, ipv6 src + ipv4 dst = 32bytes
sv_mac_ipv6_gtpu = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4", "tv_mac_ipv6")
        .replace("ipv4", "ipv6")
        .replace("IP(", "IPv6(")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu[0:-1]
]


tv_mac_ipv4_gtpu_eh_ipv4_teid_with_mask = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_teid_with_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345688)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 4},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345677)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_teid_without_mask = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_teid_without_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / ipv4 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345678)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345688)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_qfi = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_qfi",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x34)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x34)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer(QFI=0x34)", "GTPPDUSessionContainer(QFI=0x33)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "GTPPDUSessionContainer(QFI=0x34)", "GTPPDUSessionContainer(QFI=0x33)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, dst="192.168.1.2")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, dst="192.168.1.22")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_l3src = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_l3src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.1")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.11")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.2")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.11", dst="192.168.1.2")'
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.22")'
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.11", dst="192.168.1.22")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_teid_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_teid_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.2")')
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.11", dst="192.168.1.22")')
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.2")')
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.11", dst="192.168.1.22")')
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_qfi_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_qfi_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.2")')
            .replace("GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x34)")
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.11", dst="192.168.1.22")')
            .replace("GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x34)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.2")')
            .replace("GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x33)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.11", dst="192.168.1.22")')
            .replace("GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x33)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_all = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_all",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc qfi is 0x34 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.2")')
            .replace("GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x34)")
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.11", dst="192.168.1.22")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.1", dst="192.168.1.2")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_nonfrag"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.11", dst="192.168.1.11")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.11", dst="192.168.1.22")')
            .replace("GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x34)")
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.2")')
            .replace("GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x33)")
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.2")')
            .replace("GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x33)")
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_frag"]
            .replace("IP(frag=6)", 'IP(frag=6, src="192.168.1.11", dst="192.168.1.22")')
            .replace("GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x33)")
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

sv_mac_ipv4_gtpu_eh_ipv4 = [
    tv_mac_ipv4_gtpu_eh_ipv4_teid_with_mask,
    tv_mac_ipv4_gtpu_eh_ipv4_teid_without_mask,
    tv_mac_ipv4_gtpu_eh_ipv4_qfi,
    tv_mac_ipv4_gtpu_eh_ipv4_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_l3src,
    tv_mac_ipv4_gtpu_eh_ipv4_l3src_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_teid_l3src_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_qfi_l3src_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_all,
]

sv_mac_ipv4_gtpu_eh_ipv6 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv4", "tv_mac_ipv4_gtpu_eh_ipv6")
        .replace(" ipv4 ", " ipv61 ")
        .replace("eth / ipv61 ", "eth / ipv4 ")
        .replace(" ipv61 ", " ipv6 ")
        .replace("IP(", "IPv61(")
        .replace(':55")/IPv61(', ':55")/IP(')
        .replace("IPv61", "IPv6")
        .replace("IPv6(frag=6", "IPv6(nh=6")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv4[0:-3]
]

sv_mac_ipv6_gtpu_eh_ipv4 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv4", "tv_mac_ipv6_gtpu_eh_ipv4")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv4
]

sv_mac_ipv6_gtpu_eh_ipv6 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv6", "tv_mac_ipv6_gtpu_eh_ipv6")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv6
]

tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_with_mask = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_with_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_without_mask = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_without_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / ipv4 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_qfi = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_qfi",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x34)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x33)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / udp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")/UDP(dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")/UDP(dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src_l4src = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / udp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(sport=22)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")/UDP(sport=22)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(sport=12)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")/UDP(sport=12)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l3dst_l4src = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l3dst_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / udp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")/UDP(sport=22)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")/UDP(sport=22)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")/UDP(sport=12)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")/UDP(sport=12)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l3dst_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l3dst_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / udp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")/UDP(dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")/UDP(dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")/UDP(dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")/UDP(dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(dport=23)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(dport=13)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l4src = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(sport=22)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(sport=12)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l4src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l4src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(sport=22, dport=23)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(sport=22, dport=13)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(sport=12, dport=23)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(sport=12, dport=13)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_qfi_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_qfi_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_l4src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_l4src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 / udp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(sport=22, dport=23)",
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(sport=12, dport=13)",
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(sport=22, dport=23)",
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer()/IP()/UDP(sport=12, dport=13)",
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_qfi_l4src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_qfi_l4src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 / udp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer(QFI=0x34)/IP()/UDP(sport=22, dport=23)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer(QFI=0x34)/IP()/UDP(sport=12, dport=13)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer(QFI=0x33)/IP()/UDP(sport=22, dport=23)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                "GTPPDUSessionContainer(QFI=0x33)/IP()/UDP(sport=12, dport=13)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_l3_l4 = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_l3_l4",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=22, dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.22")/UDP(sport=22, dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.2")/UDP(sport=22, dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=22, dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=12, dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=22, dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=12, dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"].replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=12, dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_udp_all = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_udp_all",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc qfi is 0x34 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=22, dport=23)',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=22, dport=23)',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=22, dport=23)',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=12, dport=13)',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_udp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/UDP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=12, dport=13)',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

sv_mac_ipv4_gtpu_eh_ipv4_udp_1 = [
    tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_with_mask,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_without_mask,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_qfi,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l3dst_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l3dst_l4src,
]

sv_mac_ipv4_gtpu_eh_ipv4_udp_2 = [
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src_l4src,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l4src,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l4src_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_l4src_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_qfi_l4src_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l3src_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_teid_l3src_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_qfi_l3src_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_l3_l4,
    tv_mac_ipv4_gtpu_eh_ipv4_udp_all,
]


sv_mac_ipv4_gtpu_eh_ipv4_udp = [
    sv_mac_ipv4_gtpu_eh_ipv4_udp_1,
    sv_mac_ipv4_gtpu_eh_ipv4_udp_2,
]

sv_mac_ipv4_gtpu_eh_ipv6_udp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv4", "tv_mac_ipv4_gtpu_eh_ipv6")
        .replace(" ipv4 ", " ipv61 ")
        .replace("eth / ipv61 ", "eth / ipv4 ")
        .replace(" ipv61 ", " ipv6 ")
        .replace("IP(", "IPv61(")
        .replace(':55")/IPv61(', ':55")/IP(')
        .replace("IPv61", "IPv6")
        .replace("IPv6(frag=6", "IPv6(nh=6")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv4_udp_1
]

sv_mac_ipv4_gtpu_eh_ipv6_udp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv4", "tv_mac_ipv4_gtpu_eh_ipv6")
        .replace(" ipv4 ", " ipv61 ")
        .replace("eth / ipv61 ", "eth / ipv4 ")
        .replace(" ipv61 ", " ipv6 ")
        .replace("IP(", "IPv61(")
        .replace(':55")/IPv61(', ':55")/IP(')
        .replace("IPv61", "IPv6")
        .replace("IPv6(frag=6", "IPv6(nh=6")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv4_udp_2[0:-6]
]

sv_mac_ipv4_gtpu_eh_ipv6_udp = [
    sv_mac_ipv4_gtpu_eh_ipv6_udp_1,
    sv_mac_ipv4_gtpu_eh_ipv6_udp_2,
]

sv_mac_ipv6_gtpu_eh_ipv4_udp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv4", "tv_mac_ipv6_gtpu_eh_ipv4")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv4_udp_1
]

sv_mac_ipv6_gtpu_eh_ipv4_udp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv4", "tv_mac_ipv6_gtpu_eh_ipv4")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv4_udp_2
]

sv_mac_ipv6_gtpu_eh_ipv4_udp = [
    sv_mac_ipv6_gtpu_eh_ipv4_udp_1,
    sv_mac_ipv6_gtpu_eh_ipv4_udp_2,
]

sv_mac_ipv6_gtpu_eh_ipv6_udp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv6", "tv_mac_ipv6_gtpu_eh_ipv6")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv6_udp_1
]

sv_mac_ipv6_gtpu_eh_ipv6_udp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv6", "tv_mac_ipv6_gtpu_eh_ipv6")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv6_udp_2
]

sv_mac_ipv6_gtpu_eh_ipv6_udp = [
    sv_mac_ipv6_gtpu_eh_ipv6_udp_1,
    sv_mac_ipv6_gtpu_eh_ipv6_udp_2,
]

tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_with_mask = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_with_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_without_mask = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_without_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / ipv4 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_qfi = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_qfi",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x34)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()", "GTPPDUSessionContainer(QFI=0x33)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / tcp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")/TCP(dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")/TCP(dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")/TCP(dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")/TCP(dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src_l4src = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / tcp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")/TCP(sport=22)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")/TCP(sport=22)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1")/TCP(sport=12)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11")/TCP(sport=12)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3dst_l4src = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3dst_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / tcp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")/TCP(sport=22)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")/TCP(sport=22)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")/TCP(sport=12)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")/TCP(sport=12)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3dst_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3dst_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.1.2 / tcp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")/TCP(dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")/TCP(dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.2")/TCP(dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(dst="192.168.1.22")/TCP(dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(dport=23)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(dport=13)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l4src = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(sport=22)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(sport=12)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l4src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l4src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(sport=22, dport=23)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(sport=22, dport=13)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(sport=12, dport=23)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(sport=12, dport=13)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_qfi_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_qfi_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_l4src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_l4src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc / ipv4 / tcp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(sport=22, dport=23)",
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(sport=12, dport=13)",
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(sport=22, dport=23)",
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer()/IP()/TCP(sport=12, dport=13)",
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_qfi_l4src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_qfi_l4src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 / tcp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer(QFI=0x34)/IP()/TCP(sport=22, dport=23)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer(QFI=0x34)/IP()/TCP(sport=12, dport=13)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer(QFI=0x33)/IP()/TCP(sport=22, dport=23)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                "GTPPDUSessionContainer(QFI=0x33)/IP()/TCP(sport=12, dport=13)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3_l4 = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3_l4",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=22, dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.22")/TCP(sport=22, dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.2")/TCP(sport=22, dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/TCP(sport=22, dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=12, dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=22, dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=12, dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"].replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer()/IP(src="192.168.1.11", dst="192.168.1.22")/TCP(sport=12, dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_eh_ipv4_tcp_all = {
    "name": "tv_mac_ipv4_gtpu_eh_ipv4_tcp_all",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / gtp_psc qfi is 0x34 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=22, dport=23)',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=22, dport=23)',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=22, dport=23)',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer(QFI=0x34)/IP(src="192.168.1.11", dst="192.168.1.22")/TCP(sport=12, dport=13)',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"),
            mac_ipv4_gtpu_basic["ipv4_gtpu_eh_ipv4_tcp"]
            .replace(
                "GTPPDUSessionContainer()/IP()/TCP()",
                'GTPPDUSessionContainer(QFI=0x33)/IP(src="192.168.1.11", dst="192.168.1.22")/TCP(sport=12, dport=13)',
            )
            .replace("GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

sv_mac_ipv4_gtpu_eh_ipv4_tcp_1 = [
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_with_mask,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_without_mask,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_qfi,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3dst_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3dst_l4src,
]

sv_mac_ipv4_gtpu_eh_ipv4_tcp_2 = [
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src_l4src,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l4src,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l4src_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_l4src_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_qfi_l4src_l4dst,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3src_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_teid_l3src_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_qfi_l3src_l3dst,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_l3_l4,
    tv_mac_ipv4_gtpu_eh_ipv4_tcp_all,
]

sv_mac_ipv4_gtpu_eh_ipv4_tcp = [
    sv_mac_ipv4_gtpu_eh_ipv4_tcp_1,
    sv_mac_ipv4_gtpu_eh_ipv4_tcp_2,
]

sv_mac_ipv4_gtpu_eh_ipv6_tcp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv4", "tv_mac_ipv4_gtpu_eh_ipv6")
        .replace(" ipv4 ", " ipv61 ")
        .replace("eth / ipv61 ", "eth / ipv4 ")
        .replace(" ipv61 ", " ipv6 ")
        .replace("IP(", "IPv61(")
        .replace(':55")/IPv61(', ':55")/IP(')
        .replace("IPv61", "IPv6")
        .replace("IPv6(frag=6", "IPv6(nh=6")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv4_tcp_1
]

sv_mac_ipv4_gtpu_eh_ipv6_tcp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv4", "tv_mac_ipv4_gtpu_eh_ipv6")
        .replace(" ipv4 ", " ipv61 ")
        .replace("eth / ipv61 ", "eth / ipv4 ")
        .replace(" ipv61 ", " ipv6 ")
        .replace("IP(", "IPv61(")
        .replace(':55")/IPv61(', ':55")/IP(')
        .replace("IPv61", "IPv6")
        .replace("IPv6(frag=6", "IPv6(nh=6")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv4_tcp_2[0:-5]
]

sv_mac_ipv4_gtpu_eh_ipv6_tcp = [
    sv_mac_ipv4_gtpu_eh_ipv6_tcp_1,
    sv_mac_ipv4_gtpu_eh_ipv6_tcp_2,
]

sv_mac_ipv6_gtpu_eh_ipv4_tcp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv4", "tv_mac_ipv6_gtpu_eh_ipv4")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv4_tcp_1
]

sv_mac_ipv6_gtpu_eh_ipv4_tcp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv4", "tv_mac_ipv6_gtpu_eh_ipv4")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv4_tcp_2
]

sv_mac_ipv6_gtpu_eh_ipv4_tcp = [
    sv_mac_ipv6_gtpu_eh_ipv4_tcp_1,
    sv_mac_ipv6_gtpu_eh_ipv4_tcp_2,
]

sv_mac_ipv6_gtpu_eh_ipv6_tcp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv6", "tv_mac_ipv6_gtpu_eh_ipv6")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv6_tcp_1
]

sv_mac_ipv6_gtpu_eh_ipv6_tcp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_eh_ipv6", "tv_mac_ipv6_gtpu_eh_ipv6")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_eh_ipv6_tcp_2
]

sv_mac_ipv6_gtpu_eh_ipv6_tcp = [
    sv_mac_ipv6_gtpu_eh_ipv6_tcp_1,
    sv_mac_ipv6_gtpu_eh_ipv6_tcp_2,
]

tv_mac_ipv4_gtpu_ipv4_teid_with_mask = {
    "name": "tv_mac_ipv4_gtpu_ipv4_teid_with_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 4},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_teid_without_mask = {
    "name": "tv_mac_ipv4_gtpu_ipv4_teid_without_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / ipv4 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_l3dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(dst="192.168.1.2")'
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, dst="192.168.1.2")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(dst="192.168.1.22")'
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, dst="192.168.1.22")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_l3src = {
    "name": "tv_mac_ipv4_gtpu_ipv4_l3src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(src="192.168.1.1")'
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.1")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(src="192.168.1.11")'
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.11")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.2")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.11", dst="192.168.1.2")'
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.1", dst="192.168.1.22")'
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "IP(frag=6)", 'IP(frag=6, src="192.168.1.11", dst="192.168.1.22")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_all = {
    "name": "tv_mac_ipv4_gtpu_ipv4_all",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "GTP_U_Header()/IP(frag=6)",
                'GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=6, src="192.168.1.1", dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_nonfrag"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "GTP_U_Header()/IP(frag=6)",
                'GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=6, src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "GTP_U_Header()/IP(frag=6)",
                'GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(frag=6, src="192.168.1.1", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_frag"].replace(
                "GTP_U_Header()/IP(frag=6)",
                'GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(frag=6, src="192.168.1.11", dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

sv_mac_ipv4_gtpu_ipv4 = [
    tv_mac_ipv4_gtpu_ipv4_teid_with_mask,
    tv_mac_ipv4_gtpu_ipv4_teid_without_mask,
    tv_mac_ipv4_gtpu_ipv4_l3dst,
    tv_mac_ipv4_gtpu_ipv4_l3src,
    tv_mac_ipv4_gtpu_ipv4_l3src_l3dst,
    tv_mac_ipv4_gtpu_ipv4_all,
]

sv_mac_ipv4_gtpu_ipv6 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv4_gtpu_ipv6")
        .replace(" ipv4 ", " ipv61 ")
        .replace("eth / ipv61 ", "eth / ipv4 ")
        .replace(" ipv61 ", " ipv6 ")
        .replace("IP(", "IPv61(")
        .replace(':55")/IPv61(', ':55")/IP(')
        .replace("IPv61", "IPv6")
        .replace("IPv6(frag=6", "IPv6(nh=6")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu_ipv4[0:-2]
]

sv_mac_ipv6_gtpu_ipv4 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv6_gtpu_ipv4")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_ipv4
]

sv_mac_ipv6_gtpu_ipv6 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv4_gtpu_ipv6")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_ipv6
]

tv_mac_ipv4_gtpu_ipv4_udp_teid_with_mask = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_teid_with_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_teid_without_mask = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_teid_without_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / ipv4 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_l3dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(dst="192.168.1.2")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(dst="192.168.1.22")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_l3src = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l3src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(src="192.168.1.1")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(src="192.168.1.11")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_l3src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l3src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / udp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.1")/UDP(dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.11")/UDP(dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.1")/UDP(dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.11")/UDP(dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_l3src_l4src = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l3src_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / udp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.1")/UDP(sport=22)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.11")/UDP(sport=22)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.1")/UDP(sport=12)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.11")/UDP(sport=12)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_l3dst_l4src = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l3dst_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / udp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(dst="192.168.1.2")/UDP(sport=22)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(dst="192.168.1.22")/UDP(sport=22)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(dst="192.168.1.2")/UDP(sport=12)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(dst="192.168.1.22")/UDP(sport=12)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / udp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(dst="192.168.1.2")/UDP(dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(dst="192.168.1.22")/UDP(dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(dst="192.168.1.2")/UDP(dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(dst="192.168.1.22")/UDP(dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_l4dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()", "GTP_U_Header()/IP()/UDP(dport=23)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()", "GTP_U_Header()/IP()/UDP(dport=13)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_l4src = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()", "GTP_U_Header()/IP()/UDP(sport=22)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()", "GTP_U_Header()/IP()/UDP(sport=12)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_l4src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l4src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                "GTP_U_Header()/IP()/UDP(sport=22, dport=23)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                "GTP_U_Header()/IP()/UDP(sport=22, dport=13)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                "GTP_U_Header()/IP()/UDP(sport=12, dport=23)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                "GTP_U_Header()/IP()/UDP(sport=12, dport=13)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_teid_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_teid_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_udp_teid_l4src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_teid_l4src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 / udp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                "GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP(sport=22, dport=23)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                "GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP(sport=12, dport=13)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                "GTP_U_Header(gtp_type=255, teid=0x12345677)/IP()/UDP(sport=22, dport=23)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                "GTP_U_Header(gtp_type=255, teid=0x12345677)/IP()/UDP(sport=12, dport=13)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}


tv_mac_ipv4_gtpu_ipv4_udp_l3_l4 = {
    "name": "tv_mac_ipv4_gtpu_ipv4_udp_l3_l4",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=22, dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=12, dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=22, dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_udp"].replace(
                "GTP_U_Header()/IP()/UDP()",
                'GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")/UDP(sport=12, dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

sv_mac_ipv4_gtpu_ipv4_udp_1 = [
    tv_mac_ipv4_gtpu_ipv4_udp_teid_with_mask,
    tv_mac_ipv4_gtpu_ipv4_udp_teid_without_mask,
    tv_mac_ipv4_gtpu_ipv4_udp_l3dst,
    tv_mac_ipv4_gtpu_ipv4_udp_l3src,
    tv_mac_ipv4_gtpu_ipv4_udp_l3src_l4dst,
    tv_mac_ipv4_gtpu_ipv4_udp_l3src_l4src,
]

sv_mac_ipv4_gtpu_ipv4_udp_2 = [
    tv_mac_ipv4_gtpu_ipv4_udp_l3dst_l4src,
    tv_mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst,
    tv_mac_ipv4_gtpu_ipv4_udp_l4dst,
    tv_mac_ipv4_gtpu_ipv4_udp_l4src,
    tv_mac_ipv4_gtpu_ipv4_udp_l4src_l4dst,
    tv_mac_ipv4_gtpu_ipv4_udp_teid_l4src_l4dst,
    tv_mac_ipv4_gtpu_ipv4_udp_teid_l3src_l3dst,
    tv_mac_ipv4_gtpu_ipv4_udp_l3src_l3dst,
    tv_mac_ipv4_gtpu_ipv4_udp_l3_l4,
]

sv_mac_ipv4_gtpu_ipv4_udp = [sv_mac_ipv4_gtpu_ipv4_udp_1, sv_mac_ipv4_gtpu_ipv4_udp_2]

sv_mac_ipv4_gtpu_ipv6_udp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv4_gtpu_ipv6")
        .replace(" ipv4 ", " ipv61 ")
        .replace("eth / ipv61 ", "eth / ipv4 ")
        .replace(" ipv61 ", " ipv6 ")
        .replace("IP(", "IPv61(")
        .replace(':55")/IPv61(', ':55")/IP(')
        .replace("IPv61", "IPv6")
        .replace("IPv6(frag=6", "IPv6(nh=6")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu_ipv4_udp_1
]

sv_mac_ipv4_gtpu_ipv6_udp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv4_gtpu_ipv6")
        .replace(" ipv4 ", " ipv61 ")
        .replace("eth / ipv61 ", "eth / ipv4 ")
        .replace(" ipv61 ", " ipv6 ")
        .replace("IP(", "IPv61(")
        .replace(':55")/IPv61(', ':55")/IP(')
        .replace("IPv61", "IPv6")
        .replace("IPv6(frag=6", "IPv6(nh=6")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu_ipv4_udp_2[0:-3]
]

sv_mac_ipv4_gtpu_ipv6_udp = [sv_mac_ipv4_gtpu_ipv6_udp_1, sv_mac_ipv4_gtpu_ipv6_udp_2]

sv_mac_ipv6_gtpu_ipv4_udp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv6_gtpu_ipv4")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_ipv4_udp_1
]

sv_mac_ipv6_gtpu_ipv4_udp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv6_gtpu_ipv4")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_ipv4_udp_2
]

sv_mac_ipv6_gtpu_ipv4_udp = [sv_mac_ipv6_gtpu_ipv4_udp_1, sv_mac_ipv6_gtpu_ipv4_udp_2]

sv_mac_ipv6_gtpu_ipv6_udp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv6", "tv_mac_ipv6_gtpu_ipv6")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_ipv6_udp_1
]

sv_mac_ipv6_gtpu_ipv6_udp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv6", "tv_mac_ipv6_gtpu_ipv6")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_ipv6_udp_2
]

sv_mac_ipv6_gtpu_ipv6_udp = [sv_mac_ipv6_gtpu_ipv6_udp_1, sv_mac_ipv6_gtpu_ipv6_udp_2]

tv_mac_ipv4_gtpu_ipv4_tcp_teid_with_mask = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_teid_with_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 2},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_teid_without_mask = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_teid_without_mask",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / ipv4 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345678)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345677)"
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()", "GTP_U_Header(gtp_type=255, teid=0x12345688)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l3dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(dst="192.168.1.2")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(dst="192.168.1.22")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l3src = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l3src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(src="192.168.1.1")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()", 'GTP_U_Header()/IP(src="192.168.1.11")'
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l3src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l3src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / tcp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.1")/TCP(dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.11")/TCP(dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.1")/TCP(dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.11")/TCP(dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l3src_l4src = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l3src_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.1.1 / tcp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.1")/TCP(sport=22)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.11")/TCP(sport=22)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.1")/TCP(sport=12)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.11")/TCP(sport=12)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l3dst_l4src = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l3dst_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / tcp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(dst="192.168.1.2")/TCP(sport=22)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(dst="192.168.1.22")/TCP(sport=22)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(dst="192.168.1.2")/TCP(sport=12)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(dst="192.168.1.22")/TCP(sport=12)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l3dst_l4dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l3dst_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.1.2 / tcp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(dst="192.168.1.2")/TCP(dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(dst="192.168.1.22")/TCP(dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(dst="192.168.1.2")/TCP(dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(dst="192.168.1.22")/TCP(dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l4dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()", "GTP_U_Header()/IP()/TCP(dport=23)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()", "GTP_U_Header()/IP()/TCP(dport=13)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l4src = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l4src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()", "GTP_U_Header()/IP()/TCP(sport=22)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()", "GTP_U_Header()/IP()/TCP(sport=12)"
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l4src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l4src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                "GTP_U_Header()/IP()/TCP(sport=22, dport=23)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                "GTP_U_Header()/IP()/TCP(sport=22, dport=13)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                "GTP_U_Header()/IP()/TCP(sport=12, dport=23)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                "GTP_U_Header()/IP()/TCP(sport=12, dport=13)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_teid_l3src_l3dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_teid_l3src_l3dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(src="192.168.1.1", dst="192.168.1.2")',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()",
                'GTP_U_Header(gtp_type=255, teid=0x12345677)/IP(src="192.168.1.11", dst="192.168.1.22")',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_teid_l4src_l4dst = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_teid_l4src_l4dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 / tcp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                "GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=22, dport=23)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                "GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=12, dport=13)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                "GTP_U_Header(gtp_type=255, teid=0x12345677)/IP()/TCP(sport=22, dport=23)",
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                "GTP_U_Header(gtp_type=255, teid=0x12345677)/IP()/TCP(sport=12, dport=13)",
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

tv_mac_ipv4_gtpu_ipv4_tcp_l3_l4 = {
    "name": "tv_mac_ipv4_gtpu_ipv4_tcp_l3_l4",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 teid mask 0x00000001 / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 22 dst is 23 / end actions vf id 1 / end",
    "matched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=22, dport=23)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 1},
    },
    "mismatched": {
        "scapy_str": [
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=12, dport=13)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")/TCP(sport=22, dport=23)',
            ),
            mac_ipv4_gtpu_basic["ipv4_gtpu_ipv4_tcp"].replace(
                "GTP_U_Header()/IP()/TCP()",
                'GTP_U_Header()/IP(src="192.168.1.11", dst="192.168.1.22")/TCP(sport=12, dport=13)',
            ),
        ],
        "param": {"expect_port": 1, "expect_queues": "null"},
        "expect_results": {"expect_pkts": 0},
    },
}

sv_mac_ipv4_gtpu_ipv4_tcp_1 = [
    tv_mac_ipv4_gtpu_ipv4_tcp_teid_with_mask,
    tv_mac_ipv4_gtpu_ipv4_tcp_teid_without_mask,
    tv_mac_ipv4_gtpu_ipv4_tcp_l3dst,
    tv_mac_ipv4_gtpu_ipv4_tcp_l3src,
    tv_mac_ipv4_gtpu_ipv4_tcp_l3src_l4dst,
    tv_mac_ipv4_gtpu_ipv4_tcp_l3src_l4src,
]

sv_mac_ipv4_gtpu_ipv4_tcp_2 = [
    tv_mac_ipv4_gtpu_ipv4_tcp_l3dst_l4src,
    tv_mac_ipv4_gtpu_ipv4_tcp_l3dst_l4dst,
    tv_mac_ipv4_gtpu_ipv4_tcp_l4dst,
    tv_mac_ipv4_gtpu_ipv4_tcp_l4src,
    tv_mac_ipv4_gtpu_ipv4_tcp_l4src_l4dst,
    tv_mac_ipv4_gtpu_ipv4_tcp_teid_l4src_l4dst,
    tv_mac_ipv4_gtpu_ipv4_tcp_teid_l3src_l3dst,
    tv_mac_ipv4_gtpu_ipv4_tcp_l3src_l3dst,
    tv_mac_ipv4_gtpu_ipv4_tcp_l3_l4,
]

sv_mac_ipv4_gtpu_ipv4_tcp = [sv_mac_ipv4_gtpu_ipv4_tcp_1, sv_mac_ipv4_gtpu_ipv4_tcp_2]

sv_mac_ipv4_gtpu_ipv6_tcp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv4_gtpu_ipv6")
        .replace(" ipv4 ", " ipv61 ")
        .replace("eth / ipv61 ", "eth / ipv4 ")
        .replace(" ipv61 ", " ipv6 ")
        .replace("IP(", "IPv61(")
        .replace(':55")/IPv61(', ':55")/IP(')
        .replace("IPv61", "IPv6")
        .replace("IPv6(frag=6", "IPv6(nh=6")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu_ipv4_tcp_1
]

sv_mac_ipv4_gtpu_ipv6_tcp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv4_gtpu_ipv6")
        .replace(" ipv4 ", " ipv61 ")
        .replace("eth / ipv61 ", "eth / ipv4 ")
        .replace(" ipv61 ", " ipv6 ")
        .replace("IP(", "IPv61(")
        .replace(':55")/IPv61(', ':55")/IP(')
        .replace("IPv61", "IPv6")
        .replace("IPv6(frag=6", "IPv6(nh=6")
        .replace("192.168.1.1", "2001::1")
        .replace("192.168.1.11", "2001::11")
        .replace("192.168.1.2", "2001::2")
        .replace("192.168.1.22", "2001::22")
    )
    for sv in sv_mac_ipv4_gtpu_ipv4_tcp_2[0:-3]
]

sv_mac_ipv4_gtpu_ipv6_tcp = [sv_mac_ipv4_gtpu_ipv6_tcp_1, sv_mac_ipv4_gtpu_ipv6_tcp_2]

sv_mac_ipv6_gtpu_ipv4_tcp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv6_gtpu_ipv4")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_ipv4_tcp_1
]

sv_mac_ipv6_gtpu_ipv4_tcp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv4", "tv_mac_ipv6_gtpu_ipv4")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_ipv4_tcp_2
]

sv_mac_ipv6_gtpu_ipv4_tcp = [sv_mac_ipv6_gtpu_ipv4_tcp_1, sv_mac_ipv6_gtpu_ipv4_tcp_2]

sv_mac_ipv6_gtpu_ipv6_tcp_1 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv6", "tv_mac_ipv6_gtpu_ipv6")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_ipv6_tcp_1
]

sv_mac_ipv6_gtpu_ipv6_tcp_2 = [
    eval(
        str(sv)
        .replace("tv_mac_ipv4_gtpu_ipv6", "tv_mac_ipv6_gtpu_ipv6")
        .replace("eth / ipv4 ", "eth / ipv6 ")
        .replace(':55")/IP()', ':55")/IPv6()')
    )
    for sv in sv_mac_ipv4_gtpu_ipv6_tcp_2
]

sv_mac_ipv6_gtpu_ipv6_tcp = [sv_mac_ipv6_gtpu_ipv6_tcp_1, sv_mac_ipv6_gtpu_ipv6_tcp_2]


class CVLDCFSwitchFilterGTPUTest(TestCase):
    supported_nic = ["columbiaville_100g", "columbiaville_25g", "columbiaville_25gx2"]

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
        self.__tx_iface = self.tester.get_interface(localPort)
        self.pkt = Packet()
        self.testpmd_status = "close"
        self.pass_flag = "passed"
        self.fail_flag = "failed"
        # bind pf to kernel
        self.dut.bind_interfaces_linux("ice")

        # set vf driver
        self.vf_driver = "vfio-pci"
        self.dut.send_expect("modprobe vfio-pci", "#")
        self.path = self.dut.apps_name["test-pmd"]

    def setup_1pf_vfs_env(self, pf_port=0, driver="default"):
        """
        create and set vfs

        :param pf_port: pf port generate vfs
        :param driver:  set vf driver
        """
        self.reload_ice()
        self.used_dut_port_0 = self.dut_ports[pf_port]
        # get PF interface name
        self.pf0_intf = self.dut.ports_info[self.used_dut_port_0]["intf"]
        # generate 4 VFs on PF
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 2, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        # set VF0 as trust
        self.dut.send_expect("ip link set %s vf 0 trust on" % self.pf0_intf, "#")
        # bind VFs to dpdk driver
        for port in self.sriov_vfs_port_0:
            port.bind_driver(self.vf_driver)
        time.sleep(5)

    def set_up(self):
        """
        Run before each test case.
        """
        self.setup_1pf_vfs_env()

    def reload_ice(self):
        """
        dcf switch need reload driver to ensure create rule sucessful
        """
        self.dut.send_expect("rmmod ice", "# ", 15)
        self.dut.send_expect("modprobe ice", "# ", 15)

    def create_testpmd_command(self):
        """
        splice create testpmd command

        :return: create testpmd command
        """
        # Prepare testpmd EAL and parameters
        vf0_pci = self.sriov_vfs_port_0[0].pci
        vf1_pci = self.sriov_vfs_port_0[1].pci
        all_eal_param = self.dut.create_eal_parameters(
            cores="1S/4C/1T",
            ports=[vf0_pci, vf1_pci],
            port_options={vf0_pci: "cap=dcf"},
        )
        command = self.path + all_eal_param + " -- -i"
        return command

    def launch_testpmd(self):
        """
        launch testpmd with the command
        """
        command = self.create_testpmd_command()
        self.dut.send_expect(command, "testpmd> ", 15)
        self.testpmd_status = "running"
        self.dut.send_expect("set portlist 1", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)

    def send_and_check_packets(self, dic, session_name="", tx_iface=""):
        """
        general packets processing workflow.

        :param dic: scapy str dic
        :param session_name: testpmd seesion
        :param tx_iface: send pkts port
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
        rfc.check_vf_rx_packets_number(out, dic["param"], dic["expect_results"])

    def validate_switch_filter_rule(
        self, rte_flow_pattern, session_name="", check_stats=True
    ):
        """
        validate switch rule

        :param rte_flow_pattern: switch rule list or str
        :param session_name: testpmd session
        :param check_stats: check requirement validate rule true or false
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
        create switch rule

        :param rte_flow_pattern: switch rule list or str
        :param session_name: testpmd session
        :param check_stats: check requirement create rule true or false
        :return: return rule list for destroy rule test
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

        :param port_id: create rule port
        :param rule_list: create rule list
        :param session_name: testpmd session
        :param need_verify: check rule create status
        :return: return not the same as expected rule list
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
        """
        destroy the created switch rule

        :param port_id: create rule port
        :param rule_list: create rule list
        :param session_name: testpmd session
        :param need_verify: check rule destroy status
        :return: return not the same as expected rule list
        """
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

    def destroy_testpmd_and_vf(self):
        """
        quit testpmd and destroy vf
        """
        if self.testpmd_status != "close":
            # destroy all flow rules on DCF
            self.dut.send_expect("flow flush 0", "testpmd> ", 15)
            self.dut.send_expect("clear port stats all", "testpmd> ", 15)
            self.dut.send_expect("quit", "#", 15)
            # kill all DPDK application
            self.dut.kill_all()
            # destroy vfs
            for port_id in self.dut_ports:
                self.dut.destroy_sriov_vfs_by_port(port_id)
        self.testpmd_status = "close"
        if getattr(self, "session_secondary", None):
            self.dut.close_session(self.session_secondary)

    def _rte_flow_validate_pattern(self, test_vector):
        """
        validate/create/check pkts status/result

        :param test_vector: switch rule and pkts dic
        """
        test_results = dict()
        for tvs in test_vector:
            self.destroy_testpmd_and_vf()
            self.setup_1pf_vfs_env()
            self.launch_testpmd()
            for tv in tvs:
                try:
                    self.logger.info(
                        "===================Test sub case: {}================".format(
                            tv["name"]
                        )
                    )
                    # validate a rule
                    self.validate_switch_filter_rule(tv["rte_flow_pattern"])
                    # create a rule
                    rule_list = self.create_switch_filter_rule(tv["rte_flow_pattern"])
                    self.check_switch_filter_rule_list(0, rule_list)
                    # send matched packets and check
                    matched_dic = tv["matched"]
                    self.send_and_check_packets(matched_dic)
                    # send mismatched packets and check
                    mismatched_dic = tv["mismatched"]
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
                    test_results[tv["name"]] = self.pass_flag
                    self.logger.info("sub_case %s passed" % tv["name"])
                except Exception as e:
                    self.logger.warning("sub_case %s failed: %s" % (tv["name"], e))
                    test_results[tv["name"]] = self.fail_flag
                    self.dut.send_expect("flow flush 0", "testpmd> ", 15)
        pass_rate = (
            round(
                list(test_results.values()).count(self.pass_flag) / len(test_results), 4
            )
            * 100
        )
        self.logger.info(test_results)
        self.logger.info("pass rate is: %s" % pass_rate)
        self.verify(pass_rate == 100.00, "some subcases failed")

    def test_mac_ipv4_gtpu(self):
        self._rte_flow_validate_pattern([sv_mac_ipv4_gtpu])

    def test_mac_ipv6_gtpu(self):
        self._rte_flow_validate_pattern([sv_mac_ipv6_gtpu])

    def test_mac_ipv4_gtpu_ipv4(self):
        self._rte_flow_validate_pattern([sv_mac_ipv4_gtpu_ipv4])

    def test_mac_ipv4_gtpu_ipv6(self):
        self._rte_flow_validate_pattern([sv_mac_ipv4_gtpu_ipv6])

    def test_mac_ipv6_gtpu_ipv4(self):
        self._rte_flow_validate_pattern([sv_mac_ipv6_gtpu_ipv4])

    def test_mac_ipv6_gtpu_ipv6(self):
        self._rte_flow_validate_pattern([sv_mac_ipv6_gtpu_ipv6])

    def test_mac_ipv4_gtpu_ipv4_udp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv4_gtpu_ipv4_udp)

    def test_mac_ipv4_gtpu_ipv6_udp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv4_gtpu_ipv6_udp)

    def test_mac_ipv6_gtpu_ipv4_udp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv6_gtpu_ipv4_udp)

    def test_mac_ipv6_gtpu_ipv6_udp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv6_gtpu_ipv6_udp)

    def test_mac_ipv4_gtpu_ipv4_tcp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv4_gtpu_ipv4_tcp)

    def test_mac_ipv4_gtpu_ipv6_tcp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv4_gtpu_ipv6_tcp)

    def test_mac_ipv6_gtpu_ipv4_tcp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv6_gtpu_ipv4_tcp)

    def test_mac_ipv6_gtpu_ipv6_tcp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv6_gtpu_ipv6_tcp)

    def test_mac_ipv4_gtpu_eh_ipv4(self):
        self._rte_flow_validate_pattern([sv_mac_ipv4_gtpu_eh_ipv4])

    def test_mac_ipv4_gtpu_eh_ipv6(self):
        self._rte_flow_validate_pattern([sv_mac_ipv4_gtpu_eh_ipv6])

    def test_mac_ipv6_gtpu_eh_ipv4(self):
        self._rte_flow_validate_pattern([sv_mac_ipv6_gtpu_eh_ipv4])

    def test_mac_ipv6_gtpu_eh_ipv6(self):
        self._rte_flow_validate_pattern([sv_mac_ipv6_gtpu_eh_ipv6])

    def test_mac_ipv4_gtpu_eh_ipv4_udp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv4_gtpu_eh_ipv4_udp)

    def test_mac_ipv4_gtpu_eh_ipv6_udp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv4_gtpu_eh_ipv6_udp)

    def test_mac_ipv6_gtpu_eh_ipv4_udp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv6_gtpu_eh_ipv4_udp)

    def test_mac_ipv6_gtpu_eh_ipv6_udp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv6_gtpu_eh_ipv6_udp)

    def test_mac_ipv4_gtpu_eh_ipv4_tcp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv4_gtpu_eh_ipv4_tcp)

    def test_mac_ipv4_gtpu_eh_ipv6_tcp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv4_gtpu_eh_ipv6_tcp)

    def test_mac_ipv6_gtpu_eh_ipv4_tcp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv6_gtpu_eh_ipv4_tcp)

    def test_mac_ipv6_gtpu_eh_ipv6_tcp(self):
        self._rte_flow_validate_pattern(sv_mac_ipv6_gtpu_eh_ipv6_tcp)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.destroy_testpmd_and_vf()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
