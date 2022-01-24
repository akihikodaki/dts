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

from .rte_flow_common import RssProcessing, FdirProcessing, check_mark

# toeplitz related data start
mac_ipv4_toeplitz_basic_pkt = {
    'ipv4-nonfrag': [
       'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
    ],
    'ipv4-frag': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2", frag=6)/("X"*480)',
    ],
    'ipv4-icmp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)',
    ],
    'ipv4-tcp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    'ipv4-udp-vxlan': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv4_udp_toeplitz_basic_pkt = {
    'ipv4-udp': [
       'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
    ],
    'nvgre': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv4_udp_toeplitz_non_basic_pkt = [
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    ]

mac_ipv4_tcp_toeplitz_basic_pkt = {
    'ipv4-tcp': [
       'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    'nvgre': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv4_tcp_toeplitz_non_basic_pkt = [
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)'
    ]

mac_ipv4_sctp_toeplitz_basic_pkt = {
    'ipv4-sctp': [
       'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
    ],
    'nvgre': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv4_sctp_toeplitz_non_basic_pkt = [
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    ]

mac_ipv6_toeplitz_basic_pkt = {
    'ipv6-nonfrag': [
       'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    ],
    'ipv6-frag': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
    ],
    'ipv6-icmp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
    ],
    'ipv6-udp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
    ],
    'nvgre': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    ],
}

mac_ipv6_toeplitz_non_basic_pkt = [
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
    ]

mac_ipv6_udp_toeplitz_basic_pkt = {
    'ipv6-udp': [
       'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
    ],
    'ipv4_udp_vxlan_ipv6_udp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv6_udp_toeplitz_non_basic_pkt = [
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(src="192.168.0.1",dst="192.168.0.2")/UDP(sport=22,dport=23)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
    ]

mac_ipv6_tcp_toeplitz_basic_pkt = {
    'ipv6-tcp': [
       'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    'ipv4_tcp_vxlan_ipv6_tcp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv6_tcp_toeplitz_non_basic_pkt = [
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(src="192.168.0.1",dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
    ]

mac_ipv6_sctp_toeplitz_basic_pkt = {
    'ipv6-sctp': [
       'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
    ],
    'ipv4_sctp_vxlan_ipv6_sctp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv6_sctp_toeplitz_non_basic_pkt = [
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(src="192.168.0.1",dst="192.168.0.2")/SCTP(sport=22,dport=23)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
    ]

mac_ipv4_l2src_changed = {
    'ipv4-nonfrag': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
    ],
    'ipv4-frag': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2", frag=6)/("X"*480)',
    ],
    'ipv4-icmp': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)',
    ],
    'ipv4-tcp': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    'ipv4-udp-vxlan': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv4_l2dst_changed = {
    'ipv4-nonfrag': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
    ],
    'ipv4-frag': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2", frag=6)/("X"*480)',
    ],
    'ipv4-icmp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)',
    ],
    'ipv4-tcp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    'ipv4-udp-vxlan': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv4_l3src_changed = {
    'ipv4-nonfrag': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)',
    ],
    'ipv4-frag': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2", frag=6)/("X"*480)',
    ],
    'ipv4-icmp': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)',
    ],
    'ipv4-tcp': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    'ipv4-udp-vxlan': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv4_l3dst_changed = {
    'ipv4-nonfrag': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)',
    ],
    'ipv4-frag': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2", frag=6)/("X"*480)',
    ],
    'ipv4-icmp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)',
    ],
    'ipv4-tcp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
    ],
    'ipv4-udp-vxlan': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv6_l2src_changed = {
    'ipv6-nonfrag': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
    ],
    'ipv6-frag': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
    ],
    'ipv6-icmp': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
    ],
    'ipv6-udp': [
        'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
    ],
}

mac_ipv6_l2dst_changed = {
    'ipv6-nonfrag': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)',
    ],
    'ipv6-frag': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/("X"*480)',
    ],
    'ipv6-icmp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/ICMP()/("X"*480)',
    ],
    'ipv6-udp': [
        'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)',
    ],
}

#mac_ipv4
mac_ipv4_l2_src = {
    'sub_casename': 'mac_ipv4_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-nonfrag'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-frag'],
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-frag'],
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-icmp'],
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-icmp'],
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'],
            'action': {'save_hash': 'ipv4-udp-vxlan'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-udp-vxlan'],
            'action': {'check_hash_different': 'ipv4-udp-vxlan'},
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-udp-vxlan'],
            'action': {'check_hash_same': 'ipv4-udp-vxlan'},
        }
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-frag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'][0],
                ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_l2_dst = {
    'sub_casename': 'mac_ipv4_l2dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'],
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-nonfrag'],
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-nonfrag'],
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-frag'],
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-frag'],
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-icmp'],
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-icmp'],
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'],
            'action': {'save_hash': 'ipv4-udp-vxlan'},
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-udp-vxlan'],
            'action': {'check_hash_different': 'ipv4-udp-vxlan'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-udp-vxlan'],
            'action': {'check_hash_same': 'ipv4-udp-vxlan'},
        }
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-frag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'][0],
            ],
            'action': {'check_no_hash': ''},
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
            'send_packet': mac_ipv4_l2dst_changed['ipv4-nonfrag'],
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-nonfrag'],
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/("X"*480)',
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-frag'],
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-frag'],
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5",frag=7)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-icmp'],
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-icmp'],
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'],
            'action': {'save_hash': 'ipv4-udp-vxlan'},
        },
        {
            'send_packet': mac_ipv4_l2dst_changed['ipv4-udp-vxlan'],
            'action': {'check_hash_different': 'ipv4-udp-vxlan'},
        },
        {
            'send_packet': mac_ipv4_l2src_changed['ipv4-udp-vxlan'],
            'action': {'check_hash_different': 'ipv4-udp-vxlan'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-udp-vxlan'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=23,dport=25)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-udp-vxlan'},
        }
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-frag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'][0],
            ],
            'action': {'check_no_hash': ''},
        },
    ],
}

mac_ipv4_l3_src = {
    'sub_casename': 'mac_ipv4_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'],
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_l3src_changed['ipv4-nonfrag'],
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_l3dst_changed['ipv4-nonfrag'],
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l3src_changed['ipv4-frag'],
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l3dst_changed['ipv4-frag'],
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l3src_changed['ipv4-icmp'],
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l3dst_changed['ipv4-icmp'],
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-frag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'][0],
            ],
            'action': {'check_no_hash': ''},
        },
    ],
}

mac_ipv4_l3_dst = {
    'sub_casename': 'mac_ipv4_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'],
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_l3dst_changed['ipv4-nonfrag'],
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_l3src_changed['ipv4-nonfrag'],
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l3dst_changed['ipv4-frag'],
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l3src_changed['ipv4-frag'],
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l3dst_changed['ipv4-icmp'],
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l3src_changed['ipv4-icmp'],
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-frag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'][0],
            ],
            'action': {'check_no_hash': ''},
        },
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
            'send_packet': mac_ipv4_l3dst_changed['ipv4-nonfrag'],
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_l3src_changed['ipv4-nonfrag'],
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-frag'],
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l3dst_changed['ipv4-frag'],
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_l3src_changed['ipv4-frag'],
            'action': {'check_hash_different': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'],
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l3dst_changed['ipv4-icmp'],
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': mac_ipv4_l3src_changed['ipv4-icmp'],
            'action': {'check_hash_different': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-frag'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-icmp'][0],
                mac_ipv4_toeplitz_basic_pkt['ipv4-udp-vxlan'][0],
            ],
            'action': {'check_no_hash': ''},
        },
    ],
}

