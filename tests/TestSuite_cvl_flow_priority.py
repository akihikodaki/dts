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

import json
import time
import re
import copy

from framework.test_case import TestCase, skip_unsupported_pkg, check_supported_nic
from framework.pmd_output import PmdOutput
from framework.packet import Packet
from .rte_flow_common import FdirProcessing, check_drop

tv_mac_ipv4_pay = {
    'name': 'tv_mac_ipv4_pay',
    'rule': ['flow create 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions queue index 4 / end'],
    'packet': {
        'matched': ['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/("X"*480)'],
        'mismatched': ['Ether(dst="68:05:ca:8d:ed:a1")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/("X"*480)',
                       'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.3",dst="192.168.0.2",tos=4,ttl=2)/("X"*480)',
                       'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.7",tos=4,ttl=2)/("X"*480)',
                       'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=2)/("X"*480)',
                       'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=9)/("X"*480)']},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 4},}
}

tv_mac_ipv4_udp_pay = {
    'name': 'tv_mac_ipv4_udp_pay',
    'rule': ['flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end',
             'flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)'],
        'mismatched': ['Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)',
                       'Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)',
                       'Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5)/UDP(sport=50,dport=23)/Raw("x"*80)',
                       'Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw("x"*80)',
                       'Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=3)/Raw("x"*80)']},
    'check_param': {
        'check_0': {'queue': [4, 5]},
        'check_1': {'queue': 2}}
}

tv_mac_ipv6 = {
    'name': 'tv_mac_ipv6',
    'rule': ['flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 4 5 end / end',
             'flow create 0 priority 1 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 8 / end'],
    'packet': {
        'matched': ['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
                    ],
        'mismatched': ['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
                       'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/("X"*480)',
                       'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
                       'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/("X"*480)']},
    'check_param': {
        'check_0': {'queue': [4, 5]},
        'check_1': {'queue': 8}}
}

tv_mac_ipv6_tcp = {
    'name': 'tv_mac_ipv6_tcp',
    'rule': ['flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end',
             'flow create 0 priority 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions queue index 3 / end'],
    'packet': {
        'matched': ['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw("x"*80)'],
        'mismatched': ['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/TCP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=7)/TCP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=1,dport=23)/Raw("x"*80)',
                       'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw("x"*80)']
    },
    'check_param': {
        'check_0': {'queue': [4, 5]},
        'check_1': {'queue': 3}},
}

tv_mac_ipv4_vxlan_ipv4_frag = {
    'name': 'tv_mac_ipv4_vxlan_ipv4_frag',
    'rule': ['flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 2 3 end / end',
             'flow create 0 priority 1 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 5 / end'],
    'packet': {
        'matched': ['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)'],
        'mismatched': ['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",frag=5)/Raw("x"*80)',
                       'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",frag=5)/Raw("x"*80)',
                       ]},
    'check_param': {
        'check_0': {'queue': [2, 3]},
        'check_1': {'queue': 5}}
}

tv_mac_ipv4_vxlan_ipv4_pay = {
    'name': 'tv_mac_ipv4_vxlan_ipv4_pay',
    'rule': ['flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 5 / end',
             'flow create 0 priority 1 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 2 3 end / end'],
    'packet': {
        'matched': ['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)',
                    'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)'],
        'mismatched': ['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.5", dst="192.168.0.3")/Raw("x"*80)',
                       'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.7")/Raw("x"*80)',
                       'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.5", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                       'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.7")/TCP()/Raw("x"*80)',
                       ]},
    'check_param': {
        'check_0': {'queue': 5},
        'check_1': {'queue': [2, 3]}}
}

tv_mac_ipv4_nvgre_ipv4_udp_pay = {
    'name': 'tv_mac_ipv4_nvgre_ipv4_udp_pay',
    'rule': ['flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions rss queues 2 3 end / end',
             'flow create 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions queue index 4 / end'],
    'packet': {
        'matched': ['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)'],
        'mismatched': ['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x1)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw("x"*80)']},
    'check_param': {
        'check_0': {'queue': [2, 3]},
        'check_1': {'queue': 4}}
}

tv_mac_ipv4_nvgre_ipv4_tcp = {
    'name': 'tv_mac_ipv4_nvgre_ipv4_tcp',
    'rule': ['flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions queue index 5 / end',
             'flow create 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions rss queues 2 3 end / end'],
    'packet': {
        'matched': ['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)'],
        'mismatched': ['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.5", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw("x"*80)',
                       'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw("x"*80)']},
    'check_param': {
        'check_0': {'queue': 5},
        'check_1': {'queue': [2, 3]}}
}

