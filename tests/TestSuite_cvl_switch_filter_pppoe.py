# BSD LICENSE
#
# Copyright(c) 2019-2020 Intel Corporation. All rights reserved.
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
import random
from itertools import groupby

from test_case import TestCase, skip_unsupported_pkg
from pmd_output import PmdOutput
from packet import Packet
from utils import BLUE, RED, GREEN
from collections import OrderedDict
import rte_flow_common as rfc

import os

#test vector ethertype_filter_pppoes
ethertype_filter_pppoes_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55", type=0x8864)/PPPoE(sessionid=3)/Raw("x" *80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55", type=0x8863)/PPPoED()/Raw("x" *80)'
    ]
}

tv_ethertype_filter_pppoes_in_queue_01 = {
    "name":"tv_ethertype_filter_pppoes_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8864 / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":ethertype_filter_pppoes_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":ethertype_filter_pppoes_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":1}}
}

tv_ethertype_filter_pppoes_queue_region_02 = {
    "name":"tv_ethertype_filter_pppoes_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8864 / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":ethertype_filter_pppoes_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":ethertype_filter_pppoes_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":1}}
}

tv_ethertype_filter_pppoes_drop_03 = {
    "name":"tv_ethertype_filter_pppoes_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8864 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":ethertype_filter_pppoes_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":ethertype_filter_pppoes_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tvs_ethertype_filter_pppoes = [
    tv_ethertype_filter_pppoes_in_queue_01,
    tv_ethertype_filter_pppoes_queue_region_02,
    tv_ethertype_filter_pppoes_drop_03
    ]

#l4 mask
#ipv4/ipv6 + udp/tcp pipeline mode
mac_pppoes_ipv4_udp_l4_mask_scapy_str = {
    "matched": [
        'Ether()/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=2304,dport=23)/Raw("x"*80)'],
    "mismatched": [
        'Ether()/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=2244,dport=23)/Raw("x"*80)'
    ]
}

tv_mac_pppoes_ipv4_udp_l4_mask_in_queue_01 = {
    "name":"tv_mac_pppoes_ipv4_udp_l4_mask_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 2500 src mask 0xf00 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":False,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoes_ipv4_udp_l4_mask_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoes_ipv4_udp_l4_mask_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":1}}
}

mac_pppoes_ipv4_tcp_l4_mask_scapy_str = {
    "matched": [
        'Ether()/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=2304,dport=23)/Raw("x"*80)'],
    "mismatched": [
        'Ether()/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=2244,dport=23)/Raw("x"*80)'
    ]
}

tv_mac_pppoes_ipv4_tcp_l4_mask_in_queue_02 = {
    "name":"tv_mac_pppoes_ipv4_tcp_l4_mask_in_queue_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 2500 src mask 0xf00 / end actions queue index 3 / end",
    "configuration":{
        "is_non_pipeline":False,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoes_ipv4_tcp_l4_mask_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoes_ipv4_tcp_l4_mask_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":1}}
}

mac_pppoes_ipv6_udp_l4_mask_scapy_str = {
    "matched":[
        'Ether()/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=1282)/Raw("x"*80)'],
    "mismatched": [
        'Ether()/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=1040)/Raw("x"*80)'
    ]
}

tv_mac_pppoes_ipv6_udp_l4_mask_queue_region_03 = {
    "name":"tv_mac_pppoes_ipv6_udp_l4_mask_queue_region_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp dst is 1025 dst mask 0xf0 / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":False,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoes_ipv6_udp_l4_mask_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoes_ipv6_udp_l4_mask_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":1}}
}

mac_pppoes_ipv6_tcp_l4_mask_scapy_str = {
    "matched":[
        'Ether()/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=1282)/Raw("x"*80)'],
    "mismatched": [
        'Ether()/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=1040)/Raw("x"*80)'
    ]
}

tv_mac_pppoes_ipv6_tcp_l4_mask_drop_04 = {
    "name":"tv_mac_pppoes_ipv6_tcp_l4_mask_drop_04",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp dst is 1025 dst mask 0xf0 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":False,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoes_ipv6_tcp_l4_mask_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoes_ipv6_tcp_l4_mask_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tvs_mac_pppoes_l4_mask = [
    tv_mac_pppoes_ipv4_udp_l4_mask_in_queue_01,
    tv_mac_pppoes_ipv4_tcp_l4_mask_in_queue_02,
    tv_mac_pppoes_ipv6_udp_l4_mask_queue_region_03,
    tv_mac_pppoes_ipv6_tcp_l4_mask_drop_04,
]

#vlan non-pipeline mode

mac_vlan_pppoes_ipv4_udp_l4_mask_scapy_str = {
    "matched": [
        'Ether()/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=50,dport=1024)/Raw("x"*80)'],
    "mismatched": [
        'Ether()/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=50,dport=1281)/Raw("x"*80)'
    ]
}

tv_mac_vlan_pppoes_ipv4_udp_l4_mask_in_queue_01 = {
    "name":"tv_mac_vlan_pppoes_ipv4_udp_l4_mask_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp dst is 1280 dst mask 0x00ff / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoes_ipv4_udp_l4_mask_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoes_ipv4_udp_l4_mask_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":1}}
}

mac_vlan_pppoes_ipv4_tcp_l4_mask_scapy_str = {
    "matched": [
        'Ether()/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=50,dport=1024)/Raw("x"*80)'],
    "mismatched": [
        'Ether()/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=50,dport=1281)/Raw("x"*80)'
    ]
}

tv_mac_vlan_pppoes_ipv4_tcp_l4_mask_queue_region_02 = {
    "name":"tv_mac_vlan_pppoes_ipv4_tcp_l4_mask_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp dst is 1280 dst mask 0x00ff / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoes_ipv4_tcp_l4_mask_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoes_ipv4_tcp_l4_mask_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":1}}
}

#vlan pipeline mode
mac_vlan_pppoes_ipv6_udp_l4_mask_scapy_str = {
    "matched":[
        'Ether()/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=16,dport=23)/Raw("x"*80)'],
    "mismatched": [
        'Ether()/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=17,dport=23)/Raw("x"*80)'
    ]
}

tv_mac_vlan_pppoes_ipv6_udp_l4_mask_drop_03 = {
    "name":"tv_mac_vlan_pppoes_ipv6_udp_l4_mask_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 32 src mask 0x0f / end actions drop / end",
    "configuration":{
        "is_non_pipeline":False,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoes_ipv6_udp_l4_mask_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoes_ipv6_udp_l4_mask_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

mac_vlan_pppoes_ipv6_tcp_l4_mask_scapy_str = {
    "matched": [
        'Ether()/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(dport=16)/Raw("x"*80)'],
    "mismatched": [
        'Ether()/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(dport=17)/Raw("x"*80)'
    ]
}

tv_mac_vlan_pppoes_ipv6_tcp_l4_mask_in_queue_04 = {
    "name":"tv_mac_vlan_pppoes_ipv6_tcp_l4_mask_in_queue_04",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp dst is 32 dst mask 0x0f / end actions queue index 7 / end",
    "configuration":{
        "is_non_pipeline":False,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoes_ipv6_tcp_l4_mask_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":7}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoes_ipv6_tcp_l4_mask_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":7}},
                  "expect_results":{"expect_pkts":1}}
}

tvs_mac_vlan_pppoes_l4_mask = [
    tv_mac_vlan_pppoes_ipv4_udp_l4_mask_in_queue_01,
    tv_mac_vlan_pppoes_ipv4_tcp_l4_mask_queue_region_02,
    tv_mac_vlan_pppoes_ipv6_udp_l4_mask_drop_03,
    tv_mac_vlan_pppoes_ipv6_tcp_l4_mask_in_queue_04,

]