mac_ipv4_ipv4_chksum = {
    'sub_casename': 'mac_ipv4_ipv4_chksum',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-chksum  end queues end / end',
    'test': [
        {
            'send_packet': eval(str(mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag']).replace('src="192.168.0.2"',
                                                                                         'src="192.168.0.2", chksum=0x1')),
            'action': 'save_hash',
        },
        {
            'send_packet': eval(str(mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag']).replace('src="192.168.0.2"',
                                                                                         'src="192.168.0.2", chksum=0xffff')),
            'action': 'check_hash_different',
        },
        {
            'send_packet': eval(str(mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag']).replace('dst="192.168.0.1", src="192.168.0.2"',
                                                                                         'dst="192.168.1.1", src="192.168.1.2", chksum=0x1')),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': eval(str(mac_ipv4_toeplitz_basic_pkt['ipv4-nonfrag']).replace('src="192.168.0.2"',
                                                                                         'src="192.168.0.2", chksum=0x1')),
            'action': 'check_no_hash',
        },
    ],
}

#mac ipv4_udp
mac_ipv4_udp_l2_src = {
    'sub_casename': 'mac_ipv4_udp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
                mac_ipv4_udp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_l3_dst = {
    'sub_casename': 'mac_ipv4_udp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
                mac_ipv4_udp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
                mac_ipv4_udp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
                mac_ipv4_udp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
                mac_ipv4_udp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
                mac_ipv4_udp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_l4_src = {
    'sub_casename': 'mac_ipv4_udp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
                mac_ipv4_udp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_l4_dst = {
    'sub_casename': 'mac_ipv4_udp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
                mac_ipv4_udp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_all = {
    'sub_casename': 'mac_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
                mac_ipv4_udp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_ipv4 = {
    'sub_casename': 'mac_ipv4_udp_ipv4',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:53", src="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp'][0],
                mac_ipv4_udp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_l4_chksum = {
    'sub_casename': 'mac_ipv4_udp_l4_chksum',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l4-chksum  end queues end / end',
    'test': [
        {
            'send_packet': eval(str(mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp']).replace("dport=23", "dport=23,chksum=0xffff")),
            'action': 'save_hash',
        },
        {
            'send_packet': eval(str(mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp']).replace("dport=23", "dport=23,chksum=0xfffe")),
            'action': 'check_hash_different',
        },
        {
            'send_packet': eval(str(mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp']).replace('dst="192.168.0.1", src="192.168.0.2"',
                                                                                         'dst="192.168.1.1", src="192.168.1.2", chksum=0x3')
                                                                                .replace('sport=22,dport=23', 'sport=32,dport=33,chksum=0xffff')),
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1",dst="192.168.0.2")/SCTP(sport=22, dport=23,chksum=0xffff)/("X"*48)',
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': eval(str(mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp']).replace("dport=23", "dport=23,chksum=0xffff")),
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_ipv4_chksum = {
    'sub_casename': 'mac_ipv4_udp_ipv4_chksum',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-chksum  end queues end / end',
    'test': [
        {
            'send_packet': eval(str(mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp']).replace('src="192.168.0.2"', 'src="192.168.0.2",chksum=0xffff')),
            'action': 'save_hash',
        },
        {
            'send_packet': eval(str(mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp']).replace('src="192.168.0.2"', 'src="192.168.0.2",chksum=0xfffe')),
            'action': 'check_hash_different',
        },
        {
            'send_packet': eval(str(mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp']).replace('dst="192.168.0.1", src="192.168.0.2"',
                                                                                         'dst="192.168.1.1", src="192.168.1.2", chksum=0xffff')
                                                                                .replace('sport=22,dport=23', 'sport=32,dport=33,chksum=0xffff')),
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1",dst="192.168.0.2")/SCTP(sport=22, dport=23,chksum=0xffff)/("X"*48)',
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': eval(str(mac_ipv4_udp_toeplitz_basic_pkt['ipv4-udp']).replace('src="192.168.0.2"', 'src="192.168.0.2",chksum=0xffff')),
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_chksum = [mac_ipv4_udp_l4_chksum, mac_ipv4_udp_ipv4_chksum]

#mac ipv4_tcp
mac_ipv4_tcp_l2_src = {
    'sub_casename': 'mac_ipv4_tcp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
                mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_tcp_l3_dst = {
    'sub_casename': 'mac_ipv4_tcp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
                mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_tcp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_tcp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
                mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_tcp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_tcp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
                mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_tcp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_tcp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
                mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_tcp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_tcp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
                mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_tcp_l4_src = {
    'sub_casename': 'mac_ipv4_tcp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.1.2")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
                mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_tcp_l4_dst = {
    'sub_casename': 'mac_ipv4_tcp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.1.2")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
                mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_tcp_all = {
    'sub_casename': 'mac_ipv4_tcp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
                mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_tcp_ipv4 = {
    'sub_casename': 'mac_ipv4_tcp_ipv4',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_tcp_toeplitz_basic_pkt['ipv4-tcp'][0],
                mac_ipv4_tcp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_tcp_chksum = [eval(str(element).replace("mac_ipv4_udp", "mac_ipv4_tcp")
                                        .replace("ipv4 / udp", "ipv4 / tcp")
                                        .replace("/UDP(sport=", "/TCP(sport="))
                                    for element in mac_ipv4_udp_chksum]

#mac ipv4_sctp
mac_ipv4_sctp_l2_src = {
    'sub_casename': 'mac_ipv4_sctp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/SCTP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/SCTP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/SCTP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
                mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_sctp_l3_dst = {
    'sub_casename': 'mac_ipv4_sctp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
                mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_sctp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_sctp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
                mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_sctp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_sctp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
                mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_sctp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_sctp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
                mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_sctp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_sctp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
                mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_sctp_l4_src = {
    'sub_casename': 'mac_ipv4_sctp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.1.2")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
                mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_sctp_l4_dst = {
    'sub_casename': 'mac_ipv4_sctp_l4_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.1.1", src="192.168.1.2")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
                mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_sctp_all = {
    'sub_casename': 'mac_ipv4_sctp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
                mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_sctp_ipv4 = {
    'sub_casename': 'mac_ipv4_sctp_ipv4',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv4_sctp_toeplitz_basic_pkt['ipv4-sctp'][0],
                mac_ipv4_sctp_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_sctp_chksum = [eval(str(element).replace("mac_ipv4_udp", "mac_ipv4_sctp")
                                         .replace("SCTP(sport=", "TCP(sport=")
                                         .replace("ipv4 / udp", "ipv4 / sctp")
                                         .replace("/UDP(sport=", "/SCTP(sport="))
                                    for element in mac_ipv4_udp_chksum]

#mac_ipv6
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
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)',
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-frag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_l2_dst = {
    'sub_casename': 'mac_ipv6_l2dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'],
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)',
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(sport=25,dport=99)/("X"*480)',
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-frag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-udp'][0],
            ],
            'action': {'check_no_hash': ''},
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
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)',
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)',
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-frag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-udp'][0],
            ],
            'action': {'check_no_hash': ''},
        },
    ],
}

mac_ipv6_l3_src = {
    'sub_casename': 'mac_ipv6_l3src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'],
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)',
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=33)/("X"*480)',
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-frag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': {'check_no_hash': ''},
        },
    ],
}

mac_ipv6_l3_dst = {
    'sub_casename': 'mac_ipv6_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'],
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)',
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)',
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-frag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_toeplitz_basic_pkt['nvgre'][0],
            ],
            'action': {'check_no_hash': ''},
        },
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
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)',
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_hash_different': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-frag'],
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'],
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_basic_pkt['ipv6-udp'],
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)',
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        {
            'send_packet': mac_ipv6_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_toeplitz_basic_pkt['ipv6-nonfrag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-frag'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-icmp'][0],
                mac_ipv6_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_toeplitz_basic_pkt['nvgre'][0]
            ],
            'action': {'check_no_hash': ''},
        },
    ],
}

#mac_ipv6_udp
mac_ipv6_udp_l2_src = {
    'sub_casename': 'mac_ipv6_udp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_l3_dst = {
    'sub_casename': 'mac_ipv6_udp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv6_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv6_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv6_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv6_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_l4_src = {
    'sub_casename': 'mac_ipv6_udp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_l4_dst = {
    'sub_casename': 'mac_ipv6_udp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_all = {
    'sub_casename': 'mac_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_ipv6 = {
    'sub_casename': 'mac_ipv6_udp_ipv6',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_udp_toeplitz_basic_pkt['ipv6-udp'][0],
                mac_ipv6_udp_toeplitz_basic_pkt['ipv4_udp_vxlan_ipv6_udp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_l4_chksum = {
    'sub_casename': 'mac_ipv6_udp_l4_chksum',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types l4-chksum  end queues end / end',
    'test': [
        {
            'send_packet': eval(str(mac_ipv6_toeplitz_basic_pkt['ipv6-udp']).replace("dport=23", "dport=23, chksum=0x1")),
            'action': 'save_hash',
        },
        {
            'send_packet': eval(str(mac_ipv6_toeplitz_basic_pkt['ipv6-udp']).replace("dport=23", "dport=23, chksum=0x2")),
            'action': 'check_hash_different',
        },
        {
            'send_packet': eval(str(mac_ipv6_toeplitz_basic_pkt['ipv6-udp']).replace("sport=22,dport=23", "sport=22,dport=23,chksum=0x1")
                                                                            .replace("1800:2929", "1800:3939")
                                                                            .replace("2020", "3030")),
            'action': 'check_hash_same',
        },
        {
            'send_packet': eval(str(mac_ipv6_toeplitz_basic_pkt['ipv6-udp']).replace("/UDP(sport=22,dport=23)", "/SCTP(sport=22,dport=23,chksum=0x1)")),
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': eval(str(mac_ipv6_toeplitz_basic_pkt['ipv6-udp']).replace("dport=23", "dport=23, chksum=0x1")),
            'action': 'check_no_hash',
        },
    ],
}

#mac_ipv6_tcp
mac_ipv6_tcp_l2_src = {
    'sub_casename': 'mac_ipv6_tcp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_tcp_l3_dst = {
    'sub_casename': 'mac_ipv6_tcp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_tcp_l3src_l4src = {
    'sub_casename': 'mac_ipv6_tcp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_tcp_l3src_l4dst = {
    'sub_casename': 'mac_ipv6_tcp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_tcp_l3dst_l4src = {
    'sub_casename': 'mac_ipv6_tcp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_tcp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv6_tcp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_tcp_l4_src = {
    'sub_casename': 'mac_ipv6_tcp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_tcp_l4_dst = {
    'sub_casename': 'mac_ipv6_tcp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_tcp_all = {
    'sub_casename': 'mac_ipv6_tcp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_tcp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_tcp_ipv6 = {
    'sub_casename': 'mac_ipv6_tcp_ipv6',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv6-tcp'][0],
                mac_ipv6_tcp_toeplitz_basic_pkt['ipv4_tcp_vxlan_ipv6_tcp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_tcp_l4_chksum = eval(str(mac_ipv6_udp_l4_chksum).replace("mac_ipv6_udp", "mac_ipv6_tcp")
                                                         .replace("ipv6 / udp", "ipv6 / tcp")
                                                         .replace("/UDP(sport=", "/TCP(sport="))

#mac_ipv6_sctp
mac_ipv6_sctp_l2_src = {
    'sub_casename': 'mac_ipv6_sctp_l2_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/SCTP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/SCTP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/SCTP(sport=25,dport=99)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
            ],
            'action': 'check_no_hash',
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
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_sctp_l3_dst = {
    'sub_casename': 'mac_ipv6_sctp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_sctp_l3src_l4src = {
    'sub_casename': 'mac_ipv6_sctp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_sctp_l3src_l4dst = {
    'sub_casename': 'mac_ipv6_sctp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_sctp_l3dst_l4src = {
    'sub_casename': 'mac_ipv6_sctp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_sctp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv6_sctp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_sctp_l4_src = {
    'sub_casename': 'mac_ipv6_sctp_l4_src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_sctp_l4_dst = {
    'sub_casename': 'mac_ipv6_sctp_l3_dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_sctp_all = {
    'sub_casename': 'mac_ipv6_sctp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=33)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_sctp_toeplitz_non_basic_pkt,
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_sctp_ipv6 = {
    'sub_casename': 'mac_ipv6_sctp_ipv6',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'],
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:53", dst="68:05:CA:BB:27:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=33)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv6-sctp'][0],
                mac_ipv6_sctp_toeplitz_basic_pkt['ipv4_sctp_vxlan_ipv6_sctp'][0],
            ],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_sctp_l4_chksum = eval(str(mac_ipv6_udp_l4_chksum).replace("mac_ipv6_udp", "mac_ipv6_sctp")
                                                          .replace("/SCTP(sport=", "/TCP(sport=")
                                                          .replace("ipv6 / udp", "ipv6 / sctp")
                                                          .replace("/UDP(sport=", "/SCTP(sport="))

# toeplitz related data end

mac_ipv4_1 = [mac_ipv4_l2_src, mac_ipv4_l2_dst, mac_ipv4_l2src_l2dst]
mac_ipv4_2 = [mac_ipv4_l3_src, mac_ipv4_l3_dst, mac_ipv4_all]
mac_ipv4_ipv4_chksum = [mac_ipv4_ipv4_chksum]

mac_ipv4_udp = [mac_ipv4_udp_l2_src, mac_ipv4_udp_l2_dst, mac_ipv4_udp_l2src_l2dst,
                mac_ipv4_udp_l3_src, mac_ipv4_udp_l3_dst, mac_ipv4_udp_l3src_l4src,
                mac_ipv4_udp_l3src_l4dst, mac_ipv4_udp_l3dst_l4src, mac_ipv4_udp_l3dst_l4dst,
                mac_ipv4_udp_l4_src, mac_ipv4_udp_l4_dst, mac_ipv4_udp_all, mac_ipv4_udp_ipv4]

mac_ipv4_tcp = [mac_ipv4_tcp_l2_src, mac_ipv4_tcp_l2_dst, mac_ipv4_tcp_l2src_l2dst,
                mac_ipv4_tcp_l3_src, mac_ipv4_tcp_l3_dst, mac_ipv4_tcp_l3src_l4src,
                mac_ipv4_tcp_l3src_l4dst, mac_ipv4_tcp_l3dst_l4src, mac_ipv4_tcp_l3dst_l4dst,
                mac_ipv4_tcp_l4_src, mac_ipv4_tcp_l4_dst, mac_ipv4_tcp_all, mac_ipv4_tcp_ipv4]

mac_ipv4_sctp = [mac_ipv4_sctp_l2_src, mac_ipv4_sctp_l2_dst, mac_ipv4_sctp_l2src_l2dst,
                mac_ipv4_sctp_l3_src, mac_ipv4_sctp_l3_dst, mac_ipv4_sctp_l3src_l4src,
                mac_ipv4_sctp_l3src_l4dst, mac_ipv4_sctp_l3dst_l4src, mac_ipv4_sctp_l3dst_l4dst,
                mac_ipv4_sctp_l4_src, mac_ipv4_sctp_l4_dst, mac_ipv4_sctp_all, mac_ipv4_sctp_ipv4]

mac_ipv6 = [mac_ipv6_l2_src, mac_ipv6_l2_dst, mac_ipv6_l2src_l2dst, mac_ipv6_l3_src, mac_ipv6_l3_dst, mac_ipv6_all]

mac_ipv6_udp = [mac_ipv6_udp_l2_src, mac_ipv6_udp_l2_dst, mac_ipv6_udp_l2src_l2dst,
                mac_ipv6_udp_l3_src, mac_ipv6_udp_l3_dst, mac_ipv6_udp_l3src_l4src,
                mac_ipv6_udp_l3src_l4dst, mac_ipv6_udp_l3dst_l4src, mac_ipv6_udp_l3dst_l4dst,
                mac_ipv6_udp_l4_src, mac_ipv6_udp_l4_dst, mac_ipv6_udp_all, mac_ipv6_udp_ipv6]
mac_ipv6_udp_l4_chksum = [mac_ipv6_udp_l4_chksum]

mac_ipv6_tcp = [mac_ipv6_tcp_l2_src, mac_ipv6_tcp_l2_dst, mac_ipv6_tcp_l2src_l2dst,
                mac_ipv6_tcp_l3_src, mac_ipv6_tcp_l3_dst, mac_ipv6_tcp_l3src_l4src,
                mac_ipv6_tcp_l3src_l4dst, mac_ipv6_tcp_l3dst_l4src, mac_ipv6_tcp_l3dst_l4dst,
                mac_ipv6_tcp_l4_src, mac_ipv6_tcp_l4_dst, mac_ipv6_tcp_all, mac_ipv6_tcp_ipv6]
mac_ipv6_tcp_l4_chksum = [mac_ipv6_tcp_l4_chksum]

mac_ipv6_sctp = [mac_ipv6_sctp_l2_src, mac_ipv6_sctp_l2_dst, mac_ipv6_sctp_l2src_l2dst,
                mac_ipv6_sctp_l3_src, mac_ipv6_sctp_l3_dst, mac_ipv6_sctp_l3src_l4src,
                mac_ipv6_sctp_l3src_l4dst, mac_ipv6_sctp_l3dst_l4src, mac_ipv6_sctp_l3dst_l4dst,
                mac_ipv6_sctp_l4_src, mac_ipv6_sctp_l4_dst, mac_ipv6_sctp_all, mac_ipv6_sctp_ipv6]
mac_ipv6_sctp_l4_chksum = [mac_ipv6_sctp_l4_chksum]

# symmetric related data start
mac_ipv4_symmetric = {
    'sub_casename': 'mac_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
            'action': {'save_hash': 'ipv4-nonfrag-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)',
            'action': {'check_hash_different': 'ipv4-nonfrag-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)',
            'action': {'save_hash': 'ipv4-frag-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-frag-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)',
            'action': {'save_hash': 'ipv4-icmp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv4-icmp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-tcp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-tcp-pre'},
        },
    ],
    'test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)',
            'action': {'check_hash_same': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)',
            'action': {'save_hash': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)',
            'action': {'save_hash': 'ipv4-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'ipv4-icmp'},
        },
        {
           'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
           'action': {'save_hash': 'ipv4-tcp'},
        },
        {
           'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)',
           'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'save_hash': 'ipv6'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2928")/("X"*480)',
            'action': {'check_hash_different': 'ipv6'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
            'action': {'save_or_no_hash': 'ipv4-nonfrag-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv4-nonfrag-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)',
            'action': {'save_or_no_hash': 'ipv4-frag-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv4-frag-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)',
            'action': {'save_or_no_hash': 'ipv4-icmp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/ICMP()/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv4-icmp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'save_or_no_hash': 'ipv4-tcp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv4-tcp-post'},
        },
    ],
}

mac_ipv4_udp_symmetric = {
    'sub_casename': 'mac_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-udp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-udp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-udp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-udp-pre'},
        },
    ],
    'test': [
		{
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-tcp'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-udp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv4-udp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv4-udp-post'},
        },
    ],
}

mac_ipv4_tcp_symmetric = {
    'sub_casename': 'mac_ipv4_tcp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-tcp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-tcp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-tcp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-tcp-pre'},
        },
    ],
    'test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-tcp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-udp'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-tcp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv4-tcp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv4-tcp-post'},
        },
    ],
}

mac_ipv4_sctp_symmetric = {
    'sub_casename': 'mac_ipv4_sctp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss func symmetric_toeplitz types ipv4-sctp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-sctp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-sctp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-sctp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-sctp-pre'},
        },
    ],
    'test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)',
            'action': {'check_hash_same': 'ipv4-sctp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv4-udp'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv4-sctp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv4-sctp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv4-sctp-post'},
        },
    ],
}