tv_ethertype_filter_pppoed = {
    'name': 'tv_ethertype_filter_pppoed',
    'rule': ['flow create 0 priority 0 ingress pattern eth type is 0x8863 / end actions queue index 4 / end',
             'flow create 0 priority 1 ingress pattern eth type is 0x8863 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(type=0x8863)/Raw("x" *80)',
                    'Ether()/PPPoED()/Raw("x" *80)'],
        'mismatched': ['Ether(type=0x8864)/Raw("x" *80)',
                       'Ether()/PPPoE()/Raw("x" *80)']},
    'check_param': {
        'check_0': {'queue': 4},
        'check_1': {'queue': 2}}
}

tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id = {
    'name': 'tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id',
    'rule': ['flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x"*80)'],
        'mismatched': ['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IPv6()/Raw("x" * 80)']},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 2}}
}

tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id = {
    'name': 'tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id',
    'rule': ['flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'],
        'mismatched': ['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IP()/Raw("x" * 80)']},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 2}}
}

tv_mac_pppoe_ipv4_pay_ip_address = {
    'name': 'tv_mac_pppoe_ipv4_pay_ip_address',
    'rule': ['flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'],
        'mismatched': ['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)']},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 2}}
}

tv_mac_pppoe_ipv6_udp_pay = {
    'name': 'tv_mac_pppoe_ipv6_udp_pay',
    'rule': ['flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
        'mismatched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)']},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 2}}
}

tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port = {
    'name': 'tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port',
    'rule': ['flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
        'mismatched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                       'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)']},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 2}}
}

tv_mac_vlan_pppoe_ipv6_pay_ip_address = {
    'name': 'tv_mac_vlan_pppoe_ipv6_pay_ip_address',
    'rule': ['flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'],
        'mismatched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)']},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 2}}
}

tv_mac_pppoe_lcp_pay = {
    'name': 'tv_mac_pppoe_lcp_pay',
    'rule': ['flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)'],
        'mismatched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)']},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 2}}
}

tv_mac_pppoe_ipcp_pay = {
    'name': 'tv_mac_pppoe_ipcp_pay',
    'rule': ['flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'],
        'mismatched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)']},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 2}}
}

tv_mac_vlan_pppoe_lcp_pay = {
    'name': 'tv_mac_vlan_pppoe_lcp_pay',
    'rule': ['flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)'],
        'mismatched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)']},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 2}}
}

tv_mac_vlan_pppoe_ipcp_pay = {
    'name': 'tv_mac_vlan_pppoe_ipcp_pay',
    'rule': ['flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end',
             'flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 2 / end'],
    'packet': {
        'matched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'],
        'mismatched': ['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
                       'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'
                       ]},
    'check_param': {
        'check_0': {'queue': 1},
        'check_1': {'queue': 2}}
}