#20.08
mac_vlan_pppoe_ipv4_pay_session_id_proto_id_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x"*80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv4_pay_session_id_proto_id_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv4_pay_session_id_proto_id_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id_drop_03 = {
    "name":"tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_vlan_pppoe_ipv4_pay_session_id_proto_id = [
    tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id_in_queue_01,
    tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id_queue_region_02,
    tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id_drop_03
    ]

mac_vlan_pppoe_ipv6_pay_session_id_proto_id_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv6_pay_session_id_proto_id_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv6_pay_session_id_proto_id_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id_drop_03 = {
    "name":"mac_vlan_pppoe_ipv6_pay_session_id_proto_id_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_vlan_pppoe_ipv6_pay_session_id_proto_id = [
    tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id_in_queue_01,
    tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id_queue_region_02,
    tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id_drop_03
    ]

mac_pppoe_ipv4_pay_session_id_proto_id_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipv4_pay_session_id_proto_id_in_queue_01 = {
    "name":"mac_pppoe_ipv4_pay_session_id_proto_id_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_ipv4_pay_session_id_proto_id_queue_region_02 = {
    "name":"mac_pppoe_ipv4_pay_session_id_proto_id_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_ipv4_pay_session_id_proto_id_drop_03 = {
    "name":"mac_pppoe_ipv4_pay_session_id_proto_id_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":3}}
}

tvs_mac_pppoe_ipv4_pay_session_id_proto_id = [
    tv_mac_pppoe_ipv4_pay_session_id_proto_id_in_queue_01,
    tv_mac_pppoe_ipv4_pay_session_id_proto_id_queue_region_02,
    tv_mac_pppoe_ipv4_pay_session_id_proto_id_drop_03
    ]

mac_pppoe_ipv6_pay_session_id_proto_id_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipv6_pay_session_id_proto_id_in_queue_01 = {
    "name":"mac_pppoe_ipv6_pay_session_id_proto_id_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_ipv6_pay_session_id_proto_id_queue_region_02 = {
    "name":"mac_pppoe_ipv6_pay_session_id_proto_id_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_ipv6_pay_session_id_proto_id_drop_03 = {
    "name":"mac_pppoe_ipv6_pay_session_id_proto_id_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_pay_session_id_proto_id_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_pay_session_id_proto_id_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":3}}
}

tvs_mac_pppoe_ipv6_pay_session_id_proto_id = [
    tv_mac_pppoe_ipv6_pay_session_id_proto_id_in_queue_01,
    tv_mac_pppoe_ipv6_pay_session_id_proto_id_queue_region_02,
    tv_mac_pppoe_ipv6_pay_session_id_proto_id_drop_03
    ]

mac_pppoe_ipv4_pay_ip_address_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)'
    ]
}

tv_mac_pppoe_ipv4_pay_ip_address_in_queue_01 = {
    "name":"mac_pppoe_ipv4_pay_ip_address_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_pppoe_ipv4_pay_ip_address_queue_region_02 = {
    "name":"mac_pppoe_ipv4_pay_ip_address_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_pppoe_ipv4_pay_ip_address_drop_03 = {
    "name":"mac_pppoe_ipv4_pay_ip_address_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_pppoe_ipv4_pay_ip_address = [
    tv_mac_pppoe_ipv4_pay_ip_address_in_queue_01,
    tv_mac_pppoe_ipv4_pay_ip_address_queue_region_02,
    tv_mac_pppoe_ipv4_pay_ip_address_drop_03
    ]

mac_pppoe_ipv4_udp_pay_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipv4_udp_pay_in_queue_01 = {
    "name":"mac_pppoe_ipv4_udp_pay_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv4_udp_pay_queue_region_02 = {
    "name":"mac_pppoe_ipv4_udp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[7, 8]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[7, 8]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv4_udp_pay_drop_03 = {
    "name":"mac_pppoe_ipv4_udp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_pppoe_ipv4_udp_pay = [
    tv_mac_pppoe_ipv4_udp_pay_in_queue_01,
    tv_mac_pppoe_ipv4_udp_pay_queue_region_02,
    tv_mac_pppoe_ipv4_udp_pay_drop_03
    ]

mac_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port_in_queue_01 = {
    "name":"mac_pppoe_ipv4_udp_pay_non_src_dst_port_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port_queue_region_02 = {
    "name":"mac_pppoe_ipv4_udp_pay_non_src_dst_port_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port_drop_03 = {
    "name":"mac_pppoe_ipv4_udp_pay_non_src_dst_port_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_pppoe_ipv4_udp_pay_non_src_dst_port = [
    tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port_in_queue_01,
    tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port_queue_region_02,
    tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port_drop_03
    ]

mac_pppoe_ipv4_tcp_pay_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipv4_tcp_pay_in_queue_01 = {
    "name":"mac_pppoe_ipv4_tcp_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv4_tcp_pay_queue_region_02 = {
    "name":"mac_pppoe_ipv4_tcp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[7, 8]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[7, 8]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv4_tcp_pay_drop_03 = {
    "name":"mac_pppoe_ipv4_tcp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_pppoe_ipv4_tcp_pay = [
    tv_mac_pppoe_ipv4_tcp_pay_in_queue_01,
    tv_mac_pppoe_ipv4_tcp_pay_queue_region_02,
    tv_mac_pppoe_ipv4_tcp_pay_drop_03
    ]

mac_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_in_queue_01 = {
    "name":"mac_pppoe_ipv4_tcp_pay_non_src_dst_port_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_queue_region_02 = {
    "name":"mac_pppoe_ipv4_tcp_pay_non_src_dst_port_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[7, 8]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[7, 8]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_drop_03 = {
    "name":"mac_pppoe_ipv4_tcp_pay_non_src_dst_port_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_pppoe_ipv4_tcp_pay_non_src_dst_port = [
    tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_in_queue_01,
    tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_queue_region_02,
    tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_drop_03
    ]

mac_pppoe_ipv6_pay_ip_address_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)'
    ]
}

tv_mac_pppoe_ipv6_pay_ip_address_in_queue_01 = {
    "name":"mac_pppoe_ipv6_pay_ip_address_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_pppoe_ipv6_pay_ip_address_queue_region_02 = {
    "name":"mac_pppoe_ipv6_pay_ip_address_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_pppoe_ipv6_pay_ip_address_drop_03 = {
    "name":"mac_pppoe_ipv6_pay_ip_address_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_pppoe_ipv6_pay_ip_address = [
    tv_mac_pppoe_ipv6_pay_ip_address_in_queue_01,
    tv_mac_pppoe_ipv6_pay_ip_address_queue_region_02,
    tv_mac_pppoe_ipv6_pay_ip_address_drop_03
    ]

mac_pppoe_ipv6_udp_pay_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipv6_udp_pay_in_queue_01 = {
    "name":"mac_pppoe_ipv6_udp_pay_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_ipv6_udp_pay_queue_region_02 = {
    "name":"mac_pppoe_ipv6_udp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_ipv6_udp_pay_drop_03 = {
    "name":"mac_pppoe_ipv6_udp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":3}}
}

tvs_mac_pppoe_ipv6_udp_pay = [
    tv_mac_pppoe_ipv6_udp_pay_in_queue_01,
    tv_mac_pppoe_ipv6_udp_pay_queue_region_02,
    tv_mac_pppoe_ipv6_udp_pay_drop_03
    ]

