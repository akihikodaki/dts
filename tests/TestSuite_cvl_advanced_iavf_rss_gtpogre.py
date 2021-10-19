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


import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

from .rte_flow_common import RssProcessing

# ipv4+ipv4+ipv4
mac_ipv4_gre_ipv4_gtpu_ipv4_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")',
}

mac_ipv4_gre_ipv4_gtpu_ipv4_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv4_basic).replace('1.1.2.6', '1.1.2.16'))
mac_ipv4_gre_ipv4_gtpu_ipv4_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv4_basic).replace('1.1.2.7', '1.1.2.17'))
mac_ipv4_gre_ipv4_gtpu_ipv4_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
]

mac_ipv4_gre_ipv4_gtpu_ipv4_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'].replace('1.1.2.7', '1.1.2.17'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_toeplitz = [mac_ipv4_gre_ipv4_gtpu_ipv4_l3dst_only, mac_ipv4_gre_ipv4_gtpu_ipv4_l3src_only,
                                        mac_ipv4_gre_ipv4_gtpu_ipv4_all]

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)',
}

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic).replace('1.1.2.6', '1.1.2.16'))
mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic).replace('1.1.2.7', '1.1.2.17'))
mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic).replace('sport=4', 'sport=14'))
mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic).replace('dport=2', 'dport=12'))

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=4, dport=2)/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)/("X"*480)',
]

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3srcl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3srcl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3srcl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3srcl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dstl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dstl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dstl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dstl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv4_udp_toeplitz = [mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dst_only, mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3src_only,
                                            mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4dst_only, mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l4src_only,
                                            mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dstl4dst, mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3srcl4dst,
                                            mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3dstl4src, mac_ipv4_gre_ipv4_gtpu_ipv4_udp_l3srcl4src,
                                            mac_ipv4_gre_ipv4_gtpu_ipv4_udp_all]


mac_ipv4_gre_ipv4_gtpu_ipv4_tcp_toeplitz = [eval(str(element).replace('_udp', '_tcp')
                                        .replace('TCP(sport', 'UDP(sport')
                                        .replace('UDP(dport', 'TCP(dport')
                                        .replace('gtpu / ipv4 / udp', 'gtpu / ipv4 / tcp')
                                        .replace('ipv4-udp', 'ipv4-tcp'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_ipv4_udp_toeplitz]

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")',
    'gtpogre-ipv4-ul': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")',
    'gtpogre-ipv4-dl': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")',
}
mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic).replace('1.1.2.6', '1.1.2.16'))
mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic).replace('1.1.2.7', '1.1.2.17'))

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
]

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_toeplitz = [mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3dst_only, mac_ipv4_gre_ipv4_gtpu_eh_ipv4_l3src_only,
                                           mac_ipv4_gre_ipv4_gtpu_eh_ipv4_all]

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)',
    'gtpogre-ipv4-ul': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)',
    'gtpogre-ipv4-dl': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)',
}
mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic).replace('1.1.2.6', '1.1.2.16'))
mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic).replace('1.1.2.7', '1.1.2.17'))
mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic).replace('sport=4', 'sport=14'))
mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic).replace('dport=2', 'dport=12'))

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(dport=2, sport=4)/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/TCP(sport=4, dport=2)'
]

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3srcl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3srcl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3srcl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3srcl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dstl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dstl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dstl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dstl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv4_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_toeplitz = [mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dst_only, mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3src_only,
                                               mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4dst_only, mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l4src_only,
                                               mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dstl4dst, mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3srcl4dst,
                                               mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3dstl4src, mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_l3srcl4src,
                                               mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_all]

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp_toeplitz = [eval(str(element).replace('_udp', '_tcp')
                                        .replace('ipv4-udp', 'ipv4-tcp')
                                        .replace('TCP(sport', 'UDP(sport')
                                        .replace('UDP(dport', 'TCP(dport')
                                        .replace('gtp_psc / ipv4 / udp', 'gtp_psc / ipv4 / tcp'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_toeplitz]

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_basic = {
    'gtpogre-ipv4-ul': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")',
}
mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv4_basic).replace('1.1.2.6', '1.1.2.16'))
mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv4_basic).replace('1.1.2.7', '1.1.2.17'))

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
]

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_basic['gtpogre-ipv4-ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_basic['gtpogre-ipv4-ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_basic['gtpogre-ipv4-ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_toeplitz = [mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3dst_only, mac_ipv4_gre_ipv4_gtpu_ul_ipv4_l3src_only,
                                           mac_ipv4_gre_ipv4_gtpu_ul_ipv4_all]

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic = {
    'gtpogre-ipv4-ul': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)',
    }
mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic).replace('1.1.2.6', '1.1.2.16'))
mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic).replace('1.1.2.7', '1.1.2.17'))
mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic).replace('sport=4', 'sport=14'))
mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic).replace('dport=2', 'dport=12'))

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(dport=2, sport=4)/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/TCP(sport=4, dport=2)'
]

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.17")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3srcl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3srcl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3srcl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3srcl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.17")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dstl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dstl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dstl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dstl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.16", dst="1.1.2.7")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv4_basic['gtpogre-ipv4-ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz = [mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dst_only, mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3src_only,
                                               mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4dst_only, mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l4src_only,
                                               mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dstl4dst, mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3srcl4dst,
                                               mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3dstl4src, mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_l3srcl4src,
                                               mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_all]

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_toeplitz = [eval(str(element).replace('_udp', '_tcp')
                                        .replace('TCP(sport', 'UDP(sport')
                                        .replace('UDP(dport', 'TCP(dport')
                                        .replace('gtp_psc pdu_t is 1 / ipv4 / udp', 'gtp_psc pdu_t is 1 / ipv4 / tcp')
                                        .replace('ipv4-udp', 'ipv4-tcp'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz]

mac_ipv4_gre_ipv4_gtpu_dl_ipv4_toeplitz = [eval(str(element).replace('_ul_', '_dl_')
                                           .replace('gtp_psc pdu_t is 1', 'gtp_psc pdu_t is 0')
                                           .replace('type=1', 'type=0'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_toeplitz]

mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp_toeplitz = [eval(str(element).replace('_ul_', '_dl_')
                                           .replace('gtp_psc pdu_t is 1', 'gtp_psc pdu_t is 0')
                                           .replace('type=1', 'type=0'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz]

mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp_toeplitz = [eval(str(element).replace('_ul_', '_dl_')
                                           .replace('gtp_psc pdu_t is 1', 'gtp_psc pdu_t is 0')
                                           .replace('type=1', 'type=0'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_toeplitz]
# global variable
ipv4_case_name = 'mac_ipv4_gre_ipv4'
ipv4_rule = '/ ipv4 / gre / ipv4 /'
ipv4_match_ip1 = 'IP(src="1.1.2.2", dst="1.1.2.3")'
ipv4_match_ip2 = 'IP(src="1.1.2.4", dst="1.1.2.5")'
ipv4_mismatch_ip1 = 'IP(src="1.1.2.12", dst="1.1.2.13")'
ipv4_mismatch_ip2 = 'IP(src="1.1.2.14", dst="1.1.2.15")'

# new global variable
ipv6_ipv4_name = 'mac_ipv6_gre_ipv4'
ipv6_ipv4_rule = '/ ipv6 / gre / ipv4 /'
ipv4_ipv6_name = 'mac_ipv4_gre_ipv6'
ipv4_ipv6_rule = '/ ipv4 / gre / ipv6 /'
ipv6_ipv6_name = 'mac_ipv6_gre_ipv6'
ipv6_ipv6_rule = '/ ipv6 / gre / ipv6 /'

ipv6_match_ip1 = 'IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2927",dst="CDCD:910A:2222:5498:8475:1111:3900:2022")'
ipv6_mismatch_ip1 = 'IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2922",dst="CDCD:910A:2222:5498:8475:1111:3900:2023")'
ipv6_match_ip2 = 'IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")'
ipv6_mismatch_ip2 = 'IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2924",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")'

# ipv6+ipv4+ipv4
mac_ipv6_gre_ipv4_gtpu_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv4_toeplitz]

mac_ipv6_gre_ipv4_gtpu_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv4_udp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv4_tcp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_eh_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv4_toeplitz]

mac_ipv6_gre_ipv4_gtpu_eh_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_eh_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_ul_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_toeplitz]

mac_ipv6_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_ul_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_dl_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv4_toeplitz]

mac_ipv6_gre_ipv4_gtpu_dl_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_dl_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp_toeplitz]

# ipv4+ipv6+ipv4
mac_ipv4_gre_ipv6_gtpu_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv4_toeplitz]

mac_ipv4_gre_ipv6_gtpu_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv4_udp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv4_tcp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_eh_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv4_toeplitz]

mac_ipv4_gre_ipv6_gtpu_eh_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_eh_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_ul_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_toeplitz]

mac_ipv4_gre_ipv6_gtpu_ul_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_ul_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_dl_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv4_toeplitz]

mac_ipv4_gre_ipv6_gtpu_dl_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_dl_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp_toeplitz]

# ipv6+ipv6+ipv4
mac_ipv6_gre_ipv6_gtpu_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv4_toeplitz]

mac_ipv6_gre_ipv6_gtpu_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv4_udp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv4_tcp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_eh_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv4_toeplitz]

mac_ipv6_gre_ipv6_gtpu_eh_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_eh_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_ul_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_toeplitz]

mac_ipv6_gre_ipv6_gtpu_ul_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_ul_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_dl_ipv4_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv4_toeplitz]

mac_ipv6_gre_ipv6_gtpu_dl_ipv4_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_dl_ipv4_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp_toeplitz]
# ipv4+ipv4+ipv6
mac_ipv4_gre_ipv4_gtpu_ipv6_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
}

mac_ipv4_gre_ipv4_gtpu_ipv6_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv6_basic).replace('ABAB:910B:6666:3457:8295:3333:1800:2929', 'ABAB:910B:6666:3457:8295:3333:1800:2926'))
mac_ipv4_gre_ipv4_gtpu_ipv6_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv6_basic).replace('CDCD:910A:2222:5498:8475:1111:3900:2020', 'CDCD:910A:2222:5498:8475:1111:3900:2027'))
mac_ipv4_gre_ipv4_gtpu_ipv6_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
]

mac_ipv4_gre_ipv4_gtpu_ipv6_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_l3src_changed_pkt['gtpogre-ipv4-nonfrag'].replace('CDCD:910A:2222:5498:8475:1111:3900:2020', 'CDCD:910A:2222:5498:8475:1111:3900:2027'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_toeplitz = [mac_ipv4_gre_ipv4_gtpu_ipv6_l3dst_only, mac_ipv4_gre_ipv4_gtpu_ipv6_l3src_only,
                                        mac_ipv4_gre_ipv4_gtpu_ipv6_all]


mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)',
}

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic).replace('ABAB:910B:6666:3457:8295:3333:1800:2929', 'ABAB:910B:6666:3457:8295:3333:1800:2926'))
mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic).replace('CDCD:910A:2222:5498:8475:1111:3900:2020', 'CDCD:910A:2222:5498:8475:1111:3900:2027'))
mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic).replace('sport=4', 'sport=14'))
mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic).replace('dport=2', 'dport=12'))

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=4, dport=2)/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)/("X"*480)',
]

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3srcl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3srcl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3srcl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3srcl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dstl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dstl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dstl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dstl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ipv6_udp_toeplitz = [mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dst_only, mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3src_only,
                                            mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4dst_only, mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l4src_only,
                                            mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dstl4dst, mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3srcl4dst,
                                            mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3dstl4src, mac_ipv4_gre_ipv4_gtpu_ipv6_udp_l3srcl4src,
                                            mac_ipv4_gre_ipv4_gtpu_ipv6_udp_all]