class CVLPFFlowPriorityTest(TestCase):
    supported_nic = ['columbiaville_100g', 'columbiaville_25g', 'columbiaville_25gx2']

    @check_supported_nic(supported_nic)
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.tester_port1 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_iface1 = self.tester.get_interface(self.tester_port0)
        self.pf_pci=self.dut.ports_info[self.dut_ports[0]]['pci']
        self.pkt = Packet()
        self.pmdout = PmdOutput(self.dut)
        self.rxq = 16
        self.process = FdirProcessing(self, self.pmdout, [self.tester_iface0, self.tester_iface1], self.rxq)

    def set_up(self):
        """
        Run before each test case.
        """
        self.reload_ice()
        self.launch_testpmd()

    def reload_ice(self):
        self.dut.bind_interfaces_linux('ice')
        self.dut.send_expect('rmmod ice', '#', 120)
        self.dut.send_expect('modprobe ice', '#', 120)
        self.dut.bind_interfaces_linux('vfio-pci')

    def launch_testpmd(self, eal_param=False):
        """
        launch testpmd with the command
        """
        #if eal_param:
        if self._suite_result.test_case == 'test_flow_priority_filter':
            self.pmdout.start_testpmd(cores='1S/4C/1T', ports=[self.pf_pci], eal_param='--log-level=ice,8', param="--rxq=16 --txq=16")
        else:
            self.pmdout.start_testpmd(cores='1S/4C/1T', ports=[self.pf_pci], param="--rxq=16 --txq=16")
        self.pmdout.execute_cmd('set fwd rxonly')
        self.pmdout.execute_cmd('set verbose 1')
        self.pmdout.execute_cmd('rx_vxlan_port add 4789 0')
        self.pmdout.execute_cmd('start')

    def test_mac_ipv4_pay(self):
        self.process.handle_priority_cases(tv_mac_ipv4_pay)

    def test_mac_ipv4_udp_pay(self):
        self.process.handle_priority_cases(tv_mac_ipv4_udp_pay)

    def test_mac_ipv6(self):
        self.process.handle_priority_cases(tv_mac_ipv6)

    def test_mac_ipv6_tcp(self):
        self.process.handle_priority_cases(tv_mac_ipv6_tcp)

    def test_mac_ipv4_vxlan_ipv4_frag(self):
        self.process.handle_priority_cases(tv_mac_ipv4_vxlan_ipv4_frag)

    def test_mac_ipv4_vxlan_ipv4_pay(self):
        self.process.handle_priority_cases(tv_mac_ipv4_vxlan_ipv4_pay)

    def test_mac_ipv4_nvgre_ipv4_udp_pay(self):
        self.process.handle_priority_cases(tv_mac_ipv4_nvgre_ipv4_udp_pay)

    def test_mac_ipv4_nvgre_ipv4_tcp(self):
        self.process.handle_priority_cases(tv_mac_ipv4_nvgre_ipv4_tcp)

    def test_ethertype_filter_pppoed(self):
        self.process.handle_priority_cases(tv_ethertype_filter_pppoed)

    def test_mac_vlan_pppoe_ipv4_pay_session_id_proto_id(self):
        self.process.handle_priority_cases(tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id)

    def test_mac_vlan_pppoe_ipv6_pay_session_id_proto_id(self):
        self.process.handle_priority_cases(tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id)

    def test_mac_pppoe_ipv4_pay_ip_address(self):
        self.process.handle_priority_cases(tv_mac_pppoe_ipv4_pay_ip_address)

    def test_mac_pppoe_ipv6_udp_pay(self):
        self.process.handle_priority_cases(tv_mac_pppoe_ipv6_udp_pay)

    def test_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port(self):
        self.process.handle_priority_cases(tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port)

    def test_mac_vlan_pppoe_ipv6_pay_ip_address(self):
        self.process.handle_priority_cases(tv_mac_vlan_pppoe_ipv6_pay_ip_address)

    def test_mac_pppoe_lcp_pay(self):
        self.process.handle_priority_cases(tv_mac_pppoe_lcp_pay)

    def test_mac_pppoe_ipcp_pay(self):
        self.process.handle_priority_cases(tv_mac_pppoe_ipcp_pay)

    def test_mac_vlan_pppoe_lcp_pay(self):
        self.process.handle_priority_cases(tv_mac_vlan_pppoe_lcp_pay)

    def test_mac_vlan_pppoe_ipcp_pay(self):
        self.process.handle_priority_cases(tv_mac_vlan_pppoe_ipcp_pay)

    def create_rule_and_check(self, rule_list, check_param):
        for rule in rule_list:
            out = self.pmdout.execute_cmd(rule)
            if isinstance(check_param, list):
                self.verify(check_param[0] in out or check_param[1] in out, "create rule result not meet expected")
            else:
                self.verify(check_param in out, "create rule result not meet expected")

        self.pmdout.execute_cmd('flow flush 0')

    def test_flow_priority_filter(self):
        rule_list1 = ['flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end',
                      'flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end',
                      'flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end']

        rule_list2 = [
                      'flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / mark id 3 / end',
                      ]

        rule_list3 = ['flow create 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end',
                      'flow create 0 priority 1 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end',
                      'flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end']

        rule_list4 = ['flow create 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / mark id 3 / end',
                      'flow create 0 priority 1 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / mark id 3 / end',
                      'flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / mark id 3 / end']

        self.create_rule_and_check(rule_list1, 'Succeeded to create (2) flow')
        self.create_rule_and_check(rule_list2, 'Succeeded to create (1) flow')
        self.create_rule_and_check(rule_list3, 'Succeeded to create (2) flow')
        self.create_rule_and_check(rule_list4, 'Failed to create flow')

    def test_negative(self):
        rules = ['flow create 0 priority 2 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 3 / end',
                 'flow create 0 priority a ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 3 / end',
                 'flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions mark / rss / end']

        self.create_rule_and_check(rules, ['Failed to create flow', 'Bad arguments'])

    def test_exclusive(self):
        p = 'port\s+\d+/queue(.+?):\s+received\s+\d+\s+packets'
        p1 = 'Forward\s+statistics\s+for\s+port\s+0.*?\n.*?RX-packets:\s+(\d+)'

        rule_list1 = ['flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 3 / end',
                      'flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 3 / end']
        pkts1 = 'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)'

        rule_list2 = ['flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 3 / end',
                      'flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions rss queues 4 5 end / end']

        rule_list3 = ['flow create 0 priority 0 ingress pattern eth / vlan / vlan / pppoes / pppoe_proto_id is 0x21 / end actions queue index 3 / end',
                      'flow create 0 priority 1 ingress pattern eth / vlan / vlan / pppoes seid is 1 / ipv4 / end actions queue index 2 / end',
                      'flow create 0 priority 1 ingress pattern eth / vlan / vlan tci is 12 / ipv4 src is 196.222.232.221 / end actions queue index 4 / end',
                      'flow create 0 priority 0 ingress pattern eth / vlan / vlan tci is 12 / ipv4 src is 196.222.232.221 / end actions rss queues 7 8 end / end',
                      'flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / vlan tci is 2 / end actions drop / end',
                      'flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / vlan tci is 2 / end actions queue index 5 / end']
        pkts3 = ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)',
                 'Ether()/Dot1Q(vlan=1)/Dot1Q(vlan=12)/IP(src="196.222.232.221")/Raw("x"*480)',
                 'Ether()/Dot1Q(vlan=1)/Dot1Q(vlan=2)/Raw("x"*480)']
        # subcase1: same pattern/input set/action different priority
        rule_id = self.process.create_rule(rule_list1)
        self.process.check_rule(rule_list=rule_id)
        out = self.process.send_pkt_get_out(pkts1)
        self.pmdout.execute_cmd('flow flush 0')
        queue = re.search(p, out).group(1)
        self.verify(int(queue) == 3, "queue {} receive pkt, expect queue 3".format(queue))

        # subcase2: same pattern/input set/priority different action
        for rule in rule_list2:
            out = self.pmdout.execute_cmd(rule)
            rule_index = rule_list2.index(rule)
            check_param = 'Flow rule #0 created' if rule_index == 0 else 'Failed to create flow'
            self.verify(check_param in out, 'create rule result not meet expected')
        self.pmdout.execute_cmd('flow flush 0')

        # subcase3: some rules overlap
        rule_id = self.process.create_rule(rule_list3)
        self.process.check_rule(rule_list=rule_id)

        out = self.process.send_pkt_get_out(pkts3[0])
        queue = re.search(p, out).group(1)
        self.verify(int(queue) == 3, "queue {} receive pkt, expect queue 3".format(queue))

        out = self.process.send_pkt_get_out(pkts3[1])
        queue = re.search(p, out).group(1)
        self.verify(int(queue) in [7, 8], "queue {} receive pkt, expect queue 7/8".format(queue))

        out = self.process.send_pkt_get_out(pkts3[2])
        pkt_num = re.search(p1, out).group(1)
        self.verify(int(pkt_num) == 0, 'drop pkt failed')

        # destroy rule
        self.process.destroy_rule(rule_id=0)
        self.process.destroy_rule(rule_id=3)
        self.process.destroy_rule(rule_id=4)
        out = self.process.send_pkt_get_out(pkts3[0])
        queue = re.findall(p, out)
        self.verify(len(queue) == 1 and int(queue[0]) == 2, 'queue 3 not receive this pkt')

        out = self.process.send_pkt_get_out(pkts3[1])
        queue = re.findall(p, out)
        self.verify(len(queue) == 1 and int(queue[0]) == 4, 'queue 1/2 not receive this pkt')

        out = self.process.send_pkt_get_out(pkts3[2])
        queue = re.findall(p, out)
        self.verify(len(queue) == 1 and int(queue[0]) == 5, 'drop pkt failed')

    def tear_down(self):
        """
        Run after each test case.
        """
        self.pmdout.execute_cmd('quit', '# ')

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()