mac_ipv6_symmetric = {
    'sub_casename': 'mac_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'save_hash': 'ipv6-nonfrag-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_hash_different': 'ipv6-nonfrag-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'save_hash': 'ipv6-frag-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-frag-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'save_hash': 'ipv6-icmp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_different': 'ipv6-icmp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-udp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp-pre'},
        },
    ],
    'test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'save_hash': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_hash_same': 'ipv6-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'save_hash': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-frag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'save_hash': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_hash_same': 'ipv6-icmp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
            'action': {'save_hash': 'ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)',
            'action': {'check_hash_different': 'ipv4-nonfrag'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'save_or_no_hash': 'ipv6-nonfrag-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv6-nonfrag-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'save_or_no_hash': 'ipv6-frag-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv6-frag-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'save_or_no_hash': 'ipv6-icmp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv6-icmp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_or_no_hash': 'ipv6-udp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv6-udp-post'},
        },
    ],
}

mac_ipv6_udp_symmetric = {
    'sub_casename': 'mac_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-udp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp-pre'},
        },
    ],
    'test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_same': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-tcp'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-udp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv6-udp-post'},
        },
    ],
}

mac_ipv6_tcp_symmetric = {
    'sub_casename': 'mac_ipv6_tcp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-tcp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-tcp-pre'},
        },
    ],
    'test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_same': 'ipv6-tcp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-udp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-udp'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-tcp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv6-tcp-post'},
        },
    ],
}