mac_ipv4_gre_ipv4_gtpu_ipv6_tcp_toeplitz = [eval(str(element).replace('_udp', '_tcp')
                                        .replace('TCP(sport', 'UDP(sport')
                                        .replace('UDP(dport', 'TCP(dport')
                                        .replace('gtpu / ipv6 / udp', 'gtpu / ipv6 / tcp')
                                        .replace('ipv6-udp', 'ipv6-tcp'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_ipv6_udp_toeplitz]

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
    'gtpogre-ipv4-ul': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
    'gtpogre-ipv4-dl': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
}
mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic).replace('ABAB:910B:6666:3457:8295:3333:1800:2929', 'ABAB:910B:6666:3457:8295:3333:1800:2926'))
mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic).replace('CDCD:910A:2222:5498:8475:1111:3900:2020', 'CDCD:910A:2222:5498:8475:1111:3900:2027'))

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer()/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
]

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_toeplitz = [mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3dst_only, mac_ipv4_gre_ipv4_gtpu_eh_ipv6_l3src_only,
                                           mac_ipv4_gre_ipv4_gtpu_eh_ipv6_all]

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)',
    'gtpogre-ipv4-ul': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)',
    'gtpogre-ipv4-dl': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)',
}
mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic).replace('ABAB:910B:6666:3457:8295:3333:1800:2929', 'ABAB:910B:6666:3457:8295:3333:1800:2926'))
mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic).replace('CDCD:910A:2222:5498:8475:1111:3900:2020', 'CDCD:910A:2222:5498:8475:1111:3900:2027'))
mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic).replace('sport=4', 'sport=14'))
mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic).replace('dport=2', 'dport=12'))

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(dport=2, sport=4)/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=4, dport=2)'
]

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3srcl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3srcl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3srcl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3srcl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dstl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dstl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dstl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dstl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-dl'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-ul'],
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-dl'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_eh_ipv6_basic['gtpogre-ipv4-nonfrag'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_toeplitz = [mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dst_only, mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3src_only,
                                               mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4dst_only, mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l4src_only,
                                               mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dstl4dst, mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3srcl4dst,
                                               mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3dstl4src, mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_l3srcl4src,
                                               mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_all]

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp_toeplitz = [eval(str(element).replace('_udp', '_tcp')
                                        .replace('TCP(sport', 'UDP(sport')
                                        .replace('UDP(dport', 'TCP(dport')
                                        .replace('gtp_psc / ipv6 / udp', 'gtp_psc / ipv6 / tcp')
                                        .replace('ipv6-udp', 'ipv6-tcp'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_toeplitz]

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_basic = {
    'gtpogre-ipv4-ul': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
}
mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv6_basic).replace('ABAB:910B:6666:3457:8295:3333:1800:2929', 'ABAB:910B:6666:3457:8295:3333:1800:2926'))
mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv6_basic).replace('CDCD:910A:2222:5498:8475:1111:3900:2020', 'CDCD:910A:2222:5498:8475:1111:3900:2027'))

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
]

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_basic['gtpogre-ipv4-ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_basic['gtpogre-ipv4-ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_basic['gtpogre-ipv4-ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_toeplitz = [mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3dst_only, mac_ipv4_gre_ipv4_gtpu_ul_ipv6_l3src_only,
                                           mac_ipv4_gre_ipv4_gtpu_ul_ipv6_all]

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic = {
    'gtpogre-ipv4-ul': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)',
    }
mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic).replace('ABAB:910B:6666:3457:8295:3333:1800:2929', 'ABAB:910B:6666:3457:8295:3333:1800:2926'))
mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic).replace('CDCD:910A:2222:5498:8475:1111:3900:2020', 'CDCD:910A:2222:5498:8475:1111:3900:2027'))
mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4src_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic).replace('sport=4', 'sport=14'))
mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4dst_changed_pkt = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic).replace('dport=2', 'dport=12'))

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_unmatched_pkt = [
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(dport=2, sport=4)/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer()/IP(src="1.1.2.6", dst="1.1.2.7")/UDP(dport=2, sport=4)/("X"*480)',
    'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.2", dst="1.1.2.3")/GRE()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=4, dport=2)'
]

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4dst_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4src_only = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3srcl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3srcl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3srcl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3srcl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dstl4src = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dstl4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=12, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dstl4dst = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dstl4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2926",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=14)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
                ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_all = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_basic['gtpogre-ipv4-ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4src_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4dst_changed_pkt['gtpogre-ipv4-ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="1.1.2.12", dst="1.1.2.13")/GRE()/IP(src="1.1.2.14", dst="1.1.2.15")/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2, sport=4)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gre_ipv4_gtpu_ul_ipv6_basic['gtpogre-ipv4-ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz = [mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dst_only, mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3src_only,
                                               mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4dst_only, mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l4src_only,
                                               mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dstl4dst, mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3srcl4dst,
                                               mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3dstl4src, mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_l3srcl4src,
                                               mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_all]

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_toeplitz = [eval(str(element).replace('_udp', '_tcp')
                                            .replace('TCP(sport', 'UDP(sport')
                                            .replace('UDP(dport', 'TCP(dport')
                                            .replace('gtp_psc pdu_t is 1 / ipv6 / udp', 'gtp_psc pdu_t is 1 / ipv6 / tcp')
                                            .replace('ipv6-udp', 'ipv6-tcp'))
                                    for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz]

