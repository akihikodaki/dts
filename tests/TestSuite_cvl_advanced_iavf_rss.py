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


import random
import re

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

from .rte_flow_common import RssProcessing

vf0_mac = "00:11:22:33:44:55"

# toeplitz related data start
mac_ipv4_toeplitz_basic_pkt = {
    'ipv4-nonfrag': [
       'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
    ],
    'ipv4-frag': [
        'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2", frag=6)/("X"*480)' % vf0_mac,
    ],
    'ipv4-icmp': [
        'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)' % vf0_mac,
    ],
    'ipv4-tcp': [
        'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    ],
    # 'ipv4-udp-vxlan': [
    #     'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    # ],
}

mac_ipv4_udp_toeplitz_basic_pkt = {
    'ipv4-udp': [
       'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    ],
    # 'nvgre': [
    #     'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    # ],
}

mac_ipv4_tcp_toeplitz_basic_pkt = {
    'ipv4-tcp': [
       'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    ],
    # 'nvgre': [
    #     'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    # ],
}

mac_ipv4_sctp_toeplitz_basic_pkt = {
    'ipv4-sctp': [
       'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    ],
    # 'nvgre': [
    #     'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    # ],
}

mac_ipv6_toeplitz_basic_pkt = {
    'ipv6-nonfrag': [
       'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
    ],
    'ipv6-frag': [
        'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
    ],
    'ipv6-icmp': [
        'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)'  % vf0_mac,
    ],
    'ipv6-udp': [
        'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    ],
    # 'nvgre': [
    #     'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)'  % vf0_mac,
    # ],
}

mac_ipv6_udp_toeplitz_basic_pkt = {
    'ipv6-udp': [
       'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    ],
    # 'ipv4_udp_vxlan_ipv6_udp': [
    #     'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    # ],
}

mac_ipv6_tcp_toeplitz_basic_pkt = {
    'ipv6-tcp': [
       'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    ],
    # 'ipv4_tcp_vxlan_ipv6_tcp': [
    #     'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    # ],
}

mac_ipv6_sctp_toeplitz_basic_pkt = {
    'ipv6-sctp': [
       'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    ],
    # 'ipv4_sctp_vxlan_ipv6_sctp': [
    #     'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
    # ],
}

#mac_ipv4
mac_ipv4_l2_src = {
    'sub_casename': 'mac_ipv4_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'],
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2", frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5",frag=7)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=19,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_l2_dst = {
    'sub_casename': 'mac_ipv4_l2_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'],
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5",frag=7)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=19,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_l2src_l2dst = {
    'sub_casename': 'mac_ipv4_l2src_l2dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'],
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5",frag=7)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=23,dport=25)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_l3_src = {
    'sub_casename': 'mac_ipv4_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'],
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'],
        #     'action': {'save_hash': 'ipv4-udp-vxlan'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4-udp-vxlan'},
        # },
    ],
}

mac_ipv4_l3_dst = {
    'sub_casename': 'mac_ipv4_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'],
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'],
        #     'action': {'save_hash': 'ipv4-udp-vxlan'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4-udp-vxlan'},
        # },
    ],
}

mac_ipv4_all = {
    'sub_casename': 'mac_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'],
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'],
        #     'action': {'save_hash': 'ipv4-udp-vxlan'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480))' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan'},
        # },
    ],
}

# mac ipv4_udp
mac_ipv4_udp_l2_src = {
    'sub_casename': 'mac_ipv4_udp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
    ],
}

mac_ipv4_udp_l2_dst = {
    'sub_casename': 'mac_ipv4_udp_l2_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': ' Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
    ],
}

mac_ipv4_udp_l2src_l2dst = {
    'sub_casename': 'mac_ipv4_udp_l2src_l2dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
    ],
}

mac_ipv4_udp_l3_src = {
    'sub_casename': 'mac_ipv4_udp_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        # {
        #     'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_udp_l3_dst = {
    'sub_casename': 'mac_ipv4_udp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        # {
        #     'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        # {
        #     'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        # {
        #     'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        # {
        #     'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        # {
        #     'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_udp_l4_src = {
    'sub_casename': 'mac_ipv4_udp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        # {
        #     'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_udp_l4_dst = {
    'sub_casename': 'mac_ipv4_udp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        # {
        #     'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_udp_all = {
    'sub_casename': 'mac_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        # {
        #     'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
    ],
}

# mac ipv4_tcp
mac_ipv4_tcp_l2_src = {
    'sub_casename': 'mac_ipv4_tcp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_tcp_l2_dst = {
    'sub_casename': 'mac_ipv4_tcp_l2_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': ' Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_tcp_l2src_l2dst = {
    'sub_casename': 'mac_ipv4_tcp_l2src_l2dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_tcp_l3_src = {
    'sub_casename': 'mac_ipv4_tcp_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_tcp_l3_dst = {
    'sub_casename': 'mac_ipv4_tcp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_tcp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_tcp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_tcp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_tcp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_tcp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_tcp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_tcp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_tcp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_tcp_l4_src = {
    'sub_casename': 'mac_ipv4_tcp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_tcp_l4_dst = {
    'sub_casename': 'mac_ipv4_tcp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.1.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.1.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_tcp_all = {
    'sub_casename': 'mac_ipv4_tcp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
    ],
}

# mac ipv4_sctp
mac_ipv4_sctp_l2_src = {
    'sub_casename': 'mac_ipv4_sctp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/SCTP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
    ],
}

mac_ipv4_sctp_l2_dst = {
    'sub_casename': 'mac_ipv4_sctp_l2_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': ' Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5")/SCTP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
    ],
}

mac_ipv4_sctp_l2src_l2dst = {
    'sub_casename': 'mac_ipv4_sctp_l2src_l2dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/SCTP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
    ],
}

mac_ipv4_sctp_l3_src = {
    'sub_casename': 'mac_ipv4_sctp_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        # {
        #     'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_sctp_l3_dst = {
    'sub_casename': 'mac_ipv4_sctp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        # {
        #     'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_sctp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_sctp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        # {
        #     'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_sctp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_sctp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        # {
        #     'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_sctp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_sctp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        # {
        #     'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_sctp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_sctp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        # {
        #     'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_sctp_l4_src = {
    'sub_casename': 'mac_ipv4_sctp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.1.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        # {
        #     'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.1.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_sctp_l4_dst = {
    'sub_casename': 'mac_ipv4_sctp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.1.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        # {
        #     'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.1.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv4_sctp_all = {
    'sub_casename': 'mac_ipv4_sctp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        # {
        #     'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
    ],
}