mac_ipv6_sctp_symmetric = {
    'sub_casename': 'mac_ipv6_sctp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-sctp-pre'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_different': 'ipv6-sctp-pre'},
        },
    ],
    'test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-sctp'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'check_hash_same': 'ipv6-sctp'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'save_hash': 'ipv6-sctp-post'},
        },
        {
            'send_packet': 'Ether(src="00:11:22:33:44:55", dst="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different': 'ipv6-sctp-post'},
        },
    ],
}
# symmetric related data end

mac_l3_address_switched = {
    'sub_casename': 'mac_l3_address_switched',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end',
    'pre-test': [
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=22, dport=23)/("X" * 80)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X" * 80)',
            'action': 'check_hash_different',
        },
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=22, dport=23)/("X" * 80)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X" * 80)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)',
            'action': 'check_hash_different',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=22, dport=23)/("X" * 80)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X" * 80)',
            'action': 'check_hash_different',
        },
    ],
}

mac_global_simple_xor = [mac_l3_address_switched]

ipv6_32bit_prefix_l3_src_only = {
    'sub_casename': 'ipv6_32bit_prefix_l3_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre32 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'save_hash': 'ipv6-32bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe83:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-32bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:b6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-32bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-32bit'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_no_hash_or_different': 'ipv6-32bit'},
        },
    ],
}