mac_ipv4_gre_ipv4_gtpu_dl_ipv6_toeplitz = [eval(str(element).replace('_ul_', '_dl_')
                                           .replace('gtp_psc pdu_t is 1', 'gtp_psc pdu_t is 0')
                                           .replace('type=1', 'type=0'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_toeplitz]

mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp_toeplitz = [eval(str(element).replace('_ul_', '_dl_')
                                           .replace('gtp_psc pdu_t is 1', 'gtp_psc pdu_t is 0')
                                           .replace('type=1', 'type=0'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz]

mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp_toeplitz = [eval(str(element).replace('_ul_', '_dl_')
                                           .replace('gtp_psc pdu_t is 1', 'gtp_psc pdu_t is 0')
                                           .replace('type=1', 'type=0'))
                                   for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_toeplitz]

# ipv4+ipv6+ipv6
mac_ipv4_gre_ipv6_gtpu_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv6_toeplitz]

mac_ipv4_gre_ipv6_gtpu_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv6_udp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv6_tcp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_eh_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv6_toeplitz]

mac_ipv4_gre_ipv6_gtpu_eh_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_eh_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_ul_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_toeplitz]

mac_ipv4_gre_ipv6_gtpu_ul_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_ul_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_dl_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv6_toeplitz]

mac_ipv4_gre_ipv6_gtpu_dl_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp_toeplitz]

mac_ipv4_gre_ipv6_gtpu_dl_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv4_ipv6_name)
                           .replace(ipv4_rule, ipv4_ipv6_rule)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp_toeplitz]

# ipv6+ipv4+ipv6
mac_ipv6_gre_ipv4_gtpu_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv6_toeplitz]

mac_ipv6_gre_ipv4_gtpu_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv6_udp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv6_tcp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_eh_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv6_toeplitz]

mac_ipv6_gre_ipv4_gtpu_eh_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_eh_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_ul_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_toeplitz]

mac_ipv6_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_ul_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_dl_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv6_toeplitz]

mac_ipv6_gre_ipv4_gtpu_dl_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp_toeplitz]

mac_ipv6_gre_ipv4_gtpu_dl_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv4_name)
                           .replace(ipv4_rule, ipv6_ipv4_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1))
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp_toeplitz]

# ipv6+ipv6+ipv6
mac_ipv6_gre_ipv6_gtpu_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv6_toeplitz]

mac_ipv6_gre_ipv6_gtpu_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv6_udp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ipv6_tcp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_eh_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv6_toeplitz]

mac_ipv6_gre_ipv6_gtpu_eh_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_eh_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_ul_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_toeplitz]

mac_ipv6_gre_ipv6_gtpu_ul_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_ul_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_dl_ipv6_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv6_toeplitz]

mac_ipv6_gre_ipv6_gtpu_dl_ipv6_udp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp_toeplitz]

mac_ipv6_gre_ipv6_gtpu_dl_ipv6_tcp_toeplitz = [eval(str(element).replace(ipv4_case_name, ipv6_ipv6_name)
                           .replace(ipv4_rule, ipv6_ipv6_rule)
                           .replace(ipv4_match_ip1, ipv6_match_ip1)
                           .replace(ipv4_match_ip2, ipv6_match_ip2)
                           .replace(ipv4_mismatch_ip1, ipv6_mismatch_ip1)
                           .replace(ipv4_mismatch_ip2, ipv6_mismatch_ip2)
                           )
                      for element in mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp_toeplitz]
## symmetric cases
# IPV4+IPV4+IPV4
ipv4_mac = 'IP(src="1.1.2.6", dst="1.1.2.7")'
swap_ipv4_mac = 'IP(src="1.1.2.7", dst="1.1.2.6")'

ipv6_mac = 'IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")'
swap_ipv6_mac = 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929", src="CDCD:910A:2222:5498:8475:1111:3900:2020")'

mac_ipv4_gre_ipv4_gtpu_ipv4_pkt = {
    'basic_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/{}'.format(ipv4_mac),
    'symmetric_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/{}'.format(swap_ipv4_mac)
}

mac_ipv4_gre_ipv4_gtpu_ipv4_symmetric = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_pkt['basic_packet'],
            'action': {'save_hash': 'gtpogre-ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_pkt['symmetric_packet'],
            'action': 'check_hash_same',
        },
        {   # unmatch MAC_IPV4_GRE_IPV4_GTPU_IPV6
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/{}'.format(ipv6_match_ip2),
            'action': 'check_no_hash',
        },
        {   # unmatch MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/{}'.format(ipv4_mac),
            'action': 'check_no_hash',
        },
    ],
    'post_test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ipv4_pkt['basic_packet'],
            'action': 'check_no_hash',
        }
    ]
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt = {
    'basic_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/{}/UDP(dport=2, sport=4)'.format(ipv4_mac),
    'symmetric_packet1': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/{}/UDP(dport=2, sport=4)'.format(swap_ipv4_mac),
    'symmetric_packet2': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/{}/UDP(dport=4, sport=2)'.format(ipv4_mac),
    'symmetric_packet3': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/{}/UDP(dport=4, sport=2)'.format(swap_ipv4_mac),
    'symmetric_packet4': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/{}/UDP(dport=2, sport=4)'.format(ipv4_mac),
    'symmetric_packet5': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/{}/UDP(dport=2, sport=4)'.format(ipv4_mac),
}

mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_symmetric = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ipv4_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt['basic_packet'],
            'action': {'save_hash': 'gtpogre-ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt['symmetric_packet1'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt['symmetric_packet2'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt['symmetric_packet3'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt['symmetric_packet4'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt['symmetric_packet5'],
            'action': 'check_hash_same',
        },
        {   # unmatch MAC_IPV4_GRE_IPV4_GTPU_EH_IPV6_UDP
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/{}/UDP(dport=2, sport=4)'.format(ipv6_match_ip2),
            'action': 'check_no_hash',
        },
        {   # unmatch MAC_IPV4_GRE_IPV4_GTPU_EH_IPV4_TCP
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/{}/TCP(dport=2, sport=4)'.format(ipv4_mac),
            'action': 'check_no_hash',
        },
        {   # unmatch MAC_IPV4_GRE_IPV4_GTPU_IPV4_UDP
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/{}/UDP(dport=2, sport=4)'.format(ipv4_mac),
            'action': 'check_no_hash',
        },
    ],
    'post_test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_pkt['basic_packet'],
            'action': 'check_no_hash',
        }
    ]
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_pkt = {
    'basic_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/{}/TCP(dport=2, sport=4)'.format(ipv4_mac),
    'symmetric_packet1': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/{}/TCP(dport=2, sport=4)'.format(swap_ipv4_mac),
    'symmetric_packet2': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/{}/TCP(dport=4, sport=2)'.format(ipv4_mac),
    'symmetric_packet3': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/{}/TCP(dport=4, sport=2)'.format(swap_ipv4_mac),
}

mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_pkt['basic_packet'],
            'action': {'save_hash': 'gtpogre-ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_pkt['symmetric_packet1'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_pkt['symmetric_packet2'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_pkt['symmetric_packet3'],
            'action': 'check_hash_same',
        },
        {   # unmatch MAC_IPV4_GRE_IPV4_GTPU_UL_IPV6_TCP
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/{}/TCP(dport=2, sport=4)'.format(ipv6_match_ip2),
            'action': 'check_no_hash',
        },
        {   # unmatch MAC_IPV4_GRE_IPV4_GTPU_UL_IPV4_UDP
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/{}/UDP(dport=2, sport=4)'.format(ipv4_mac),
            'action': 'check_no_hash',
        },
        {  # unmatch MAC_IPV4_GRE_IPV4_GTPU_DL_IPV4_TCP
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/{}/TCP(dport=2, sport=4)'.format(ipv4_mac),
            'action': 'check_no_hash',
        },
        {  # unmatch MAC_IPV4_GRE_IPV4_GTPU_IPV4_TCP
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/{}/TCP(dport=2, sport=4)'.format(ipv4_mac),
            'action': 'check_no_hash',
        },
    ],
    'post_test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_pkt['basic_packet'],
        'action': 'check_no_hash',
        }
    ]
}

mac_ipv4_gre_ipv4_gtpu_dl_ipv4_pkt = {
    'basic_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/{}'.format(ipv4_mac),
    'symmetric_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/{}'.format(swap_ipv4_mac)
}

mac_ipv4_gre_ipv4_gtpu_dl_ipv4_symmetric = {
    'sub_casename': 'mac_ipv4_gre_ipv4_gtpu_dl_ipv4_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_dl_ipv4_pkt['basic_packet'],
            'action': {'save_hash': 'gtpogre-ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_dl_ipv4_pkt['symmetric_packet'],
            'action': 'check_hash_same',
        },
        {   # unmatch MAC_IPV4_GRE_IPV4_GTPU_DL_IPV6
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/{}'.format(ipv6_match_ip2),
            'action': 'check_no_hash',
        },
        {   # unmatch MMAC_IPV4_GRE_IPV4_GTPU_UL_IPV4
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/{}'.format(ipv4_mac),
            'action': 'check_no_hash',
        },
        {   # unmatch MAC_IPV4_GRE_IPV4_GTPU_IPV4
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/{}'.format(ipv4_mac),
            'action': 'check_no_hash',
        },
    ],
    'post_test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_gtpu_dl_ipv4_pkt['basic_packet'],
            'action': 'check_no_hash',
        }
    ]
}

# packet
ipv4_packet = '/IP()/GRE()/IP()/'
ipv6_ipv4_packet = '/IPv6()/GRE()/IP()/'
ipv4_ipv6_packet = '/IP()/GRE()/IPv6()/'
ipv6_ipv6_packet = '/IPv6()/GRE()/IPv6()/'

mac_ipv6_gre_ipv4_gtpu_ipv4_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv4_symmetric).replace(ipv4_packet, ipv6_ipv4_packet)
                                             .replace(ipv4_case_name, ipv6_ipv4_name)
                                             .replace(ipv4_rule, ipv6_ipv4_rule))

mac_ipv6_gre_ipv4_gtpu_eh_ipv4_udp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_symmetric).replace(ipv4_packet, ipv6_ipv4_packet)
                                             .replace(ipv4_case_name, ipv6_ipv4_name)
                                             .replace(ipv4_rule, ipv6_ipv4_rule))

mac_ipv6_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric).replace(ipv4_packet, ipv6_ipv4_packet)
                                             .replace(ipv4_case_name, ipv6_ipv4_name)
                                             .replace(ipv4_rule, ipv6_ipv4_rule))

mac_ipv6_gre_ipv4_gtpu_dl_ipv4_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_dl_ipv4_symmetric).replace(ipv4_packet, ipv6_ipv4_packet)
                                             .replace(ipv4_case_name, ipv6_ipv4_name)
                                             .replace(ipv4_rule, ipv6_ipv4_rule))

# IPV6+IPV4+IPV4
mac_ipv4_gre_ipv6_gtpu_ipv4_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv4_symmetric).replace(ipv4_packet, ipv4_ipv6_packet)
                                             .replace(ipv4_case_name, ipv4_ipv6_name)
                                             .replace(ipv4_rule, ipv4_ipv6_rule))