# mac_ipv6
mac_ipv6_l2_src = {
    'sub_casename': 'mac_ipv6_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'],
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
    ],
}

mac_ipv6_l2_dst = {
    'sub_casename': 'mac_ipv6_l2_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'],
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
    ],
}

mac_ipv6_l2src_l2dst = {
    'sub_casename': 'mac_ipv6_l2src_l2dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'],
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
    ],
}

mac_ipv6_l3_src = {
    'sub_casename': 'mac_ipv6_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'],
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv6_l3_dst = {
    'sub_casename': 'mac_ipv6_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'],
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}

mac_ipv6_all = {
    'sub_casename': 'mac_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'],
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_toeplitz_basic_pkt['nvgre'],
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
    ],
}
# mac_ipv6_udp
mac_ipv6_udp_l2_src = {
    'sub_casename': 'mac_ipv6_udp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
    ],
}

mac_ipv6_udp_l2_dst = {
    'sub_casename': 'mac_ipv6_udp_l2_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
    ],
}

mac_ipv6_udp_l2src_l2dst = {
    'sub_casename': 'mac_ipv6_udp_l2src_l2dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
    ],
}

mac_ipv6_udp_l3_src = {
    'sub_casename': 'mac_ipv6_udp_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'],
        #     'action': {'save_hash': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
    ],
}

mac_ipv6_udp_l3_dst = {
    'sub_casename': 'mac_ipv6_udp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'],
        #     'action': {'save_hash': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
    ],
}

mac_ipv6_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv6_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'],
        #     'action': {'save_hash': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
    ],
}

mac_ipv6_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv6_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'],
        #     'action': {'save_hash': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
    ],
}

mac_ipv6_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv6_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'],
        #     'action': {'save_hash': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
    ],
}

mac_ipv6_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv6_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'],
        #     'action': {'save_hash': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
    ],
}

mac_ipv6_udp_l4_src = {
    'sub_casename': 'mac_ipv6_udp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'],
        #     'action': {'save_hash': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
    ],
}

mac_ipv6_udp_l4_dst = {
    'sub_casename': 'mac_ipv6_udp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'],
        #     'action': {'save_hash': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
    ],
}

mac_ipv6_udp_all = {
    'sub_casename': 'mac_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'],
        #     'action': {'save_hash': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_udp_vxlan_ipv6_udp'},
        # },
    ],
}
# mac_ipv6_tcp
mac_ipv6_tcp_l2_src = {
    'sub_casename': 'mac_ipv6_tcp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ],
}

mac_ipv6_tcp_l2_dst = {
    'sub_casename': 'mac_ipv6_tcp_l2_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ],
}

mac_ipv6_tcp_l2src_l2dst = {
    'sub_casename': 'mac_ipv6_tcp_l2src_l2dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ],
}

mac_ipv6_tcp_l3_src = {
    'sub_casename': 'mac_ipv6_tcp_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        # {
        #     'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'],
        #     'action': {'save_hash': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
    ],
}

mac_ipv6_tcp_l3_dst = {
    'sub_casename': 'mac_ipv6_tcp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        # {
        #     'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'],
        #     'action': {'save_hash': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
    ],
}

mac_ipv6_tcp_l3src_l4src = {
    'sub_casename': 'mac_ipv6_tcp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        # {
        #     'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'],
        #     'action': {'save_hash': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
    ],
}

mac_ipv6_tcp_l3src_l4dst = {
    'sub_casename': 'mac_ipv6_tcp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        # {
        #     'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'],
        #     'action': {'save_hash': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
    ],
}

mac_ipv6_tcp_l3dst_l4src = {
    'sub_casename': 'mac_ipv6_tcp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        # {
        #     'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'],
        #     'action': {'save_hash': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
    ],
}

mac_ipv6_tcp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv6_tcp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        # {
        #     'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'],
        #     'action': {'save_hash': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
    ],
}

mac_ipv6_tcp_l4_src = {
    'sub_casename': 'mac_ipv6_tcp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        # {
        #     'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'],
        #     'action': {'save_hash': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
    ],
}

mac_ipv6_tcp_l4_dst = {
    'sub_casename': 'mac_ipv6_tcp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        # {
        #     'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'],
        #     'action': {'save_hash': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
    ],
}

mac_ipv6_tcp_all = {
    'sub_casename': 'mac_ipv6_tcp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        # {
        #     'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'],
        #     'action': {'save_hash': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/TCP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_tcp_vxlan_ipv6_tcp'},
        # },
    ],
}
# mac_ipv6_sctp
mac_ipv6_sctp_l2_src = {
    'sub_casename': 'mac_ipv6_sctp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/SCTP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
    ],
}

mac_ipv6_sctp_l2_dst = {
    'sub_casename': 'mac_ipv6_sctp_l2_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/SCTP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
    ],
}

mac_ipv6_sctp_l2src_l2dst = {
    'sub_casename': 'mac_ipv6_sctp_l2src_l2dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/SCTP(sport=25,dport=99)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
    ],
}

mac_ipv6_sctp_l3_src = {
    'sub_casename': 'mac_ipv6_sctp_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
        # {
        #     'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'],
        #     'action': {'save_hash': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
    ],
}

mac_ipv6_sctp_l3_dst = {
    'sub_casename': 'mac_ipv6_sctp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
        # {
        #     'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'],
        #     'action': {'save_hash': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
    ],
}

mac_ipv6_sctp_l3src_l4src = {
    'sub_casename': 'mac_ipv6_sctp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
        # {
        #     'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'],
        #     'action': {'save_hash': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
    ],
}

mac_ipv6_sctp_l3src_l4dst = {
    'sub_casename': 'mac_ipv6_sctp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
        # {
        #     'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'],
        #     'action': {'save_hash': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
    ],
}

mac_ipv6_sctp_l3dst_l4src = {
    'sub_casename': 'mac_ipv6_sctp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
        # {
        #     'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'],
        #     'action': {'save_hash': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
    ],
}

mac_ipv6_sctp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv6_sctp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
        # {
        #     'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'],
        #     'action': {'save_hash': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
    ],
}

