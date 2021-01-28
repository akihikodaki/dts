# BSD LICENSE
#
# Copyright(c)2020 Intel Corporation. All rights reserved.
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
import random
import string
from test_case import TestCase
from pmd_output import PmdOutput
from packet import Packet
from rte_flow_common import RssProcessing
from config import UserConf

mac_ipv4_pfcp_session_packets = {
    'match': [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=2)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:54")/IP(src="192.168.0.25",dst="192.168.0.23")/UDP(sport=23,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)'],
    'mismatch': [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=25)/Raw("x"*80)']
}

mac_ipv4_pfcp_session = {
    'sub_casename': 'mac_ipv4_pfcp_session',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_pfcp_session_packets['match'][0],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_pfcp_session_packets['match'][1],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_pfcp_session_packets['match'][2],
            'action': 'check_hash_same',
        },
        {
            'send_packet': [i for i in mac_ipv4_pfcp_session_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_ipv4_pfcp_session_packets['match']],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_pfcp_session_packets = {
    'match': [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=2)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:53")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)'],
    'mismatch': [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(S=1, seid=1)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=25)/Raw("x"*80)']
}

mac_ipv6_pfcp_session = {
    'sub_casename': 'mac_ipv6_pfcp_session',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_pfcp_session_packets['match'][0],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv6_pfcp_session_packets['match'][1],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv6_pfcp_session_packets['match'][2],
            'action': 'check_hash_same',
        },
        {
            'send_packet': [i for i in mac_ipv6_pfcp_session_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_ipv6_pfcp_session_packets['match']],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_l2tpv3_packets = {
    'match': [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5", proto=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.4", proto=115)/L2TP(b\'\\x00\\x00\\x00\\x12\')/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:53")/IP(src="192.168.0.5",dst="192.168.0.7", proto=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)'
    ],
    'mismatch': [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=25)/Raw("x"*80)'
    ]
}

mac_ipv4_l2tpv3 = {
    'sub_casename': 'mac_ipv4_l2tpv3',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_l2tpv3_packets['match'][0],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_l2tpv3_packets['match'][1],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_l2tpv3_packets['match'][2],
            'action': 'check_hash_same',
        },
        {
            'send_packet': [i for i in mac_ipv4_l2tpv3_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_ipv4_l2tpv3_packets['match']],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_l2tpv3_packets = {
    'match': [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP(b\'\\x00\\x00\\x00\\x12\')/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:53")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)'
    ],
    'mismatch': [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5", proto=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=25)/Raw("x"*80)'
    ]
}

mac_ipv6_l2tpv3 = {
    'sub_casename': 'mac_ipv6_l2tpv3',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_l2tpv3_packets['match'][0],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv6_l2tpv3_packets['match'][1],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv6_l2tpv3_packets['match'][2],
            'action': 'check_hash_same',
        },
        {
            'send_packet': [i for i in mac_ipv6_l2tpv3_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_ipv6_l2tpv3_packets['match']],
            'action': 'check_no_hash',
        }
    ]
}

mac_ipv4_esp_packets = {
    'match': [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=11)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=12)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:53")/IP(src="192.168.0.4",dst="192.168.0.7",proto=50)/ESP(spi=11)/Raw("x"*480)'],
    'mismatch': [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5", proto=115)/L2TP(b\'\\x00\\x00\\x00\\x11\')/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=12)/Raw("x"*480)'
    ]
}

mac_ipv4_esp = {
    'sub_casename': 'mac_ipv4_esp',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_esp_packets['match'][0],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_esp_packets['match'][1],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_esp_packets['match'][2],
            'action': 'check_hash_same',
        },
        {
            'send_packet': [
                i for i in mac_ipv4_esp_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                i for i in mac_ipv4_esp_packets['match']],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv4_udp_esp_packets = {
    'match': [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=12)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:53")/IP(src="192.168.0.4",dst="192.168.0.7")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)'],
    'mismatch': [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=11)/Raw("x"*480)']
}

mac_ipv4_udp_esp = {
    'sub_casename': 'mac_ipv4_udp_esp',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / esp / end actions rss types esp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_udp_esp_packets['match'][0],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_udp_esp_packets['match'][1],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_udp_esp_packets['match'][2],
            'action': 'check_hash_same',
        },
        {
            'send_packet': [i for i in mac_ipv4_udp_esp_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [
                i for i in mac_ipv4_esp_packets['match']],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_esp_packets = {
    'match': [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=11)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=12)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:53")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=50)/ESP(spi=11)/Raw("x"*480)'],
    'mismatch': [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=11)/Raw("x"*480)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)']
}

mac_ipv6_esp = {
    'sub_casename': 'mac_ipv6_esp',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / esp / end actions rss types esp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_esp_packets['match'][0],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv6_esp_packets['match'][1],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv6_esp_packets['match'][2],
            'action': 'check_hash_same',
        },
        {
            'send_packet': [i for i in mac_ipv6_esp_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_ipv6_esp_packets['match']],
            'action': 'check_no_hash',
        },
    ],
}

mac_ipv6_udp_esp_packets = {
    'match': [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=12)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:53")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)'],
    'mismatch': [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=11)/Raw("x"*480)']
}

mac_ipv6_udp_esp = {
    'sub_casename': 'mac_ipv6_udp_esp',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / udp / esp / end actions rss types esp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_udp_esp_packets['match'][0],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv6_udp_esp_packets['match'][1],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv6_udp_esp_packets['match'][2],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv6_udp_esp_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_ipv6_udp_esp_packets['match'],
            'action': 'check_no_hash',
        },
    ],

}

mac_ipv4_ah_packets = {
    'match': ['Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=11)/Raw("x"*480)',
              'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=12)/Raw("x"*480)',
              'Ether(dst="00:11:22:33:44:53")/IP(src="192.168.0.4",dst="192.168.0.8",proto=51)/AH(spi=11)/Raw("x"*480)'],
    'mismatch': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=11)/Raw("x"*480)']
}

mac_ipv4_ah = {
    'sub_casename': 'mac_ipv4_ah',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / ah / end actions rss types ah end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_ah_packets['match'][0],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_ah_packets['match'][1],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_ah_packets['match'][2],
            'action': 'check_hash_same',
        },
        {
            'send_packet': [i for i in mac_ipv4_ah_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_ipv4_ah_packets['match']],
            'action': 'check_no_hash',
        },
    ],

}

mac_ipv6_ah_packets = {
    'match': [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=11)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=12)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:53")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=51)/AH(spi=11)/Raw("x"*480)'],
    'mismatch': [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=11)/Raw("x"*480)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)']
}

mac_ipv6_ah = {
    'sub_casename': 'mac_ipv6_ah',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv6 / ah / end actions rss types ah end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv6_ah_packets['match'][0],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv6_ah_packets['match'][1],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv6_ah_packets['match'][2],
            'action': 'check_hash_same',
        },
        {
            'send_packet': [i for i in mac_ipv6_ah_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_ipv6_ah_packets['match']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_pay_packets = {
    'mismatch': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)']
}

mac_pppoe_pay_l2_src_only_packets = {
    'mac_pppoe_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/Raw("x"*80)'
    ],
    'mac_pppoe_lcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=7)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)'
    ],
    'mac_pppoe_ipcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=7)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'
    ],
}