mac_ipv4_gre_ipv6_gtpu_eh_ipv4_udp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_symmetric).replace(ipv4_packet, ipv4_ipv6_packet)
                                             .replace(ipv4_case_name, ipv4_ipv6_name)
                                             .replace(ipv4_rule, ipv4_ipv6_rule))

mac_ipv4_gre_ipv6_gtpu_ul_ipv4_tcp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric).replace(ipv4_packet, ipv4_ipv6_packet)
                                             .replace(ipv4_case_name, ipv4_ipv6_name)
                                             .replace(ipv4_rule, ipv4_ipv6_rule))

mac_ipv4_gre_ipv6_gtpu_dl_ipv4_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_dl_ipv4_symmetric).replace(ipv4_packet, ipv4_ipv6_packet)
                                             .replace(ipv4_case_name, ipv4_ipv6_name)
                                             .replace(ipv4_rule, ipv4_ipv6_rule))

# IPV6+IPV6+IPV4
mac_ipv6_gre_ipv6_gtpu_ipv4_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv4_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv6_gre_ipv6_gtpu_eh_ipv4_udp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv6_gre_ipv6_gtpu_ul_ipv4_tcp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv6_gre_ipv6_gtpu_dl_ipv4_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_dl_ipv4_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

# IPV4+IPV4+IPV6
ipv4_mac = 'IP(src="1.1.2.6", dst="1.1.2.7")'
swap_ipv4_mac = 'IP(src="1.1.2.7", dst="1.1.2.6")'

ipv6_mac = 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")'
swap_ipv6_mac = 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")'

mac_ipv4_gre_ipv4_gtpu_ipv6_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv4_symmetric).replace('ipv4_symmetric', 'ipv6_symmetric')
                                             .replace(ipv4_mac, ipv6_mac)
                                             .replace(swap_ipv4_mac, swap_ipv6_mac)
                                             .replace(ipv6_match_ip2, ipv4_mac)
                                             .replace('/ gtpu / ipv4 /', '/ gtpu / ipv6 /')
                                             .replace('symmetric_toeplitz types ipv4', 'symmetric_toeplitz types ipv6'))

mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_symmetric).replace('ipv4_symmetric', 'ipv6_symmetric')
                                             .replace(ipv4_mac, ipv6_mac)
                                             .replace(swap_ipv4_mac, swap_ipv6_mac)
                                             .replace(ipv6_match_ip2, ipv4_mac)
                                             .replace('/ gtp_psc / ipv4 / udp /', '/ gtp_psc / ipv6 / udp /')
                                             .replace('symmetric_toeplitz types ipv4', 'symmetric_toeplitz types ipv6'))

mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric).replace('ipv4_symmetric', 'ipv6_symmetric')
                                             .replace(ipv4_mac, ipv6_mac)
                                             .replace(swap_ipv4_mac, swap_ipv6_mac)
                                             .replace(ipv6_match_ip2, ipv4_mac)
                                             .replace('/ gtp_psc pdu_t is 1 / ipv4 / tcp /', '/ gtp_psc pdu_t is 1 / ipv6 / tcp /')
                                             .replace('symmetric_toeplitz types ipv4', 'symmetric_toeplitz types ipv6'))

mac_ipv4_gre_ipv4_gtpu_dl_ipv6_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_dl_ipv4_symmetric).replace('ipv4_symmetric', 'ipv6_symmetric')
                                             .replace(ipv4_mac, ipv6_mac)
                                             .replace(swap_ipv4_mac, swap_ipv6_mac)
                                             .replace(ipv6_match_ip2, ipv4_mac)
                                             .replace('/ gtp_psc pdu_t is 0 / ipv4 /', '/ gtp_psc pdu_t is 0 / ipv6 /')
                                             .replace('symmetric_toeplitz types ipv4', 'symmetric_toeplitz types ipv6'))

# IPV4+IPV6+IPV6
mac_ipv4_gre_ipv6_gtpu_ipv6_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv6_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv4_gre_ipv6_gtpu_eh_ipv6_udp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv4_gre_ipv6_gtpu_ul_ipv6_tcp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv4_gre_ipv6_gtpu_dl_ipv6_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_dl_ipv6_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

# IPV6+IPV4+IPV6
mac_ipv6_gre_ipv4_gtpu_ipv6_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv6_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv6_gre_ipv4_gtpu_eh_ipv6_udp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv6_gre_ipv4_gtpu_ul_ipv6_tcp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv6_gre_ipv4_gtpu_dl_ipv6_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_dl_ipv6_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

# IPV6+IPV6+IPV6
mac_ipv6_gre_ipv6_gtpu_ipv6_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ipv6_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv6_gre_ipv6_gtpu_eh_ipv6_udp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv6_gre_ipv6_gtpu_ul_ipv6_tcp_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

mac_ipv6_gre_ipv6_gtpu_dl_ipv6_symmetric = eval(str(mac_ipv4_gre_ipv4_gtpu_dl_ipv6_symmetric).replace(ipv4_packet, ipv6_ipv6_packet)
                                             .replace(ipv4_case_name, ipv6_ipv6_name)
                                             .replace(ipv4_rule, ipv6_ipv6_rule))

exclusive_with_eh_without_eh = {
    'sub_casename': 'exclusive_eh_without_eh',
    'port_id': 0,
    'rule': ['flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end',
             'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end'],
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()',
            'action': 'check_hash_same',
        }
    ]
}

exclusive_with_l4_without_l4 = {
    'sub_casename': 'exclusive_with_l4_without_l4',
    'port_id': 0,
    'rule': ['flow create 0 ingress pattern eth / ipv6 / gre / ipv6 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
             'flow create 0 ingress pattern eth / ipv6 / gre / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end'],
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()',
            'action': 'check_hash_same',
        }
    ],
    'destroy_rule_1':[
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()',
            'action': 'check_hash_different',
        }
    ],
    'destroy_rule_0':[
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.5")',
            'action': 'check_no_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.14", dst="1.1.2.5")',
            'action': 'check_no_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP()/UDP()/GTP_U_Header()/IP(src="1.1.2.4", dst="1.1.2.15")',
            'action': 'check_no_hash',
        },
    ],
}