mac_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port_in_queue_01 = {
    "name":"mac_pppoe_ipv6_udp_pay_non_src_dst_port_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port_queue_region_02 = {
    "name":"mac_pppoe_ipv6_udp_pay_non_src_dst_port_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port_drop_03 = {
    "name":"mac_pppoe_ipv6_udp_pay_non_src_dst_port_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_pppoe_ipv6_udp_pay_non_src_dst_port = [
    tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port_in_queue_01,
    tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port_queue_region_02,
    tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port_drop_03
    ]

mac_pppoe_ipv6_tcp_pay_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipv6_tcp_pay_in_queue_01 = {
    "name":"mac_pppoe_ipv6_tcp_pay_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_ipv6_tcp_pay_queue_region_02 = {
    "name":"mac_pppoe_ipv6_tcp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_ipv6_tcp_pay_drop_03 = {
    "name":"mac_pppoe_ipv6_tcp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":3}}
}

tvs_mac_pppoe_ipv6_tcp_pay = [
    tv_mac_pppoe_ipv6_tcp_pay_in_queue_01,
    tv_mac_pppoe_ipv6_tcp_pay_queue_region_02,
    tv_mac_pppoe_ipv6_tcp_pay_drop_03
    ]

mac_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_in_queue_01 = {
    "name":"mac_pppoe_ipv6_tcp_pay_non_src_dst_port_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_queue_region_02 = {
    "name":"mac_pppoe_ipv6_tcp_pay_non_src_dst_port_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_drop_03 = {
    "name":"mac_pppoe_ipv6_tcp_pay_non_src_dst_port_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_pppoe_ipv6_tcp_pay_non_src_dst_port = [
    tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_in_queue_01,
    tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_queue_region_02,
    tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_drop_03
    ]

mac_vlan_pppoe_ipv4_pay_ip_address_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)'
    ]
}

tv_mac_vlan_pppoe_ipv4_pay_ip_address_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv4_pay_ip_address_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_vlan_pppoe_ipv4_pay_ip_address_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv4_pay_ip_address_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_vlan_pppoe_ipv4_pay_ip_address_drop_03 = {
    "name":"mac_vlan_pppoe_ipv4_pay_ip_address_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":3}}
}

tvs_mac_vlan_pppoe_ipv4_pay_ip_address = [
    tv_mac_vlan_pppoe_ipv4_pay_ip_address_in_queue_01,
    tv_mac_vlan_pppoe_ipv4_pay_ip_address_queue_region_02,
    tv_mac_vlan_pppoe_ipv4_pay_ip_address_drop_03
    ]

mac_vlan_pppoe_ipv4_udp_pay_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipv4_udp_pay_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv4_udp_pay",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_vlan_pppoe_ipv4_udp_pay_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv4_udp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[7, 8]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[7, 8]}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_vlan_pppoe_ipv4_udp_pay_drop_03 = {
    "name":"mac_vlan_pppoe_ipv4_udp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":5}}
}

tvs_mac_vlan_pppoe_ipv4_udp_pay = [
    tv_mac_vlan_pppoe_ipv4_udp_pay_in_queue_01,
    tv_mac_vlan_pppoe_ipv4_udp_pay_queue_region_02,
    tv_mac_vlan_pppoe_ipv4_udp_pay_drop_03
    ]

mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 7 8 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 7 8 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[7, 8]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[7, 8]}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_drop_03 = {
    "name":"mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":5}}
}

tvs_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port = [
    tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_in_queue_01,
    tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_queue_region_02,
    tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_drop_03
    ]

mac_vlan_pppoe_ipv4_tcp_pay_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipv4_tcp_pay_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv4_tcp_pay_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_vlan_pppoe_ipv4_tcp_pay_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv4_tcp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[7, 8]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[7, 8]}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_vlan_pppoe_ipv4_tcp_pay_drop_03 = {
    "name":"mac_vlan_pppoe_ipv4_tcp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":5}}
}

tvs_mac_vlan_pppoe_ipv4_tcp_pay = [
    tv_mac_vlan_pppoe_ipv4_tcp_pay_in_queue_01,
    tv_mac_vlan_pppoe_ipv4_tcp_pay_queue_region_02,
    tv_mac_vlan_pppoe_ipv4_tcp_pay_drop_03
    ]

mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str = {
    "matched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[7, 8]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[7, 8]}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_drop_03 = {
    "name":"mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":5}}
}

tvs_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port = [
    tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_in_queue_01,
    tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_queue_region_02,
    tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_drop_03
    ]

mac_vlan_pppoe_ipv6_pay_ip_address_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'
    ]
}

tv_mac_vlan_pppoe_ipv6_pay_ip_address_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv6_pay_ip_address_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_vlan_pppoe_ipv6_pay_ip_address_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv6_pay_ip_address_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_vlan_pppoe_ipv6_pay_ip_address_drop_03 = {
    "name":"mac_vlan_pppoe_ipv6_pay_ip_address_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_ip_address_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_pay_ip_address_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_vlan_pppoe_ipv6_pay_ip_address = [
    tv_mac_vlan_pppoe_ipv6_pay_ip_address_in_queue_01,
    tv_mac_vlan_pppoe_ipv6_pay_ip_address_queue_region_02,
    tv_mac_vlan_pppoe_ipv6_pay_ip_address_drop_03
    ]

mac_vlan_pppoe_ipv6_udp_pay_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipv6_udp_pay_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv6_udp_pay_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv6_udp_pay_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv6_udp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv6_udp_pay_drop_03 = {
    "name":"mac_vlan_pppoe_ipv6_udp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_vlan_pppoe_ipv6_udp_pay = [
    tv_mac_vlan_pppoe_ipv6_udp_pay_in_queue_01,
    tv_mac_vlan_pppoe_ipv6_udp_pay_queue_region_02,
    tv_mac_vlan_pppoe_ipv6_udp_pay_drop_03
    ]

mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_drop_03 = {
    "name":"mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port = [
    tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_in_queue_01,
    tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_queue_region_02,
    tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_drop_03
    ]

mac_vlan_pppoe_ipv6_tcp_pay_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipv6_tcp_pay_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv6_tcp_pay_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv6_tcp_pay_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv6_tcp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv6_tcp_pay_drop_03 = {
    "name":"mac_vlan_pppoe_ipv6_tcp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_vlan_pppoe_ipv6_tcp_pay = [
    tv_mac_vlan_pppoe_ipv6_tcp_pay_in_queue_01,
    tv_mac_vlan_pppoe_ipv6_tcp_pay_queue_region_02,
    tv_mac_vlan_pppoe_ipv6_tcp_pay_drop_03
    ]

mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_drop_03 = {
    "name":"mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":False},
    "matched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port = [
    tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_in_queue_01,
    tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_queue_region_02,
    tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_drop_03
    ]

mac_pppoe_lcp_pay_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_lcp_pay_in_queue_01 = {
    "name":"mac_pppoe_lcp_pay_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_pppoe_lcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_lcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_lcp_pay_queue_region_02 = {
    "name":"mac_pppoe_lcp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_pppoe_lcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_lcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_lcp_pay_drop_03 = {
    "name":"mac_pppoe_lcp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_pppoe_lcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_lcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":3}}
}

tvs_mac_pppoe_lcp_pay = [
    tv_mac_pppoe_lcp_pay_in_queue_01,
    tv_mac_pppoe_lcp_pay_queue_region_02,
    tv_mac_pppoe_lcp_pay_drop_03
    ]

mac_pppoe_ipcp_pay_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'
    ]
}

tv_mac_pppoe_ipcp_pay_in_queue_01 = {
    "name":"mac_pppoe_ipcp_pay_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_pppoe_ipcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_ipcp_pay_queue_region_02 = {
    "name":"mac_pppoe_ipcp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_pppoe_ipcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_pppoe_ipcp_pay_drop_03 = {
    "name":"mac_pppoe_ipcp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_pppoe_ipcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_pppoe_ipcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":3}}
}