mac_pppoe_pay_l2_src_only = {
    'sub_casename': 'mac_pppoe_pay_l2_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_pay_l2_src_only_packets['mac_pppoe_pay'][0],
            'action': {'save_hash': 'mac_pppoe_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_packets['mac_pppoe_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_packets['mac_pppoe_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_packets['mac_pppoe_lcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_packets['mac_pppoe_lcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_packets['mac_pppoe_lcp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_packets['mac_pppoe_ipcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_packets['mac_pppoe_ipcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_packets['mac_pppoe_ipcp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [mac_pppoe_pay_l2_src_only_packets[key][i] for i in range(0, 3) for key in
                            ['mac_pppoe_pay', 'mac_pppoe_lcp_pay', 'mac_pppoe_ipcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_pay_l2_dst_only_packets = {
    'mac_pppoe_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/Raw("x"*80)']

}

mac_pppoe_pay_l2_dst_only = {
    'sub_casename': 'mac_pppoe_pay_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_pay_l2_dst_only_packets['mac_pppoe_pay'][0],
            'action': {'save_hash': 'mac_pppoe_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_dst_only_packets['mac_pppoe_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_dst_only_packets['mac_pppoe_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_pay_l2_dst_only_packets['mac_pppoe_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_pay_l2_src_only_l2_dst_only_packets = {
    'mac_pppoe_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/Raw("x"*80)'
    ]

}

mac_pppoe_pay_l2_src_only_l2_dst_only = {
    'sub_casename': 'mac_pppoe_pay_l2_src_only_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_pay'][0],
            'action': {'save_hash': 'mac_pppoe_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_pay_session_id_packets = {
    'mac_pppoe_lcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
    ],
    'mac_pppoe_ipcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'
    ]

}

mac_pppoe_pay_session_id = {
    'sub_casename': 'mac_pppoe_pay_session_id',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_pay_session_id_packets['mac_pppoe_lcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_session_id_packets['mac_pppoe_lcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_session_id_packets['mac_pppoe_lcp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_session_id_packets['mac_pppoe_ipcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_session_id_packets['mac_pppoe_ipcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_session_id_packets['mac_pppoe_ipcp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [mac_pppoe_pay_session_id_packets[key][i] for i in range(0, 3) for key in
                            ['mac_pppoe_lcp_pay', 'mac_pppoe_ipcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_pay_l2_src_only_session_id_packets = {
    'mac_pppoe_lcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)'
    ],
    'mac_pppoe_ipcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'
    ]

}

mac_pppoe_pay_l2_src_only_session_id = {
    'sub_casename': 'mac_pppoe_pay_l2_src_only_session_id',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / end actions rss types eth l2-src-only pppoe end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_pay_l2_src_only_session_id_packets['mac_pppoe_lcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_session_id_packets['mac_pppoe_lcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_session_id_packets['mac_pppoe_lcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_session_id_packets['mac_pppoe_lcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_session_id_packets['mac_pppoe_lcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_lcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_session_id_packets['mac_pppoe_ipcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_session_id_packets['mac_pppoe_ipcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_session_id_packets['mac_pppoe_ipcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_session_id_packets['mac_pppoe_ipcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipcp_pay'},
        },
        {
            'send_packet': mac_pppoe_pay_l2_src_only_session_id_packets['mac_pppoe_ipcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipcp_pay'},
        },

        {
            'send_packet': mac_pppoe_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [mac_pppoe_pay_l2_src_only_session_id_packets[key][i] for i in range(0, 4) for key in
                            ['mac_pppoe_lcp_pay', 'mac_pppoe_ipcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}


mac_pppoe_ipv4_pay_packets = {
    'mismatch': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=5)/Raw("x"*80)']
}

mac_pppoe_ipv4_pay = [
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=4)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/Raw("x"*80)'
]

mac_pppoe_ipv4_frag = [
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=4)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5", frag=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5", frag=3)/Raw("x"*80)'
]

mac_pppoe_ipv4_pay_src_test = [
    {
        'send_packet': mac_pppoe_ipv4_pay[0],
        'action': {'save_hash': 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_pay[1],
        'action': {'check_hash_different': 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_pay[2],
        'action': {'check_hash_same', 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[0],
        'action': {'save_hash': 'mac_pppoe_ipv4_frag'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[1],
        'action': {'check_hash_different': 'mac_pppoe_ipv4_frag'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[2],
        'action': {'check_hash_same', 'mac_pppoe_ipv4_frag'},
    },

    {
        'send_packet': [i for i in mac_pppoe_ipv4_pay_packets['mismatch']],
        'action': 'check_no_hash',
    },
]

mac_pppoe_ipv4_pay_dst_test = [
    {
        'send_packet': mac_pppoe_ipv4_pay[0],
        'action': {'save_hash': 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_pay[2],
        'action': {'check_hash_different': 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_pay[1],
        'action': {'check_hash_same', 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[0],
        'action': {'save_hash': 'mac_pppoe_ipv4_frag'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[2],
        'action': {'check_hash_different': 'mac_pppoe_ipv4_frag'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[1],
        'action': {'check_hash_same', 'mac_pppoe_ipv4_frag'},
    },

    {
        'send_packet': [i for i in mac_pppoe_ipv4_pay_packets['mismatch']],
        'action': 'check_no_hash',
    },
]

mac_pppoe_ipv4_pay_src_dst_test = [
    {
        'send_packet': mac_pppoe_ipv4_pay[0],
        'action': {'save_hash': 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_pay[1],
        'action': {'check_hash_different': 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_pay[2],
        'action': {'check_hash_different': 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_pay[3],
        'action': {'check_hash_different': 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_pay[-1],
        'action': {'check_hash_same', 'mac_pppoe_ipv4_pay'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[0],
        'action': {'save_hash': 'mac_pppoe_ipv4_frag'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[1],
        'action': {'check_hash_different': 'mac_pppoe_ipv4_frag'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[2],
        'action': {'check_hash_different': 'mac_pppoe_ipv4_frag'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[3],
        'action': {'check_hash_different': 'mac_pppoe_ipv4_frag'},
    },
    {
        'send_packet': mac_pppoe_ipv4_frag[-1],
        'action': {'check_hash_same', 'mac_pppoe_ipv4_frag'},
    },

    {
        'send_packet': [i for i in mac_pppoe_ipv4_pay_packets['mismatch']],
        'action': 'check_no_hash',
    },
]

mac_pppoe_ipv4_pay_post_test = [
                                   {
                                       'send_packet': [item for item in mac_pppoe_ipv4_pay + mac_pppoe_ipv4_frag],
                                       'action': 'check_no_hash',
                                   },
                               ],

mac_pppoe_ipv4_pay_l2_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_pay_l2_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': mac_pppoe_ipv4_pay_src_test,
    'post-test': mac_pppoe_ipv4_pay_post_test
}

mac_pppoe_ipv4_pay_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_pay_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': mac_pppoe_ipv4_pay_dst_test,
    'post-test': mac_pppoe_ipv4_pay_post_test
}

mac_pppoe_ipv4_pay_l2_src_only_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_pay_l2_src_only_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types eth end key_len 0 queues end / end',
    'test': mac_pppoe_ipv4_pay_src_dst_test,
    'post-test': mac_pppoe_ipv4_pay_post_test
}


mac_pppoe_ipv4_pay_l3_src_only_packets = {
    'mac_pppoe_ipv4_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:54", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/Raw("x"*80)',
    ],
    'mac_pppoe_ipv4_frag': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2", frag=5)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:54", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7", frag=3)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_pay_l3_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_pay_l2_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_packets['mac_pppoe_ipv4_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_packets['mac_pppoe_ipv4_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_packets['mac_pppoe_ipv4_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_packets['mac_pppoe_ipv4_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_packets['mac_pppoe_ipv4_frag'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_packets['mac_pppoe_ipv4_frag'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_frag'},
        },

        {
            'send_packet': mac_pppoe_ipv4_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_packets['mac_pppoe_ipv4_pay'] +
                           mac_pppoe_ipv4_pay_l3_src_only_packets['mac_pppoe_ipv4_frag'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_pay_l3_dst_only_packets = {
    'mac_pppoe_ipv4_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.3")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.7", dst="192.168.1.2")/Raw("x"*80)',
    ],
    'mac_pppoe_ipv4_frag': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.3", frag=5)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.7", dst="192.168.1.2", frag=3)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_pay_l3_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_pay_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_dst_only_packets['mac_pppoe_ipv4_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_dst_only_packets['mac_pppoe_ipv4_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_dst_only_packets['mac_pppoe_ipv4_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_dst_only_packets['mac_pppoe_ipv4_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_dst_only_packets['mac_pppoe_ipv4_frag'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_dst_only_packets['mac_pppoe_ipv4_frag'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_frag'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv4_pay_l3_dst_only_packets['mac_pppoe_ipv4_pay'] +
                            mac_pppoe_ipv4_pay_l3_dst_only_packets['mac_pppoe_ipv4_frag']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets = {
    'mac_pppoe_ipv4_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.7")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'
    ],
    'mac_pppoe_ipv4_frag': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2", frag=5)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7", frag=5)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.7", frag=5)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2", frag=3)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_frag'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_frag'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_frag'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_frag'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_frag'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv4_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_pay'] +
                            mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv4_frag']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_packets = {
    'mismatch': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:'
        '910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=25,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l2_src_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/UDP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l2_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l2_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_src_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_src_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_src_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_src_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_l2_dst_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/UDP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_dst_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_dst_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_dst_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },

        {
            'send_packet': mac_pppoe_ipv4_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_dst_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],

}

mac_pppoe_ipv4_udp_pay_l2_src_only_l2_dst_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/UDP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l2_src_only_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l2_src_only_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],

}

mac_pppoe_ipv4_udp_pay_l3_src_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l3_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l3_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },

        {
            'send_packet': mac_pppoe_ipv4_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_l3_dst_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l3_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_l4_src_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=9,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.7")/UDP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },

        {
            'send_packet': mac_pppoe_ipv4_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_l4_dst_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.7")/UDP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },

        {
            'send_packet': mac_pppoe_ipv4_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_l3_src_only_l4_src_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.9")/UDP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l3_src_only_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l3_src_only_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_l3_src_only_l4_dst_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l3_src_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l3_src_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv4_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_src_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv4_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_dst_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)'

    ]
}

mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv4_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets = {
    'mac_pppoe_ipv4_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.7")/UDP(sport=19,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                'mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv4_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv4_udp_pay'][4],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv4_udp_pay'][5],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                'mac_pppoe_ipv4_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv4_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                'mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_ipv4_packets = {
    'mac_pppoe_ipv4_udp_pay':[
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=99)/Raw("x"*80)',
         ]
}

mac_pppoe_ipv4_udp_pay_ipv4 = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_ipv4',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_ipv4_packets[
                'mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_ipv4_packets[
                'mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_ipv4_packets[
                'mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_ipv4_packets[
                'mac_pppoe_ipv4_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_ipv4_packets[
                'mac_pppoe_ipv4_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv4_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_ipv4_packets[
                'mac_pppoe_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_packets = {
    'mismatch': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/'
        'IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=25,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l2_src_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/TCP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l2_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l2_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_src_only_packets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_src_only_packets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_src_only_packets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_l2_src_only_packets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l2_dst_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/TCP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_l2_dst_only_packets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l2_src_only_l2_dst_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/TCP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l2_src_only_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l2_src_only_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv4_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l3_src_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l3_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l3_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_packets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_packets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_packets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_l3_src_only_packets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l3_dst_only_pakets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l3_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_pakets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_pakets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_pakets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_l3_dst_only_pakets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l4_src_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.7")/TCP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l4_dst_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.7")/TCP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_src_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.9")/TCP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_dst_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_src_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=9,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=9,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_dst_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=90)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=25,dport=90)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.5")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/TCP(sport=19,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)'

    ]
}

mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                'mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv4_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv4_tcp_pay'][4],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv4_tcp_pay'][5],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                'mac_pppoe_ipv4_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv4_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                                'mac_pppoe_ipv4_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_ipv4_packets = {
    'mac_pppoe_ipv4_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=19,dport=99)/Raw("x"*80)',
    ]
}

mac_pppoe_ipv4_tcp_pay_ipv4 = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_ipv4',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_ipv4_packets[
                'mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_ipv4_packets[
                'mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_ipv4_packets[
                'mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_ipv4_packets[
                'mac_pppoe_ipv4_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_ipv4_packets[
                'mac_pppoe_ipv4_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv4_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_ipv4_packets['mac_pppoe_ipv4_tcp_pay'],
            'action': 'check_no_hash',
        },
    ],
}
mac_pppoe_ipv6_pay_packets = {
    'mismatch': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_pay_l2_src_only_packets = {
    'mac_pppoe_ipv6_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)'
    ],
    'mac_pppoe_ipv6_frag': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/Raw("x"*80)',
    ]
}

mac_pppoe_ipv6_pay_l2_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_pay_l2_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_packets['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_packets['mac_pppoe_ipv6_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_packets['mac_pppoe_ipv6_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_packets['mac_pppoe_ipv6_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_packets['mac_pppoe_ipv6_frag'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_packets['mac_pppoe_ipv6_frag'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_frag'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_l2_src_only_packets['mac_pppoe_ipv6_frag']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_pay_l2_dst_only_packets = {
    'mac_pppoe_ipv6_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)'
    ],
    'mac_pppoe_ipv6_frag': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/Raw("x"*80)'
    ]

}

mac_pppoe_ipv6_pay_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_pay_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_dst_only_packets['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_dst_only_packets['mac_pppoe_ipv6_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_dst_only_packets['mac_pppoe_ipv6_pay'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_dst_only_packets['mac_pppoe_ipv6_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_dst_only_packets['mac_pppoe_ipv6_frag'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_dst_only_packets['mac_pppoe_ipv6_frag'][2],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_frag'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_l2_dst_only_packets['mac_pppoe_ipv6_frag']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets = {
    'mac_pppoe_ipv6_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)'
    ],
    'mac_pppoe_ipv6_frag': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/Raw("x"*80)'

    ]
}

mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_frag'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_frag'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_frag'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_frag'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_frag'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_frag']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_pay_l3_src_only_packets = {
    'mac_pppoe_ipv6_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:54", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)',
    ],
    'mac_pppoe_ipv6_frag': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:54", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/Raw("x"*80)',

    ]
}

mac_pppoe_ipv6_pay_l3_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_pay_l3_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_packets['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_packets['mac_pppoe_ipv6_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_packets['mac_pppoe_ipv6_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_packets['mac_pppoe_ipv6_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_packets['mac_pppoe_ipv6_frag'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_packets['mac_pppoe_ipv6_frag'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_frag'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_l3_src_only_packets['mac_pppoe_ipv6_frag']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_pay_l3_dst_only_packets = {
    'mac_pppoe_ipv6_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'
    ],
    'mac_pppoe_ipv6_frag': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)'

    ]
}

mac_pppoe_ipv6_pay_l3_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_pay_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_dst_only_packets['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_dst_only_packets['mac_pppoe_ipv6_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_dst_only_packets['mac_pppoe_ipv6_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_dst_only_packets['mac_pppoe_ipv6_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_dst_only_packets['mac_pppoe_ipv6_frag'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_dst_only_packets['mac_pppoe_ipv6_frag'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_frag'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_l3_dst_only_packets['mac_pppoe_ipv6_frag']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets = {
    'mac_pppoe_ipv6_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'
    ],
    'mac_pppoe_ipv6_frag': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)'

    ]
}

mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_frag'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_frag'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_frag'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_frag'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_frag'},
        },

        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only_packets['mac_pppoe_ipv6_frag']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_packets = {
    'mismatch': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l2_src_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l2_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l2_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_src_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_src_only_packets['mac_pppoe_ipv6_udp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_src_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_l2_src_only_packets['mac_pppoe_ipv6_udp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l2_dst_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_dst_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_dst_only_packets['mac_pppoe_ipv6_udp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_dst_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_l2_dst_only_packets['mac_pppoe_ipv6_udp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l2_src_only_l2_dst_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l2_src_only_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l2_src_only_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_udp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_udp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l3_src_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l3_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l3_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_packets['mac_pppoe_ipv6_udp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_udp_pay_l3_src_only_packets['mac_pppoe_ipv6_udp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l3_dst_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=99)/Raw("x"*80)'

    ]
}

mac_pppoe_ipv6_udp_pay_l3_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_packets['mac_pppoe_ipv6_udp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_udp_pay_l3_dst_only_packets['mac_pppoe_ipv6_udp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l4_src_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_udp_pay_l4_src_only_packets['mac_pppoe_ipv6_udp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l4_dst_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_udp_pay_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l3_src_only_l4_src_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l3_src_only_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l3_src_only_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_udp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l3_src_only_l4_dst_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l3_src_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l3_src_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_udp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_src_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_dst_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=19,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                'mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv6_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv6_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv6_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv6_udp_pay'][4],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                'mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_udp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                                'mac_pppoe_ipv6_udp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_udp_pay_ipv6_packets = {
    'mac_pppoe_ipv6_udp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1538", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=99)/Raw("x"*80)',
    ]
}

mac_pppoe_ipv6_udp_pay_ipv6 = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_ipv6',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_ipv6_packets[
                'mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_ipv6_packets[
                'mac_pppoe_ipv6_udp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_ipv6_packets[
                'mac_pppoe_ipv6_udp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_ipv6_packets[
                'mac_pppoe_ipv6_udp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_ipv6_packets[
                'mac_pppoe_ipv6_udp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_udp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet':mac_pppoe_ipv6_udp_pay_ipv6_packets['mac_pppoe_ipv6_udp_pay'],
            'action': 'check_no_hash',
        },
    ],

}

mac_pppoe_ipv6_tcp_pay_packets = {
    'mismatch': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l2_src_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l2_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l2_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_src_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_src_only_packets['mac_pppoe_ipv6_tcp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_src_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l2_src_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],

}

mac_pppoe_ipv6_tcp_pay_l2_dst_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x"*80)',
    ]
}

mac_pppoe_ipv6_tcp_pay_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l2_dst_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay_l2_src_only_l2_dst_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l2_src_only_l2_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l2_src_only_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types eth end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l2_src_only_l2_dst_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay_l3_src_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l3_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l3_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_packets['mac_pppoe_ipv6_tcp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l3_src_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay_l3_dst_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l3_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l3_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l3_dst_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay_l4_src_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay_l4_dst_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][1:-1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_src_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_dst_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],

}

mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_src_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_src_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_src_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_dst_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_dst_only_packets['mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=19,dport=99)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)'
    ]
}

mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                'mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv6_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv6_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv6_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv6_tcp_pay'][4],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                               'mac_pppoe_ipv6_tcp_pay'][5],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                'mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': [i for i in mac_pppoe_ipv6_tcp_pay_packets['mismatch']],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only_packets[
                                'mac_pppoe_ipv6_tcp_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay_ipv6_packets = {
    'mac_pppoe_ipv6_tcp_pay': [
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1538", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/TCP(sport=25,dport=23)/Raw("x"*80)',
        'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=99)/Raw("x"*80)',
    ]
}

mac_pppoe_ipv6_tcp_pay_ipv6 = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_ipv6',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_ipv6_packets['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_ipv6_packets['mac_pppoe_ipv6_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_ipv6_packets['mac_pppoe_ipv6_tcp_pay'][2],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_ipv6_packets['mac_pppoe_ipv6_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_ipv6_packets['mac_pppoe_ipv6_tcp_pay'][-1],
            'action': {'check_hash_same', 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_ipv6_packets['mac_pppoe_ipv6_tcp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv6_tcp_pay = [
    mac_pppoe_ipv6_tcp_pay_l2_src_only,
    mac_pppoe_ipv6_tcp_pay_l2_dst_only,
    mac_pppoe_ipv6_tcp_pay_l2_src_only_l2_dst_only,
    mac_pppoe_ipv6_tcp_pay_l3_src_only,
    mac_pppoe_ipv6_tcp_pay_l3_dst_only,
    mac_pppoe_ipv6_tcp_pay_l4_src_only,
    mac_pppoe_ipv6_tcp_pay_l4_dst_only,
    mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_src_only,
    mac_pppoe_ipv6_tcp_pay_l3_src_only_l4_dst_only,
    mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_src_only,
    mac_pppoe_ipv6_tcp_pay_l3_dst_only_l4_dst_only,
    mac_pppoe_ipv6_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only,
    mac_pppoe_ipv6_tcp_pay_ipv6
]

mac_pppoe_ipv6_udp_pay = [
    mac_pppoe_ipv6_udp_pay_l2_src_only,
    mac_pppoe_ipv6_udp_pay_l2_dst_only,
    mac_pppoe_ipv6_udp_pay_l2_src_only_l2_dst_only,
    mac_pppoe_ipv6_udp_pay_l3_src_only,
    mac_pppoe_ipv6_udp_pay_l3_dst_only,
    mac_pppoe_ipv6_udp_pay_l4_src_only,
    mac_pppoe_ipv6_udp_pay_l4_dst_only,
    mac_pppoe_ipv6_udp_pay_l3_src_only_l4_src_only,
    mac_pppoe_ipv6_udp_pay_l3_src_only_l4_dst_only,
    mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_src_only,
    mac_pppoe_ipv6_udp_pay_l3_dst_only_l4_dst_only,
    mac_pppoe_ipv6_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only,
    mac_pppoe_ipv6_udp_pay_ipv6

]

mac_pppoe_ipv6_pay = [
    mac_pppoe_ipv6_pay_l2_src_only,
    mac_pppoe_ipv6_pay_l2_dst_only,
    mac_pppoe_ipv6_pay_l2_src_only_l2_dst_only,
    mac_pppoe_ipv6_pay_l3_src_only,
    mac_pppoe_ipv6_pay_l3_dst_only,
    mac_pppoe_ipv6_pay_l3_src_only_l3_dst_only
]

mac_pppoe_ipv4_tcp_pay = [
    mac_pppoe_ipv4_tcp_pay_l2_src_only,
    mac_pppoe_ipv4_tcp_pay_l2_dst_only,
    mac_pppoe_ipv4_tcp_pay_l2_src_only_l2_dst_only,
    mac_pppoe_ipv4_tcp_pay_l3_src_only,
    mac_pppoe_ipv4_tcp_pay_l3_dst_only,
    mac_pppoe_ipv4_tcp_pay_l4_src_only,
    mac_pppoe_ipv4_tcp_pay_l4_dst_only,
    mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_src_only,
    mac_pppoe_ipv4_tcp_pay_l3_src_only_l4_dst_only,
    mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_src_only,
    mac_pppoe_ipv4_tcp_pay_l3_dst_only_l4_dst_only,
    mac_pppoe_ipv4_tcp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only,
    mac_pppoe_ipv4_tcp_pay_ipv4
]

mac_pppoe_ipv4_udp_pay = [
    mac_pppoe_ipv4_udp_pay_l2_src_only,
    mac_pppoe_ipv4_udp_pay_l2_dst_only,
    mac_pppoe_ipv4_udp_pay_l2_src_only_l2_dst_only,
    mac_pppoe_ipv4_udp_pay_l3_src_only,
    mac_pppoe_ipv4_udp_pay_l3_dst_only,
    mac_pppoe_ipv4_udp_pay_l4_src_only,
    mac_pppoe_ipv4_udp_pay_l4_dst_only,
    mac_pppoe_ipv4_udp_pay_l3_src_only_l4_src_only,
    mac_pppoe_ipv4_udp_pay_l3_src_only_l4_dst_only,
    mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_src_only,
    mac_pppoe_ipv4_udp_pay_l3_dst_only_l4_dst_only,
    mac_pppoe_ipv4_udp_pay_l3_src_only_l3_dst_only_l4_src_only_l4_dst_only,
    mac_pppoe_ipv4_udp_pay_ipv4,
    ]

mac_pppoe_ipv4_pay_cases = [
    mac_pppoe_ipv4_pay_l2_src_only,
    mac_pppoe_ipv4_pay_l2_dst_only,
    mac_pppoe_ipv4_pay_l2_src_only_l2_dst_only,
    mac_pppoe_ipv4_pay_l3_src_only,
    mac_pppoe_ipv4_pay_l3_dst_only,
    mac_pppoe_ipv4_pay_l3_src_only_l3_dst_only
]

mac_pppoe_pay = [
    mac_pppoe_pay_l2_src_only,
    mac_pppoe_pay_l2_dst_only,
    mac_pppoe_pay_l2_src_only_l2_dst_only,
    mac_pppoe_pay_session_id,
    mac_pppoe_pay_l2_src_only_session_id
]

mac_pppoe_ipv6_tcp_pay_symmetric_packets = {
    'match': {
        'mac_pppoe_ipv6_tcp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=23,dport=25)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=23,dport=25)/Raw("x"*80)'
        ],
    },
    'mismatch': {
        'mac_pppoe_ipv4_tcp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=23,dport=25)/Raw("x"*80)'
        ],
        'mac_pppoe_ipv6_udp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=23,dport=25)/Raw("x"*80)',
        ],
        'mac_pppoe_ipv6_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)'
        ],
        'mac_ipv6_tcp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=23,dport=25)/Raw("x"*80)'
        ]
    }

}

mac_pppoe_ipv6_tcp_pay_symmetric = {
    'sub_casename': 'mac_pppoe_ipv6_tcp_pay_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv6_tcp_pay'][1],
            'action': {'check_hash_same': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv6_tcp_pay'][2],
            'action': {'check_hash_same': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv6_tcp_pay'][3],
            'action': {'check_hash_same': 'mac_pppoe_ipv6_tcp_pay'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_tcp_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_udp_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['mismatch']['mac_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_ipv6_tcp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['mismatch']['mac_ipv6_tcp_pay'][1:],
            'action': {'check_hash_different': 'mac_ipv6_tcp_pay_mismatch'},
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay_match_post'},
        },
        {
            'send_packet': mac_pppoe_ipv6_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv6_tcp_pay'][3],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay_match_post'},
        },
    ],
}

mac_pppoe_ipv6_udp_pay_symmetric_packets = {
    'match': {
        'mac_pppoe_ipv6_udp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=23,dport=25)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=23,dport=25)/Raw("x"*80)'
        ]
    },
    'mismatch': {
        'mac_pppoe_ipv4_udp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=23,dport=25)/Raw("x"*80)'
        ],
        'mac_pppoe_ipv6_tcp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=23,dport=25)/Raw("x"*80)',
        ],
        'mac_pppoe_ipv6_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)'
        ],
        'mac_ipv6_udp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=23,dport=25)/Raw("x"*80)'
        ]
    }
}

