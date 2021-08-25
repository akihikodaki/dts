# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
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
from packet import Packet
from pmd_output import PmdOutput
from test_case import TestCase, skip_unsupported_pkg, check_supported_nic
from rte_flow_common import RssProcessing


mac_ipv4_gtpu_ipv4_basic = {
    'ipv4-nonfrag': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
    'ipv4-frag': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
    'ipv4-icmp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
    'ipv4-udp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
}

mac_ipv4_gtpu_ipv4_l3src_changed_pkt = eval(str(mac_ipv4_gtpu_ipv4_basic).replace('192.168.0.2', '192.168.1.2'))
mac_ipv4_gtpu_ipv4_l3dst_changed_pkt = eval(str(mac_ipv4_gtpu_ipv4_basic).replace('192.168.0.1', '192.168.1.1'))
mac_ipv4_gtpu_ipv4_unmatched_pkt = [
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
]

mac_ipv4_gtpu_ipv4_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3dst_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3src_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3dst_changed_pkt['ipv4-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3src_changed_pkt['ipv4-frag'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3dst_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3src_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3dst_changed_pkt['ipv4-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3src_changed_pkt['ipv4-udp'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_ipv4_basic['ipv4-nonfrag'],
                mac_ipv4_gtpu_ipv4_basic['ipv4-frag'],
                mac_ipv4_gtpu_ipv4_basic['ipv4-icmp'],
                mac_ipv4_gtpu_ipv4_basic['ipv4-udp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv4_l3src_only = eval(str(mac_ipv4_gtpu_ipv4_l3dst_only)
                                     .replace('mac_ipv4_gtpu_ipv4_l3dst', 'mac_ipv4_gtpu_ipv4_l3src')
                                     .replace('l3-dst-only', 'l3-src-only')
                                     .replace('check_hash_same', 'hash_check_different')
                                     .replace('check_hash_different', 'check_hash_same')
                                     .replace('hash_check_different', 'check_hash_different'))
mac_ipv4_gtpu_ipv4_all = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3dst_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3src_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-nonfrag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3dst_changed_pkt['ipv4-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3src_changed_pkt['ipv4-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-frag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3dst_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3src_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-icmp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3dst_changed_pkt['ipv4-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3src_changed_pkt['ipv4-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-udp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_ipv4_basic['ipv4-nonfrag'],
                mac_ipv4_gtpu_ipv4_basic['ipv4-frag'],
                mac_ipv4_gtpu_ipv4_basic['ipv4-icmp'],
                mac_ipv4_gtpu_ipv4_basic['ipv4-udp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv4_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-nonfrag'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-nonfrag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-frag'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-frag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-icmp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-icmp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['ipv4-udp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_ipv4_basic['ipv4-nonfrag'],
                mac_ipv4_gtpu_ipv4_basic['ipv4-frag'],
                mac_ipv4_gtpu_ipv4_basic['ipv4-icmp'],
                mac_ipv4_gtpu_ipv4_basic['ipv4-udp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv4_toeplitz = [mac_ipv4_gtpu_ipv4_l3dst_only, mac_ipv4_gtpu_ipv4_l3src_only,
                               mac_ipv4_gtpu_ipv4_all, mac_ipv4_gtpu_ipv4_gtpu]

mac_ipv4_gtpu_ipv4_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'action': {'save_hash': 'nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
            'action': {'save_hash': 'frag'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
            'action': {'save_hash': 'icmp'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            'action': 'check_hash_same',
        },
        {   # unmatch MAC_IPV4_GTPU_IPV6 nonfrag
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': 'check_hash_same',
        },
        {   # unmatch MAC_IPV4_GTPU_EH_IPV4
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'action': 'save_hash',
        },
        {   # unmatch MAC_IPV4_GTPU_EH_IPV4
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'action': {'save_hash': 'nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': {'check_hash_same': 'nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
            'action': {'save_hash': 'frag'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            'action': {'check_hash_same': 'frag'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
            'action': {'save_hash': 'icmp'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'icmp'},
        },
    ],
}

mac_ipv4_gtpu_ipv6_symmetric = eval(str(mac_ipv4_gtpu_ipv4_symmetric).replace('IPv6', 'IPv61')
                                    .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                    .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                    .replace(', frag=6)', ')/IPv6ExtHdrFragment()')
                                    .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                    .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                    .replace('gtpu / ipv4', 'gtpu / ipv6').replace('types ipv4', 'types ipv6')
                                    )

mac_ipv4_gtpu_ipv4_udp_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': {'save_hash': 'basic_with_rule'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': {'save_hash': 'basic_with_rule'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': {'check_hash_different': 'basic_with_rule'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': {'save_hash': 'basic_with_rule'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': {'check_hash_different': 'basic_with_rule'},
        },
    ],
}

mac_ipv4_gtpu_ipv6_udp_symmetric = eval(str(mac_ipv4_gtpu_ipv4_udp_symmetric).replace('IPv6', 'IPv61')
                                        .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                        .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                        .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                        .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                        .replace('gtpu / ipv4', 'gtpu / ipv6').replace('types ipv4-udp', 'types ipv6-udp')
                                        )

mac_ipv4_gtpu_ipv4_tcp_symmetric = eval(str(mac_ipv4_gtpu_ipv4_udp_symmetric).replace('TCP(', 'TCP1(')
                                        .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                        .replace('udp / end', 'tcp / end ').replace('ipv4-udp', 'ipv4-tcp')
                                        .replace('udp_symmetric', 'tcp_symmetric'))

mac_ipv4_gtpu_ipv6_tcp_symmetric = eval(str(mac_ipv4_gtpu_ipv4_tcp_symmetric).replace('IPv6', 'IPv61')
                                        .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                        .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                        .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                        .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                        .replace('gtpu / ipv4', 'gtpu / ipv6').replace('types ipv4-tcp', 'types ipv6-tcp')
                                        )

mac_ipv4_gtpu_eh_dl_ipv4_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP()/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP()/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP()/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
}
mac_ipv4_gtpu_eh_ul_ipv4_symmetric = eval(str(mac_ipv4_gtpu_eh_dl_ipv4_symmetric)
                                          .replace('(type=1', '(type=2')
                                          .replace('(type=0', '(type=1')
                                          .replace('(type=2', '(type=0')
                                          .replace('eh_dl', 'eh_ul')
                                          .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                                          )

mac_ipv4_gtpu_eh_ipv4_symmetric = [mac_ipv4_gtpu_eh_dl_ipv4_symmetric,  mac_ipv4_gtpu_eh_ul_ipv4_symmetric]

mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_different',
        },
    ],
}
mac_ipv4_gtpu_eh_ul_ipv4_udp_symmetric = eval(str(mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric)
                                              .replace('(type=1', '(type=2')
                                              .replace('(type=0', '(type=1')
                                              .replace('(type=2', '(type=0')
                                              .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                                              .replace('eh_dl', 'eh_ul'))
mac_ipv4_gtpu_eh_ipv4_udp_symmetric = [mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric, mac_ipv4_gtpu_eh_ul_ipv4_udp_symmetric]

mac_ipv4_gtpu_eh_ipv4_tcp_symmetric = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                                        .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                                        .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                       for element in mac_ipv4_gtpu_eh_ipv4_udp_symmetric]

mac_ipv4_gtpu_eh_ipv6_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_symmetric).replace('IPv6', 'IPv61')
                                       .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                       .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                       .replace(', frag=6)', ')/IPv6ExtHdrFragment()')
                                       .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                       .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                       .replace('ipv4 / end', 'ipv6 / end').replace('types ipv4', 'types ipv6')
                                       .replace('ipv4_symmetric', 'ipv6_symmetric')
                                       )

mac_ipv4_gtpu_eh_ipv6_udp_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_udp_symmetric).replace('IPv6', 'IPv61')
                                        .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                        .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                        .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                        .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                        .replace('ipv4 / udp / end', 'ipv6 / udp / end').replace('types ipv4-udp', 'types ipv6-udp')
                                        .replace('ipv4_udp_symmetric', 'ipv6_udp_symmetric')
                                        )


mac_ipv4_gtpu_eh_ipv6_tcp_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_tcp_symmetric).replace('IPv6', 'IPv61')
                                        .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                        .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                        .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                        .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                        .replace('ipv4 / tcp / end', 'ipv6 / tcp / end').replace('types ipv4-tcp', 'types ipv6-tcp')
                                        .replace('ipv4_tcp_symmetric', 'ipv6_tcp_symmetric')
                                        )

mac_ipv4_gtpu_ipv4_udp_basic = {
        'ipv4-udp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
}