mac_ipv6_sctp_l4_src = {
    'sub_casename': 'mac_ipv6_sctp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
        # {
        #     'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'],
        #     'action': {'save_hash': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
    ],
}

mac_ipv6_sctp_l4_dst = {
    'sub_casename': 'mac_ipv6_sctp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
        # {
        #     'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'],
        #     'action': {'save_hash': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
    ],
}

mac_ipv6_sctp_all = {
    'sub_casename': 'mac_ipv6_sctp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
        # {
        #     'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'],
        #     'action': {'save_hash': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4_sctp_vxlan_ipv6_sctp'},
        # },
    ],
}
# toeplitz related data end

mac_ipv4 = [mac_ipv4_l2_src, mac_ipv4_l2_dst, mac_ipv4_l2src_l2dst, mac_ipv4_l3_src, mac_ipv4_l3_dst, mac_ipv4_all]

mac_ipv4_udp = [mac_ipv4_udp_l2_src, mac_ipv4_udp_l2_dst, mac_ipv4_udp_l2src_l2dst,
                mac_ipv4_udp_l3_src, mac_ipv4_udp_l3_dst, mac_ipv4_udp_l3src_l4src,
                mac_ipv4_udp_l3src_l4dst, mac_ipv4_udp_l3dst_l4src, mac_ipv4_udp_l3dst_l4dst,
                mac_ipv4_udp_l4_src, mac_ipv4_udp_l4_dst, mac_ipv4_udp_all]

mac_ipv4_tcp = [mac_ipv4_tcp_l2_src, mac_ipv4_tcp_l2_dst, mac_ipv4_tcp_l2src_l2dst,
                mac_ipv4_tcp_l3_src, mac_ipv4_tcp_l3_dst, mac_ipv4_tcp_l3src_l4src,
                mac_ipv4_tcp_l3src_l4dst, mac_ipv4_tcp_l3dst_l4src, mac_ipv4_tcp_l3dst_l4dst,
                mac_ipv4_tcp_l4_src, mac_ipv4_tcp_l4_dst, mac_ipv4_tcp_all]

mac_ipv4_sctp = [mac_ipv4_sctp_l2_src, mac_ipv4_sctp_l2_dst, mac_ipv4_sctp_l2src_l2dst,
                mac_ipv4_sctp_l3_src, mac_ipv4_sctp_l3_dst, mac_ipv4_sctp_l3src_l4src,
                mac_ipv4_sctp_l3src_l4dst, mac_ipv4_sctp_l3dst_l4src, mac_ipv4_sctp_l3dst_l4dst,
                mac_ipv4_sctp_l4_src, mac_ipv4_sctp_l4_dst, mac_ipv4_sctp_all]

mac_ipv6 = [mac_ipv6_l2_src, mac_ipv6_l2_dst, mac_ipv6_l2src_l2dst, mac_ipv6_l3_src, mac_ipv6_l3_dst, mac_ipv6_all]

mac_ipv6_udp = [mac_ipv6_udp_l2_src, mac_ipv6_udp_l2_dst, mac_ipv6_udp_l2src_l2dst,
                mac_ipv6_udp_l3_src, mac_ipv6_udp_l3_dst, mac_ipv6_udp_l3src_l4src,
                mac_ipv6_udp_l3src_l4dst, mac_ipv6_udp_l3dst_l4src, mac_ipv6_udp_l3dst_l4dst,
                mac_ipv6_udp_l4_src, mac_ipv6_udp_l4_dst, mac_ipv6_udp_all]

mac_ipv6_tcp = [mac_ipv6_tcp_l2_src, mac_ipv6_tcp_l2_dst, mac_ipv6_tcp_l2src_l2dst,
                mac_ipv6_tcp_l3_src, mac_ipv6_tcp_l3_dst, mac_ipv6_tcp_l3src_l4src,
                mac_ipv6_tcp_l3src_l4dst, mac_ipv6_tcp_l3dst_l4src, mac_ipv6_tcp_l3dst_l4dst,
                mac_ipv6_tcp_l4_src, mac_ipv6_tcp_l4_dst, mac_ipv6_tcp_all]

mac_ipv6_sctp = [mac_ipv6_sctp_l2_src, mac_ipv6_sctp_l2_dst, mac_ipv6_sctp_l2src_l2dst,
                mac_ipv6_sctp_l3_src, mac_ipv6_sctp_l3_dst, mac_ipv6_sctp_l3src_l4src,
                mac_ipv6_sctp_l3src_l4dst, mac_ipv6_sctp_l3dst_l4src, mac_ipv6_sctp_l3dst_l4dst,
                mac_ipv6_sctp_l4_src, mac_ipv6_sctp_l4_dst, mac_ipv6_sctp_all]

# symmetric related data start
mac_ipv4_symmetric = {
    'sub_casename': 'mac_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-nonfrag-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-nonfrag-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-frag-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-frag-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-icmp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-icmp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-tcp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp-pre'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vlan-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vlan-pre'},
        # },
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
           'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
           'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #    'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #    'action': {'save_hash': 'ipv4-udp-vlan'},
        # },
        # {
        #    'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #    'action': {'check_hash_same': 'ipv4-udp-vlan'},
        # },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2928")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6'},
        },
    ],
    'post-test': [
         {
             'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
             'action': {'save_hash': 'ipv4-nonfrag-post'},
         },
         {
             'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)' % vf0_mac,
             'action': {'check_hash_different': 'ipv4-nonfrag-post'},
         },
         {
             'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)' % vf0_mac,
             'action': {'save_hash': 'ipv4-frag-post'},
         },
         {
             'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)' % vf0_mac,
             'action': {'check_hash_different': 'ipv4-frag-post'},
         },
         {
             'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)' % vf0_mac,
             'action': {'save_hash': 'ipv4-icmp-post'},
         },
         {
             'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/ICMP()/("X"*480)' % vf0_mac,
             'action': {'check_hash_different': 'ipv4-icmp-post'},
         },
         {
             'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
             'action': {'save_hash': 'ipv4-tcp-post'},
         },
         {
             'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
             'action': {'check_hash_different': 'ipv4-tcp-post'},
         },
         # {
         #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
         #     'action': {'save_hash': 'ipv4-udp-vlan-post'},
         # },
         # {
         #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
         #     'action': {'check_no_hash_or_different': 'ipv4-udp-vlan-post'},
         # },
    ],
}