exclusive_eh_with_ul_without_eh_dl_ul = {
    'sub_casename': 'exclusive_eh_with_ul_without_eh_dl_ul',
    'port_id': 0,
    'rule': ['flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end',
             'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end'],
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()',
            'action': 'check_hash_same',
        }
    ],
    'destroy_rule_1': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.5")/UDP()',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.4", dst="1.1.2.15")/UDP()',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="1.1.2.14", dst="1.1.2.5")/UDP()',
            'action': 'check_hash_different',
        }
    ]
}

exclusive = [exclusive_with_eh_without_eh, exclusive_with_l4_without_l4, exclusive_eh_with_ul_without_eh_dl_ul]

class TestCVLAdvancedIAVFRSSGTPoGRE(TestCase):

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
        self.pci0 = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.pci1 = self.dut.ports_info[self.dut_ports[1]]['pci']
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]['intf']

        self.vf_driver = self.get_suite_cfg()['vf_driver']
        if self.vf_driver is None:
            self.vf_driver = 'vfio-pci'
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=self.kdriver)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port_0]['vfs_port']
        self.dut.send_expect('ip link set %s vf 0 mac 00:11:22:33:44:55' % self.pf0_intf, '#')
        self.vf0_pci = self.sriov_vfs_port[0].pci
        for port in self.sriov_vfs_port:
            port.bind_driver(self.vf_driver)

        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.rxq = 16
        self.rssprocess = RssProcessing(self, self.pmd_output, [self.tester_iface0, self.tester_iface1], self.rxq)
        self.logger.info('rssprocess.tester_ifaces: {}'.format(self.rssprocess.tester_ifaces))
        self.logger.info('rssprocess.test_case: {}'.format(self.rssprocess.test_case))

    def set_up(self):
        """
        Run before each test case.
        """
        #if "toeplitz" in self.running_case:
        #    self.skip_case(False, "not support the case")
        #else:
        self.launch_testpmd()

    def tear_down(self):
        # destroy all flow rule on port 0
        #if "toeplitz" not in self.running_case:
        self.pmd_output.execute_cmd("quit", "# ")

    def tear_down_all(self):
        self.destroy_vf()

    def destroy_vf(self):
        self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)

    def launch_testpmd(self):
        # if support add --disable-rss
        param = "--rxq=16 --txq=16 --rxd=384 --txd=384 --disable-rss"
        self.pmd_output.start_testpmd(cores="1S/4C/1T", param=param,
                                          eal_param=f"-a {self.vf0_pci}", socket=self.ports_socket)
        '''self.symmetric = symmetric
        if symmetric:
            # Need config rss in setup
            self.pmd_output.execute_cmd("port config all rss all")'''
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")
        res = self.pmd_output.wait_link_status_up('all', timeout=15)
        self.verify(res is True, 'there have port link is down')

    def test_mac_ipv4_gre_ipv4_gtpu_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ipv4_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ipv4_udp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_eh_ipv4_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_eh_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ul_ipv4_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_dl_ipv4_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_dl_ipv4_udp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_dl_ipv4_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ipv4_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ipv4_udp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ipv4_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_eh_ipv4_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_eh_ipv4_udp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_eh_ipv4_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ul_ipv4_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ul_ipv4_udp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ul_ipv4_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_dl_ipv4_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_dl_ipv4_udp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_dl_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ipv4_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ipv4_udp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_eh_ipv4_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_eh_ipv4_udp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_eh_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ul_ipv4_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ul_ipv4_udp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ul_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_dl_ipv4_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_dl_ipv4_udp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_dl_ipv4_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ipv4_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ipv4_udp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ipv4_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_eh_ipv4_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_eh_ipv4_udp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_eh_ipv4_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ul_ipv4_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ul_ipv4_udp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ul_ipv4_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv4_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_dl_ipv4_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv4_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_dl_ipv4_udp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv4_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_dl_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ipv6_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ipv6_udp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ipv6_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_eh_ipv6_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_eh_ipv6_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ul_ipv6_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_dl_ipv6_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_dl_ipv6_udp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_dl_ipv6_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ipv6_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ipv6_udp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ipv6_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_eh_ipv6_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_eh_ipv6_udp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_eh_ipv6_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ul_ipv6_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ul_ipv6_udp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ul_ipv6_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_dl_ipv6_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_dl_ipv6_udp_toeplitz)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_dl_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ipv6_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ipv6_udp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_eh_ipv6_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_eh_ipv6_udp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_eh_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ul_ipv6_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ul_ipv6_udp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ul_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_dl_ipv6_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_dl_ipv6_udp_toeplitz)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_dl_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ipv6_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ipv6_udp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_eh_ipv6_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_eh_ipv6_udp_toeplitz)

    def mac_ipv6_gre_ipv6_gtpu_eh_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_eh_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ul_ipv6_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ul_ipv6_udp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ul_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv6_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_dl_ipv6_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv6_udp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_dl_ipv6_udp_toeplitz)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv6_tcp_toeplitz(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_dl_ipv6_tcp_toeplitz)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv4_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ipv4_symmetric)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_eh_ipv4_udp_symmetric)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv4_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_dl_ipv4_symmetric)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv4_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ipv4_symmetric)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv4_udp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_eh_ipv4_udp_symmetric)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ul_ipv4_tcp_symmetric)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv4_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_dl_ipv4_symmetric)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv4_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ipv4_symmetric)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv4_udp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_eh_ipv4_udp_symmetric)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv4_tcp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ul_ipv4_tcp_symmetric)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv4_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_dl_ipv4_symmetric)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv4_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ipv4_symmetric)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv4_udp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_eh_ipv4_udp_symmetric)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv4_tcp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ul_ipv4_tcp_symmetric)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv4_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_dl_ipv4_symmetric)

    def test_mac_ipv4_gre_ipv4_gtpu_ipv6_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ipv6_symmetric)

    def test_mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_eh_ipv6_udp_symmetric)

    def test_mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_ul_ipv6_tcp_symmetric)

    def test_mac_ipv4_gre_ipv4_gtpu_dl_ipv6_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_gtpu_dl_ipv6_symmetric)

    def test_mac_ipv4_gre_ipv6_gtpu_ipv6_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ipv6_symmetric)

    def test_mac_ipv4_gre_ipv6_gtpu_eh_ipv6_udp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_eh_ipv6_udp_symmetric)

    def test_mac_ipv4_gre_ipv6_gtpu_ul_ipv6_tcp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_ul_ipv6_tcp_symmetric)

    def test_mac_ipv4_gre_ipv6_gtpu_dl_ipv6_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_gtpu_dl_ipv6_symmetric)

    def test_mac_ipv6_gre_ipv4_gtpu_ipv6_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ipv6_symmetric)

    def test_mac_ipv6_gre_ipv4_gtpu_eh_ipv6_udp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_eh_ipv6_udp_symmetric)

    def test_mac_ipv6_gre_ipv4_gtpu_ul_ipv6_tcp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_ul_ipv6_tcp_symmetric)

    def test_mac_ipv6_gre_ipv4_gtpu_dl_ipv6_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_gtpu_dl_ipv6_symmetric)

    def test_mac_ipv6_gre_ipv6_gtpu_ipv6_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ipv6_symmetric)

    def test_mac_ipv6_gre_ipv6_gtpu_eh_ipv6_udp_symmetric(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_eh_ipv6_udp_symmetric)

    def test_mac_ipv6_gre_ipv6_gtpu_ul_ipv6_tcp_symmetric(self):
        """

        """
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_ul_ipv6_tcp_symmetric)

    def test_mac_ipv6_gre_ipv6_gtpu_dl_ipv6_symmetric(self):
        """
        mac_ipv6_gre_ipv6_gtpu_dl_ipv6_symmetric
        """
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_gtpu_dl_ipv6_symmetric)

    def test_negative(self):
        """
        negative test case
        """
        rules = ['flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv4-udp gtpu end key_len 0 queues end / end',
                 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc is 1 / ipv4 / udp / end actions rss types ipv6-tcp end key_len 0 queues end / end',
                 'flow create 0 ingress pattern eth / ipv6 / gre / ipv4 / udp / gtpu / gtp_psc is 1 / ipv4 / end actions rss types ipv4 l4-dst-only end key_len 0 queues end / end',
                 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l2-src-only end key_len 0 queues end / end',
                 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc is 1 / ipv6 / tcp / end actions rss func symmetric_toeplitz types l3-src-only end key_len 0 queues end / end',
                 'flow create 0 ingress pattern eth / ipv6 / gre / ipv6 / udp / gtpu / gtp_psc is 1 / ipv4 / end actions rss func symmetric_toeplitz types l4-src-only end key_len 0 queues end / end']
        for rule in rules:
            rule_index = rules.index(rule)
            out = self.pmd_output.execute_cmd(rule)
            check_param = 'Failed to create flow' if rule_index == 3 else 'Bad arguments'
            print("check_param===%s" % check_param)
            self.verify(check_param in out, 'create rule successfully, not as expected')

    def check_exclusive_cases(self, case_list):

        for case in case_list:
            self.logger.info('===================Test sub case: {}================'.format(case['sub_casename']))
            rule_ids = self.rssprocess.create_rule(rule=case['rule'], check_stats=True)
            self.rssprocess.check_rule(rule_list=rule_ids)
            self.rssprocess.handle_tests(case['test'])
            if 'destroy_rule_1' in case:
                self.rssprocess.destroy_rule(rule_id=1)
                self.rssprocess.handle_tests(case['destroy_rule_1'])
            if case['sub_casename'] == 'exclusive_with_l4_without_l4':
                self.pmd_output.execute_cmd('flow flush 0')
                rule_ids = self.rssprocess.create_rule(rule=case['rule'], check_stats=True)
                self.rssprocess.check_rule(rule_list=rule_ids)
                if 'destroy_rule_0' in case:
                    self.rssprocess.destroy_rule(rule_id=0)
                    self.rssprocess.handle_tests(case['destroy_rule_0'])
            self.pmd_output.execute_cmd('flow flush 0')

    def test_exclusive(self):
        """
        exclusive test case
        """
        rule1 = 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 13 / mark id 13 / end'
        rule2 = 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / udp / gtpu / gtp_psc / ipv4 src is 1.1.2.4 dst is 1.1.2.5 / end actions queue index 3 / mark id 3 / end'
        self.check_exclusive_cases(exclusive)
        rule_ids = self.rssprocess.create_rule(rule=rule1, check_stats=True)
        self.rssprocess.check_rule(rule_list=rule_ids)
        out = self.pmd_output.execute_cmd(rule2)
        self.verify('Failed to create flow' in out, 'create rule successfully, not as expected')
        self.pmd_output.execute_cmd('flow flush 0')
        rule_ids = self.rssprocess.create_rule(rule=rule2, check_stats=True)
        self.rssprocess.check_rule(rule_list=rule_ids)
        out = self.pmd_output.execute_cmd(rule1)
        self.verify('Failed to create flow' in out, 'create rule successfully, not as expected')
        self.pmd_output.execute_cmd('flow flush 0')