mac_ipv4_gtpu_ipv4_udp_unmatch = [
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)'
]
mac_ipv4_gtpu_ipv4_udp_l3dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv4_udp_l3src = eval(str(mac_ipv4_gtpu_ipv4_udp_l3dst)
                                    .replace('mac_ipv4_gtpu_ipv4_udp_l3dst', 'mac_ipv4_gtpu_ipv4_udp_l3src')
                                    .replace('l3-dst-only', 'l3-src-only')
                                    .replace('check_hash_same', 'hash_check_different')
                                    .replace('check_hash_different', 'check_hash_same')
                                    .replace('hash_check_different', 'check_hash_different'))

mac_ipv4_gtpu_ipv4_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33').replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv4_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32').replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv4_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33').replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32').replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_ipv4_udp_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32')
                                                       .replace('192.168.0', '192.168.1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_ipv4_udp_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=32')
                                                       .replace('192.168.0', '192.168.1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv4_udp_all = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv4_udp_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0', '192.168.1')
                                                       .replace('sport=22', 'sport=32')
                                                       .replace('dport=23', 'dport=33'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv4_udp_ipv4 = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_ipv4',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32')
                                                       .replace('dport=23', 'dport=33'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}


mac_ipv4_gtpu_ipv4_udp_toeplitz = [mac_ipv4_gtpu_ipv4_udp_l3dst, mac_ipv4_gtpu_ipv4_udp_l3src,
                                   mac_ipv4_gtpu_ipv4_udp_l3dst_l4src, mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst,
                                   mac_ipv4_gtpu_ipv4_udp_l3src_l4src, mac_ipv4_gtpu_ipv4_udp_l3src_l4dst,
                                   mac_ipv4_gtpu_ipv4_udp_l4src, mac_ipv4_gtpu_ipv4_udp_l4dst,
                                   mac_ipv4_gtpu_ipv4_udp_all, mac_ipv4_gtpu_ipv4_udp_gtpu, mac_ipv4_gtpu_ipv4_udp_ipv4]

mac_ipv4_gtpu_ipv4_tcp_toeplitz = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                        .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                        .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                   for element in mac_ipv4_gtpu_ipv4_udp_toeplitz]

mac_ipv4_gtpu_ipv6_basic = {
    'ipv6-nonfrag': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    'ipv6-frag': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
    'ipv6-icmp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
    'ipv6-udp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/("X"*480)',
}