mac_ipv4_udp_symmetric = {
    'sub_casename': 'mac_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-udp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp-pre'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre-pre'},
        # },
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre'},
        # },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre'},
        # },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-udp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp-post'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'nvgre-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'nvgre-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'nvgre-post'},
        # },
    ],
}

mac_ipv4_tcp_symmetric = {
    'sub_casename': 'mac_ipv4_tcp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-tcp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp-pre'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vxlan-eth-ipv4-tcp-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan-eth-ipv4-tcp-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan-eth-ipv4-tcp-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan-eth-ipv4-tcp-pre'},
        # },
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vxlan-eth-ipv4-tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4-udp-vxlan-eth-ipv4-tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4-udp-vxlan-eth-ipv4-tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4-udp-vxlan-eth-ipv4-tcp'},
        # },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vxlan-eth-ipv4-udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan-eth-ipv4-udp'},
        # },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-tcp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-tcp-post'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vxlan-eth-ipv4-tcp-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'ipv4-udp-vxlan-eth-ipv4-tcp-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'ipv4-udp-vxlan-eth-ipv4-tcp-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'ipv4-udp-vxlan-eth-ipv4-tcp-post'},
        # },
    ],
}

mac_ipv4_sctp_symmetric = {
    'sub_casename': 'mac_ipv4_sctp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss func symmetric_toeplitz types ipv4-sctp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-sctp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp-pre'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vxlan-eth-ipv4-sctp-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan-eth-ipv4-sctp-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan-eth-ipv4-sctp-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan-eth-ipv4-sctp-pre'},
        # },
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vxlan-eth-ipv4-sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4-udp-vxlan-eth-ipv4-sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4-udp-vxlan-eth-ipv4-sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4-udp-vxlan-eth-ipv4-sctp'},
        # },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-udp'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-sctp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-sctp-post'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vxlan-eth-ipv4-sctp-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'ipv4-udp-vxlan-eth-ipv4-sctp-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'ipv4-udp-vxlan-eth-ipv4-sctp-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'ipv4-udp-vxlan-eth-ipv4-sctp-post'},
        # },
    ],
}

mac_ipv6_symmetric = {
    'sub_casename': 'mac_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-nonfrag-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-nonfrag-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-frag-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-frag-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-icmp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-icmp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-udp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp-pre'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vxlan-eth-ipv6-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv4-udp-vxlan-eth-ipv6-pre'},
        # },
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vxlan-eth-ipv6'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'ipv4-udp-vxlan-eth-ipv6'},
        # },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-nonfrag-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-nonfrag-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-frag-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-frag-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-icmp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-icmp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-udp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp-post'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv4-udp-vxlan-eth-ipv6-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'ipv4-udp-vxlan-eth-ipv6-post'},
        # },
    ],
}

mac_ipv6_udp_symmetric = {
    'sub_casename': 'mac_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-udp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp-pre'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-udp-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre-eth-ipv6-udp-pre'},
        # },
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre-eth-ipv6-udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'ipv6-tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'ipv6-tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre-eth-ipv6-tcp'},
        # },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-udp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp-post'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-udp-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'nvgre-eth-ipv6-udp-post'},
        # },
    ],
}

mac_ipv6_tcp_symmetric = {
    'sub_casename': 'mac_ipv6_tcp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-tcp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp-pre'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-tcp-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre-eth-ipv6-tcp-pre'},
        # },
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-tcp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre-eth-ipv6-tcp'},
        # },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-udp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre-eth-ipv6-udp'},
        # },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-tcp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-tcp-post'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-tcp-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'nvgre-eth-ipv6-tcp-post'},
        # },
    ],
}

mac_ipv6_sctp_symmetric = {
    'sub_casename': 'mac_ipv6_sctp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-sctp-pre'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp-pre'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-sctp-pre'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_different': 'nvgre-eth-ipv6-sctp-pre'},
        # },
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-sctp'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_hash_same': 'nvgre-eth-ipv6-sctp'},
        # },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-udp'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-sctp-post'},
        },
        {
            'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-sctp-post'},
        },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'save_hash': 'nvgre-eth-ipv6-sctp-post'},
        # },
        # {
        #     'send_packet': 'Ether(dst="%s", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)' % vf0_mac,
        #     'action': {'check_no_hash_or_different': 'nvgre-eth-ipv6-sctp-post'},
        # },
    ],
}
# symmetric related data end

ipv6_64bit_prefix_l3_src_only = {
    'sub_casename': 'ipv6_64bit_prefix_l3_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre64 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'save_hash': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe83:1:a6bf:2ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:ee1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:ee1c::806", dst="fe82:1:a6bf:2ff:fe1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
    ],
}

ipv6_64bit_prefix_l3_dst_only = {
    'sub_casename': 'ipv6_64bit_prefix_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre64 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'save_hash': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe83:1:a6bf:2ff:fe1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:ee1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe83:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:ee1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
    ],
}

ipv6_64bit_prefix_l3_src_dst_only = {
    'sub_casename': 'ipv6_64bit_prefix_l3_src_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre64 l3-src-only l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'save_hash': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:2ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:2ff:fe1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_different': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:ee1c::806", dst="fe82:1:a6bf:1ff:ee1c::806")/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
    ],
}

ipv6_64bit_prefix = [ipv6_64bit_prefix_l3_src_only, ipv6_64bit_prefix_l3_dst_only, ipv6_64bit_prefix_l3_src_dst_only]

#gre tunnel related data
mac_ipv4_gre_ipv4_basic_pkt = {
    'ipv4-proto':
       'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.1", src="192.168.0.2", proto=6)/("X"*480)' % vf0_mac,
    'ipv4-tcp':
        'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.1", src="192.168.0.2", proto=6)/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
}

mac_ipv4_gre_ipv6_basic_pkt = {
    'ipv6-nh':
        'Ether(dst="%s")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910B:6666:3457:8295:3333:1800:2929", nh=6)/("X"*480)' % vf0_mac,
    'ipv6-tcp':
        'Ether(dst="%s")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910B:6666:3457:8295:3333:1800:2929", nh=6)/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
}