mac_pppoe_ipv6_udp_pay_symmetric = {
    'sub_casename': 'mac_pppoe_ipv6_udp_pay_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['match']['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['match']['mac_pppoe_ipv6_udp_pay'][1],
            'action': {'check_hash_same': 'mac_pppoe_ipv6_udp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['match']['mac_pppoe_ipv6_udp_pay'][2],
            'action': {'check_hash_same': 'mac_pppoe_ipv6_udp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['match']['mac_pppoe_ipv6_udp_pay'][3],
            'action': {'check_hash_same': 'mac_pppoe_ipv6_udp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_udp_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_tcp_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['mismatch']['mac_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_ipv6_udp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['mismatch']['mac_ipv6_udp_pay'][1:],
            'action': {'check_hash_different': 'mac_ipv6_udp_pay_mismatch'},
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['match']['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay_match_post'},
        },
        {
            'send_packet': mac_pppoe_ipv6_udp_pay_symmetric_packets['match']['mac_pppoe_ipv6_udp_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay_match_post'},
        },
    ],
}

mac_pppoe_ipv6_pay_symmetric_packets = {
    'match': {
        'mac_pppoe_ipv6_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)'
        ],
        'mac_pppoe_ipv6_frag': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/IPv6ExtHdrFragment()/Raw("x"*80)'
        ]
    },
    'mismatch': {
        'mac_pppoe_ipv4_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
        ],
        'mac_pppoe_ipv4_frag': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1", frag=5)/Raw("x"*80)'
        ],
        'mac_ipv6_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)'
        ],
        'mac_ipv6_frag': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/IPv6ExtHdrFragment()/Raw("x"*80)'
        ]
    }
}