mac_ipv4_gtpu_ipv6_l3src_changed_pkt = eval(str(mac_ipv4_gtpu_ipv6_basic).replace('ABAB', '1212'))
mac_ipv4_gtpu_ipv6_l3dst_changed_pkt = eval(str(mac_ipv4_gtpu_ipv6_basic).replace('CDCD', '3434'))
mac_ipv4_gtpu_ipv6_unmatched_pkt = [
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)',
]
mac_ipv4_gtpu_ipv6_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['ipv6-nonfrag'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['ipv6-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['ipv6-frag'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['ipv6-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['ipv6-icmp'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['ipv6-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['ipv6-udp'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_ipv6_basic['ipv6-nonfrag'],
                mac_ipv4_gtpu_ipv6_basic['ipv6-frag'],
                mac_ipv4_gtpu_ipv6_basic['ipv6-icmp'],
                mac_ipv4_gtpu_ipv6_basic['ipv6-udp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_l3src_only = eval(str(mac_ipv4_gtpu_ipv6_l3dst_only)
                                     .replace('mac_ipv4_gtpu_ipv6_l3dst', 'mac_ipv4_gtpu_ipv6_l3src')
                                     .replace('l3-dst-only', 'l3-src-only')
                                     .replace('check_hash_same', 'hash_check_different')
                                     .replace('check_hash_different', 'check_hash_same')
                                     .replace('hash_check_different', 'check_hash_different'))
mac_ipv4_gtpu_ipv6_all = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-nonfrag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['ipv6-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['ipv6-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-frag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['ipv6-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['ipv6-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-icmp'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['ipv6-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['ipv6-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-udp'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_ipv6_basic['ipv6-nonfrag'],
                mac_ipv4_gtpu_ipv6_basic['ipv6-frag'],
                mac_ipv4_gtpu_ipv6_basic['ipv6-icmp'],
                mac_ipv4_gtpu_ipv6_basic['ipv6-udp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-nonfrag'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-nonfrag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-frag'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-frag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-icmp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-icmp'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['ipv6-udp'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_ipv6_basic['ipv6-nonfrag'],
                mac_ipv4_gtpu_ipv6_basic['ipv6-frag'],
                mac_ipv4_gtpu_ipv6_basic['ipv6-icmp'],
                mac_ipv4_gtpu_ipv6_basic['ipv6-udp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_toeplitz = [mac_ipv4_gtpu_ipv6_l3dst_only, mac_ipv4_gtpu_ipv6_l3src_only,
                               mac_ipv4_gtpu_ipv6_all, mac_ipv4_gtpu_ipv6_gtpu]

mac_ipv4_gtpu_ipv6_udp_basic = {
        'ipv6-udp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
}
mac_ipv4_gtpu_ipv6_udp_unmatch = [
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)'
]
mac_ipv4_gtpu_ipv6_udp_l3dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_udp_l3src = eval(str(mac_ipv4_gtpu_ipv6_udp_l3dst)
                                    .replace('mac_ipv4_gtpu_ipv6_udp_l3dst', 'mac_ipv4_gtpu_ipv6_udp_l3src')
                                    .replace('l3-dst-only', 'l3-src-only')
                                    .replace('check_hash_same', 'hash_check_different')
                                    .replace('check_hash_different', 'check_hash_same')
                                    .replace('hash_check_different', 'check_hash_different'))

mac_ipv4_gtpu_ipv6_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33').replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32').replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_ipv6_udp_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32')
                                                       .replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_ipv6_udp_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=32')
                                                       .replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_udp_all = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_udp_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212').replace('CDCD', '3434')
                                                       .replace('sport=22', 'sport=32')
                                                       .replace('dport=23', 'dport=33'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_udp_ipv6 = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_ipv6',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32')
                                                       .replace('dport=23', 'dport=33'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_ipv6_udp_toeplitz = [mac_ipv4_gtpu_ipv6_udp_l3dst, mac_ipv4_gtpu_ipv6_udp_l3src,
                                   mac_ipv4_gtpu_ipv6_udp_l3dst_l4src, mac_ipv4_gtpu_ipv6_udp_l3dst_l4dst,
                                   mac_ipv4_gtpu_ipv6_udp_l3src_l4src, mac_ipv4_gtpu_ipv6_udp_l3src_l4dst,
                                   mac_ipv4_gtpu_ipv6_udp_l4src, mac_ipv4_gtpu_ipv6_udp_l4dst,
                                   mac_ipv4_gtpu_ipv6_udp_all, mac_ipv4_gtpu_ipv6_udp_gtpu, mac_ipv4_gtpu_ipv6_udp_ipv6]

mac_ipv4_gtpu_ipv6_tcp_toeplitz = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                        .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                        .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                   for element in mac_ipv4_gtpu_ipv6_udp_toeplitz]

mac_ipv4_gtpu_eh_dl_ipv4_basic = {
    'ipv4-nonfrag': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
    'ipv4-frag': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
    'ipv4-icmp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
    'ipv4-udp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
    'ipv4-tcp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/TCP()/("X"*480)',
}

mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt = eval(str(mac_ipv4_gtpu_eh_dl_ipv4_basic).replace('192.168.0.2', '192.168.1.2'))
mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt = eval(str(mac_ipv4_gtpu_eh_dl_ipv4_basic).replace('192.168.0.1', '192.168.1.1'))
mac_ipv4_gtpu_eh_ipv4_unmatched_pkt = [
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
]

mac_ipv4_gtpu_eh_dl_ipv4_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['ipv4-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['ipv4-frag'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['ipv4-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['ipv4-udp'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['ipv4-tcp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['ipv4-tcp'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-nonfrag'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-frag'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-icmp'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-udp'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-tcp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4_l3src_only = eval(str(mac_ipv4_gtpu_eh_dl_ipv4_l3dst_only)
                                           .replace('eh_dl_ipv4_l3dst', 'eh_dl_ipv4_l3src')
                                           .replace('l3-dst-only', 'l3-src-only')
                                           .replace('check_hash_same', 'hash_check_different')
                                           .replace('check_hash_different', 'check_hash_same')
                                           .replace('hash_check_different', 'check_hash_different'))
mac_ipv4_gtpu_eh_dl_ipv4_all = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-nonfrag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-nonfrag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['ipv4-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['ipv4-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-frag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-frag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-icmp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-icmp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['ipv4-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['ipv4-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-udp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-udp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['ipv4-tcp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['ipv4-tcp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-tcp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-tcp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-nonfrag'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-frag'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-icmp'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-udp'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-tcp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-nonfrag'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-nonfrag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-frag'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-frag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-icmp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-icmp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-udp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-tcp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-tcp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-nonfrag'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-frag'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-icmp'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-udp'],
                mac_ipv4_gtpu_eh_dl_ipv4_basic['ipv4-tcp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4 = [mac_ipv4_gtpu_eh_dl_ipv4_l3dst_only, mac_ipv4_gtpu_eh_dl_ipv4_l3src_only,
                            mac_ipv4_gtpu_eh_dl_ipv4_all, mac_ipv4_gtpu_eh_dl_ipv4_gtpu]

mac_ipv4_gtpu_eh_ul_ipv4 = [eval(str(element).replace('(type=1', '(type=2')
                            .replace('(type=0', '(type=1').replace('(type=2', '(type=0')
                            .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                            .replace('eh_dl', 'eh_ul'))
                            for element in mac_ipv4_gtpu_eh_dl_ipv4]

mac_ipv4_gtpu_eh_ipv4_toeplitz = mac_ipv4_gtpu_eh_dl_ipv4 + mac_ipv4_gtpu_eh_ul_ipv4

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic = {
    'ipv4-nonfrag': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
    'ipv4-nonfrag_ul': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
    'ipv4-frag': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
    'ipv4-icmp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
    'ipv4-udp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic).replace('192.168.0.2', '192.168.1.2'))
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic).replace('192.168.0.1', '192.168.1.1'))
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_unmatched_pkt = [
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
]

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['ipv4-nonfrag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag_ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['ipv4-nonfrag_ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['ipv4-nonfrag_ul'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['ipv4-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['ipv4-frag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['ipv4-icmp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['ipv4-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['ipv4-udp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag_ul'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-frag'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-icmp'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-udp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_only = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_only)
                                           .replace('ul_dl_ipv4_l3dst', 'ul_dl_ipv4_l3src')
                                           .replace('l3-dst-only', 'l3-src-only')
                                           .replace('dst="192.168.0.1",src="192.168.1.2"', 'dst="192.168.0.1",src="192.168.1.3"')
                                           .replace('dst="192.168.1.1",src="192.168.0.2"', 'dst="192.168.0.1",src="192.168.1.2"')
                                           .replace('dst="192.168.0.1",src="192.168.1.3"', 'dst="192.168.1.1",src="192.168.0.2"')
                                                      )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_all = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag_ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['ipv4-nonfrag_ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['ipv4-nonfrag_ul'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag_ul'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag_ul'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['ipv4-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['ipv4-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-frag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-frag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['ipv4-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-icmp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-icmp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['ipv4-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['ipv4-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-udp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-udp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag_ul'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-frag'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-icmp'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-udp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag_ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag_ul'].replace('0x123456', '0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag_ul'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-frag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-frag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-icmp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-icmp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-udp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-udp'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-nonfrag_ul'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-frag'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-icmp'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['ipv4-udp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz = [mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_only,
                                                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_only,
                                                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_all,
                                                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_gtpu]

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic = {
    'dl': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
    'ul': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_unmatched_pkt = [
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
]

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('192.168.0.2', '192.168.1.2')
                                                                              .replace('sport=22, dport=23', 'sport=32, dport=33')
                                                                              .replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_only = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_only)
                                                      .replace('ul_dl_ipv4_udp_l3dst', 'ul_dl_ipv4_udp_l3src')
                                                      .replace('l3-dst-only', 'l3-src-only')
                                                      .replace('dst="192.168.0.1",src="192.168.1.2"', 'dst="192.168.0.1",src="192.168.1.3"')
                                                      .replace('dst="192.168.1.1",src="192.168.0.2"', 'dst="192.168.0.1",src="192.168.1.2"')
                                                      .replace('dst="192.168.0.1",src="192.168.1.3"', 'dst="192.168.1.1",src="192.168.0.2"')
                                                      )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('192.168.0.1', '192.168.1.1')
                .replace('dport=23', 'dport=33')
                .replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'].replace('192.168.0.1', '192.168.1.1')
                .replace('dport=23', 'dport=33')
                .replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4dst = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src)
                                                           .replace('udp_l3src_l4src', 'udp_l3src_l4dst')
                                                           .replace('l4-src-only', 'l4-dst-only')
                                                           .replace('sport=32, dport=23', 'sport=22, dport=34')
                                                           .replace('sport=22, dport=33', 'sport=32, dport=23')
                                                           )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4src = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src)
                                                           .replace('udp_l3src_l4src', 'udp_l3dst_l4src')
                                                           .replace('l3-src-only', 'l3-dst-only')
                                                           .replace('dst="192.168.0.1",src="192.168.1.2"', 'dst="192.168.0.1",src="192.168.1.3"')
                                                           .replace('dst="192.168.1.1",src="192.168.0.2"', 'dst="192.168.0.1",src="192.168.1.2"')
                                                           .replace('dst="192.168.0.1",src="192.168.1.3"', 'dst="192.168.1.1",src="192.168.0.2"')
                                                           )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4dst = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4src)
                                                           .replace('udp_l3dst_l4src', 'udp_l3dst_l4dst')
                                                           .replace('l3-src-only', 'l3-dst-only')
                                                           .replace('l4-src-only', 'l4-dst-only')
                                                           .replace('sport=32, dport=23', 'sport=22, dport=34')
                                                           .replace('sport=22, dport=33', 'sport=32, dport=23')
                                                           )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('192.168.0', '192.168.1')
            .replace('dport=23', 'dport=33')
            .replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'].replace('192.168.0', '192.168.1')
            .replace('dport=23', 'dport=33')
            .replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4dst_only = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only)
                                                          .replace('udp_l4src_only', 'udp_l4dst_only')
                                                          .replace('l4-src-only', 'l4-dst-only')
                                                          .replace('sport=32, dport=23', 'sport=22, dport=34')
                                                          .replace('sport=22, dport=33', 'sport=32, dport=23')
                                                          )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl']
            .replace('192.168.0.', '192.168.1.')
            .replace('sport=22, dport=23', 'sport=32, dport=33'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul']
            .replace('192.168.0.', '192.168.1.')
            .replace('sport=22, dport=23', 'sport=32, dport=33'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('0x123456', '0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_ipv4_6 = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_ipv4_6',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'].replace('sport=22', 'sport=32')
                                                                              .replace('dport=23', 'dport=33'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'].replace('sport=22', 'sport=32')
                                                                              .replace('dport=23', 'dport=33'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['dl'],
                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['ul'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz = [
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4dst,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4src,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4dst,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4dst_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_gtpu,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_ipv4_6,
]

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                           .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                           .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                      for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz]

mac_ipv4_gtpu_eh_without_ul_dl_ipv6_toeplitz = [eval(str(element).replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                     .replace('types ipv4', 'types ipv6')
                                                     .replace('ul_dl_ipv4', 'ul_dl_ipv6')
                                                     .replace(', frag=6)', ')/IPv6ExtHdrFragment()')
                                                     .replace('IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(dst="192.168.0.3", src="192.168.0.3"',)
                                                     .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                     .replace('IP(dst="192.168.1.1",src="192.168.0.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                     .replace('IP(dst="192.168.0.1",src="192.168.1.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"')
                                                     .replace('IP(dst="192.168.1.1",src="192.168.1.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"')
                                                     .replace('IP(dst="192.168.0.3",src="192.168.0.3"', 'IP(dst="192.168.0.1",src="192.168.0.2"'))
                                                for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz]

mac_ipv4_gtpu_eh_without_ul_dl_ipv6_udp_toeplitz = [eval(str(element).replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                         .replace('ipv4-udp', 'ipv6-udp')
                                                         .replace('ul_dl_ipv4_udp', 'ul_dl_ipv6_udp')
                                                         .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.1.1",src="192.168.0.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.0.1",src="192.168.1.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.1.1",src="192.168.1.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('rss types ipv4', 'rss types ipv6'))
                                                    for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz]

mac_ipv4_gtpu_eh_without_ul_dl_ipv6_tcp_toeplitz = [eval(str(element).replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                         .replace('ipv4 / tcp', 'ipv6 / tcp')
                                                         .replace('ipv4-tcp', 'ipv6-tcp')
                                                         .replace('ul_dl_ipv4_tcp', 'ul_dl_ipv6_tcp')
                                                         .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.1.1",src="192.168.0.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.0.1",src="192.168.1.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.1.1",src="192.168.1.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('rss types ipv4', 'rss types ipv6'))
                                                    for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz]

mac_ipv4_gtpu_eh_dl_ipv4_udp_basic = {
        'ipv4-udp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
}
mac_ipv4_gtpu_eh_dl_ipv4_udp_unmatch = [
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
]
mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src = eval(str(mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst)
                                          .replace('mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst', 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src')
                                          .replace('l3-dst-only', 'l3-src-only')
                                          .replace('check_hash_same', 'hash_check_different')
                                          .replace('check_hash_different', 'check_hash_same')
                                          .replace('hash_check_different', 'check_hash_different'))

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33').replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32').replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33').replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32')
                                                                         .replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_eh_dl_ipv4_udp_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32')
                                                                         .replace('192.168.0', '192.168.1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_eh_dl_ipv4_udp_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=32')
                                                                         .replace('192.168.0', '192.168.1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_all = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0', '192.168.1')
                                                                         .replace('sport=22', 'sport=32')
                                                                         .replace('dport=23', 'dport=33'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_ipv4 = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_ipv4',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'].replace('sport=22', 'sport=32')
                                                             .replace('dport=23', 'dport=33'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['ipv4-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_toeplitz = [mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst, mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src,
                                         mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4src, mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4dst,
                                         mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4src, mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4dst,
                                         mac_ipv4_gtpu_eh_dl_ipv4_udp_l4src, mac_ipv4_gtpu_eh_dl_ipv4_udp_l4dst,
                                         mac_ipv4_gtpu_eh_dl_ipv4_udp_all, mac_ipv4_gtpu_eh_dl_ipv4_udp_gtpu, mac_ipv4_gtpu_eh_dl_ipv4_udp_ipv4]

mac_ipv4_gtpu_eh_ul_ipv4_udp_toeplitz = [eval(str(element).replace('(type=1', '(type=2')
                                                          .replace('(type=0', '(type=1').replace('(type=2', '(type=0')
                                                          .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                                                          .replace('eh_dl', 'eh_ul'))
                                         for element in mac_ipv4_gtpu_eh_dl_ipv4_udp_toeplitz]

mac_ipv4_gtpu_eh_ipv4_udp_toeplitz = mac_ipv4_gtpu_eh_dl_ipv4_udp_toeplitz + mac_ipv4_gtpu_eh_ul_ipv4_udp_toeplitz

mac_ipv4_gtpu_eh_ipv4_tcp_toeplitz = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                                       .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                                       .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                      for element in mac_ipv4_gtpu_eh_ipv4_udp_toeplitz]

mac_ipv4_gtpu_eh_dl_ipv6_basic = {
    'ipv6-nonfrag': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    'ipv6-frag': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
    'ipv6-icmp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
    'ipv6-udp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/("X"*480)',
    'ipv6-tcp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP()/("X"*480)',
}

mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt = eval(str(mac_ipv4_gtpu_eh_dl_ipv6_basic).replace('ABAB', '1212'))
mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt = eval(str(mac_ipv4_gtpu_eh_dl_ipv6_basic).replace('CDCD', '3434'))
mac_ipv4_gtpu_eh_dl_ipv6_unmatched_pkt = [
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)',
]
mac_ipv4_gtpu_eh_dl_ipv6_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['ipv6-nonfrag'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['ipv6-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['ipv6-frag'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['ipv6-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['ipv6-icmp'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['ipv6-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['ipv6-udp'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['ipv6-tcp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['ipv6-tcp'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-nonfrag'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-frag'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-icmp'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-udp'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-tcp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_l3src_only = eval(str(mac_ipv4_gtpu_eh_dl_ipv6_l3dst_only)
                                     .replace('mac_ipv4_gtpu_eh_dl_ipv6_l3dst', 'mac_ipv4_gtpu_eh_dl_ipv6_l3src')
                                     .replace('l3-dst-only', 'l3-src-only')
                                     .replace('check_hash_same', 'hash_check_different')
                                     .replace('check_hash_different', 'check_hash_same')
                                     .replace('hash_check_different', 'check_hash_different'))
mac_ipv4_gtpu_eh_dl_ipv6_all = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-nonfrag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-nonfrag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['ipv6-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['ipv6-frag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-frag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-frag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['ipv6-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['ipv6-icmp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-icmp'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-icmp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['ipv6-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['ipv6-udp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-udp'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-udp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['ipv6-tcp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['ipv6-tcp'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-tcp'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-tcp'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-nonfrag'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-frag'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-icmp'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-udp'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-tcp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-nonfrag'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-nonfrag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-frag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-frag'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-frag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-icmp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-icmp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-icmp'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-udp'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-tcp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-tcp'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_unmatched_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-nonfrag'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-frag'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-icmp'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-udp'],
                mac_ipv4_gtpu_eh_dl_ipv6_basic['ipv6-tcp'],
            ],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_toeplitz = [mac_ipv4_gtpu_eh_dl_ipv6_l3dst_only, mac_ipv4_gtpu_eh_dl_ipv6_l3src_only,
                                     mac_ipv4_gtpu_eh_dl_ipv6_all, mac_ipv4_gtpu_eh_dl_ipv6_gtpu]

mac_ipv4_gtpu_eh_ul_ipv6_toeplitz = [eval(str(element).replace('(type=1', '(type=2')
                                                      .replace('(type=0', '(type=1').replace('(type=2', '(type=0')
                                                      .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                                                      .replace('eh_dl', 'eh_ul'))
                                     for element in mac_ipv4_gtpu_eh_dl_ipv6_toeplitz]

mac_ipv4_gtpu_eh_ipv6_toeplitz = mac_ipv4_gtpu_eh_dl_ipv6_toeplitz + mac_ipv4_gtpu_eh_ul_ipv6_toeplitz

mac_ipv4_gtpu_eh_dl_ipv6_udp_basic = {
        'ipv6-udp': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
}
mac_ipv4_gtpu_eh_dl_ipv6_udp_unmatch = [
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)',
    'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/("X"*480)',
]
mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src = eval(str(mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst)
                                          .replace('mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst', 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src')
                                          .replace('l3-dst-only', 'l3-src-only')
                                          .replace('check_hash_same', 'hash_check_different')
                                          .replace('check_hash_different', 'check_hash_same')
                                          .replace('hash_check_different', 'check_hash_different'))

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33').replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32').replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_eh_dl_ipv6_udp_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32')
                                                       .replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}
mac_ipv4_gtpu_eh_dl_ipv6_udp_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=32')
                                                       .replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_all = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212').replace('CDCD', '3434')
                                                       .replace('sport=22', 'sport=32')
                                                       .replace('dport=23', 'dport=33'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_unmatch,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_ipv6 = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_ipv6',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'].replace('sport=22', 'sport=32')
                                                       .replace('dport=23', 'dport=33'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['ipv6-udp'],
            'action': 'check_no_hash',
        },
    ]
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_toeplitz = [mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst, mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src,
                                   mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4src, mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4dst,
                                   mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4src, mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4dst,
                                   mac_ipv4_gtpu_eh_dl_ipv6_udp_l4src, mac_ipv4_gtpu_eh_dl_ipv6_udp_l4dst,
                                   mac_ipv4_gtpu_eh_dl_ipv6_udp_all, mac_ipv4_gtpu_eh_dl_ipv6_udp_gtpu, mac_ipv4_gtpu_eh_dl_ipv6_udp_ipv6]
mac_ipv4_gtpu_eh_ul_ipv6_udp_toeplitz = [eval(str(element).replace('(type=1', '(type=2')
                                                          .replace('(type=0', '(type=1').replace('(type=2', '(type=0')
                                                          .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                                                          .replace('eh_dl', 'eh_ul'))
                                         for element in mac_ipv4_gtpu_eh_dl_ipv6_udp_toeplitz]
mac_ipv4_gtpu_eh_ipv6_udp_toeplitz = mac_ipv4_gtpu_eh_dl_ipv6_udp_toeplitz + mac_ipv4_gtpu_eh_ul_ipv6_udp_toeplitz

mac_ipv4_gtpu_eh_ipv6_tcp_toeplitz = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                                       .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                                       .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                      for element in mac_ipv4_gtpu_eh_ipv6_udp_toeplitz]

default_pattern_ipv4_gtpu_eh_dl_ipv4_src = 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)'
default_pattern_ipv4_gtpu_eh_dl_ipv4_dst = 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)'
default_pattern_ipv4_gtpu_eh_dl_ipv6_src = 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)'
default_pattern_ipv4_gtpu_eh_dl_ipv6_dst = 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)'
default_pattern_support_ipv4 = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_gtpu',
    'port_id': 0,
    'rule': '',
    'test': [
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_src,
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst,
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_src.replace('(type=0', '(type=1'),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst.replace('(type=0', '(type=1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_src.replace('/("X"', '/UDP(sport=22,dport=23)/("X"'),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst.replace('/("X"', '/UDP(sport=22,dport=23)/("X"'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_src
            .replace('/("X"', '/UDP(sport=22,dport=23)/("X"')
            .replace('(type=0', '(type=1'),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst
            .replace('/("X"', '/UDP(sport=22,dport=23)/("X"')
            .replace('(type=0', '(type=1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_src.replace('/("X"', '/TCP(sport=22,dport=23)/("X"'),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst.replace('/("X"', '/TCP(sport=22,dport=23)/("X"'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_src
            .replace('/("X"', '/TCP(sport=22,dport=23)/("X"')
            .replace('(type=0', '(type=1'),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst
            .replace('/("X"', '/TCP(sport=22,dport=23)/("X"')
            .replace('(type=0', '(type=1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_src
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_src
            .replace('/("X"', '/UDP(sport=22,dport=23)/("X"')
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst
            .replace('/("X"', '/UDP(sport=22,dport=23)/("X"')
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_src
            .replace('/("X"', '/TCP(sport=22,dport=23)/("X"')
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst
            .replace('/("X"', '/TCP(sport=22,dport=23)/("X"')
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv6_src,
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst,
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv6_src.replace('(type=0', '(type=1'),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst.replace('(type=0', '(type=1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv6_src.replace('/("X"', '/UDP(sport=22,dport=23)/("X"'),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst.replace('/("X"', '/UDP(sport=22,dport=23)/("X"'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv6_src
            .replace('/("X"', '/UDP(sport=22,dport=23)/("X"')
            .replace('(type=0', '(type=1'),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst
            .replace('/("X"', '/UDP(sport=22,dport=23)/("X"')
            .replace('(type=0', '(type=1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv6_src.replace('/("X"', '/TCP(sport=22,dport=23)/("X"'),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst.replace('/("X"', '/TCP(sport=22,dport=23)/("X"'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv6_src
            .replace('/("X"', '/TCP(sport=22,dport=23)/("X"')
            .replace('(type=0', '(type=1'),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst
            .replace('/("X"', '/TCP(sport=22,dport=23)/("X"')
            .replace('(type=0', '(type=1'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv6_src
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv6_src
            .replace('/("X"', '/UDP(sport=22,dport=23)/("X"')
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst
            .replace('/("X"', '/UDP(sport=22,dport=23)/("X"')
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'check_hash_same',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv6_src
            .replace('/("X"', '/TCP(sport=22,dport=23)/("X"')
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'save_hash',
        },
        {
            'send_packet': default_pattern_ipv4_gtpu_eh_dl_ipv4_dst
            .replace('/("X"', '/TCP(sport=22,dport=23)/("X"')
            .replace('/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) ', ''),
            'action': 'check_hash_same',
        },
    ],
}

inner_l4_mac_ipv4_gtpu_ipv4_udp_tcp = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_tcp',
    'port_id': 0,
    'rule': [
       'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
       'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
    ]
}
inner_l4_mac_ipv6_gtpu_ipv4_udp_tcp = eval(str(inner_l4_mac_ipv4_gtpu_ipv4_udp_tcp)
                                           .replace('eth / ipv4', 'eth / ipv6')
                                           .replace('gtpu / ipv4', 'gtpu / gtp_psc / ipv4')
                                           .replace('IP()', 'IPv6()')
                                           .replace('teid=0x123456)', 'teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) ')
                                           .replace('mac_ipv4', 'mac_ipv6'))
inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp = {
    'sub_casename': 'mac_ipv4_gtpu_eh_ipv6_udp_tcp',
    'port_id': 0,
    'rule': [
        'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
        'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end',
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
    ]
}
inner_l4_mac_ipv6_gtpu_eh_ipv6_udp_tcp = eval(str(inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp)
                                              .replace('eth / ipv4', 'eth / ipv6')
                                              .replace('pdu_t is 0', 'pdu_t is 1')
                                              .replace('(type=0', '(type=1')
                                              .replace('IP()', 'IPv6()')
                                              .replace('mac_ipv4', 'mac_ipv6')
                                              .replace('GTP_PDUSession_ExtensionHeader(pdu_type=0', 'GTP_PDUSession_ExtensionHeader(pdu_type=1'))
inner_l4_protocal_hash = [inner_l4_mac_ipv4_gtpu_ipv4_udp_tcp, inner_l4_mac_ipv6_gtpu_ipv4_udp_tcp,
                          inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp, inner_l4_mac_ipv6_gtpu_eh_ipv6_udp_tcp]

mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2",frag=6)/("X"*480)',
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1",frag=6)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2",frag=6)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1",frag=6)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/ICMP()/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
}

mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric)
                                                     .replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                     .replace('types ipv4', 'types ipv6')
                                                     .replace('gtpu_eh_ipv4', 'gtpu_eh_ipv6')
                                                     .replace(',frag=6)', ')/IPv6ExtHdrFragment()')
                                                     .replace('IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(dst="192.168.1.1", src="192.168.1.2"',)
                                                     .replace('IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(src="192.168.1.1", dst="192.168.1.2"',)
                                                     .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                     .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                                     )

mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_different',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
}
mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric)
                                                         .replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                         .replace('types ipv4', 'types ipv6')
                                                         .replace('gtpu_eh_ipv4', 'gtpu_eh_ipv6')
                                                         .replace('IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(dst="192.168.1.1", src="192.168.1.2"',)
                                                         .replace('IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(src="192.168.1.1", dst="192.168.1.2"',)
                                                         .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                                         )

mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_different',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
}

mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric)
                                                         .replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                         .replace('types ipv4', 'types ipv6')
                                                         .replace('gtpu_eh_ipv4', 'gtpu_eh_ipv6')
                                                         .replace('IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(dst="192.168.1.1", src="192.168.1.2"',)
                                                         .replace('IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(src="192.168.1.1", dst="192.168.1.2"',)
                                                         .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                                         )


class TestCVLAdvancedRSSGTPU(TestCase):
    supported_nic = ['columbiaville_100g', 'columbiaville_25g', 'columbiaville_25gx2']

    @check_supported_nic(supported_nic)
    @skip_unsupported_pkg('os default')
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
        self.pass_flag = 'passed'
        self.fail_flag = 'failed'

        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.launch_testpmd()
        self.enable_rss = False
        self.rxq = 64
        self.rssprocess = RssProcessing(self, self.pmd_output, [self.tester_iface0, self.tester_iface1], self.rxq)
        self.logger.info('rssprocess.tester_ifaces: {}'.format(self.rssprocess.tester_ifaces))
        self.logger.info('rssprocess.test_case: {}'.format(self.rssprocess.test_case))

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def launch_testpmd(self, enable_rss=False, set_rss=None):
        if enable_rss:
            param = "--rxq=64 --txq=64"
        else:
            param = "--rxq=64 --txq=64 --disable-rss  --rxd=384 --txd=384"
        self.pmd_output.start_testpmd(cores="1S/4C/1T", param=param,
                                            eal_param=f"-w {self.pci0}", socket=self.ports_socket)
        self.enable_rss = enable_rss
        if set_rss:
            self.pmd_output.execute_cmd('port config all rss all')
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        res = self.pmd_output.wait_link_status_up('all', timeout=15)
        self.verify(res is True, 'there have port link is down')

    def switch_testpmd(self, enable_rss=True, set_rss=False):
        if enable_rss != self.enable_rss:
            self.pmd_output.quit()
            self.launch_testpmd(enable_rss=enable_rss, set_rss=set_rss)
        self.pmd_output.execute_cmd("start")
        if set_rss:
            self.pmd_output.execute_cmd('port config all rss all')

    def test_mac_ipv4_gtpu_ipv4(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_toeplitz)

    def test_mac_ipv4_gtpu_ipv4_udp(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_udp_toeplitz)

    def test_mac_ipv4_gtpu_ipv4_tcp(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gtpu_ipv6(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_toeplitz)

    def test_mac_ipv4_gtpu_ipv6_udp(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_udp_toeplitz)

    def test_mac_ipv4_gtpu_ipv6_tcp(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gtpu_ipv4(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv4_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv4_udp(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv4_udp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv4_tcp(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv4_tcp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv6_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6_udp(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv6_udp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6_tcp(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv6_tcp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpu_eh_ipv4(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_toeplitz)

    def test_mac_ipv4_gtpu_eh_ipv4_udp(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_udp_toeplitz)

    def test_mac_ipv4_gtpu_eh_ipv4_tcp(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gtpu_eh_ipv6(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_toeplitz)

    def test_mac_ipv4_gtpu_eh_ipv6_udp(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_udp_toeplitz)

    def test_mac_ipv4_gtpu_eh_ipv6_tcp(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gtpu_eh_ipv4(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv4_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_udp(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv4_udp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_tcp(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv4_tcp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv6_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_udp(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv6_udp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_tcp(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv6_tcp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpu_eh_ipv4_without_ul_dl(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz)

    def test_mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz)

    def test_mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gtpu_eh_ipv6_without_ul_dl(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv6_toeplitz)

    def test_mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv6_udp_toeplitz)

    def test_mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl(self):
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gtpu_eh_ipv4_without_ul_dl(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_udp_without_ul_dl(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_tcp_without_ul_dl(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_without_ul_dl(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_without_ul_dl_ipv6_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_udp_without_ul_dl(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_without_ul_dl_ipv6_udp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_tcp_without_ul_dl(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_without_ul_dl_ipv6_tcp_toeplitz)
        self.switch_testpmd(enable_rss=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpu_ipv4_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_symmetric)

    def test_mac_ipv4_gtpu_ipv4_udp_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_udp_symmetric)

    def test_mac_ipv4_gtpu_ipv4_tcp_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_tcp_symmetric)

    def test_mac_ipv4_gtpu_ipv6_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_symmetric)

    def test_mac_ipv4_gtpu_ipv6_udp_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_udp_symmetric)

    def test_mac_ipv4_gtpu_ipv6_tcp_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_tcp_symmetric)

    def test_mac_ipv6_gtpu_ipv4_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv4_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv4_udp_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv4_udp_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv4_tcp_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv4_tcp_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv6_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6_udp_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv6_udp_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_ipv6_tcp_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_ipv6_tcp_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpu_eh_ipv4_symmetric(self):
        self.switch_testpmd(enable_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_symmetric)

    def test_mac_ipv4_gtpu_eh_ipv4_udp_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_udp_symmetric)

    def test_mac_ipv4_gtpu_eh_ipv4_tcp_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_tcp_symmetric)

    def test_mac_ipv4_gtpu_eh_ipv6_symmetric(self):
        self.switch_testpmd(enable_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_symmetric)

    def test_mac_ipv4_gtpu_eh_ipv6_udp_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_udp_symmetric)

    def test_mac_ipv4_gtpu_eh_ipv6_tcp_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_tcp_symmetric)

    def test_mac_ipv6_gtpu_eh_ipv4_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv4_symmetric)
        self.switch_testpmd(enable_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_udp_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv4_udp_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_tcp_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv4_tcp_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv6_symmetric)
        self.switch_testpmd(enable_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_udp_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv6_udp_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_tcp_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv6_tcp_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric(self):
        self.switch_testpmd(enable_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric)

    def test_mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric)

    def test_mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric)

    def test_mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric(self):
        self.switch_testpmd(enable_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric)

    def test_mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric)

    def test_mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric(self):
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric)

    def test_mac_ipv6_gtpu_eh_ipv4_without_ul_dl_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric)
        self.switch_testpmd(enable_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_udp_without_ul_dl_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_without_ul_dl_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric)
        self.switch_testpmd(enable_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_udp_without_ul_dl_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric)
        self.switch_testpmd(enable_rss=True, set_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_inner_l4_protocal_hash(self):
        self.switch_testpmd(enable_rss=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=inner_l4_protocal_hash)

    def test_default_pattern_support(self):
        self.switch_testpmd(enable_rss=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4(default_pattern_support_ipv4)
        self.rssprocess.handle_rss_distribute_cases(cases_info=[default_pattern_support_ipv4] + ipv6_template)

    def test_negative_cases(self):
        negative_rules = [
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss types tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end',
        ]
        self.rssprocess.create_rule(rule=negative_rules, check_stats=False)

    def test_symmetric_negative_cases(self):
        rules = [
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types gtpu end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 l3-dst-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp l3-src-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp l4-dst-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end',
        ]
        self.rssprocess.create_rule(rule=rules, check_stats=False)

    def test_global_simple_xor(self):
        self.switch_testpmd()
        rule1 = 'flow create 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end'
        rule_li1 = self.rssprocess.create_rule(rule=rule1)
        pkts1 = [
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="68:05:ca:a3:28:94")/IP(src="1.1.4.1",dst="2.2.2.3")/("X"*480)',
            'Ether(dst="68:05:ca:a3:28:94")/IP(src="2.2.2.3",dst="1.1.4.1")/("X"*480)',
            'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)',
            'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)',
            'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=22, dport=23)/("X" * 80)',
            'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X" * 80)', ]
        output = self.rssprocess.send_pkt_get_output(pkts=pkts1)
        hash_values, rss_distribute = self.rssprocess.get_hash_verify_rss_distribute(output)
        for i in range(0, len(hash_values), 2):
            self.verify(hash_values[i] == hash_values[i + 1],
                        'the pair of packets with switched l3 address should have same hash value')
        rule2 = [
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp  / end actions rss types ipv6-udp end key_len 0 queues end / end']
        rule_li2 = self.rssprocess.create_rule(rule=rule2)
        pkts2 = [
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=22, dport=23)/("X" * 80)',
            'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=23, dport=22)/("X" * 80)', ]
        output = self.rssprocess.send_pkt_get_output(pkts=pkts2)
        hash_values, rss_distribute = self.rssprocess.get_hash_verify_rss_distribute(output)
        for i in range(0, len(hash_values), 2):
            self.verify(hash_values[i] != hash_values[i + 1],
                        'the packets with switched l4 port should have different hash values.')

    def test_rss_function_when_disable_rss(self):
        self.switch_testpmd(False)
        rule = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end'
        self.rssprocess.create_rule(rule=rule)
        pkt = 'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst=RandIP(),src=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)'
        output = self.rssprocess.send_pkt_get_output(pkts=pkt, count=1280)
        hashes, rss_distribute = self.rssprocess.get_hash_verify_rss_distribute(output)
        self.verify(len(hashes) == 1280,
                    'all the packets should have hash value and distributed to all queues by RSS.')
        self.verify(rss_distribute, 'the packet do not distribute by rss')

    def test_stress_cases(self):
        # Subcase: add/delete IPV4_GTPU_UL_IPV4_TCP rules
        self.switch_testpmd(enable_rss=True)
        rule1 = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end'
        for _ in range(100):
            self.pmd_output.execute_cmd(rule1)
            self.pmd_output.execute_cmd('flow destroy 0 rule 0')
        rule_li = self.rssprocess.create_rule(rule=rule1)
        out = self.pmd_output.execute_cmd('flow list 0')
        p = re.compile("^(\d+)\s")
        li = out.splitlines()
        res = list(filter(bool, list(map(p.match, li))))
        result = [i.group(1) for i in res]
        self.verify(result == rule_li, 'should only rule 0 existed')
        pkts1 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(src="192.168.1.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=32, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.1.2")/TCP(sport=22, dport=33)/("X"*480)', ]
        output = self.rssprocess.send_pkt_get_output(pkts=pkts1)
        hash_values1, rss_distribute = self.rssprocess.get_hash_verify_rss_distribute(output)
        self.verify(hash_values1[1] != hash_values1[0] and hash_values1[2] != hash_values1[0] and hash_values1[3] ==
                    hash_values1[0],
                    'packet 2 and packet 3 should have different hash value with packet 1, packet 4 should has same hash value with packet 1.')
        self.pmd_output.execute_cmd('flow flush 0')
        # Subcase: add/delete IPV4_GTPU_DL_IPV4 rules
        rule2 = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end'
        for _ in range(100):
            self.pmd_output.execute_cmd(rule2)
            self.pmd_output.execute_cmd('flow destroy 0 rule 0')
        rule_li = self.rssprocess.create_rule(rule=rule2)
        out = self.pmd_output.execute_cmd('flow list 0')
        p = re.compile("^(\d+)\s")
        li = out.splitlines()
        res = list(filter(bool, list(map(p.match, li))))
        result = [i.group(1) for i in res]
        self.verify(result == rule_li, 'should only rule 0 existed')
        pkts2 = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)', ]
        output = self.rssprocess.send_pkt_get_output(pkts=pkts2)
        hash_values2, rss_distribute = self.rssprocess.get_hash_verify_rss_distribute(output)
        self.verify(hash_values2[1] != hash_values2[0] and hash_values2[2] == hash_values2[0],
                    'packet 2 should has different hash value with packet 1, packet 3 should has same hash value with packet 1.')

    def test_ipv4_gtpu_ipv4_ipv4_gtpu_eh_ipv4(self):
        self.switch_testpmd(enable_rss=True)
        rules = [
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end'
        ]
        pkts1 = [
            [
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)', ],
            [
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)', ],
            [
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)', ]
        ]

        pkts2 = [
            [
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)', ],
            [
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)', ],
            [
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)', ]
        ]
        rule_li1 = self.rssprocess.create_rule(rule=rules[0])
        hash_value1, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1[0])
        self.verify(hash_value1[0] == hash_value1[1] and hash_value1[0] != hash_value1[2],
                    'got wrong hash, expect 1st hash equal to 2nd and different with 3rd')

        rule_li2 = self.rssprocess.create_rule(rule=rules[1])
        hash_value1, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2[0])
        self.verify(hash_value1[0] == hash_value1[1] and hash_value1[0] != hash_value1[2],
                    'got wrong hash, expect 1st hash equal to 2nd and different with 3rd')
        hash_value2, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2[1])
        self.verify(hash_value2[0] != hash_value2[1] and hash_value2[0] == hash_value2[2],
                    'got wrong hash, expect 1st hash equal to 3rd and different with 2nd')
        hash_value3, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2[2])
        self.verify(hash_value3[0] != hash_value3[1] and hash_value3[0] == hash_value3[2],
                    'got wrong hash, expect 1st hash equal to 3rd and different with 2nd')

    def test_ipv4_gtpu_eh_ipv4_with_without_ul_dl(self):
        self.switch_testpmd(enable_rss=True)
        rules = [
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end']
        pkts1 = [
            [
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)',
            ],
            [
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)',
            ]
        ]

        pkts2 = [
            [
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)', ],
            [
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
                'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)', ]
        ]
        rule_li1 = self.rssprocess.create_rule(rule=rules[0])
        hash_value1, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1[0])
        self.verify(hash_value1[0] == hash_value1[1] and hash_value1[0] != hash_value1[2],
                    'got wrong hash, expect 1st hash equal to 2nd and different with 3rd')

        rule_li2 = self.rssprocess.create_rule(rule=rules[1])
        hash_value1, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2[0])
        self.verify(hash_value1[0] != hash_value1[1] and hash_value1[0] == hash_value1[2],
                    'got wrong hash, expect 1st hash equal to 3rd and different with 2nd')
        hash_value2, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts2[1])
        self.verify(hash_value2[0] != hash_value2[1] and hash_value2[0] == hash_value2[2],
                    'got wrong hash, expect 1st hash equal to 3rd and different with 2nd')

    def test_ipv4_gtpu_eh_ipv4_without_with_ul_dl(self):
        self.switch_testpmd(enable_rss=True)
        rules = [
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end']
        pkts1 = [
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)', ]
        rule0 = self.rssprocess.create_rule(rules[0])
        hash_values, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(hash_values[1] == hash_values[0], 'packet 2 should has same hash value with packet 1')
        self.verify(hash_values[2] != hash_values[0], 'packet 3 should has different hash value with packet 1')
        self.verify(hash_values[4] == hash_values[3], 'packet 5 should has same hash value with packet 4')
        self.verify(hash_values[5] != hash_values[3], 'packet 6 should has different hash value with packet 4')

        rule1 = self.rssprocess.create_rule(rules[1])
        hash_values, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(hash_values[1] == hash_values[0], 'packet 2 should has same hash value with packet 1')
        self.verify(hash_values[2] != hash_values[0], 'packet 3 should has different hash value with packet 1')
        self.verify(hash_values[4] != hash_values[3], 'packet 5 should has different hash value with packet 4')
        self.verify(hash_values[5] == hash_values[3], 'packet 6 should has same hash value with packet 4')

    def test_ipv4_gtpu_eh_ipv4_and_ipv4_gtpu_eh_ipv4_udp_tcp(self):
        self.switch_testpmd(enable_rss=True)
        pkts1 = [
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)', ]

        rule1 = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end'
        rule_li1 = self.rssprocess.create_rule(rule=rule1)
        hash_values, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(hash_values[1] == hash_values[0], 'packet 2 should has same hash value with packet 1')
        self.verify(hash_values[2] == hash_values[0], 'packet 3 should has same hash value with packet 1')
        self.verify(hash_values[4] != hash_values[3], 'packet 5 should has different hash value with packet 4')
        self.verify(hash_values[5] == hash_values[3], 'packet 6 should has same hash value with packet 4')
        self.verify(hash_values[7] == hash_values[6], 'packet 8 should has same hash value to packet 7')
        self.verify(hash_values[8] == hash_values[6] and hash_values[8] == hash_values[7],
                    'packet 9 should have same hash value to packet 7 and 8')
        self.verify(hash_values[10] == hash_values[9], 'packet 11 should has same hash value to packet 10')
        self.verify(hash_values[11] == hash_values[9] and hash_values[11] == hash_values[10],
                    'packet 12 have same hash value to packet 10 and 11')
        rule2 = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end'
        rule_li2 = self.rssprocess.create_rule(rule=rule2)
        hash_values, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(hash_values[1] == hash_values[0], 'packet 2 should has same hash value with packet 1')
        self.verify(hash_values[2] == hash_values[0], 'packet 3 should has same hash value with packet 1')
        self.verify(hash_values[4] != hash_values[3], 'packet 5 should has different hash value with packet 4')
        self.verify(hash_values[5] == hash_values[3], 'packet 6 should has same hash value with packet 4')
        self.verify(hash_values[7] == hash_values[6], 'packet 8 should has same hash value to packet 7')
        self.verify(hash_values[8] == hash_values[6] and hash_values[8] == hash_values[7],
                    'packet 9 should have same hash value to packet 7 and 8')
        self.verify(hash_values[10] != hash_values[9], 'packet 11 should has different hash value to packet 10')
        self.verify(hash_values[11] == hash_values[9],
                    'packet 12 have same hash value to packet 10')

    def test_ipv6_gtpu_eh_ipv6_and_ipv6_gtpu_eh_ipv6_udp_tcp(self):
        self.switch_testpmd(enable_rss=True)
        pkts1 = [
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)', ]

        rule1 = 'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end'
        rule_li1 = self.rssprocess.create_rule(rule=rule1)
        hash_values, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(hash_values[1] != hash_values[0], 'packet 2 should has different hash value with packet 1')
        self.verify(hash_values[2] == hash_values[0], 'packet 3 should has same hash value with packet 1')
        self.verify(hash_values[4] == hash_values[3], 'packet 5 should has same hash value with packet 4')
        self.verify(hash_values[5] == hash_values[3], 'packet 6 should has same hash value with packet 4')
        self.verify(hash_values[7] == hash_values[6], 'packet 8 should has same hash value to packet 7')
        self.verify(hash_values[8] == hash_values[6] and hash_values[8] == hash_values[7],
                    'packet 9 should have different hash value to packet 7 and 8')
        self.verify(hash_values[10] == hash_values[9], 'packet 11 should has different hash value to packet 10')
        self.verify(hash_values[11] == hash_values[9] and hash_values[11] == hash_values[10],
                    'packet 12 have different hash value to packet 10 and 11')
        rule2 = 'flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end'
        rule_li2 = self.rssprocess.create_rule(rule=rule2)
        hash_values, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(hash_values[1] == hash_values[0], 'packet 2 should has same hash value with packet 1')
        self.verify(hash_values[2] != hash_values[0], 'packet 3 should has same hash value with packet 1')
        self.verify(hash_values[4] == hash_values[3], 'packet 5 should has same hash value with packet 4')
        self.verify(hash_values[5] == hash_values[3], 'packet 6 should has same hash value with packet 4')
        self.verify(hash_values[7] == hash_values[6], 'packet 8 should has same hash value to packet 7')
        self.verify(hash_values[8] != hash_values[6],
                    'packet 9 should have different hash value to packet 7')
        self.verify(hash_values[10] == hash_values[9], 'packet 11 should has same hash value to packet 10')
        self.verify(hash_values[11] == hash_values[9] and hash_values[11] == hash_values[10],
                    'packet 12 have same hash value to packet 10 and 11')

    def test_ipv4_gtpu_eh_ipv6_and_ipv4_gtpu_eh_ipv6_udp_tcp_without_ul_dl(self):
        self.switch_testpmd(enable_rss=True)
        pkts1 = [
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)', ]

        rule1 = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end'
        self.rssprocess.create_rule(rule=rule1)
        hash_values, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(hash_values[1] == hash_values[0] and hash_values[2] == hash_values[0],
                    'packet 2 should has same hash value with packet 1, packet 3 should has same hash value to packet 1')
        self.verify(hash_values[3] != hash_values[0], 'packet 4 should have different hash value to packet 1.')
        self.verify(hash_values[5] == hash_values[4], 'packet 6 should has same hash value to packet 5.')
        self.verify(hash_values[6] != hash_values[4], 'packet 7 should has differnt hash value to packet 5.')

    def test_ipv6_gtpu_ipv4_and_ipv6_gtpu_ipv4_udp_tcp(self):
        self.switch_testpmd(enable_rss=True)
        pkts1 = [
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)',
            'Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)', ]

        self.rssprocess.create_rule(
            rule='flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end')
        hash_values, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(hash_values[1] != hash_values[0],
                    'packet 2 should has defferent hash value with packet 1')
        self.verify(hash_values[2] == hash_values[0] and hash_values[3] == hash_values[0],
                    'packet 3 and packet 4 should have same hash value to packet 1.')
        self.verify(len({hash_values[4], hash_values[5], hash_values[6]}) == 1,
                    'packet 5 and packet 6 and packet 7 have same hash value.')
        self.rssprocess.create_rule(
            rule='flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end')
        hash_values, queues = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts1)
        self.verify(hash_values[1] == hash_values[0],
                    'packet 2 should has same hash value with packet 1')
        self.verify(hash_values[2] != hash_values[0], 'packet 3 should has different hash value to packet 1.')
        self.verify(hash_values[3] == hash_values[0],
                    'packet 4 should has same hash value with packet 1')
        self.verify(hash_values[5] == hash_values[4],
                    'packet 6 should has same hash value with packet 5')
        self.verify(hash_values[6] != hash_values[4], 'packet 7 should has different hash value to packet 5.')

    def test_toeplitz_symmetric_combination(self):
        self.switch_testpmd(False)
        self.logger.info('Subcase: toeplitz/symmetric with same pattern')
        # step 1
        rule_toeplitz = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end'
        rule_id_toeplitz = self.rssprocess.create_rule(rule=rule_toeplitz)
        self.rssprocess.check_rule(rule_list=rule_id_toeplitz)
        pkts_toeplitz = ['Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
                    'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)',
                    'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)']
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(hash_value[1] != hash_value[0], 'second packet should hash value different from the first packet')
        self.verify(hash_value[2] == hash_value[0], 'third packet should hash value same with the first packet')
        # step 2
        rule_symmetric = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end'
        rule_id_symmetric = self.rssprocess.create_rule(rule=rule_symmetric)
        pkts_symmetric =['Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)',
              'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)']
        self.rssprocess.check_rule(rule_list=rule_id_symmetric)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_symmetric)
        self.verify(hash_value[0] == hash_value[1], 'second packet should hash value same with the first packet')
        # step 3
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(len(hash_value[0]) != hash_value[2], 'the toeplitz should not work')
        for temp in range(len(hash_value)):
            self.verify(len(hash_value[temp]) != 0, 'all the toeplitz packet should have hash value')
        self.pmd_output.execute_cmd('flow flush 0')

        self.logger.info('Subcase: toeplitz/symmetric with same pattern (switched rule order)')
        # step 1
        rule_id_symmetric = self.rssprocess.create_rule(rule=rule_symmetric)
        self.rssprocess.check_rule(rule_list=rule_id_symmetric)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_symmetric)
        self.verify(hash_value[0] == hash_value[1], 'second packet should hash value same with the first packet')
        rule_id_toeplitz = self.rssprocess.create_rule(rule=rule_toeplitz)
        self.rssprocess.check_rule(rule_list=rule_id_toeplitz)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(hash_value[1] != hash_value[0], 'second packet should hash value different from the first packet')
        self.verify(hash_value[2] == hash_value[0], 'third packet should hash value same with the first packet')
        # step 2
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_symmetric)
        self.verify(hash_value[0] != hash_value[1], 'symmetric rule should not work')
        self.pmd_output.execute_cmd('flow flush 0')

        self.logger.info('Subcase: toeplitz/symmetric with different pattern (different UL/DL)')
        # step 1
        rule_toeplitz = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end'
        pkts_toeplitz = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)'
        ]
        rule_symmetric = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end'
        pkts_symmetric = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)'
        ]
        rule_id_toeplitz = self.rssprocess.create_rule(rule=rule_toeplitz)
        self.rssprocess.check_rule(rule_list=rule_id_toeplitz)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(hash_value[1] != hash_value[0], 'second packet should hash value different from the first packet')
        self.verify(hash_value[2] == hash_value[0], 'third packet should hash value same with the first packet')
        rule_id_symmetric = self.rssprocess.create_rule(rule=rule_symmetric)
        self.rssprocess.check_rule(rule_list=rule_id_symmetric)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_symmetric)
        self.verify(hash_value[0] == hash_value[1], 'second packet should hash value same with the first packet')
        # step 2
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(hash_value[1] != hash_value[0], 'second packet should hash value different from the first packet')
        self.verify(hash_value[2] == hash_value[0], 'third packet should hash value same with the first packet')
        self.pmd_output.execute_cmd('flow flush 0')

        self.logger.info('Subcase: toeplitz/symmetric with different pattern (with/without UL/DL)')
        # step 1
        rule_toeplitz = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end'
        pkts_toeplitz = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)'
        ]
        rule_symmetric = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end'
        pkts_symmetric = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)'
        ]
        rule_id_toeplitz = self.rssprocess.create_rule(rule=rule_toeplitz)
        self.rssprocess.check_rule(rule_list=rule_id_toeplitz)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(hash_value[1] != hash_value[0], 'hash_value[1] should hash value different from hash_value[0]')
        self.verify(hash_value[2] == hash_value[0], 'hash_value[2] should hash value same with hash_value[0]')
        self.verify(hash_value[4] != hash_value[3], 'hash_value[4] should hash value different from hash_value[3]')
        self.verify(hash_value[5] == hash_value[3], 'hash_value[5] should hash value same with hash_value[3]')
        rule_id_symmetric = self.rssprocess.create_rule(rule=rule_symmetric)
        self.rssprocess.check_rule(rule_list=rule_id_symmetric)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_symmetric)
        self.verify(hash_value[0] == hash_value[1], 'second packet should hash value same with the first packet')
        # step 2
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        for temp in range(len(hash_value)):
            self.verify(len(hash_value[temp]) != 0, 'all the toeplitz packet should have hash value')
        self.pmd_output.execute_cmd('flow flush 0')

        self.logger.info('Subcase: toeplitz/symmetric with different pattern')
        # step 1
        rule_toeplitz = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end'
        pkts_toeplitz = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.1.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34) /IP(src="192.168.0.1", dst="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)'
        ]
        rule_symmetric = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end'
        pkts_symmetric = [
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34) /IPv6(src="2222:3333:4444:5555:6666:7777:8888:9999",dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)'
        ]
        rule_id_toeplitz = self.rssprocess.create_rule(rule=rule_toeplitz)
        self.rssprocess.check_rule(rule_list=rule_id_toeplitz)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        self.verify(hash_value[1] != hash_value[0], 'hash_value[1] should hash value different from hash_value[0]')
        self.verify(hash_value[2] != hash_value[0], 'hash_value[2] should hash value different with hash_value[0]')
        self.verify(hash_value[3] == hash_value[0], 'hash_value[3] should hash value same from hash_value[0]')
        rule_id_symmetric = self.rssprocess.create_rule(rule=rule_symmetric)
        self.rssprocess.check_rule(rule_list=rule_id_symmetric)
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_symmetric)
        self.verify(hash_value[0] == hash_value[1], 'second packet should hash value same with the first packet')
        # step 2
        hash_value, _ = self.rssprocess.send_pkt_get_hash_queues(pkts=pkts_toeplitz)
        for temp in range(len(hash_value)):
            self.verify(len(hash_value[temp]) != 0, 'all the toeplitz packet should have hash value')
        self.pmd_output.execute_cmd('flow flush 0')

    def tear_down(self):
        # destroy all flow rule on port 0
        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")

    def tear_down_all(self):
        self.dut.kill_all()