mac_ipv4_gre_ipv4_all = {
    'sub_casename': 'ipv4_gre_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-proto'],
            'action': {'save_hash': 'ipv4-proto'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-proto'].replace('dst="192.168.0.1"','dst="192.168.1.1"'),
            'action': {'check_hash_different': 'ipv4-proto'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-proto'].replace('src="192.168.0.2"','src="192.168.1.2"'),
            'action': {'check_hash_different': 'ipv4-proto'},
        },
    ],
}

mac_ipv4_gre_ipv4_l3_src = {
    'sub_casename': 'ipv4_gre_ipv4_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-proto'],
            'action': {'save_hash': 'ipv4-proto'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-proto'].replace('src="192.168.0.2"','src="192.168.1.2"'),
            'action': {'check_hash_different': 'ipv4-proto'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-proto'].replace('dst="192.168.0.1"','dst="192.168.1.1"'),
            'action': {'check_hash_same': 'ipv4-proto'},
        },
    ],
}

mac_ipv4_gre_ipv4_l3_dst = {
    'sub_casename': 'ipv4_gre_ipv4_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-proto'],
            'action': {'save_hash': 'ipv4-proto'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-proto'].replace('dst="192.168.0.1"','dst="192.168.1.1"'),
            'action': {'check_hash_different': 'ipv4-proto'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-proto'].replace('src="192.168.0.2"','src="192.168.1.2"'),
            'action': {'check_hash_same': 'ipv4-proto'},
        },
    ],
}

mac_ipv4_gre_ipv4_tcp_l3_src = {
    'sub_casename': 'ipv4_gre_ipv4_tcp_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('src="192.168.0.2"', 'src="192.168.1.2"'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dst="192.168.0.1"', 'dst="192.168.1.1"'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_gre_ipv4_tcp_l3_dst = {
    'sub_casename': 'ipv4_gre_ipv4_tcp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dst="192.168.0.1"', 'dst="192.168.1.1"'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('src="192.168.0.2"', 'src="192.168.1.2"'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_gre_ipv4_tcp_l3_src_l4_src = {
    'sub_casename': 'ipv4_gre_ipv4_tcp_l3_src_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('src="192.168.0.2"', 'src="192.168.1.2"'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dst="192.168.0.1"', 'dst="192.168.1.1"'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_gre_ipv4_tcp_l3_src_l4_dst = {
    'sub_casename': 'ipv4_gre_ipv4_tcp_l3_src_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('src="192.168.0.2"', 'src="192.168.1.2"'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dst="192.168.0.1"', 'dst="192.168.1.1"'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_gre_ipv4_tcp_l3_dst_l4_src = {
    'sub_casename': 'ipv4_gre_ipv4_tcp_l3_dst_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dst="192.168.0.1"', 'dst="192.168.1.1"'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('src="192.168.0.2"', 'src="192.168.1.2"'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet':mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_gre_ipv4_tcp_l3_dst_l4_dst = {
    'sub_casename': 'ipv4_gre_ipv4_tcp_l3_dst_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dst="192.168.0.1"', 'dst="192.168.1.1"'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('src="192.168.0.2"', 'src="192.168.1.2"'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ],
}

mac_ipv4_gre_ipv4_tcp_l4_src = {
    'sub_casename': 'ipv4_gre_ipv4_tcp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dst="192.168.0.1"', 'dst="192.168.1.1"'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('src="192.168.0.2"', 'src="192.168.1.2"'),

            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv4_tcp_l4_dst = {
    'sub_casename': 'ipv4_gre_ipv4_tcp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dst="192.168.0.1"', 'dst="192.168.1.1"'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('src="192.168.0.2"', 'src="192.168.1.2"'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv4_tcp_all = {
    'sub_casename': 'ipv4_gre_ipv4_tcp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dst="192.168.0.1"', 'dst="192.168.1.1"'),
            'action': {'check_hash_different': 'ipv4-tcp'}
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('src="192.168.0.2"', 'src="192.168.1.2"'),
            'action': {'check_hash_different': 'ipv4-tcp'}
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_different': 'ipv4-tcp'}
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_different': 'ipv4-tcp'}
        },
    ]
}

mac_ipv4_gre_ipv4_tcp_ipv4 = {
    'sub_casename': 'ipv4_gre_ipv4_tcp_ipv4',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'],
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dst="192.168.0.1"', 'dst="192.168.1.1"'),
            'action': {'check_hash_different': 'ipv4-tcp'}
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('src="192.168.0.2"', 'src="192.168.1.2"'),

            'action': {'check_hash_different': 'ipv4-tcp'}
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('sport=22', 'sport=21'),

            'action': {'check_hash_same': 'ipv4-tcp'}
        },
        {
            'send_packet': mac_ipv4_gre_ipv4_basic_pkt['ipv4-tcp'].replace('dport=23', 'dport=24'),

            'action': {'check_hash_same': 'ipv4-tcp'}
        },
    ]
}

mac_ipv4_gre_ipv6_l3_src = {
    'sub_casename': 'ipv4_gre_ipv6_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'],
            'action': {'save_hash': 'ipv6-nh'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'].replace('src="ABAB:910B:6666:3457:8295:3333:1800:2929"','src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_different': 'ipv6-nh'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'].replace('dst="CDCD:910A:2222:5498:8475:1111:3900:2020"', 'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_same': 'ipv6-nh'},
        },
    ]
}

mac_ipv4_gre_ipv6_l3_dst = {
    'sub_casename': 'ipv4_gre_ipv6_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'],
            'action': {'save_hash': 'ipv6-nh'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'].replace('dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                                                                          'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_different': 'ipv6-nh'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'].replace('src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
                                                                          'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_same': 'ipv6-nh'},
        },
    ]
}

mac_ipv4_gre_ipv6_all = {
    'sub_casename': 'ipv4_gre_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'],
            'action': {'save_hash': 'ipv6-nh'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'].replace('dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                                                                          'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_different': 'ipv6-nh'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'].replace('src="ABAB:910B:6666:3457:8295:3333:1800:2929"',
                                                                          'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_different': 'ipv6-nh'},
        },
    ]
}