ipv6_32bit_prefix_l3_dst_only = {
    'sub_casename': 'ipv6_32bit_prefix_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre32 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'save_hash': 'ipv6-32bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe83:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-32bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:b6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-32bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-32bit'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81::a6bf:1ff:fe1c:806", dst="fe82::a6bf:1ff:fe1c:806")/Raw("x"*64)',
            'action': {'check_no_hash_or_different': 'ipv6-32bit'},
        },
    ],
}

ipv6_32bit_prefix_l3_src_dst_only = {
    'sub_casename': 'ipv6_32bit_prefix_l3_src_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre32 l3-src-only l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'save_hash': 'ipv6-32bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe83:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-32bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe83:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-32bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:b6bf:1ff:fe1c::806", dst="fe82:1:b6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-32bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-32bit'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81::a6bf:1ff:fe1c:806", dst="fe82::a6bf:1ff:fe1c:806")/Raw("x"*64)',
            'action': {'check_no_hash_or_different': 'ipv6-32bit'},
        },
    ],
}

ipv6_32bit_prefix = [ipv6_32bit_prefix_l3_src_only, ipv6_32bit_prefix_l3_dst_only, ipv6_32bit_prefix_l3_src_dst_only]

ipv6_48bit_prefix_l3_src_only = {
    'sub_casename': 'ipv6_48bit_prefix_l3_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre48 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'save_hash': 'ipv6-48bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:b6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-48bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:2ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-48bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-48bit'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_no_hash_or_different': 'ipv6-48bit'},
        },
    ],
}

ipv6_48bit_prefix_l3_dst_only = {
    'sub_casename': 'ipv6_48bit_prefix_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre48 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'save_hash': 'ipv6-48bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe83:1:b6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-48bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:2ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-48bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-48bit'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_no_hash_or_different': 'ipv6-48bit'},
        },
    ],
}

ipv6_48bit_prefix_l3_src_dst_only = {
    'sub_casename': 'ipv6_48bit_prefix_l3_src_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre48 l3-src-only l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'save_hash': 'ipv6-48bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:b6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-48bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:b6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-48bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:2ff:fe1c::806", dst="fe82:1:a6bf:2ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-48bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-48bit'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81::a6bf:1ff:fe1c:806", dst="fe82::a6bf:1ff:fe1c:806")/Raw("x"*64)',
            'action': {'check_no_hash_or_different': 'ipv6-48bit'},
        },
    ],
}

ipv6_48bit_prefix = [ipv6_48bit_prefix_l3_src_only, ipv6_48bit_prefix_l3_dst_only, ipv6_48bit_prefix_l3_src_dst_only]

ipv6_64bit_prefix_l3_src_only = {
    'sub_casename': 'ipv6_64bit_prefix_l3_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre64 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'save_hash': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe83:1:a6bf:2ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:ee1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_no_hash_or_different': 'ipv6-64bit'},
        },
    ],
}

ipv6_64bit_prefix_l3_dst_only = {
    'sub_casename': 'ipv6_64bit_prefix_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre64 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'save_hash': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe83:1:a6bf:2ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:ee1c::806")/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_no_hash_or_different': 'ipv6-64bit'},
        },
    ],
}

ipv6_64bit_prefix_l3_src_dst_only = {
    'sub_casename': 'ipv6_64bit_prefix_l3_src_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-pre64 l3-src-only l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'save_hash': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:2ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:2ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_hash_different': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:ee1c::806", dst="fe82:1:a6bf:1ff:ee1c::806")/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/UDP(sport=1234, dport=5678)/Raw("x"*64)',
            'action': {'check_hash_same': 'ipv6-64bit'},
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="68:05:CA:BB:26:E0")/IPv6(src="fe81:1:a6bf:1ff:fe1c::806", dst="fe82:1:a6bf:1ff:fe1c::806")/Raw("x"*64)',
            'action': {'check_no_hash_or_different': 'ipv6-64bit'},
        },
    ],
}

ipv6_64bit_prefix = [ipv6_64bit_prefix_l3_src_only, ipv6_64bit_prefix_l3_dst_only, ipv6_64bit_prefix_l3_src_dst_only]