mac_pppoe_ipv6_pay_symmetric = {
    'sub_casename': 'mac_pppoe_ipv6_pay_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['match']['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['match']['mac_pppoe_ipv6_pay'][1:],
            'action': {'check_hash_same': 'mac_pppoe_ipv6_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['match']['mac_pppoe_ipv6_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_frag_match'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['match']['mac_pppoe_ipv6_frag'][1:],
            'action': {'check_hash_same': 'mac_pppoe_ipv6_frag_match'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_frag_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_frag'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_frag_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['mismatch']['mac_ipv6_pay'][0],
            'action': {'save_hash': 'mac_ipv6_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['mismatch']['mac_ipv6_pay'][1:],
            'action': {'check_hash_different': 'mac_ipv6_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['mismatch']['mac_ipv6_frag'][0],
            'action': {'save_hash': 'mac_ipv6_frag_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['mismatch']['mac_ipv6_frag'][1:],
            'action': {'check_hash_different': 'mac_ipv6_frag_mismatch'},
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv6_pay_symmetric_packets['match']['mac_pppoe_ipv6_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_pay_symmetric_packets = {
    'match': {
        'mac_pppoe_ipv4_pay': [
            'Ether(src="00:11:22:33:44:55",dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55",dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/Raw("x"*80)',
        ],
        'mac_pppoe_ipv4_frag': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1", frag=5)/Raw("x"*80)',
        ]
    },
    'mismatch': {
        'mac_pppoe_ipv6_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)'
        ],
        'mac_pppoe_ipv6_frag': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/IPv6ExtHdrFragment()/Raw("x"*80)'
        ],
        'mac_ipv4_pay': [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x"*80)',
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21",dst="192.168.0.20")/Raw("x"*80)'
        ],
        'mac_ipv4_frag': [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=5)/Raw("x"*80)',
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21",dst="192.168.0.20", frag=5)/Raw("x"*80)'
        ]
    }
}

mac_pppoe_ipv4_pay_symmetric = {
    'sub_casename': 'mac_pppoe_ipv4_pay_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['match']['mac_pppoe_ipv4_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['match']['mac_pppoe_ipv4_pay'][1],
            'action': {'check_hash_same': 'mac_pppoe_ipv4_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['match']['mac_pppoe_ipv4_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_frag_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['match']['mac_pppoe_ipv4_frag'][1],
            'action': {'check_hash_same': 'mac_pppoe_ipv4_frag_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_pay'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_frag'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_frag_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_frag'][1],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_frag_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['mismatch']['mac_ipv4_pay'][0],
            'action': {'save_hash': 'mac_ipv4_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['mismatch']['mac_ipv4_pay'][1],
            'action': {'check_hash_different': 'mac_ipv4_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['mismatch']['mac_ipv4_frag'][0],
            'action': {'save_hash': 'mac_ipv4_frag_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_pay_symmetric_packets['mismatch']['mac_ipv4_frag'][1],
            'action': {'check_hash_different': 'mac_ipv4_frag_mismatch'},
        },
    ],
    'post-test': [
        {
            'send_packet': [i for i in
                            mac_pppoe_ipv4_pay_symmetric_packets['match']['mac_pppoe_ipv4_pay']],
            'action': 'check_no_hash',
        },
    ],
}

mac_pppoe_ipv4_udp_pay_symmetric_packets = {
    'match': {
        'mac_pppoe_ipv4_udp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=23,dport=25)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/UDP(sport=23,dport=25)/Raw("x"*80)'
        ],
    },
    'mismatch': {
        'mac_pppoe_ipv4_tcp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/TCP(sport=19,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=23,dport=19)/Raw("x"*80)',
        ],
        'mac_pppoe_ipv6_udp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=23,dport=25)/Raw("x"*80)',

        ],
        'mac_pppoe_ipv4_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'
        ],
        'mac_ipv4_udp_pay': [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21",dst="192.168.0.20")/UDP(sport=23,dport=25)/Raw("x"*80)'
        ]
    }
}