mac_ipv4_gre_ipv6_tcp_l3_src = {
    'sub_casename': 'ipv4_gre_ipv6_tcp_l3_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'src="ABAB:910B:6666:3457:8295:3333:1800:2929"', 'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'].replace(
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv6_tcp_l3_dst = {
    'sub_casename': 'ipv4_gre_ipv6_tcp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-nh'].replace(
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'src="ABAB:910B:6666:3457:8295:3333:1800:2929"', 'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },

        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv6_tcp_l4_src = {
    'sub_casename': 'ipv4_gre_ipv6_tcp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'src="ABAB:910B:6666:3457:8295:3333:1800:2929"', 'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv6_tcp_l4_dst = {
    'sub_casename': 'ipv4_gre_ipv6_tcp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'src="ABAB:910B:6666:3457:8295:3333:1800:2929"', 'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv6_tcp_l3_src_l4_src = {
    'sub_casename': 'ipv4_gre_ipv6_tcp_l3_src_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'src="ABAB:910B:6666:3457:8295:3333:1800:2929"', 'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv6_tcp_l3_src_l4_dst = {
    'sub_casename': 'ipv4_gre_ipv6_tcp_l3_src_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'src="ABAB:910B:6666:3457:8295:3333:1800:2929"', 'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv6_tcp_l3_dst_l4_src = {
    'sub_casename': 'ipv4_gre_ipv6_tcp_l3_dst_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'src="ABAB:910B:6666:3457:8295:3333:1800:2929"', 'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv6_tcp_l3_dst_l4_dst = {
    'sub_casename': 'ipv4_gre_ipv6_tcp_l3_dst_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'src="ABAB:910B:6666:3457:8295:3333:1800:2929"', 'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv6_tcp_all = {
    'sub_casename': 'ipv4_gre_ipv6_tcp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'src="ABAB:910B:6666:3457:8295:3333:1800:2929"', 'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv6_tcp_ipv6 = {
    'sub_casename': 'ipv4_gre_ipv6_tcp_ipv6',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'],
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2020"',
                'dst="CDCD:910A:2222:5498:8475:1111:3900:2021"'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('dport=23', 'dport=24'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace(
                'src="ABAB:910B:6666:3457:8295:3333:1800:2929"', 'src="ABAB:910B:6666:3457:8295:3333:1800:2930"'),
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
        {
            'send_packet': mac_ipv4_gre_ipv6_basic_pkt['ipv6-tcp'].replace('sport=22', 'sport=21'),
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
    ]
}

mac_ipv4_gre_ipv4 = [
                     mac_ipv4_gre_ipv4_l3_src,
                     mac_ipv4_gre_ipv4_l3_dst,
                     mac_ipv4_gre_ipv4_all
                     ]

mac_ipv6_gre_ipv4 = [eval(str(each).replace('ipv4_gre_ipv4','ipv6_gre_ipv4').replace('IP()','IPv6()')
                           .replace('eth / ipv4','eth / ipv6')) for each in mac_ipv4_gre_ipv4]

mac_ipv4_gre_ipv6 = [
                     mac_ipv4_gre_ipv6_l3_src,
                     mac_ipv4_gre_ipv6_l3_dst,
                     mac_ipv4_gre_ipv6_all
                    ]

mac_ipv6_gre_ipv6 = [eval(str(each).replace('ipv4_gre_ipv6','ipv6_gre_ipv6').replace('IP()','IPv6()')
                           .replace('eth / ipv4','eth / ipv6')) for each in mac_ipv4_gre_ipv6]

mac_ipv4_gre_ipv4_tcp = [
                     mac_ipv4_gre_ipv4_tcp_l3_src,
                     mac_ipv4_gre_ipv4_tcp_l3_dst,
                     mac_ipv4_gre_ipv4_tcp_l4_src,
                     mac_ipv4_gre_ipv4_tcp_l4_dst,
                     mac_ipv4_gre_ipv4_tcp_l3_src_l4_src,
                     mac_ipv4_gre_ipv4_tcp_l3_src_l4_dst,
                     mac_ipv4_gre_ipv4_tcp_l3_dst_l4_src,
                     mac_ipv4_gre_ipv4_tcp_l3_dst_l4_dst,
                     mac_ipv4_gre_ipv4_tcp_all,
                     mac_ipv4_gre_ipv4_tcp_ipv4,
                    ]

mac_ipv6_gre_ipv4_tcp = [eval(str(each).replace('ipv4_gre_ipv4','ipv6_gre_ipv4').replace('IP()','IPv6()')
                           .replace('eth / ipv4','eth / ipv6')) for each in mac_ipv4_gre_ipv4_tcp]

mac_ipv4_gre_ipv6_tcp = [
                    mac_ipv4_gre_ipv6_tcp_l3_src,
                    mac_ipv4_gre_ipv6_tcp_l3_dst,
                    mac_ipv4_gre_ipv6_tcp_l4_src,
                    mac_ipv4_gre_ipv6_tcp_l4_dst,
                    mac_ipv4_gre_ipv6_tcp_l3_src_l4_src,
                    mac_ipv4_gre_ipv6_tcp_l3_src_l4_dst,
                    mac_ipv4_gre_ipv6_tcp_l3_dst_l4_src,
                    mac_ipv4_gre_ipv6_tcp_l3_dst_l4_dst,
                    mac_ipv4_gre_ipv6_tcp_all,
                    mac_ipv4_gre_ipv6_tcp_ipv6,
    ]

mac_ipv6_gre_ipv6_tcp = [eval(str(each).replace('ipv4_gre_ipv6','ipv6_gre_ipv6').replace('IP()','IPv6()')
                           .replace('eth / ipv4','eth / ipv6')) for each in mac_ipv4_gre_ipv6_tcp]

mac_ipv4_gre_ipv4_udp = [eval(str(each).replace('tcp','udp').replace('TCP','UDP').replace('proto=6','proto=17')) for each in mac_ipv4_gre_ipv4_tcp]

mac_ipv6_gre_ipv4_udp = [eval(str(each).replace('tcp','udp').replace('TCP','UDP').replace('proto=6','proto=17')) for each in mac_ipv6_gre_ipv4_tcp]

mac_ipv4_gre_ipv6_udp = [eval(str(each).replace('tcp','udp').replace('TCP','UDP').replace('nh=6','nh=17')) for each in mac_ipv4_gre_ipv6_tcp]

mac_ipv6_gre_ipv6_udp = [eval(str(each).replace('tcp','udp').replace('TCP','UDP').replace('nh=6','nh=17')) for each in mac_ipv6_gre_ipv6_tcp]

mac_ipv4_gre_ipv4_symmetric = {
    'sub_casename': 'mac_ipv4_gre_ipv4_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.1", src="192.168.0.2",proto=6)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-proto'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.2", src="192.168.0.1",proto=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-proto'},
        },
    ],
}

mac_ipv6_gre_ipv4_symmetric = eval(str(mac_ipv4_gre_ipv4_symmetric).replace('ipv4_gre_ipv4','ipv6_gre_ipv4').replace('IP()','IPv6()')
                           .replace('eth / ipv4','eth / ipv6'))

mac_ipv4_gre_ipv6_symmetric = {
    'sub_casename': 'mac_ipv4_gre_ipv6_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-nh'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-nh'},
        },
    ],
}

mac_ipv6_gre_ipv6_symmetric = eval(str(mac_ipv4_gre_ipv6_symmetric).replace('ipv4_gre_ipv6','ipv6_gre_ipv6').replace('IP()','IPv6()')
                           .replace('eth / ipv4','eth / ipv6'))

mac_ipv4_gre_ipv4_tcp_symmetric = {
    'sub_casename': 'mac_ipv4_gre_ipv4_tcp_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.1", src="192.168.0.2",proto=6)/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv4-proto'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.2", src="192.168.0.1",proto=6)/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-proto'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IP(dst="192.168.0.1", src="192.168.0.2",proto=6)/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv4-proto'},
        },
    ],
}

mac_ipv6_gre_ipv4_tcp_symmetric = eval(str(mac_ipv4_gre_ipv4_tcp_symmetric).replace('ipv4_gre_ipv4','ipv6_gre_ipv4').replace('IP()','IPv6()')
                           .replace('eth / ipv4','eth / ipv6'))

mac_ipv4_gre_ipv6_tcp_symmetric = {
    'sub_casename': 'mac_ipv4_gre_ipv6_tcp_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / gre / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'save_hash': 'ipv6-nh'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/TCP(sport=22,dport=23)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-nh'},
        },
        {
            'send_packet': 'Ether(dst="%s")/IP()/GRE()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/TCP(sport=23,dport=22)/("X"*480)' % vf0_mac,
            'action': {'check_hash_same': 'ipv6-nh'},
        },
    ],
}

mac_ipv6_gre_ipv6_tcp_symmetric = eval(str(mac_ipv4_gre_ipv6_tcp_symmetric).replace('ipv4_gre_ipv6','ipv6_gre_ipv6').replace('IP()','IPv6()')
                           .replace('eth / ipv4','eth / ipv6'))

mac_ipv4_gre_ipv4_udp_symmetric = eval(str(mac_ipv4_gre_ipv4_tcp_symmetric).replace('tcp','udp').replace('TCP','UDP').replace('proto=6','proto=17'))

mac_ipv6_gre_ipv4_udp_symmetric = eval(str(mac_ipv6_gre_ipv4_tcp_symmetric).replace('tcp','udp').replace('TCP','UDP').replace('proto=6','proto=17'))

mac_ipv4_gre_ipv6_udp_symmetric = eval(str(mac_ipv4_gre_ipv6_tcp_symmetric).replace('tcp','udp').replace('TCP','UDP').replace('nh=6','nh=17'))

mac_ipv6_gre_ipv6_udp_symmetric = eval(str(mac_ipv6_gre_ipv6_tcp_symmetric).replace('tcp','udp').replace('TCP','UDP').replace('nh=6','nh=17'))
#gre tunnel end

class AdvancedIavfRSSTest(TestCase):

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

        self.used_dut_port = self.dut_ports[0]
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.vf_flag = False
        self.create_iavf()

    def set_up(self):
        """
        Run before each test case.
        """
        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.launch_testpmd()
        self.rxq = 16
        self.rssprocess = RssProcessing(self, self.pmd_output, [self.tester_iface0, self.tester_iface1], self.rxq)
        self.logger.info('rssprocess.tester_ifaces: {}'.format(self.rssprocess.tester_ifaces))
        self.logger.info('rssprocess.test_case: {}'.format(self.rssprocess.test_case))

        self.pmd_output.execute_cmd("start")

    def create_iavf(self):

        if self.vf_flag is False:
            self.dut.bind_interfaces_linux('ice')
            self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 1)
            self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]['vfs_port']
            self.vf_flag = True

            try:
                for port in self.sriov_vfs_port:
                    port.bind_driver(self.drivername)

                self.vf0_prop = {'opt_host': self.sriov_vfs_port[0].pci}
                self.dut.send_expect("ifconfig %s up" % self.pf_interface, "# ")
                self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf_interface, vf0_mac), "# ")
            except Exception as e:
                self.destroy_iavf()
                raise Exception(e)

    def destroy_iavf(self):
        if self.vf_flag is True:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.vf_flag = False

    def launch_testpmd(self):
        param = "--rxq=16 --txq=16"
        self.pmd_output.start_testpmd(cores="1S/4C/1T", param=param,
                                            ports=[self.sriov_vfs_port[0].pci], socket=self.ports_socket)
        self.pmd_output.execute_cmd("port config all rss all")
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        res = self.pmd_output.wait_link_status_up('all', timeout=15)
        self.verify(res is True, 'there have port link is down')

    def test_mac_ipv4(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4)

    def test_mac_ipv4_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_udp)

    def test_mac_ipv4_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_tcp)

    def test_mac_ipv4_sctp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_sctp)

    def test_mac_ipv6(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6)

    def test_mac_ipv6_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_udp)

    def test_mac_ipv6_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_tcp)

    def test_mac_ipv6_sctp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_sctp)

    def test_symmetric_mac_ipv4(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_symmetric)

    def test_symmetric_mac_ipv4_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_udp_symmetric)

    def test_symmetric_mac_ipv4_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_tcp_symmetric)

    def test_symmetric_mac_ipv4_sctp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_sctp_symmetric)

    def test_symmetric_mac_ipv6(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_symmetric)

    def test_symmetric_mac_ipv6_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_udp_symmetric)

    def test_symmetric_mac_ipv6_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_tcp_symmetric)

    def test_symmetric_mac_ipv6_sctp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_sctp_symmetric)

    def test_64bit_ipv6_prefix(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_64bit_prefix)

    def test_negative_case(self):
        negative_rules = [
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l3-src-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-udp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 l3-src-only end key_len 0 queues end / end',
        ]
        for i in negative_rules:
            out = self.pmd_output.execute_cmd(i, timeout=1)
            self.verify('iavf_flow_create(): Failed to create flow' in out, "rule %s create successfully" % i)

    def test_multirules(self):
        # Subcase 1: two rules with same pattern but different hash input set, not hit default profile
        self.logger.info('===================Test sub case: multirules subcase 1 ================')
        self.rssprocess.error_msgs = []
        rule_id_0 = self.rssprocess.create_rule(
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end',
            check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_0)
        tests = [
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'save_hash': 'ipv4-udp'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_different': 'ipv4-udp'},
            },
        ]
        self.rssprocess.handle_tests(tests, 0)
        rule_id_1 = self.rssprocess.create_rule(
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
            check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_1)
        tests = [
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'save_hash': 'ipv4-udp'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_same': 'ipv4-udp'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.7")/UDP(dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_different': 'ipv4-udp'},
            },
        ]
        self.rssprocess.handle_tests(tests, 0)
        self.dut.send_command("flow flush 0", timeout=1)

        # Subcase 2: two rules with same pattern but different hash input set, hit default profile
        self.logger.info('===================Test sub case: multirules subcase 2 ================')
        rule_id_0 = self.rssprocess.create_rule(
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
            check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_0)
        tests = [
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*480)' % vf0_mac,
                'action': {'save_hash': 'ipv4-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.7",dst="192.168.0.5")/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_different': 'ipv4-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.8")/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_same': 'ipv4-pay'},
            },
        ]
        self.rssprocess.handle_tests(tests, 0)
        rule_id_1 = self.rssprocess.create_rule(
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
            check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_1)
        tests = [
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*480)' % vf0_mac,
                'action': {'save_hash': 'ipv4-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.7",dst="192.168.0.5")/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_same': 'ipv4-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.7")/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_different': 'ipv4-pay'},
            },
        ]
        self.rssprocess.handle_tests(tests, 0)
        self.dut.send_command("flow flush 0", timeout=1)

        # Subcase 3: two rules, scope smaller created first, and the larger one created later
        self.logger.info('===================Test sub case: multirules subcase 3 ================')
        rule_id_0 = self.rssprocess.create_rule(
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
            check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_0)
        tests_3 = [
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'save_hash': 'ipv4-udp-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25, dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_different': 'ipv4-udp-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.7",dst="192.168.0.8")/UDP(sport=23, dport=44)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_same': 'ipv4-udp-pay'},
            },
        ]
        self.rssprocess.handle_tests(tests_3, 0)
        rule_id_1 = self.rssprocess.create_rule(
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
            check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_1)
        tests = [
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'save_hash': 'ipv4-udp-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_different': 'ipv4-udp-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.8")/UDP(sport=25, dport=99)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_same': 'ipv4-udp-pay'},
            },
        ]
        self.rssprocess.handle_tests(tests, 0)
        self.dut.send_command("flow flush 0", timeout=1)

        # Subcase 4: two rules, scope larger created first, and the smaller one created later
        self.logger.info('===================Test sub case: multirules subcase 4 ================')
        rule_id_0 = self.rssprocess.create_rule(
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
            check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_0)
        tests_4 = [
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'save_hash': 'ipv4-udp-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_different': 'ipv4-udp-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.8")/UDP(sport=25, dport=99)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_same': 'ipv4-udp-pay'},
            },
        ]
        self.rssprocess.handle_tests(tests_4, 0)
        rule_id_1 = self.rssprocess.create_rule(
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
            check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_1)
        tests = [
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'save_hash': 'ipv4-udp-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25, dport=45)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_different': 'ipv4-udp-pay'},
            },
            {
                'send_packet': 'Ether(dst="%s")/IP(src="192.168.0.7",dst="192.168.0.8")/UDP(sport=23, dport=44)/Raw("x"*480)' % vf0_mac,
                'action': {'check_hash_same': 'ipv4-udp-pay'},
            },
        ]
        self.rssprocess.handle_tests(tests, 0)
        self.verify(not self.rssprocess.error_msgs, 'some subcases failed')

    def test_mac_ipv4_gre_ipv4(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4)

    def test_mac_ipv6_gre_ipv4(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4)

    def test_mac_ipv4_gre_ipv6(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6)

    def test_mac_ipv6_gre_ipv6(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6)

    def test_mac_ipv4_gre_ipv4_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_tcp)

    def test_mac_ipv6_gre_ipv4_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_tcp)

    def test_mac_ipv4_gre_ipv6_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_tcp)

    def test_mac_ipv6_gre_ipv6_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_tcp)

    def test_mac_ipv4_gre_ipv4_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_udp)

    def test_mac_ipv6_gre_ipv4_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_udp)

    def test_mac_ipv4_gre_ipv6_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_udp)

    def test_mac_ipv6_gre_ipv6_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_udp)

    def test_symmetric_mac_ipv4_gre_ipv4(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_symmetric)

    def test_symmetric_mac_ipv6_gre_ipv4(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_symmetric)

    def test_symmetric_mac_ipv4_gre_ipv6(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_symmetric)

    def test_symmetric_mac_ipv6_gre_ipv6(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_symmetric)

    def test_symmetric_mac_ipv4_gre_ipv4_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_tcp_symmetric)

    def test_symmetric_mac_ipv6_gre_ipv4_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_tcp_symmetric)

    def test_symmetric_mac_ipv4_gre_ipv6_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_tcp_symmetric)

    def test_symmetric_mac_ipv6_gre_ipv6_tcp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_tcp_symmetric)

    def test_symmetric_mac_ipv4_gre_ipv4_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv4_udp_symmetric)

    def test_symmetric_mac_ipv6_gre_ipv4_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv4_udp_symmetric)

    def test_symmetric_mac_ipv4_gre_ipv6_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gre_ipv6_udp_symmetric)

    def test_symmetric_mac_ipv6_gre_ipv6_udp(self):
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_gre_ipv6_udp_symmetric)

    def tear_down(self):
        # destroy all flow rule on port 0
        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("quit", "#")

    def tear_down_all(self):
        self.dut.kill_all()
        self.destroy_iavf()