class AdvancedRSSTest(TestCase):

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
        self.package_version = self.launch_testpmd()
        self.symmetric = False
        self.rxq = 64
        self.rssprocess = RssProcessing(self, self.pmd_output, [self.tester_iface0, self.tester_iface1], self.rxq)
        self.logger.info('rssprocess.tester_ifaces: {}'.format(self.rssprocess.tester_ifaces))
        self.logger.info('rssprocess.test_case: {}'.format(self.rssprocess.test_case))

    def set_up(self):
        """
        Run before each test case.
        """
        if self.symmetric:
            self.pmd_output.execute_cmd("port config all rss all")
        self.pmd_output.execute_cmd("start")

    def launch_testpmd(self, symmetric=False, package='comms'):
        if symmetric:
            param = "--rxq=64 --txq=64"
        else:
            param = "--rxq=64 --txq=64 --disable-rss --rxd=384 --txd=384"
        out = self.pmd_output.start_testpmd(cores="1S/4C/1T", param=param,
                                            eal_param=f"-a {self.pci0}", socket=self.ports_socket)
        self.symmetric = symmetric
        if symmetric is True:
            '''
            symmetric may be False/True/2(any other not negative value)
            False: disable rss
            True: enable rss and execute port config all rss
            2: enable rss and do not execute port config all rss
            '''
            # Need config rss in setup
            self.pmd_output.execute_cmd("port config all rss all")
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        res = self.pmd_output.wait_link_status_up('all', timeout=15)
        self.verify(res is True, 'there have port link is down')

    def switch_testpmd(self, symmetric=True):
        if symmetric != self.symmetric:
            self.pmd_output.quit()
            self.launch_testpmd(symmetric=symmetric)
            self.pmd_output.execute_cmd("start")

    def test_mac_ipv4(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_1)
        self.pmd_output.execute_cmd("rx_vxlan_port add 4789 0")
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_2)

    def test_mac_ipv4_udp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_udp)

    def test_mac_ipv4_tcp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_tcp)

    def test_mac_ipv4_sctp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_sctp)

    def test_mac_ipv6(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6)

    def test_mac_ipv6_udp(self):
        self.switch_testpmd(symmetric=False)
        self.pmd_output.execute_cmd("rx_vxlan_port add 4789 0")
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_udp)

    def test_mac_ipv6_tcp(self):
        self.switch_testpmd(symmetric=False)
        self.pmd_output.execute_cmd("rx_vxlan_port add 4789 0")
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_tcp)

    def test_mac_ipv6_sctp(self):
        self.switch_testpmd(symmetric=False)
        self.pmd_output.execute_cmd("rx_vxlan_port add 4789 0")
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_sctp)

    def test_mac_ipv4_ipv4_chksum(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_ipv4_chksum)

    def test_mac_ipv4_udp_chksum(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_udp_chksum)

    def test_mac_ipv4_tcp_chksum(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_tcp_chksum)

    def test_mac_ipv4_sctp_chksum(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_sctp_chksum)

    def test_mac_ipv6_udp_l4_chksum(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_udp_l4_chksum)

    def test_mac_ipv6_tcp_l4_chksum(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_tcp_l4_chksum)

    def test_mac_ipv6_sctp_l4_chksum(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_sctp_l4_chksum)

    def test_symmetric_mac_ipv4(self):
        self.switch_testpmd(symmetric=2)
        self.pmd_output.execute_cmd("rx_vxlan_port add 4789 0")
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_symmetric)

    def test_symmetric_mac_ipv4_udp(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_udp_symmetric)

    def test_symmetric_mac_ipv4_tcp(self):
        self.switch_testpmd(symmetric=True)
        self.pmd_output.execute_cmd("rx_vxlan_port add 4789 0")
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_tcp_symmetric)

    def test_symmetric_mac_ipv4_sctp(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_sctp_symmetric)

    def test_symmetric_mac_ipv6(self):
        self.switch_testpmd(symmetric=2)
        self.pmd_output.execute_cmd("rx_vxlan_port add 4789 0")
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_symmetric)

    def test_symmetric_mac_ipv6_udp(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_udp_symmetric)

    def test_symmetric_mac_ipv6_tcp(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_tcp_symmetric)

    def test_symmetric_mac_ipv6_sctp(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv6_sctp_symmetric)

    def test_32bit_ipv6_prefix(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_32bit_prefix)

    def test_48bit_ipv6_prefix(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_48bit_prefix)

    def test_64bit_ipv6_prefix(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_64bit_prefix)

    def test_global_simple_xor(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_global_simple_xor)

    def test_negative_case(self):
        self.switch_testpmd(symmetric=False)
        rules = [
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l3-src-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l3-src-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv6 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types udp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 l3-src-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types eth end key_len 0 queues end / end',
        ]
        for i in rules:
            out = self.pmd_output.execute_cmd(i, timeout=1)
            self.verify('ice_flow_create(): Failed to create flow' in out, "rule %s create successfully" % i)

        rules_val = [
            'flow validate 0 ingress pattern eth / ipv4 / end actions rss types eth l3-src-only end key_len 0 queues end / end',
            'flow validate 0 ingress pattern eth / ipv4 / end actions rss types ipv4-udp end key_len 0 queues end / end',
            'flow validate 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
            'flow validate 0 ingress pattern eth / ipv4 / end actions rss types ipv6 end key_len 0 queues end / end',
            'flow validate 0 ingress pattern eth / ipv4 / udp / end actions rss types udp end key_len 0 queues end / end',
            'flow validate 0 ingress pattern eth / ipv6 / tcp / end actions rss types tcp end key_len 0 queues end / end',
            'flow validate 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 l3-src-only end key_len 0 queues end / end',
            'flow validate 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types eth end key_len 0 queues end / end',
        ]
        for i in rules_val:
            out = self.pmd_output.execute_cmd(i, timeout=1)
            self.verify('Invalid argument' in out, "rule %s validate successfully" % i)

        rules_chksum = [
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types l4-chksum end queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6-chksum  end queues end / end'
        ]
        for i in rules_chksum:
            out = self.pmd_output.execute_cmd(i)
            self.verify('Invalid argument' in out or 'Bad arguments' in out, "negative rules not support to create")

    def test_multirules(self):
        self.switch_testpmd(symmetric=True)
        #Subcase 1: two rules with same pattern but different hash input set, not hit default profile
        self.rssprocess.error_msgs = []
        self.logger.info('===================Test sub case: multirules subcase 1 ================')
        rule_id_0 = self.rssprocess.create_rule('flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end', check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_0)
        tests = [
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)',
                        'action': {'save_hash': 'ipv4-udp'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)',
                        'action': {'check_hash_different': 'ipv4-udp'},
                    },
                ]
        self.rssprocess.handle_tests(tests, 0)
        rule_id_1 = self.rssprocess.create_rule('flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end', check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_1)
        tests = [
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)',
                        'action': {'save_hash': 'ipv4-udp'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)',
                        'action': {'check_hash_same': 'ipv4-udp'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.7")/UDP(dport=45)/Raw("x"*480)',
                        'action': {'check_hash_different': 'ipv4-udp'},
                    },
                ]
        self.rssprocess.handle_tests(tests, 0)
        self.rssprocess.destroy_rule(port_id=0, rule_id=rule_id_1)
        self.rssprocess.check_rule(port_id=0)
        tests = [
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)',
                        'action': {'save_hash': 'ipv4-udp'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.9")/UDP(dport=45)/Raw("x"*480)',
                        'action': {'check_hash_different': 'ipv4-udp'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.9")/UDP(dport=45)/Raw("x"*480)',
                        'action': {'check_hash_different': 'ipv4-udp'},
                    },
                ]
        self.rssprocess.handle_tests(tests, 0)
        self.rssprocess.destroy_rule(port_id=0, rule_id=rule_id_0)
        self.rssprocess.handle_tests(tests, 0)

        # Subcase 2: two rules with same pattern but different hash input set, hit default profile
        self.logger.info('===================Test sub case: multirules subcase 2 ================')
        rule_id_0 = self.rssprocess.create_rule('flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end', check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_0)
        tests = [
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*480)',
                        'action': {'save_hash': 'ipv4-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/Raw("x"*480)',
                        'action': {'check_hash_different': 'ipv4-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8")/Raw("x"*480)',
                        'action': {'check_hash_same': 'ipv4-pay'},
                    },
                ]
        self.rssprocess.handle_tests(tests, 0)
        rule_id_1 = self.rssprocess.create_rule('flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end', check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_1)
        tests = [
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*480)',
                        'action': {'save_hash': 'ipv4-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/Raw("x"*480)',
                        'action': {'check_hash_same': 'ipv4-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.7")/Raw("x"*480)',
                        'action': {'check_hash_different': 'ipv4-pay'},
                    },
                ]
        self.rssprocess.handle_tests(tests, 0)
        self.rssprocess.destroy_rule(port_id=0, rule_id=rule_id_1)
        self.rssprocess.check_rule(port_id=0)
        self.rssprocess.destroy_rule(port_id=0, rule_id=rule_id_0)

        # Subcase 3: two rules, scope smaller created first, and the larger one created later
        self.logger.info('===================Test sub case: multirules subcase 3 ================')
        rule_id_0 = self.rssprocess.create_rule('flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end', check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_0)
        tests_3 = [
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)',
                        'action': {'save_hash': 'ipv4-udp-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25, dport=45)/Raw("x"*480)',
                        'action': {'check_hash_different': 'ipv4-udp-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.8")/UDP(sport=23, dport=44)/Raw("x"*480)',
                        'action': {'check_hash_same': 'ipv4-udp-pay'},
                    },
                ]
        self.rssprocess.handle_tests(tests_3, 0)
        rule_id_1 = self.rssprocess.create_rule('flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end', check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_1)
        tests = [
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)',
                        'action': {'save_hash': 'ipv4-udp-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)',
                        'action': {'check_hash_different': 'ipv4-udp-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8")/UDP(sport=25, dport=99)/Raw("x"*480)',
                        'action': {'check_hash_same': 'ipv4-udp-pay'},
                    },
                ]
        self.rssprocess.handle_tests(tests, 0)
        self.rssprocess.destroy_rule(port_id=0, rule_id=rule_id_1)
        self.rssprocess.destroy_rule(port_id=0, rule_id=rule_id_0)

        # Subcase 4: two rules, scope larger created first, and the smaller one created later
        self.logger.info('===================Test sub case: multirules subcase 4 ================')
        rule_id_0 = self.rssprocess.create_rule('flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end', check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_0)
        tests_4 = [
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)',
                        'action': {'save_hash': 'ipv4-udp-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)',
                        'action': {'check_hash_different': 'ipv4-udp-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8")/UDP(sport=25, dport=99)/Raw("x"*480)',
                        'action': {'check_hash_same': 'ipv4-udp-pay'},
                    },
                ]
        self.rssprocess.handle_tests(tests_4, 0)
        rule_id_1 = self.rssprocess.create_rule('flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end', check_stats=True)
        self.rssprocess.check_rule(port_id=0, rule_list=rule_id_1)
        tests = [
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)',
                        'action': {'save_hash': 'ipv4-udp-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25, dport=45)/Raw("x"*480)',
                        'action': {'check_hash_different': 'ipv4-udp-pay'},
                    },
                    {
                        'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.8")/UDP(sport=23, dport=44)/Raw("x"*480)',
                        'action': {'check_hash_same': 'ipv4-udp-pay'},
                    },
                ]
        self.rssprocess.handle_tests(tests, 0)
        self.rssprocess.destroy_rule(port_id=0, rule_id=rule_id_1)
        self.rssprocess.destroy_rule(port_id=0, rule_id=rule_id_0)
        self.verify(not self.rssprocess.error_msgs, 'some subcases failed')

    def test_checksum_for_different_payload_length(self):
        self.rssprocess.error_msgs = []
        self.pmd_output.quit()
        self.pmd_output.start_testpmd(cores="1S/4C/1T", param="--rxq={0} --txq={0}".format(self.rxq),
                                      eal_param=f"-a {self.pci0}", socket=self.ports_socket)
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("start")
        pkt_list = [
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/("X"*48)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/("X"*64)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/UDP()/("X"*48)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/UDP()/("X"*64)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/TCP()/("X"*48)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/TCP()/("X"*64)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/SCTP()/("X"*48)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP()/SCTP()/("X"*64)',
        ]
        rule_list = [
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp  end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp  end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp  end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l4-chksum  end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types l4-chksum  end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types l4-chksum  end queues end / end'
        ]
        test_temp = {
                'send_packet': '',
                'action': '',
            }
        pre_test = []
        for i in range(len(pkt_list)):
            if i == 0:
                tests = eval(str(test_temp).replace("'send_packet': ''", "'send_packet': '{}'".format(pkt_list[i]))
                             .replace("'action': ''", "'action': 'save_hash'"))
            else:
                tests = eval(str(test_temp).replace("'send_packet': ''", "'send_packet': '{}'".format(pkt_list[i]))
                             .replace("'action': ''", "'action': 'check_hash_same'"))
            pre_test.append(tests)
        self.rssprocess.handle_tests(pre_test)
        test_5_tuple = []
        rules = self.rssprocess.create_rule(rule_list[0:3])
        self.rssprocess.check_rule(rule_list=rules)
        for i in range(len(pkt_list)):
            if i % 2 == 0:
                tests = eval(str(test_temp).replace("'send_packet': ''", "'send_packet': '{}'".format(pkt_list[i]))
                             .replace("'action': ''", "'action': 'save_hash'"))
            else:
                tests = eval(str(test_temp).replace("'send_packet': ''", "'send_packet': '{}'".format(pkt_list[i]))
                             .replace("'action': ''", "'action': 'check_hash_same'"))
            test_5_tuple.append(tests)
        self.rssprocess.handle_tests(test_5_tuple)
        test_l4_chksum = []
        rules = self.rssprocess.create_rule(rule_list[3:])
        self.rssprocess.check_rule(rule_list=rules)
        for i in range(2, len(pkt_list)):
            if i % 2 == 0:
                tests = eval(str(test_temp).replace("'send_packet': ''", "'send_packet': '{}'".format(pkt_list[i]))
                             .replace("'action': ''", "'action': 'save_hash'"))
            else:
                tests = eval(str(test_temp).replace("'send_packet': ''", "'send_packet': '{}'".format(pkt_list[i]))
                             .replace("'action': ''", "'action': 'check_hash_different'"))
            test_l4_chksum.append(tests)
        self.rssprocess.handle_tests(test_l4_chksum)
        test_ipv4_chksum = []
        ipv4_chksum_rule = eval(str(rule_list).replace("l4-chksum", "ipv4-chksum"))
        rules = self.rssprocess.create_rule(ipv4_chksum_rule[3:] + ["flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-chksum  end queues end / end"])
        self.rssprocess.check_rule(rule_list=rules)
        for i in range(len(pkt_list)):
            if i % 2 == 0:
                tests = eval(str(test_temp).replace("'send_packet': ''", "'send_packet': '{}'".format(pkt_list[i]))
                             .replace("'action': ''", "'action': 'save_hash'"))
            else:
                tests = eval(str(test_temp).replace("'send_packet': ''", "'send_packet': '{}'".format(pkt_list[i]))
                             .replace("'action': ''", "'action': 'check_hash_different'"))
            test_ipv4_chksum.append(tests)
        self.rssprocess.handle_tests(test_ipv4_chksum)
        self.verify(not self.rssprocess.error_msgs, 'some subcases failed')

    def validate_packet_checksum(self, pkts, expect_pkts):
        expect_chksum = dict()
        checksum_pattern = re.compile("chksum.*=.*(0x[0-9a-z]+)")
        self.tester.send_expect("scapy", ">>> ")
        sniff_src = self.dut.get_mac_address(self.dut_ports[0])
        for pkt in expect_pkts:
            self.tester.send_expect("p = %s" % expect_pkts[pkt], ">>>")
            out = self.tester.send_expect("p.show2()", ">>>")
            chksums = checksum_pattern.findall(out)
            expect_chksum[pkt] = chksums
        self.logger.info(expect_chksum)
        self.tester.send_expect("exit()", "#")
        for pkt in pkts:
            inst = self.tester.tcpdump_sniff_packets(intf=self.tester_iface0, count=len(pkts), filters=[{'layer': 'ether', 'config': {'src': sniff_src}}])
            out = self.rssprocess.send_pkt_get_output(pkts=pkts[pkt])
            rece_pkt = self.tester.load_tcpdump_sniff_packets(inst)
            rece_chksum = rece_pkt[0].sprintf("%IP.chksum%;%TCP.chksum%;%UDP.chksum%;%SCTP.chksum%").split(";")
            self.logger.info(rece_chksum)
            test_chksum = []
            [test_chksum.append(i) for i in rece_chksum if i != '??']
            self.logger.info("expect_chksum:{} test_chksum:{}".format(expect_chksum[pkt], test_chksum))
            self.verify(expect_chksum[pkt] == test_chksum, 'tx checksum is incorrect')

    def test_flow_rule_not_impact_rx_tx_chksum(self):
        self.pmd_output.quit()
        self.pmd_output.start_testpmd(cores="1S/4C/1T", param="--rxq={0} --txq={0}".format(self.rxq),
                                      eal_param=f"-a {self.pci0}", socket=self.ports_socket)
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("port stop all")
        self.pmd_output.execute_cmd("set fwd csum")
        self.pmd_output.execute_cmd("csum set ip hw 0")
        self.pmd_output.execute_cmd("csum set udp hw 0")
        self.pmd_output.execute_cmd("csum set tcp hw 0")
        self.pmd_output.execute_cmd("csum set sctp hw 0")
        self.pmd_output.execute_cmd("port start all")
        self.pmd_output.execute_cmd("start")
        pkt_list = {
            'IP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1", chksum=0xfff3)/("X"*48)',
            'IP/TCP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/TCP(sport=22, chksum=0xfff3)/("X"*48)',
            'IP/UDP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/UDP(sport=22, chksum=0x1)/("X"*48)',
            'IP/SCTP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/SCTP(sport=22, chksum=0x0)/("X"*48)',
            'IPv6/TCP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/TCP(sport=22, chksum=0xe38)/("X"*48)',
            'IPv6/UDP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/UDP(sport=22, chksum=0xe38)/("X"*48)',
            'IPv6/SCTP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/SCTP(sport=22, chksum=0x0)/("X"*48)',
        }
        expect_pkt = {
            'IP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/("X"*48)',
            'IP/TCP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/TCP(sport=22)/("X"*48)',
            'IP/UDP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/UDP(sport=22)/("X"*48)',
            'IP/SCTP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/SCTP(sport=22)/("X"*48)',
            'IPv6/TCP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/TCP(sport=22)/("X"*48)',
            'IPv6/UDP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/UDP(sport=22)/("X"*48)',
            'IPv6/SCTP': 'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/SCTP(sport=22)/("X"*48)',
        }
        rule_list = [
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-chksum end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types l4-chksum end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l4-chksum end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types l4-chksum end queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types l4-chksum end queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types l4-chksum end queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types l4-chksum end queues end / end',
        ]
        self.validate_packet_checksum(pkt_list, expect_pkt)
        rss_test = {
            'sub_casename': 'rss_test',
            'port_id': 0,
            'rule': rule_list,
            'pre-test': [
                {
                    'send_packet': pkt_list['IP'],
                    'action': {'save_hash': 'IP'},
                },
                {
                    'send_packet': pkt_list['IP/TCP'],
                    'action': {'save_hash': 'IP/TCP'},
                },
                {
                    'send_packet': pkt_list['IP/UDP'],
                    'action': {'save_hash': 'IP/UDP'},
                },
                {
                    'send_packet': pkt_list['IP/SCTP'],
                    'action': {'save_hash': 'IP/SCTP'},
                },
                {
                    'send_packet': pkt_list['IPv6/TCP'],
                    'action': {'save_hash': 'IPv6/TCP'},
                },
                {
                    'send_packet': pkt_list['IPv6/UDP'],
                    'action': {'save_hash': 'IPv6/UDP'},
                },
                {
                    'send_packet': pkt_list['IPv6/SCTP'],
                    'action': {'save_hash': 'IPv6/SCTP'},
                },
            ],
            'test': [
                {
                    'send_packet': pkt_list['IP'],
                    'action': {'check_hash_different': 'IP'},
                },
                {
                    'send_packet': pkt_list['IP/TCP'],
                    'action': {'check_hash_different': 'IP/TCP'},
                },
                {
                    'send_packet': pkt_list['IP/UDP'],
                    'action': {'check_hash_different': 'IP/UDP'},
                },
                {
                    'send_packet': pkt_list['IP/SCTP'],
                    'action': {'check_hash_different': 'IP/SCTP'},
                },
                {
                    'send_packet': pkt_list['IPv6/TCP'],
                    'action': {'check_hash_different': 'IPv6/TCP'},
                },
                {
                    'send_packet': pkt_list['IPv6/UDP'],
                    'action': {'check_hash_different': 'IPv6/UDP'},
                },
                {
                    'send_packet': pkt_list['IPv6/SCTP'],
                    'action': {'check_hash_different': 'IPv6/SCTP'},
                },
            ],
        }
        self.rssprocess.handle_rss_distribute_cases(rss_test)
        self.validate_packet_checksum(pkt_list, expect_pkt)

    def test_combined_case_with_fdir_queue_group(self):
        fdirprocess = FdirProcessing(self, self.pmd_output, [self.tester_iface0, self.tester_iface1], self.rxq)
        hash_and_queue_list = []
        queue_group = re.compile("end actions rss queues (\d+)\s(\d+)")
        self.pmd_output.quit()
        self.pmd_output.start_testpmd(cores="1S/4C/1T", param="--rxq={0} --txq={0}".format(self.rxq),
                                      eal_param=f"-a {self.pci0}", socket=self.ports_socket)
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("start")
        pkt_list = [
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1", chksum=0xfff3)/("X"*48)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/TCP(sport=22, chksum=0xfff3)/("X"*48)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/UDP(sport=22, chksum=0x1)/("X"*48)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IP(src="192.168.0.1")/SCTP(sport=22, chksum=0x1)/("X"*48)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/TCP(sport=22, chksum=0xe38)/("X"*48)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6()/UDP(sport=22, chksum=0xe38)/("X"*48)',
            'Ether(dst="00:11:22:33:44:55", src="52:00:00:00:00:00")/IPv6(src="ABAB:910A:2222:5498:8475:1111:3900:1010")/SCTP(sport=22, chksum=0xf)/("X"*48)',
        ]
        rss_rule_list = [
            'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-chksum  end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types l4-chksum  end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l4-chksum  end queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types l4-chksum  end queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types l4-chksum  end queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types l4-chksum  end queues end / end',
            'flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types l4-chksum  end queues end / end',
        ]
        fdir_rule_list = [
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / tcp / end actions rss queues 4 5 end / mark / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / udp / end actions rss queues 6 7 end / mark / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / sctp / end actions rss queues 8 9 end / mark / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 / tcp / end actions rss queues 10 11 end / mark / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 / udp / end actions rss queues 12 13 end / mark / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 / sctp / end actions rss queues 14 15 end / mark / end',
        ]
        fdirprocess.create_rule(fdir_rule_list)
        fdir_rule_list.insert(0, "")
        for i in range(len(pkt_list)):
            out = fdirprocess.send_pkt_get_output(pkt_list[i])
            hash_and_queue_tuple = self.rssprocess.get_hash_and_queues(out)
            if i == 0:
                check_mark(out, pkt_num=1, check_param={"port_id": 0, "rss": True})
            else:
                queue_list = list(map(int, queue_group.search(fdir_rule_list[i]).groups()))
                check_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": queue_list, "mark_id": 0})
            hash_and_queue_list.append(hash_and_queue_tuple)
        self.rssprocess.create_rule(rss_rule_list)
        for i in range(len(pkt_list)):
            out = fdirprocess.send_pkt_get_output(pkt_list[i])
            hashes, queues = self.rssprocess.get_hash_and_queues(out)
            if i == 0:
                check_mark(out, pkt_num=1, check_param={"port_id": 0, "rss": True})
                hashes_0 = hashes
            else:
                queue_list = list(map(int, queue_group.search(fdir_rule_list[i]).groups()))
                check_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": queue_list, "mark_id": 0})
            self.logger.info("pre_hash: {}    test_hash: {}".format(hash_and_queue_list[i][0], hashes))
            self.verify(hash_and_queue_list[i][0] != hashes, "expect hash values changed")
        self.rssprocess.create_rule("flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / end actions rss queues 0 1 2 3 end / end")
        out = fdirprocess.send_pkt_get_output(pkt_list[0])
        hashes, queues = self.rssprocess.get_hash_and_queues(out)
        check_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": [1, 2, 3, 4]})
        self.logger.info("test_hash: {}       post_hash: {}".format(hashes_0, hashes))
        self.verify(hashes == hashes_0, "expect hash values not changed")

    def tear_down(self):
        # destroy all flow rule on port 0
        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")

    def tear_down_all(self):
        self.dut.kill_all()