mac_pppoe_ipv4_udp_pay_symmetric = {
    'sub_casename': 'mac_pppoe_ipv4_udp_pay_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['match']['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['match']['mac_pppoe_ipv4_udp_pay'][1],
            'action': {'check_hash_same': 'mac_pppoe_ipv4_udp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['match']['mac_pppoe_ipv4_udp_pay'][2],
            'action': {'check_hash_same': 'mac_pppoe_ipv4_udp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['match']['mac_pppoe_ipv4_udp_pay'][3],
            'action': {'check_hash_same': 'mac_pppoe_ipv4_udp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_tcp_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_tcp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_udp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_udp_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_udp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['mismatch']['mac_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_ipv4_udp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['mismatch']['mac_ipv4_udp_pay'][1:],
            'action': {'check_hash_different': 'mac_ipv4_udp_pay_mismatch'},
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['match']['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_ipv4_udp_pay_match_post'},
        },
        {
            'send_packet': mac_pppoe_ipv4_udp_pay_symmetric_packets['match']['mac_pppoe_ipv4_udp_pay'][1:],
            'action': {'check_hash_different': 'mac_ipv4_udp_pay_match_post'},
        },
    ],
}

mac_pppoe_ipv4_tcp_pay_symmetric_packets = {
    'match': {
        'mac_pppoe_ipv4_tcp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=23,dport=25)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/TCP(sport=23,dport=25)/Raw("x"*80)'
        ]
    },
    'mismatch': {
        'mac_pppoe_ipv4_udp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=23,dport=25)/Raw("x"*80)',
        ],
        'mac_pppoe_ipv6_tcp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=23,dport=25)/Raw("x"*80)',
        ],
        'mac_pppoe_ipv4_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'
        ],
        'mac_ipv4_tcp_pay': [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21",dst="192.168.0.20")/TCP(sport=23,dport=25)/Raw("x"*80)'
        ]
    }
}

mac_pppoe_ipv4_tcp_pay_symmetric = {
    'sub_casename': 'mac_pppoe_ipv4_tcp_pay_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv4_tcp_pay'][1],
            'action': {'check_hash_same': 'mac_pppoe_ipv4_tcp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv4_tcp_pay'][2],
            'action': {'check_hash_same': 'mac_pppoe_ipv4_tcp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv4_tcp_pay'][3],
            'action': {'check_hash_same': 'mac_pppoe_ipv4_tcp_pay_match'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_udp_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_udp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_tcp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv6_tcp_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv6_tcp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['mismatch']['mac_pppoe_ipv4_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['mismatch']['mac_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_ipv4_tcp_pay_mismatch'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['mismatch']['mac_ipv4_tcp_pay'][1:],
            'action': {'check_hash_different': 'mac_ipv4_tcp_pay_mismatch'},
        },
    ],
    'post-test': [
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay_match_post'},
        },
        {
            'send_packet': mac_pppoe_ipv4_tcp_pay_symmetric_packets['match']['mac_pppoe_ipv4_tcp_pay'][3],
            'action': {'check_hash_different', 'mac_pppoe_ipv4_tcp_pay_match_post'}
        },
    ],
}

simple_xor_packets = {
    'match': {
        'mac_pppoe_ipv4_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'
        ],
        'mac_pppoe_ipv4_udp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/UDP(sport=25,dport=23)/Raw("x"*80)'
        ],
        'mac_pppoe_ipv4_tcp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.2", dst="192.168.1.1")/TCP(sport=25,dport=23)/Raw("x"*80)'
        ],
        'mac_pppoe_ipv6_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)'
        ],
        'mac_ipv6_udp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=25,dport=23)/Raw("x"*80)'
        ],
        'mac_ipv6_tcp_pay': [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=25,dport=23)/Raw("x"*80)'
        ]

    }
}