tvs_mac_pppoe_ipcp_pay = [
    tv_mac_pppoe_ipcp_pay_in_queue_01,
    tv_mac_pppoe_ipcp_pay_queue_region_02,
    tv_mac_pppoe_ipcp_pay_drop_03
    ]

mac_vlan_pppoe_lcp_pay_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_lcp_pay_in_queue_01 = {
    "name":"mac_vlan_pppoe_lcp_pay_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_vlan_pppoe_lcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_lcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_lcp_pay_queue_region_02 = {
    "name":"mac_vlan_pppoe_lcp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_vlan_pppoe_lcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_lcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_lcp_pay_drop_03 = {
    "name":"mac_vlan_pppoe_lcp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_vlan_pppoe_lcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_lcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_vlan_pppoe_lcp_pay = [
    tv_mac_vlan_pppoe_lcp_pay_in_queue_01,
    tv_mac_vlan_pppoe_lcp_pay_queue_region_02,
    tv_mac_vlan_pppoe_lcp_pay_drop_03
    ]

mac_vlan_pppoe_ipcp_pay_scapy_str = {
    "matched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'],
    "mismatched": [
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
        'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'
    ]
}

tv_mac_vlan_pppoe_ipcp_pay_in_queue_01 = {
    "name":"mac_vlan_pppoe_ipcp_pay_in_queue_01",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_vlan_pppoe_ipcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipcp_pay_queue_region_02 = {
    "name":"mac_vlan_pppoe_ipcp_pay_queue_region_02",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_vlan_pppoe_ipcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_vlan_pppoe_ipcp_pay_drop_03 = {
    "name":"mac_vlan_pppoe_ipcp_pay_drop_03",
    "validate_pattern":"flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end",
    "configuration":{
        "is_non_pipeline":True,
        "is_need_rss_rule":True},
    "matched":{"scapy_str":mac_vlan_pppoe_ipcp_pay_scapy_str["matched"],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":mac_vlan_pppoe_ipcp_pay_scapy_str["mismatched"],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_vlan_pppoe_ipcp_pay = [
    tv_mac_vlan_pppoe_ipcp_pay_in_queue_01,
    tv_mac_vlan_pppoe_ipcp_pay_queue_region_02,
    tv_mac_vlan_pppoe_ipcp_pay_drop_03
    ]

test_results = OrderedDict()

class CVLSwitchFilterPPPOETest(TestCase):

    def bind_nics_driver(self, ports, driver=""):
        # modprobe vfio driver
        if driver == "vfio-pci":
            for port in ports:
                netdev = self.dut.ports_info[port]['port']
                driver = netdev.get_nic_driver()
                if driver != 'vfio-pci':
                    netdev.bind_driver(driver='vfio-pci')

        elif driver == "igb_uio":
            # igb_uio should insmod as default, no need to check
            for port in ports:
                netdev = self.dut.ports_info[port]['port']
                driver = netdev.get_nic_driver()
                if driver != 'igb_uio':
                    netdev.bind_driver(driver='igb_uio')
        else:
            for port in ports:
                netdev = self.dut.ports_info[port]['port']
                driver_now = netdev.get_nic_driver()
                if driver == "":
                    driver = netdev.default_driver
                if driver != driver_now:
                    netdev.bind_driver(driver=driver)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(self.nic in ["columbiaville_25g","columbiaville_100g"], "%s nic not support CVL switch filter" % self.nic)
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.__tx_iface = self.tester.get_interface(localPort)
        self.dut.send_expect("ifconfig %s up" % self.__tx_iface, "# ")
        self.pkt = Packet()
        self.pmd = PmdOutput(self.dut)

        self.generate_file_with_fdir_rules()
        self.path = self.dut.apps_name['test-pmd']

    def set_up(self):
        """
        Run before each test case.
        """
        self.reload_ice()

    def reload_ice(self):
        self.dut.send_expect("rmmod ice", "# ", 15)
        self.dut.send_expect("modprobe ice", "# ", 15)

    def generate_file_with_fdir_rules(self):
        """
        generate file with fdir rules to make fdir table full, then test switch filter
        """
        pf_pci = self.dut.ports_info[0]['pci']
        out = self.pmd.start_testpmd('default', eal_param='-a %s --log-level=ice,7'%pf_pci)
        self.dut.send_expect("quit", "# ")
        self.fdir_rule_number = self.pmd.get_max_rule_number(self,out)
        src_file = 'dep/testpmd_cmds_rte_flow_fdir_rules'
        flows = open(src_file, mode='w')
        rule_count = 1
        for i in range(0,255):
            for j in range(0,255):
                if not rule_count > self.fdir_rule_number:
                    flows.write('flow create 0 ingress pattern eth / ipv4 src is 192.168.%d.%d dst is 192.1.0.0 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 5 / end \n' % (i, j))
                    rule_count += 1
                else:
                    break
            if rule_count > self.fdir_rule_number:
                break
        flows.close()
        self.dut_file_dir = '/tmp'
        self.dut.session.copy_file_to(src_file, self.dut_file_dir)
        self.fdir_file = "/tmp/testpmd_cmds_rte_flow_fdir_rules"

    def create_testpmd_command(self):
        """
        Create testpmd command for non-pipeline mode
        """
        #Prepare testpmd EAL and parameters
        all_eal_param = self.dut.create_eal_parameters(cores='1S/4C/1T', ports=[0])
        command = self.path + all_eal_param + " --log-level=\"ice,8\" -- -i --rxq=16 --txq=16 --cmdline-file=%s" % self.fdir_file
        # command = "./%s/app/testpmd %s --log-level=\"ice,8\" -- -i %s" % (self.dut.target, all_eal_param, "--rxq=16 --txq=16")
        return command

    def create_testpmd_command_pipeline_mode(self):
        """
        Create testpmd command for pipeline mode
        """
        #Prepare testpmd EAL and parameters
        all_eal_param = self.dut.create_eal_parameters(cores='1S/4C/1T', ports=[0], port_options={0:"pipeline-mode-support=1"})
        command = self.path + all_eal_param + " --log-level=\"ice,8\" -- -i --rxq=16 --txq=16"
        return command

    def launch_testpmd(self, is_non_pipeline):
        """
        launch testpmd with the command
        """
        if is_non_pipeline:
            command = self.create_testpmd_command()
        else:
            command = self.create_testpmd_command_pipeline_mode()
        out = self.dut.send_expect(command, "testpmd> ", 300)
        self.dut.send_expect("port config all rss all", "testpmd> ", 15)
        self.dut.send_expect("port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd", "testpmd> ", 15)
        self.dut.send_expect("rx_vxlan_port add 4789 0", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)

    def send_and_check_packets(self, dic, port):
        """
        general packets processing workflow.
        """
        #Specify the port to use
        dic["check_func"]["param"]["expect_port"] = port
        self.dut.send_expect("start", "testpmd> ", 15)
        time.sleep(2)
        #send packets
        self.pkt.update_pkt(dic["scapy_str"])
        self.pkt.send_pkt(self.tester, tx_port=self.__tx_iface, count=1, timeout=370)
        time.sleep(3)
        out = self.dut.send_expect("stop", "testpmd> ", 15)
        result_flag, log_msg = dic["check_func"]["func"](out, dic["check_func"]["param"], dic["expect_results"])
        return result_flag, log_msg

    def send_packet_get_queue(self, packets_list):
        """
        general packets processing workflow.
        """
        self.dut.send_expect("start", "testpmd> ")
        # send packets
        self.pkt.update_pkt(packets_list)
        self.pkt.send_pkt(self.tester, tx_port=self.__tx_iface, count=1, timeout=370)
        time.sleep(3)
        out = self.dut.send_expect("stop", "testpmd> ", 15)
        p = re.compile(r"Forward Stats for RX Port= \d+/Queue=(\s?\d+)")
        res = p.findall(out)
        default_queue = [int(i) for i in res]
        return default_queue

    def get_available_queue_num(self, default_queue, expect_queue, pmd_queue=8):
        """
        general packets processing workflow.
        """
        queue_list = list(range(1, pmd_queue))
        # check if expect_queue length is power of 2
        q_len = len(expect_queue)
        self.verify(q_len & (q_len - 1) == 0, "default_queue length is not power of 2!")
        for q in default_queue:
            if q in queue_list:
                queue_list.remove(q)
        if queue_list == []:
            return []
        # according to expect_queue length get available queue
        set_queue_list = []
        if q_len == 1:
            set_queue = random.choice(queue_list)
            set_queue_list.append(set_queue)
        else:
            fun = lambda x: x[1] - x[0]
            for k, g in groupby(enumerate(queue_list), fun):
                list_group = [j for i, j in g]
                if len(list_group) >= q_len:
                    set_queue_list = list_group[:q_len]
                    break
        return set_queue_list

    def create_switch_filter_rule(self, rte_flow_pattern, pattern_name="", overall_result=True, check_stats=True):
        """
        create switch filter rules
        """
        s = "Succeeded to create (2) flow"
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        if isinstance(rte_flow_pattern, list):
            for rule in rte_flow_pattern:
                out = self.dut.send_expect(rule, "testpmd> ")  #create a rule
                if s not in out:
                    rule_list.append(False)
                else:
                    m = p.search(out)
                    if m:
                        rule_list.append(m.group(1))
                    else:
                        rule_list.append(False)
        elif isinstance(rte_flow_pattern, str):
            out = self.dut.send_expect(rte_flow_pattern, "testpmd> ")  # create a rule
            if s not in out:
                rule_list.append(False)
            else:
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            if all(rule_list):
                result_flag = True
                log_msg = ""
            else:
                result_flag = False
                log_msg = "some rules not created successfully, result %s, rule %s" % (rule_list, rte_flow_pattern)
            overall_result = self.save_results(pattern_name, "create rule", result_flag, log_msg, overall_result)
            return result_flag, overall_result, rule_list
        else:
            return rule_list

    def validate_switch_filter_rule(self, rte_flow_pattern, pattern_name="", overall_result=True, check_stats=True):
        # validate rule.
        p = "Flow rule validated"
        rule_list = []
        if isinstance(rte_flow_pattern, list):
            for i in rte_flow_pattern:
                length = len(i)
                rule_rep = i[0:5] + "validate" + i[11:length]
                out = self.dut.send_expect(rule_rep, "testpmd> ")  #validate a rule
                if (p in out) and ("Failed" not in out):
                    rule_list.append(True)
                else:
                    rule_list.append(False)
        elif isinstance(rte_flow_pattern, str):
            length = len(rte_flow_pattern)
            rule_rep = rte_flow_pattern[0:5] + "validate" + rte_flow_pattern[11:length]
            out = self.dut.send_expect(rule_rep, "testpmd> ")  #validate a rule
            if (p in out) and ("Failed" not in out):
                rule_list.append(True)
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            if all(rule_list):
                result_flag = True
                log_msg = ""
            else:
                result_flag = False
                log_msg = "some rules not validated successfully, result %s, rule %s" % (rule_list, rte_flow_pattern)
            overall_result = self.save_results(pattern_name, "validate rule", result_flag, log_msg, overall_result)
            return result_flag, overall_result
        else:
            return rule_list

    def check_switch_filter_rule_list(self, port_id, rule_list=[], is_non_pipeline=True, is_need_rss_rule=True, pattern_name="", overall_result="", flag="", check_stats=True):
        """
        check the rules in list identical to ones in rule_list
        """
        out = self.dut.send_expect("flow list %d" % port_id, "testpmd> ", 15)
        p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
        m = p.search(out)
        if not m:
            result = []
        else:
            p_spec = re.compile("^(\d+)\s")
            out_lines = out.splitlines()
            res = filter(bool, map(p_spec.match, out_lines))
            result = [i.group(1) for i in res]
            if is_non_pipeline:
                #remove 15360 fdir rules id
                del result[:self.fdir_rule_number]
            if is_need_rss_rule:
                #remove rss rule id
                del result[0]
        if check_stats:
            if result == rule_list:
                result_flag = True
                log_msg = ""
            else:
                result_flag = False
                log_msg = "the rule list is not the same. expect %s, result %s" % (rule_list, result)
            overall_result = self.save_results(pattern_name, "check rule list after "+flag, result_flag, log_msg, overall_result)
            return result_flag, overall_result
        else:
            return result

    def destroy_switch_filter_rule(self, port_id, rule_list, pattern_name="", overall_result=True, check_stats=True):
        p = re.compile(r"Flow rule #(\d+) destroyed")
        destroy_list = []
        if isinstance(rule_list, list):
            for i in rule_list:
                out = self.dut.send_expect("flow destroy %s rule %s" % (port_id, i), "testpmd> ", 15)
                m = p.search(out)
                if m:
                    destroy_list.append(m.group(1))
                else:
                    destroy_list.append(False)
        else:
            out = self.dut.send_expect("flow destroy %s rule %s" % (port_id, rule_list), "testpmd> ", 15)
            m = p.search(out)
            if m:
                destroy_list.append(m.group(1))
            else:
                destroy_list.append(False)
            rule_list = [rule_list]
        if check_stats:
            if sorted(destroy_list) == sorted(rule_list):
                    result_flag = True
                    log_msg = ""
            else:
                result_flag = False
                log_msg = "flow rule destroy failed, expect %s result %s" % (rule_list, destroy_list)
            overall_result = self.save_results(pattern_name, "destroy rule list", result_flag, log_msg, overall_result)
            return result_flag, overall_result
        else:
            return destroy_list

    def save_results(self, pattern_name, flag, result_flag, log_msg, overall_result):
        """
        save results to dictionary: test_results.
        """
        global test_results

        test_results[pattern_name][flag] = {}
        test_results[pattern_name][flag]["result_flag"] = result_flag
        test_results[pattern_name][flag]["log_msg"] = log_msg
        overall_result = overall_result and result_flag
        return overall_result

    def display_results(self):
        global test_results
        #print the results of the test case
        count = 1
        for pattern in list(test_results.keys()):
            print(str(count)+". "+pattern)
            for flag in list(test_results[pattern].keys()):
                result_flag = test_results[pattern][flag]["result_flag"]
                log_msg = test_results[pattern][flag]["log_msg"]
                print(flag+": ", end=' ')
                result = ""
                if result_flag:
                    result = "Passed"
                    print(GREEN(result), log_msg)
                else:
                    result = "failed"
                    print(RED(result+", "+log_msg))
            print()
            count += 1

    def check_and_reset_queues(self, tv, default_queue, pattern_name, overall_result):
        # check if default_queue and queues in rule have intersection
        expect_queue = tv["matched"]["check_func"]["param"]["expect_queues"]
        if expect_queue != "null":
            if isinstance(expect_queue, int):
                eq_list = []
                eq_list.append(expect_queue)
            elif isinstance(expect_queue, list):
                eq_list = expect_queue
            recover_flag = list(set(eq_list) & set(default_queue))
        else:
            recover_flag = None
        # if default_queue has intersection with expect_queue, reset queues
        if recover_flag:
            # exclude default_queue and get set_queue
            set_queue_list = self.get_available_queue_num(default_queue, eq_list, 16)
            if not set_queue_list:
                result_flag = False
                log_msg = "No enough queues to avoid default_queue. Please give more queues when launch testpmd."
                overall_result = self.save_results(pattern_name, "get queues", result_flag, log_msg, overall_result)
                return result_flag, overall_result, tv
            # reset queues in the rule
            if isinstance(expect_queue, int):
                rule_command = tv["rte_flow_pattern"].replace("/ end actions queue index %s" % str(expect_queue),
                                                              "/ end actions queue index %s" % str(set_queue_list[0]))
                tv["matched"]["check_func"]["param"]["expect_queues"] = set_queue_list[0]
                tv["mismatched"]["check_func"]["param"]["expect_queues"] = set_queue_list[0]
            elif isinstance(expect_queue, list):
                q = [str(i) for i in expect_queue]
                expect_queue_str = " ".join(q)
                s = [str(i) for i in set_queue_list]
                set_queue_str = " ".join(s)
                rule_command = tv["rte_flow_pattern"].replace("/ end actions rss queues %s" % expect_queue_str,
                                                              "/ end actions rss queues %s" % set_queue_str)
                tv["matched"]["check_func"]["param"]["expect_queues"] = set_queue_list
                tv["mismatched"]["check_func"]["param"]["expect_queues"] = set_queue_list
            tv["rte_flow_pattern"] = rule_command
        return True, overall_result, tv

    def _rte_flow_validate_pattern(self, test_vectors, launch_testpmd=True):

        global test_results
        is_non_pipeline = test_vectors[0]["configuration"]["is_non_pipeline"]
        is_need_rss_rule = test_vectors[0]["configuration"]["is_need_rss_rule"]
        if launch_testpmd:
            #launch testpmd
            self.launch_testpmd(is_non_pipeline)
        test_results.clear()
        overall_result = True
        count = 1
        for tv in test_vectors:
            pattern_name = tv["name"]
            test_results[pattern_name] = OrderedDict()
            # get the queues that packets originally came to
            if count == 1:
                packets_list  = tv["matched"]["scapy_str"] + tv["mismatched"]["scapy_str"]
                default_queue = self.send_packet_get_queue(packets_list)
            count += 1
            result_flag, overall_result, tv = self.check_and_reset_queues(tv, default_queue, pattern_name, overall_result)
            if not result_flag:
                continue

            #validate a rule
            result_flag, overall_result = self.validate_switch_filter_rule(tv["rte_flow_pattern"], pattern_name, overall_result)
            if not result_flag:
                continue
            result_flag, overall_result = self.check_switch_filter_rule_list(self.dut_ports[0], [], is_non_pipeline, is_need_rss_rule, pattern_name, overall_result, "validate")
            if not result_flag:
                continue
            #create a rule
            result_flag, overall_result, rule_list = self.create_switch_filter_rule(tv["rte_flow_pattern"], pattern_name, overall_result)   #create a rule
            if not result_flag:
                continue
            result_flag, overall_result = self.check_switch_filter_rule_list(self.dut_ports[0], rule_list, is_non_pipeline, is_need_rss_rule, pattern_name, overall_result, "create")
            if not result_flag:
                continue
            #send matched packets and check
            matched_dic = tv["matched"]
            result_flag, log_msg = self.send_and_check_packets(matched_dic, self.dut_ports[0])
            overall_result = self.save_results(pattern_name, "matched packets", result_flag, log_msg, overall_result)
            #send mismatched packets and check
            mismatched_dic = tv["mismatched"]
            if len(list(mismatched_dic.keys())) != 0:
                result_flag, log_msg = self.send_and_check_packets(mismatched_dic, self.dut_ports[0])
                overall_result = self.save_results(pattern_name, "mismatched", result_flag, log_msg, overall_result)
            #destroy rule and send matched packets
            result_flag, overall_result = self.destroy_switch_filter_rule(0, rule_list, pattern_name, overall_result)
            if not result_flag:
                continue
            result_flag, overall_result = self.check_switch_filter_rule_list(self.dut_ports[0], [], is_non_pipeline, is_need_rss_rule, pattern_name, overall_result, "destroy")
            if not result_flag:
                continue
            #send matched packets and check
            check_destroy_dict = copy.deepcopy(matched_dic)
            check_destroy_dict["check_func"]["func"] = mismatched_dic["check_func"]["func"]
            result_flag, log_msg = self.send_and_check_packets(check_destroy_dict, self.dut_ports[0])
            overall_result = self.save_results(pattern_name, "matched packets after destroying", result_flag, log_msg, overall_result)
        self.display_results()
        self.verify(overall_result == True, "Some subcase failed.")

    def test_ethertype_filter_pppoes_pipeline_mode(self):
        tvs_ethertype_filter_pppoes_pipeline_mode = copy.deepcopy(tvs_ethertype_filter_pppoes)
        for tv in tvs_ethertype_filter_pppoes_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        #launch testpmd
        self.launch_testpmd(False)
        #create a pppoe rss rule to make the pppoe packets have hash value, and queue group action work
        self.dut.send_expect("flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tvs_ethertype_filter_pppoes_pipeline_mode, False)

    def test_ethertype_filter_pppoes(self):
        #launch testpmd
        self.launch_testpmd(True)
        #create a pppoe rss rule to make the pppoe packets have hash value, and queue group action work
        self.dut.send_expect("flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tvs_ethertype_filter_pppoes, False)

    #l4 mask
    def test_mac_pppoes_l4_mask(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoes_l4_mask)

    def test_mac_vlan_pppoes_l4_mask(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoes_l4_mask)


    # 20.08
    def test_mac_vlan_pppoe_ipv4_pay_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_pay_session_id_proto_id)

    def test_mac_vlan_pppoe_ipv6_pay_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_pay_session_id_proto_id)

    def test_mac_pppoe_ipv4_pay_session_id_proto_id_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_pay_session_id_proto_id)

    def test_mac_pppoe_ipv6_pay_session_id_proto_id_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_pay_session_id_proto_id)

    def test_mac_pppoe_ipv4_pay_ip_address_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_pay_ip_address)

    def test_mac_pppoe_ipv4_udp_pay_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_udp_pay)

    def test_mac_pppoe_ipv4_udp_pay_non_src_dst_port_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_udp_pay_non_src_dst_port)

    def test_mac_pppoe_ipv4_tcp_pay_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_tcp_pay)

    def test_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_tcp_pay_non_src_dst_port)

    def test_mac_pppoe_ipv6_pay_ip_address_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_pay_ip_address)

    def test_mac_pppoe_ipv6_udp_pay_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_udp_pay)

    def test_mac_pppoe_ipv6_udp_pay_non_src_dst_port_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_udp_pay_non_src_dst_port)

    def test_mac_pppoe_ipv6_tcp_pay_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_tcp_pay)

    def test_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_tcp_pay_non_src_dst_port)

    def test_mac_vlan_pppoe_ipv4_pay_ip_address_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_pay_ip_address)

    def test_mac_vlan_pppoe_ipv4_udp_pay_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_udp_pay)

    def test_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port)

    def test_mac_vlan_pppoe_ipv4_tcp_pay_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_tcp_pay)

    def test_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port)

    def test_mac_vlan_pppoe_ipv6_pay_ip_address_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_pay_ip_address)

    def test_mac_vlan_pppoe_ipv6_udp_pay_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_udp_pay)

    def test_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port)

    def test_mac_vlan_pppoe_ipv6_tcp_pay_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_tcp_pay)

    def test_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_non_pipeline_mode(self):
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port)

    # pppoe control
    def test_mac_pppoe_lcp_pay_non_pipeline_mode(self):
        #launch testpmd
        self.launch_testpmd(True)
        #create a pppoe rss rule to make the pppoe control have hash value, and queue group action work
        self.dut.send_expect("flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tvs_mac_pppoe_lcp_pay, False)

    def test_mac_pppoe_ipcp_pay_non_pipeline_mode(self):
        #launch testpmd
        self.launch_testpmd(True)
        #create a pppoe rss rule to make the pppoe control have hash value, and queue group action work
        self.dut.send_expect("flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipcp_pay, False)

    def test_mac_vlan_pppoe_lcp_pay_non_pipeline_mode(self):
        #launch testpmd
        self.launch_testpmd(True)
        #create a pppoe rss rule to make the pppoe control have hash value, and queue group action work
        self.dut.send_expect("flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_lcp_pay, False)

    def test_mac_vlan_pppoe_ipcp_pay_non_pipeline_mode(self):
        #launch testpmd
        self.launch_testpmd(True)
        #create a pppoe rss rule to make the pppoe control have hash value, and queue group action work
        self.dut.send_expect("flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipcp_pay, False)

    # 20.08 pipeline mode
    def test_mac_vlan_pppoe_ipv4_pay_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv4_pay_session_id_proto_id_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv4_pay_session_id_proto_id)
        for tv in tvs_mac_vlan_pppoe_ipv4_pay_session_id_proto_id_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_pay_session_id_proto_id_pipeline_mode)

    def test_mac_vlan_pppoe_ipv6_pay_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv6_pay_session_id_proto_id_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv6_pay_session_id_proto_id)
        for tv in tvs_mac_vlan_pppoe_ipv6_pay_session_id_proto_id_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_pay_session_id_proto_id_pipeline_mode)

    def test_mac_pppoe_ipv4_pay_session_id_proto_id_pipeline_mode(self):
        tvs_mac_pppoe_ipv4_pay_session_id_proto_id_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv4_pay_session_id_proto_id)
        for tv in tvs_mac_pppoe_ipv4_pay_session_id_proto_id_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_pay_session_id_proto_id_pipeline_mode)

    def test_mac_pppoe_ipv6_pay_session_id_proto_id_pipeline_mode(self):
        tvs_mac_pppoe_ipv6_pay_session_id_proto_id_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv6_pay_session_id_proto_id)
        for tv in tvs_mac_pppoe_ipv6_pay_session_id_proto_id_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_pay_session_id_proto_id_pipeline_mode)

    def test_mac_pppoe_ipv4_pay_ip_address_pipeline_mode(self):
        tvs_mac_pppoe_ipv4_pay_ip_address_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv4_pay_ip_address)
        for tv in tvs_mac_pppoe_ipv4_pay_ip_address_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_pay_ip_address_pipeline_mode)

    def test_mac_pppoe_ipv4_udp_pay_pipeline_mode(self):
        tvs_mac_pppoe_ipv4_udp_pay_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv4_udp_pay)
        for tv in tvs_mac_pppoe_ipv4_udp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_udp_pay_pipeline_mode)

    def test_mac_pppoe_ipv4_udp_pay_non_src_dst_port_pipeline_mode(self):
        tvs_mac_pppoe_ipv4_udp_pay_non_src_dst_port_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv4_udp_pay_non_src_dst_port)
        for tv in tvs_mac_pppoe_ipv4_udp_pay_non_src_dst_port_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_udp_pay_non_src_dst_port_pipeline_mode)

    def test_mac_pppoe_ipv4_tcp_pay_pipeline_mode(self):
        tvs_mac_pppoe_ipv4_tcp_pay_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv4_tcp_pay)
        for tv in tvs_mac_pppoe_ipv4_tcp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_tcp_pay_pipeline_mode)

    def test_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_pipeline_mode(self):
        tvs_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv4_tcp_pay_non_src_dst_port)
        for tv in tvs_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_tcp_pay_non_src_dst_port_pipeline_mode)

    def test_mac_pppoe_ipv6_pay_ip_address_pipeline_mode(self):
        tvs_mac_pppoe_ipv6_pay_ip_address_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv6_pay_ip_address)
        for tv in tvs_mac_pppoe_ipv6_pay_ip_address_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_pay_ip_address_pipeline_mode)

    def test_mac_pppoe_ipv6_udp_pay_pipeline_mode(self):
        tvs_mac_pppoe_ipv6_udp_pay_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv6_udp_pay)
        for tv in tvs_mac_pppoe_ipv6_udp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_udp_pay_pipeline_mode)

    def test_mac_pppoe_ipv6_udp_pay_non_src_dst_port_pipeline_mode(self):
        tvs_mac_pppoe_ipv6_udp_pay_non_src_dst_port_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv6_udp_pay_non_src_dst_port)
        for tv in tvs_mac_pppoe_ipv6_udp_pay_non_src_dst_port_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_udp_pay_non_src_dst_port_pipeline_mode)

    def test_mac_pppoe_ipv6_tcp_pay_pipeline_mode(self):
        tvs_mac_pppoe_ipv6_tcp_pay_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv6_tcp_pay)
        for tv in tvs_mac_pppoe_ipv6_tcp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_tcp_pay_pipeline_mode)

    def test_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_pipeline_mode(self):
        tvs_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv6_tcp_pay_non_src_dst_port)
        for tv in tvs_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_tcp_pay_non_src_dst_port_pipeline_mode)

    def test_mac_vlan_pppoe_ipv4_pay_ip_address_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv4_pay_ip_address_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv4_pay_ip_address)
        for tv in tvs_mac_vlan_pppoe_ipv4_pay_ip_address_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_pay_ip_address_pipeline_mode)

    def test_mac_vlan_pppoe_ipv4_udp_pay_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv4_udp_pay_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv4_udp_pay)
        for tv in tvs_mac_vlan_pppoe_ipv4_udp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_udp_pay_pipeline_mode)

    def test_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port)
        for tv in tvs_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port_pipeline_mode)

    def test_mac_vlan_pppoe_ipv4_tcp_pay_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv4_tcp_pay_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv4_tcp_pay)
        for tv in tvs_mac_vlan_pppoe_ipv4_tcp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_tcp_pay_pipeline_mode)

    def test_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port)
        for tv in tvs_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port_pipeline_mode)

    def test_mac_vlan_pppoe_ipv6_pay_ip_address_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv6_pay_ip_address_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv6_pay_ip_address)
        for tv in tvs_mac_vlan_pppoe_ipv6_pay_ip_address_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_pay_ip_address_pipeline_mode)

    def test_mac_vlan_pppoe_ipv6_udp_pay_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv6_udp_pay_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv6_udp_pay)
        for tv in tvs_mac_vlan_pppoe_ipv6_udp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_udp_pay_pipeline_mode)

    def test_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port)
        for tv in tvs_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port_pipeline_mode)

    def test_mac_vlan_pppoe_ipv6_tcp_pay_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv6_tcp_pay_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv6_tcp_pay)
        for tv in tvs_mac_vlan_pppoe_ipv6_tcp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_tcp_pay_pipeline_mode)

    def test_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port)
        for tv in tvs_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port_pipeline_mode)

    # 20.08 pppoe control
    def test_mac_pppoe_lcp_pay_pipeline_mode(self):
        tvs_mac_pppoe_lcp_pay_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_lcp_pay)
        for tv in tvs_mac_pppoe_lcp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        #launch testpmd
        self.launch_testpmd(False)
        #create a pppoe rss rule to make the pppoe control have hash value, and queue group action work
        self.dut.send_expect("flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tvs_mac_pppoe_lcp_pay_pipeline_mode, False)

    def test_mac_pppoe_ipcp_pay_pipeline_mode(self):
        tvs_mac_pppoe_ipcp_pay_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipcp_pay)
        for tv in tvs_mac_pppoe_ipcp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        #launch testpmd
        self.launch_testpmd(False)
        #create a pppoe rss rule to make the pppoe control have hash value, and queue group action work
        self.dut.send_expect("flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipcp_pay_pipeline_mode, False)

    def test_mac_vlan_pppoe_lcp_pay_pipeline_mode(self):
        tvs_mac_vlan_pppoe_lcp_pay_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_lcp_pay)
        for tv in tvs_mac_vlan_pppoe_lcp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        #launch testpmd
        self.launch_testpmd(False)
        #create a pppoe rss rule to make the pppoe control have hash value, and queue group action work
        self.dut.send_expect("flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_lcp_pay_pipeline_mode, False)

    def test_mac_vlan_pppoe_ipcp_pay_pipeline_mode(self):
        tvs_mac_vlan_pppoe_ipcp_pay_pipeline_mode = copy.deepcopy(tvs_mac_vlan_pppoe_ipcp_pay)
        for tv in tvs_mac_vlan_pppoe_ipcp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        #launch testpmd
        self.launch_testpmd(False)
        #create a pppoe rss rule to make the pppoe control have hash value, and queue group action work
        self.dut.send_expect("flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tvs_mac_vlan_pppoe_ipcp_pay_pipeline_mode, False)

    def test_negative_case(self):
        """
        negative cases
        """
        self.launch_testpmd(False)
        rules = {
            "invalid parameters of queue index" : "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 16 / end",
            "invalid parameters of rss queues" : [
                "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end",
                "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 end / end",
                "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues end / end",
                "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end",
                "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 15 16 end / end",
                "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 end / end"],
            "unsupported input set" : "flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 tos is 4 / end actions queue index 1 / end",
            "multiple actions" : "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / rss queues 2 3 end / end",
            "void action" : "flow create 0 priority 0 ingress pattern eth / ipv4 / udp src is 25 dst is 23 / end actions end",
            "unsupported action": "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions mark id 1 / end",
            "void input set value" : "flow create 0 priority 0 ingress pattern eth / ipv4 / end actions queue index 1 / end",
            "invalid port" : "flow create 1 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end"
        }
        # all the rules failed to validate and create

        # invalid parameters of queue index
        rule_list = self.validate_switch_filter_rule(rules["invalid parameters of queue index"], check_stats=False)
        self.verify(not any(rule_list), "all rules should validate failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))
        rule_list = self.create_switch_filter_rule(rules["invalid parameters of queue index"], check_stats=False)
        self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))

        # invalid parameters of rss queues
        rule_list = self.validate_switch_filter_rule(rules["invalid parameters of rss queues"], check_stats=False)
        self.verify(not any(rule_list), "all rules should validate failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))
        rule_list = self.create_switch_filter_rule(rules["invalid parameters of rss queues"], check_stats=False)
        self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))

        # unsupported input set
        rule_list = self.validate_switch_filter_rule(rules["unsupported input set"], check_stats=False)
        self.verify(not any(rule_list), "all rules should validate failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))
        rule_list = self.create_switch_filter_rule(rules["unsupported input set"], check_stats=False)
        self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))

        # duplicated rules
        rule = "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end"
        rule_list = self.create_switch_filter_rule(rule, check_stats=False)
        self.verify(all(rule_list), "some rules create failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == rule_list, "the rule list is not the same. expect %s, result %s" % (rule_list, result))
        rule_list_dupli = self.create_switch_filter_rule(rule, check_stats=False)
        self.verify(not any(rule_list_dupli), "all rules should create failed, result %s" % rule_list_dupli)
        result_dupli = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result_dupli == rule_list, "the rule list is not the same. expect %s, result %s" % (rule_list, result_dupli))
        self.dut.send_expect("flow destroy 0 rule %s" % rule_list[0], "testpmd> ", 15)

        # conflicted rules
        rule = "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end"
        rule_list = self.create_switch_filter_rule(rule, check_stats=False)
        self.verify(all(rule_list), "some rules create failed, result %s, rule %s" % (rule_list, rule))
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == rule_list, "the rule list is not the same. expect %s, result %s" % (rule_list, result))
        rule1 = "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 2 / end"
        rule_list1 = self.create_switch_filter_rule(rule1, check_stats=False)
        self.verify(not any(rule_list1), "all rules should create failed, result %s" % rule_list1)
        rule2 = "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions drop / end"
        rule_list2 = self.create_switch_filter_rule(rule2, check_stats=False)
        self.verify(not any(rule_list2), "all rules should create failed, result %s" % rule_list2)
        result1 = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result1 == rule_list, "the rule list is not the same. expect %s, result %s" % (rule_list, result1))
        self.dut.send_expect("flow destroy 0 rule %s" % rule_list[0], "testpmd> ", 15)

        # multiple actions
        rule_list = self.validate_switch_filter_rule(rules["multiple actions"], check_stats=False)
        self.verify(not any(rule_list), "all rules should validate failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))
        rule_list = self.create_switch_filter_rule(rules["multiple actions"], check_stats=False)
        self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))

        # void action
        rule_list = self.validate_switch_filter_rule(rules["void action"], check_stats=False)
        self.verify(not any(rule_list), "all rules should validate failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))
        rule_list = self.create_switch_filter_rule(rules["void action"], check_stats=False)
        self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))

        # delete a non-existing rule
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))
        out = self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ", 15)
        self.verify("error" not in out, "It should be no error message.")

        # add long switch rule
        rule = "flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end"
        rule_list = self.validate_switch_filter_rule(rule, check_stats=False)
        self.verify(not any(rule_list), "all rules should validate failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))
        rule_list = self.create_switch_filter_rule(rule, check_stats=False)
        self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))
        tvs_mac_pppoe_ipv6_udp_pay_pipeline_mode = copy.deepcopy(tvs_mac_pppoe_ipv6_udp_pay)
        for tv in tvs_mac_pppoe_ipv6_udp_pay_pipeline_mode:
            create_rule = tv["rte_flow_pattern"].replace("flow create 0", "flow create 0 priority 0")
            tv["rte_flow_pattern"] = create_rule
            tv["configuration"]["is_non_pipeline"] = False
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_udp_pay_pipeline_mode, False)

        # void input set value
        rule_list = self.validate_switch_filter_rule(rules["void input set value"], check_stats=False)
        self.verify(not any(rule_list), "all rules should validate failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))
        rule_list = self.create_switch_filter_rule(rules["void input set value"], check_stats=False)
        self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))

        # invalid port
        rule_list = self.validate_switch_filter_rule(rules["invalid port"], check_stats=False)
        self.verify(not any(rule_list), "all rules should validate failed, result %s" % rule_list)
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % ([], result))
        result = self.check_switch_filter_rule_list(self.dut_ports[1], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % (rule_list, result))
        rule_list = self.create_switch_filter_rule(rules["invalid port"], check_stats=False)
        self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        # check there is no rule listed
        result = self.check_switch_filter_rule_list(self.dut_ports[0], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % (rule_list, result))
        result = self.check_switch_filter_rule_list(self.dut_ports[1], is_non_pipeline=False, is_need_rss_rule=False, check_stats=False)
        self.verify(result == [], "the rule list is not the same. expect %s, result %s" % (rule_list, result))

    def tear_down(self):
        """
        Run after each test case.
        """
        # destroy all the rules on port 0
        self.dut.send_expect("flow flush %d" % self.dut_ports[0], "testpmd> ", 300)
        self.dut.send_expect("quit", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