simple_xor = {
    'sub_casename': 'simple_xor',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end',
    'test': [
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_pay'][1:],
            'action': {'check_hash_same': 'mac_pppoe_ipv4_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_udp_pay'][1:],
            'action': {'check_same': 'mac_pppoe_ipv4_udp_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_tcp_pay'][1:],
            'action': {'check_same': 'mac_pppoe_ipv4_tcp_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv6_pay'][1:],
            'action': {'check_same': 'mac_pppoe_ipv6_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_ipv6_udp_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_ipv6_udp_pay'][1:],
            'action': {'check_same': 'mac_ipv6_udp_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_ipv6_tcp_pay_match'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_ipv6_tcp_pay'][1:],
            'action': {'check_same': 'mac_ipv6_tcp_pay_match'},
        },

    ],
    'post-test': [
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_pay'][1:],
            'action': {'check_hash_different': 'mac_pppoe_ipv4_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_udp_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_udp_pay'][1:],
            'action': {'check_same': 'mac_pppoe_ipv4_udp_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv4_tcp_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv4_tcp_pay'][1:],
            'action': {'check_same': 'mac_pppoe_ipv4_tcp_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv6_pay'][0],
            'action': {'save_hash': 'mac_pppoe_ipv6_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_pppoe_ipv6_pay'][1:],
            'action': {'check_same': 'mac_pppoe_ipv6_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_ipv6_udp_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_ipv6_udp_pay'][1:],
            'action': {'check_same': 'mac_ipv6_udp_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_ipv6_tcp_pay_match_post'},
        },
        {
            'send_packet': simple_xor_packets['match']['mac_ipv6_tcp_pay'][1:],
            'action': {'check_same': 'mac_ipv6_tcp_pay_match_post'},
        },
    ],
}

mac_vlan_ipv4_pay_packets = {
    'match': {
        'mac_vlan_ipv4_pay': [
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/Raw("x" * 80)',
        ],
    },
    'mismatch': [
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'
    ]
}

mac_vlan_ipv4_pay = {
    'sub_casename': 'mac_vlan_ipv4_pay',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / ipv4 / end actions rss types c-vlan end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_ipv4_pay_packets['match']['mac_vlan_ipv4_pay'][0],
            'action': {'save_hash': 'mac_vlan_ipv4_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_pay_packets['match']['mac_vlan_ipv4_pay'][1],
            'action': {'check_hash_different': 'mac_vlan_ipv4_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_pay_packets['match']['mac_vlan_ipv4_pay'][2],
            'action': {'check_hash_same': 'mac_vlan_ipv4_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_pay_packets['mismatch'][0],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_ipv4_pay_packets['match']['mac_vlan_ipv4_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_ipv4_udp_pay_packets = {
    'match': {
        'mac_vlan_ipv4_udp_pay': [
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/UDP(sport=19,dport=99)/Raw("x" * 80)',
        ]
    },
    'mismatch': [
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'
    ]
}

mac_vlan_ipv4_udp_pay = {
    'sub_casename': 'mac_vlan_ipv4_udp_pay',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / ipv4 / udp / end actions rss types c-vlan end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_ipv4_udp_pay_packets['match']['mac_vlan_ipv4_udp_pay'][0],
            'action': {'save_hash': 'mac_vlan_ipv4_udp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_udp_pay_packets['match']['mac_vlan_ipv4_udp_pay'][1],
            'action': {'check_hash_different': 'mac_vlan_ipv4_udp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_udp_pay_packets['match']['mac_vlan_ipv4_udp_pay'][2],
            'action': {'check_hash_same': 'mac_vlan_ipv4_udp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_ipv4_udp_pay_packets['match']['mac_vlan_ipv4_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_ipv4_tcp_pay_packets = {
    'match': {
        'mac_vlan_ipv4_tcp_pay': [
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/TCP(sport=19,dport=99)/Raw("x" * 80)'
        ]
    },
    'mismatch': [
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'
    ]
}

mac_vlan_ipv4_tcp_pay = {
    'sub_casename': 'mac_vlan_ipv4_tcp_pay',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / ipv4 / tcp / end actions rss types c-vlan end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_ipv4_tcp_pay_packets['match']['mac_vlan_ipv4_tcp_pay'][0],
            'action': {'save_hash': 'mac_vlan_ipv4_tcp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_tcp_pay_packets['match']['mac_vlan_ipv4_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_vlan_ipv4_tcp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_tcp_pay_packets['match']['mac_vlan_ipv4_tcp_pay'][2],
            'action': {'check_hash_same': 'mac_vlan_ipv4_tcp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_tcp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_ipv4_tcp_pay_packets['match']['mac_vlan_ipv4_tcp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_ipv4_sctp_pay_packets = {
    'match': {
        'mac_vlan_ipv4_sctp_pay': [
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.5")/SCTP(sport=19,dport=99)/Raw("x" * 80)'
        ]
    },
    'mismatch': [
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)'

    ]
}

mac_vlan_ipv4_sctp_pay = {
    'sub_casename': 'mac_vlan_ipv4_sctp_pay',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / ipv4 / sctp / end actions rss types c-vlan end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_ipv4_sctp_pay_packets['match']['mac_vlan_ipv4_sctp_pay'][0],
            'action': {'save_hash': 'mac_vlan_ipv4_sctp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_sctp_pay_packets['match']['mac_vlan_ipv4_sctp_pay'][1],
            'action': {'check_hash_different': 'mac_vlan_ipv4_sctp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_sctp_pay_packets['match']['mac_vlan_ipv4_sctp_pay'][2],
            'action': {'check_hash_same': 'mac_vlan_ipv4_sctp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv4_sctp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_ipv4_sctp_pay_packets['match']['mac_vlan_ipv4_sctp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_ipv6_pay_packets = {
    'match': {
        'mac_vlan_ipv6_pay': [
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("y" * 80)'
        ]
    },
    'mismatch': [
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'
    ]
}

mac_vlan_ipv6_pay = {
    'sub_casename': 'mac_vlan_ipv6_pay',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / ipv6 / end actions rss types c-vlan end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_ipv6_pay_packets['match']['mac_vlan_ipv6_pay'][0],
            'action': {'save_hash': 'mac_vlan_ipv6_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_pay_packets['match']['mac_vlan_ipv6_pay'][1],
            'action': {'check_hash_different': 'mac_vlan_ipv6_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_pay_packets['match']['mac_vlan_ipv6_pay'][2],
            'action': {'check_hash_same': 'mac_vlan_ipv6_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_ipv6_pay_packets['match']['mac_vlan_ipv6_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_ipv6_udp_pay_packets = {
    'match': {
        'mac_vlan_ipv6_udp_pay': [
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=99)/Raw("x" * 80)'
        ]
    },
    'mismatch': [
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'
    ]
}

mac_vlan_ipv6_udp_pay = {
    'sub_casename': 'mac_vlan_ipv6_udp_pay',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / ipv6 / udp / end actions rss types c-vlan end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_ipv6_udp_pay_packets['match']['mac_vlan_ipv6_udp_pay'][0],
            'action': {'save_hash': 'mac_vlan_ipv6_udp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_udp_pay_packets['match']['mac_vlan_ipv6_udp_pay'][1],
            'action': {'check_hash_different': 'mac_vlan_ipv6_udp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_udp_pay_packets['match']['mac_vlan_ipv6_udp_pay'][2],
            'action': {'check_hash_same': 'mac_vlan_ipv6_udp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_udp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_ipv6_udp_pay_packets['match']['mac_vlan_ipv6_udp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_ipv6_tcp_pay_packets = {
    'match': {
        'mac_vlan_ipv6_tcp_pay': [
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x" * 80)'
        ]
    },
    'mismatch': [
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'
    ]
}

mac_vlan_ipv6_tcp_pay = {
    'sub_casename': 'mac_vlan_ipv6_tcp_pay',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / ipv6 / tcp / end actions rss types c-vlan end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_ipv6_tcp_pay_packets['match']['mac_vlan_ipv6_tcp_pay'][0],
            'action': {'save_hash': 'mac_vlan_ipv6_tcp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_tcp_pay_packets['match']['mac_vlan_ipv6_tcp_pay'][1],
            'action': {'check_hash_different': 'mac_vlan_ipv6_tcp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_tcp_pay_packets['match']['mac_vlan_ipv6_tcp_pay'][2],
            'action': {'check_hash_same': 'mac_vlan_ipv6_tcp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_tcp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_ipv6_tcp_pay_packets['match']['mac_vlan_ipv6_tcp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_ipv6_sctp_pay_packets = {
    'match': {
        'mac_vlan_ipv6_sctp_pay': [
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)',
            'Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/SCTP(sport=25,dport=99)/Raw("x" * 80)'
        ]
    },
    'mismatch': [
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'
    ]
}

mac_vlan_ipv6_sctp_pay = {
    'sub_casename': 'mac_vlan_ipv6_sctp_pay',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / ipv6 / sctp / end actions rss types c-vlan end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_ipv6_sctp_pay_packets['match']['mac_vlan_ipv6_sctp_pay'][0],
            'action': {'save_hash': 'mac_vlan_ipv6_sctp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_sctp_pay_packets['match']['mac_vlan_ipv6_sctp_pay'][1],
            'action': {'check_hash_different': 'mac_vlan_ipv6_sctp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_sctp_pay_packets['match']['mac_vlan_ipv6_sctp_pay'][2],
            'action': {'check_hash_same': 'mac_vlan_ipv6_sctp_pay_match'},
        },
        {
            'send_packet': mac_vlan_ipv6_sctp_pay_packets['mismatch'],
            'action': 'check_no_hash',
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_ipv6_sctp_pay_packets['match']['mac_vlan_ipv6_sctp_pay'],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_pppoe_pay_l2_src_only_packets = [
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=7)/Raw("x"*80)'
]

mac_vlan_pppoe_pay_l2_src_only = {
    'sub_casename': 'mac_vlan_pppoe_pay_l2_src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / pppoes / end actions rss types eth l2-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_packets[0],
            'action': {'save_hash': 'l2_src_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_packets[1],
            'action': {'check_hash_different': 'l2_src_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_packets[2],
            'action': {'check_hash_same': 'l2_src_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_packets[3],
            'action': {'check_hash_same': 'l2_src_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_packets[4],
            'action': {'check_hash_same': 'l2_src_only'},
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_packets[1],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_pppoe_pay_l2_dst_only_packets = [
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=7)/Raw("x"*80)'
]

mac_vlan_pppoe_pay_l2_dst_only = {
    'sub_casename': 'mac_vlan_pppoe_pay_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / pppoes / end actions rss types eth l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_pppoe_pay_l2_dst_only_packets[0],
            'action': {'save_hash': 'l2_dst_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_dst_only_packets[1],
            'action': {'check_hash_different': 'l2_dst_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_dst_only_packets[2],
            'action': {'check_hash_same': 'l2_dst_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_dst_only_packets[3],
            'action': {'check_hash_same': 'l2_dst_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_dst_only_packets[4],
            'action': {'check_hash_same': 'l2_dst_only'},
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_pppoe_pay_l2_dst_only_packets[1],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_pppoe_pay_l2_src_only_l2_dst_only_packets = [
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)',
    'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=7)/Raw("x"*80)'
]

mac_vlan_pppoe_pay_l2_src_only_l2_dst_only = {
    'sub_casename': 'mac_vlan_pppoe_pay_l2_src_only_l2_dst_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / pppoes / end actions rss types eth l2-src-only l2-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_l2_dst_only_packets[0],
            'action': {'save_hash': 'l2_src_only_l2_dst_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_l2_dst_only_packets[1],
            'action': {'check_hash_different': 'l2_src_only_l2_dst_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_l2_dst_only_packets[2],
            'action': {'check_hash_same': 'l2_src_only_l2_dst_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_l2_dst_only_packets[3],
            'action': {'check_hash_same': 'l2_src_only_l2_dst_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_l2_dst_only_packets[4],
            'action': {'check_hash_same': 'l2_src_only_l2_dst_only'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_l2_dst_only_packets[5],
            'action': {'check_hash_same': 'l2_src_only_l2_dst_only'},
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_pppoe_pay_l2_src_only_l2_dst_only_packets[1],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_pppoe_pay_c_vlan_packets = [
    'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x" * 80)',
    'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/Raw("x" * 80)',
    'Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x" * 80)',
    'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x" * 80)',
    'Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=7)/Raw("x" * 80)'
]

mac_vlan_pppoe_pay_c_vlan = {
    'sub_casename': 'mac_vlan_pppoe_pay_c_vlan',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / vlan / pppoes / end actions rss types c-vlan end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_vlan_pppoe_pay_c_vlan_packets[0],
            'action': {'save_hash': 'c_vlan'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_c_vlan_packets[1],
            'action': {'check_hash_different': 'c_vlan'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_c_vlan_packets[2],
            'action': {'check_hash_same': 'c_vlan'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_c_vlan_packets[3],
            'action': {'check_hash_same': 'c_vlan'},
        },
        {
            'send_packet': mac_vlan_pppoe_pay_c_vlan_packets[4],
            'action': {'check_hash_same': 'c_vlan'},
        },
    ],
    'post-test': [
        {
            'send_packet': mac_vlan_pppoe_pay_c_vlan_packets[1],
            'action': 'check_no_hash',
        },
    ],
}

mac_vlan_pppoe_pay = [
    mac_vlan_pppoe_pay_l2_src_only,
    mac_vlan_pppoe_pay_l2_dst_only,
    mac_vlan_pppoe_pay_l2_src_only_l2_dst_only,
    mac_vlan_pppoe_pay_c_vlan
]


class Advanced_rss_pppoe_vlan_ah_l2tp_pfcp(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
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
        self.pci_list = []
        for port in self.dut.ports_info:
            self.pci_list.append(port['pci'])
        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.ddp_dir = "/lib/firmware/updates/intel/ice/ddp/"
        conf_file = 'conf/cvl_advanced_rss_pppoe.cfg'
        conf_info = UserConf(conf_file)
        conf_section = conf_info.conf._sections['suite']
        self.os_default_package = conf_section['os_default_package_file_location']
        self.comms_package = conf_section['comms_package_file_location']
        self.symmetric = False
        self.rxq = 64
        self.rsspro = RssProcessing(self, self.pmd_output, [self.tester_iface0, self.tester_iface1], self.rxq)
        self.logger.info('rssprocess.tester_ifaces: {}'.format(self.rsspro.tester_ifaces))
        self.logger.info('rssprocess.test_case: {}'.format(self.rsspro.test_case))

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def tear_down(self):
        """
        Run after each test case.
        """
        # destroy all flow rule on port 0
        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()

    def replace_package(self, package='comms'):
        ice_pkg_path = ''.join([self.ddp_dir,"ice.pkg"])
        self.dut.send_expect("rm -f {}".format(ice_pkg_path), "# ")
        if package == 'os_default':
            self.dut.send_expect("cp {} {}".format(self.os_default_package,ice_pkg_path), "# ")
        elif package == 'comms':
            self.dut.send_expect("cp {} {}".format(self.comms_package,ice_pkg_path), "# ")
        for pci in self.pci_list:
            self.dut.send_expect("echo {0} > /sys/bus/pci/devices/{0}/driver/unbind".format(pci), "# ", 60)
            self.dut.send_expect("echo {} > /sys/bus/pci/drivers/ice/bind".format(pci), "# ", 60)
        pci_str = ' '.join(self.pci_list)
        self.dut.send_expect("./usertools/dpdk-devbind.py --force --bind=vfio-pci {}".format(pci_str), "# ", 60)

    def launch_testpmd(self, symmetric=False, package='comms'):
        if symmetric:
            param = "--rxq=64 --txq=64"
        else:
            param = "--rxq=64 --txq=64 --disable-rss --rxd=384 --txd=384"
        out = self.pmd_output.start_testpmd(cores="1S/4C/1T", param=param,
                                            eal_param=f"-w {self.pci_list[0]}", socket=self.ports_socket)
        self.symmetric = symmetric
        package_version = re.search('Active\spackage\sis:\s(.+),', out).group(1)
        self.logger.info('DDP package version: %s' % package_version)
        if package == 'comms':
            self.verify(package_version in self.comms_package.split('/')[-1],
                        'package version not match')
        elif package == 'os_default':
            self.verify(package_version in self.os_default_package.split('/')[-1],
                        'package version not match')
        if symmetric:
            # Need config rss in setup
            self.pmd_output.execute_cmd("port config all rss all")
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        res = self.pmd_output.wait_link_status_up('all', timeout=15)
        self.verify(res is True, 'there have port link is down')
        return package_version

    def switch_testpmd(self, symmetric=True, pkg='comms'):
        self.dut.kill_all()
        self.launch_testpmd(symmetric, pkg)
        self.pmd_output.execute_cmd("start")

    def _gener_str(self, str_len=6):
        return ''.join(random.sample(string.ascii_letters + string.digits, k=str_len))

    def test_mac_ipv4_pfcp_session(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv4_pfcp_session)

    def test_mac_ipv6_pfcp_session(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv6_pfcp_session)

    def test_mac_ipv4_l2tpv3(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv4_l2tpv3)

    def test_mac_ipv6_l2tpv3(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv6_l2tpv3)

    def test_mac_ipv4_esp(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv4_esp)

    def test_mac_ipv4_udp_esp(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv4_udp_esp)

    def test_mac_ipv6_esp(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv6_esp)

    def test_mac_ipv6_udp_esp(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv6_udp_esp)

    def test_mac_ipv4_ah(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv4_ah)

    def test_mac_ipv6_ah(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_ipv6_ah)

    def test_mac_pppoe_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_pay)

    def test_mac_pppoe_ipv4_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv4_pay_cases)

    def test_mac_pppoe_ipv4_udp_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv4_udp_pay)

    def test_mac_pppoe_ipv4_tcp_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv4_tcp_pay)

    def test_mac_pppoe_ipv6_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv6_pay)

    def test_mac_pppoe_ipv6_udp_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv6_udp_pay)

    def test_mac_pppoe_ipv6_tcp_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv6_tcp_pay)

    def test_mac_pppoe_ipv4_pay_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv4_pay_symmetric)

    def test_mac_pppoe_ipv4_udp_pay_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv4_udp_pay_symmetric)

    def test_mac_pppoe_ipv4_tcp_pay_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv4_tcp_pay_symmetric)

    def test_mac_pppoe_ipv6_pay_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv6_pay_symmetric)

    def test_mac_pppoe_ipv6_udp_pay_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv6_udp_pay_symmetric)

    def test_mac_pppoe_ipv6_tcp_pay_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_pppoe_ipv6_tcp_pay_symmetric)

    def test_simple_xor(self):
        self.switch_testpmd(symmetric=True)
        self.rsspro.handle_rss_distribute_cases(cases_info=simple_xor)

    def test_multirules_two_rules_not_hit_default_profile(self):
        """
        Subcase 1: two rules with same pattern but different hash input set, not hit default profile
        :return:
        """
        self.rsspro.error_msgs = []
        self.switch_testpmd(symmetric=True)
        rule0 = 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end'
        self.rsspro.create_rule(rule0)
        self.rsspro.check_rule(0)
        pkts_list1 = [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)']
        out = self.rsspro.send_pkt_get_output(pkts_list1[0])
        pkt1_first_key = 'l3_src'
        self.rsspro.save_hash(out, pkt1_first_key)
        res = self.rsspro.send_pkt_get_output(pkts_list1[1])
        self.rsspro.check_hash_different(res, pkt1_first_key)

        rule1 = 'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end'
        self.rsspro.create_rule(rule1)
        pkts_list2 = [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
        ]
        self._send_pkt_action(pkts_list2)

        pkts_list3 = [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)']

        for i in range(1, 3):
            self.rsspro.destroy_rule(rule_id=i % 2)
            self.rsspro.check_rule(rule_list='rule{}'.format(i % 2), stats=False)
            pkt_base = 'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)'
            res3 = self.rsspro.send_pkt_get_output(pkt_base)
            pkt3_key = 'hash_record_{}'.format(i % 2)
            self.rsspro.save_hash(res3, pkt3_key)
            for each_rule in pkts_list3:
                result = self.rsspro.send_pkt_get_output(each_rule)
                self.rsspro.check_hash_different(result, pkt3_key)
        self.verify(not self.rsspro.error_msgs, 'some subcases failed')

    def test_multirules_two_rules_hit_default_profile(self):
        """
        # Subcase 2: two rules with same pattern but different hash input set, hit default profile
        :return:
        """
        self.rsspro.error_msgs = []
        self.switch_testpmd(symmetric=True)
        rule_list = [
            'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end'

        ]
        pkt_list = [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.5")/Raw("x"*80)',
        ]
        self._two_rules_operation(rule_list, pkt_list,action_list1=['check_no_hash' for _ in range(0,len(pkt_list))],action_list2=['check_no_hash'])
        self.verify(not self.rsspro.error_msgs, 'some subcases failed')

    def _send_pkt_action(self, pkt_list, action_list=None):
        if action_list is None:
            action_list = ['save_hash', 'check_hash_different', 'check_hash_same']
        hash_key = self._gener_str()
        for i in range(0, len(pkt_list)):
            out = self.rsspro.send_pkt_get_output(pkt_list[i])
            func = getattr(self.rsspro, action_list[i])
            func(out, hash_key)

    def _two_rules_operation(self, rule_list, pkt_list, action_list1=None, action_list2=None):
        for i in range(0, len(rule_list)):
            self.rsspro.create_rule(rule_list[i])
            self.rsspro.check_rule(rule_list=['{}'.format(i)])
            if i == 1:
                pkt_list[1], pkt_list[2] = pkt_list[2], pkt_list[1]
                self._send_pkt_action(pkt_list)
            else:
                self._send_pkt_action(pkt_list)
        # destory rule 1
        self.rsspro.destroy_rule(rule_id=1)
        self.rsspro.check_rule(rule_list=['1'], stats=False)
        pkt_list[1], pkt_list[2] = pkt_list[2], pkt_list[1]
        self._send_pkt_action(pkt_list, action_list=action_list1)
        # destory rule 0
        self.rsspro.destroy_rule(rule_id=0)
        self.rsspro.check_rule(rule_list=['0'], stats=False)
        self._send_pkt_action([pkt_list[0]], action_list=action_list2)

    def test_two_rules_smaller_first_larger_later(self, ):
        """
        two rules, scope smaller created first, and the larger one created later
        """
        self.rsspro.error_msgs = []
        self.switch_testpmd(symmetric=True)
        rule_list = [
            'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end'
        ]
        pkt_list = [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/UDP(sport=25,dport=99)/Raw("x"*80)',
        ]
        self._two_rules_operation(rule_list, pkt_list, action_list2=['check_no_hash'])
        self.verify(not self.rsspro.error_msgs, 'some subcases failed')

    def test_two_rules_larger_first_smaller_later(self):
        """
        Subcase 4: two rules, scope larger created first, and the smaller one created later
        """
        self.rsspro.error_msgs = []
        self.switch_testpmd(symmetric=True)
        rule_list = [
            'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end'
        ]
        pkt_list = [
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.5")/UDP(sport=25,dport=99)/Raw("x"*80)',
            'Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)',
        ]
        self._two_rules_operation(rule_list, pkt_list, action_list2=['check_no_hash'])

    def test_wrong_hash_input_set(self):
        self.switch_testpmd(symmetric=True)
        rule_list = [
            'flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types l2-src-only l2-dst-only end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp l3-src-only end key_len 0 queues end / end']

        for rule in rule_list:
            self.rsspro.validate_rule(rule, check_stats=False, check_msg='Invalid argument')
            self.rsspro.create_rule(rule, check_stats=False, msg='Invalid argument')

    def test_duplicated_rules(self):
        self.switch_testpmd(symmetric=True)
        rule = 'flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end'
        self.rsspro.create_rule(rule)
        self.rsspro.create_rule(rule, check_stats=False, msg='Operation not permitted')
        self.rsspro.check_rule(rule_list=[rule])

    def test_void_action(self):
        self.switch_testpmd(symmetric=True)
        rule = 'flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions end'
        self.rsspro.validate_rule(rule, check_stats=False, check_msg='Invalid argument')
        self.rsspro.create_rule(rule, check_stats=False, msg='Invalid argument')
        self.rsspro.check_rule(stats=False, rule_list=[rule])

    def test_delete_nonexisting_rule(self):
        self.switch_testpmd(symmetric=True)
        self.rsspro.check_rule(stats=False)
        out = self.dut.send_command("flow destroy 0 rule 0", timeout=1)
        self.verify('error' not in out, 'delete nonexisting rule raise err,expected no err')
        self.dut.send_command("flow flush 0", timeout=1)

    def test_unsupported_pattern_with_OS_default_package(self):
        self.replace_package('os_default')
        self.switch_testpmd(symmetric=True, pkg='os_default')
        rule_list = [
            'flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end',
            'flow create 0 ingress pattern eth / ipv4 / ah / end actions rss types ah end key_len 0 queues end / end'
        ]
        self.rsspro.validate_rule(rule_list, check_stats=False, check_msg='Invalid argument')
        self.rsspro.create_rule(rule_list, check_stats=False, msg='Invalid argument')
        self.rsspro.check_rule(stats=False)
        self.dut.kill_all()
        self.replace_package('comms')
        self.launch_testpmd()

    def test_invalid_port(self):
        self.switch_testpmd(symmetric=True)
        rule = 'flow create 1 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end'
        self.rsspro.create_rule(rule, check_stats=False, msg='No such device')
        self.rsspro.check_rule(stats=False, rule_list=[rule])
        pattern = 'Invalid port 1'
        out = self.dut.send_command("flow list 1", timeout=1)
        result = re.search(r'%s' % pattern, out)
        self.verify(result, 'actual result not match expected,expected result is:{}'.format(pattern))

    def test_mac_vlan_ipv4_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv4_pay)

    def test_mac_vlan_ipv4_udp_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv4_udp_pay)

    def test_mac_vlan_ipv4_tcp_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv4_tcp_pay)

    def test_mac_vlan_ipv4_sctp_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv4_sctp_pay)

    def test_mac_vlan_ipv6_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv6_pay)

    def test_mac_vlan_ipv6_udp_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv6_udp_pay)

    def test_mac_vlan_ipv6_tcp_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv6_tcp_pay)

    def test_mac_vlan_ipv6_sctp_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_ipv6_sctp_pay)

    def test_mac_vlan_pppoe_pay(self):
        self.switch_testpmd(symmetric=False)
        self.rsspro.handle_rss_distribute_cases(cases_info=mac_vlan_pppoe_pay)
