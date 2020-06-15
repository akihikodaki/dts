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

from test_case import TestCase
from pmd_output import PmdOutput
from packet import Packet
from utils import BLUE, RED, GREEN
from collections import OrderedDict
import rte_flow_common as rfc

import os

#vxlan non-pipeline mode
#test vector mac_ipv4_vxlan_ipv4_frag
tv_mac_ipv4_vxlan_ipv4_frag_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_frag_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",frag=5)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_ipv4_vxlan_ipv4_frag_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_frag_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",frag=5)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_ipv4_vxlan_ipv4_frag_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_frag_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",frag=5)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_ipv4_vxlan_ipv4_frag = [
    tv_mac_ipv4_vxlan_ipv4_frag_in_queue_01,
    tv_mac_ipv4_vxlan_ipv4_frag_queue_region_02,
    tv_mac_ipv4_vxlan_ipv4_frag_drop_03
    ]

#test vector mac_ipv4_vxlan_ipv4_pay
tv_mac_ipv4_vxlan_ipv4_pay_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_ipv4_vxlan_ipv4_pay_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_ipv4_vxlan_ipv4_pay_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_ipv4_vxlan_ipv4_pay = [
    tv_mac_ipv4_vxlan_ipv4_pay_in_queue_01,
    tv_mac_ipv4_vxlan_ipv4_pay_queue_region_02,
    tv_mac_ipv4_vxlan_ipv4_pay_drop_03
    ]

#test vector mac_ipv4_vxlan_ipv4_udp_pay
tv_mac_ipv4_vxlan_ipv4_udp_pay_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_udp_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 4 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":4}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":4}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_ipv4_udp_pay_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_udp_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_ipv4_udp_pay_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_udp_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_vxlan_ipv4_udp_pay = [
    tv_mac_ipv4_vxlan_ipv4_udp_pay_in_queue_01,
    tv_mac_ipv4_vxlan_ipv4_udp_pay_queue_region_02,
    tv_mac_ipv4_vxlan_ipv4_udp_pay_drop_03
]

#test vector mac_ipv4_vxlan_ipv4_tcp
tv_mac_ipv4_vxlan_ipv4_tcp_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_tcp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions queue index 5 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":5}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=29,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=100)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":5}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_ipv4_tcp_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_tcp_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=29,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=100)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_ipv4_tcp_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_tcp_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=29,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=100)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_vxlan_ipv4_tcp = [
    tv_mac_ipv4_vxlan_ipv4_tcp_in_queue_01,
    tv_mac_ipv4_vxlan_ipv4_tcp_queue_region_02,
    tv_mac_ipv4_vxlan_ipv4_tcp_drop_03
    ]

#test vector mac_ipv4_vxlan_mac_ipv4_frag
tv_mac_ipv4_vxlan_mac_ipv4_frag_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_frag_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5" ,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_ipv4_vxlan_mac_ipv4_frag_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_frag_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5" ,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_ipv4_vxlan_mac_ipv4_frag_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_frag_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5" ,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":5}}
}

tvs_mac_ipv4_vxlan_mac_ipv4_frag = [
    tv_mac_ipv4_vxlan_mac_ipv4_frag_in_queue_01,
    tv_mac_ipv4_vxlan_mac_ipv4_frag_queue_region_02,
    tv_mac_ipv4_vxlan_mac_ipv4_frag_drop_03
    ]

#test vector mac_ipv4_vxlan_mac_ipv4_pay
tv_mac_ipv4_vxlan_mac_ipv4_pay_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw("x" * 80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3") /TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5") /TCP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_ipv4_vxlan_mac_ipv4_pay_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x" * 80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_ipv4_vxlan_mac_ipv4_pay_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x" * 80)',
                            'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":5}}
}

tvs_mac_ipv4_vxlan_mac_ipv4_pay = [
    tv_mac_ipv4_vxlan_mac_ipv4_pay_in_queue_01,
    tv_mac_ipv4_vxlan_mac_ipv4_pay_queue_region_02,
    tv_mac_ipv4_vxlan_mac_ipv4_pay_drop_03
    ]

#test vector mac_ipv4_vxlan_mac_ipv4_udp_pay
tv_mac_ipv4_vxlan_mac_ipv4_udp_pay_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_udp_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=29)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_mac_ipv4_udp_pay_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_udp_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=29)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_mac_ipv4_udp_pay_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_udp_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=29)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_vxlan_mac_ipv4_udp_pay = [
    tv_mac_ipv4_vxlan_mac_ipv4_udp_pay_in_queue_01,
    tv_mac_ipv4_vxlan_mac_ipv4_udp_pay_queue_region_02,
    tv_mac_ipv4_vxlan_mac_ipv4_udp_pay_drop_03
    ]

#test vector mac_ipv4_vxlan_mac_ipv4_tcp
tv_mac_ipv4_vxlan_mac_ipv4_tcp_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_tcp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=20,dport=23)/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_mac_ipv4_tcp_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_tcp_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions rss queues 1 2 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[1, 2]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=20,dport=23)/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[1, 2]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_mac_ipv4_tcp_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_mac_ipv4_tcp_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=20,dport=23)/Raw("x" * 80)',
                               'Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_vxlan_mac_ipv4_tcp = [
    tv_mac_ipv4_vxlan_mac_ipv4_tcp_in_queue_01,
    tv_mac_ipv4_vxlan_mac_ipv4_tcp_queue_region_02,
    tv_mac_ipv4_vxlan_mac_ipv4_tcp_drop_03
    ]

#nvgre non-pipeline mode
#test vector mac_ipv4_nvgre_ipv4_frag
tv_mac_ipv4_nvgre_ipv4_frag_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_frag_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_ipv4_nvgre_ipv4_frag_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_frag_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_ipv4_nvgre_ipv4_frag_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_frag_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_ipv4_nvgre_ipv4_frag = [
    tv_mac_ipv4_nvgre_ipv4_frag_in_queue_01,
    tv_mac_ipv4_nvgre_ipv4_frag_queue_region_02,
    tv_mac_ipv4_nvgre_ipv4_frag_drop_03
    ]

#test vector mac_ipv4_nvgre_ipv4_pay
tv_mac_ipv4_nvgre_ipv4_pay_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_ipv4_nvgre_ipv4_pay_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":4}}
}

tv_mac_ipv4_nvgre_ipv4_pay_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":4}}
}

tvs_mac_ipv4_nvgre_ipv4_pay = [
    tv_mac_ipv4_nvgre_ipv4_pay_in_queue_01,
    tv_mac_ipv4_nvgre_ipv4_pay_queue_region_02,
    tv_mac_ipv4_nvgre_ipv4_pay_drop_03
    ]

#test vector mac_ipv4_nvgre_ipv4_udp_pay
tv_mac_ipv4_nvgre_ipv4_udp_pay_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_udp_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 4 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":4}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":4}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_ipv4_udp_pay_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_udp_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_ipv4_udp_pay_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_udp_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_nvgre_ipv4_udp_pay = [
    tv_mac_ipv4_nvgre_ipv4_udp_pay_in_queue_01,
    tv_mac_ipv4_nvgre_ipv4_udp_pay_queue_region_02,
    tv_mac_ipv4_nvgre_ipv4_udp_pay_drop_03
    ]

#test vector mac_ipv4_nvgre_ipv4_tcp
tv_mac_ipv4_nvgre_ipv4_tcp_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_tcp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=39)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_ipv4_tcp_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_tcp_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions rss queues 1 2 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[1, 2]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=39)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[1, 2]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_ipv4_tcp_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_tcp_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=39)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_nvgre_ipv4_tcp = [
    tv_mac_ipv4_nvgre_ipv4_tcp_in_queue_01,
    tv_mac_ipv4_nvgre_ipv4_tcp_queue_region_02,
    tv_mac_ipv4_nvgre_ipv4_tcp_drop_03
    ]

#test vector mac_ipv4_nvgre_mac_ipv4_frag
tv_mac_ipv4_nvgre_mac_ipv4_frag_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_frag_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_ipv4_nvgre_mac_ipv4_frag_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_frag_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_ipv4_nvgre_mac_ipv4_frag_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_frag_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":5}}
}

tvs_mac_ipv4_nvgre_mac_ipv4_frag = [
    tv_mac_ipv4_nvgre_mac_ipv4_frag_in_queue_01,
    tv_mac_ipv4_nvgre_mac_ipv4_frag_queue_region_02,
    tv_mac_ipv4_nvgre_mac_ipv4_frag_drop_03
    ]

#test vector mac_ipv4_nvgre_mac_ipv4_pay
tv_mac_ipv4_nvgre_mac_ipv4_pay_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_ipv4_nvgre_mac_ipv4_pay_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":5}}
}

tv_mac_ipv4_nvgre_mac_ipv4_pay_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":5}}
}

tvs_mac_ipv4_nvgre_mac_ipv4_pay = [
    tv_mac_ipv4_nvgre_mac_ipv4_pay_in_queue_01,
    tv_mac_ipv4_nvgre_mac_ipv4_pay_queue_region_02,
    tv_mac_ipv4_nvgre_mac_ipv4_pay_drop_03
    ]

#test vector mac_ipv4_nvgre_mac_ipv4_udp_pay
tv_mac_ipv4_nvgre_mac_ipv4_udp_pay_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_udp_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_mac_ipv4_udp_pay_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_udp_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_mac_ipv4_udp_pay_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_udp_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_nvgre_mac_ipv4_udp_pay = [
    tv_mac_ipv4_nvgre_mac_ipv4_udp_pay_in_queue_01,
    tv_mac_ipv4_nvgre_mac_ipv4_udp_pay_queue_region_02,
    tv_mac_ipv4_nvgre_mac_ipv4_udp_pay_drop_03
    ]

#test vector mac_ipv4_nvgre_mac_ipv4_tcp
tv_mac_ipv4_nvgre_mac_ipv4_tcp_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_tcp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_mac_ipv4_tcp_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_tcp_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_mac_ipv4_tcp_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_tcp_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_nvgre_mac_ipv4_tcp = [
    tv_mac_ipv4_nvgre_mac_ipv4_tcp_in_queue_01,
    tv_mac_ipv4_nvgre_mac_ipv4_tcp_queue_region_02,
    tv_mac_ipv4_nvgre_mac_ipv4_tcp_drop_03
    ]

#pppod non-pipeline mode
#test vector mac_pppod_pay
tv_mac_pppod_pay_in_queue_01 = {
    "name":"tv_mac_pppod_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8863 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x" *80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x" *80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_pppod_pay_queue_region_02 = {
    "name":"tv_mac_pppod_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8863 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x" *80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x" *80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_pppod_pay_drop_03 = {
    "name":"tv_mac_pppod_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8863 / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x" *80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x" *80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tvs_mac_pppod_pay = [
    tv_mac_pppod_pay_in_queue_01,
    tv_mac_pppod_pay_queue_region_02,
    tv_mac_pppod_pay_drop_03
    ]

#pppoe non-pipeline mode
#test vector mac_pppoe_pay
tv_mac_pppoe_pay_in_queue_01 = {
    "name":"tv_mac_pppoe_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8864 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_pppoe_pay_queue_region_02 = {
    "name":"tv_mac_pppoe_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8864 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_pppoe_pay_drop_03 = {
    "name":"tv_mac_pppoe_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8864 / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tvs_mac_pppoe_pay = [
    tv_mac_pppoe_pay_in_queue_01,
    tv_mac_pppoe_pay_queue_region_02,
    tv_mac_pppoe_pay_drop_03
    ]

#test vector mac_pppoe_ipv4_frag
tv_mac_pppoe_ipv4_frag_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv4_frag_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP(frag=5)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP(frag=5)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_pppoe_ipv4_frag_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv4_frag_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP(frag=5)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP(frag=5)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_pppoe_ipv4_frag_drop_03 = {
    "name":"tv_mac_pppoe_ipv4_frag_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP(frag=5)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP(frag=5)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tvs_mac_pppoe_ipv4_frag = [
    tv_mac_pppoe_ipv4_frag_in_queue_01,
    tv_mac_pppoe_ipv4_frag_queue_region_02,
    tv_mac_pppoe_ipv4_frag_drop_03
    ]

#test vector mac_pppoe_ipv4_pay
tv_mac_pppoe_ipv4_pay_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv4_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":1}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_pppoe_ipv4_pay_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv4_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_pppoe_ipv4_pay_drop_03 = {
    "name":"tv_mac_pppoe_ipv4_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_pppoe_ipv4_pay = [
    tv_mac_pppoe_ipv4_pay_in_queue_01,
    tv_mac_pppoe_ipv4_pay_queue_region_02,
    tv_mac_pppoe_ipv4_pay_drop_03
    ]

#test vector mac_pppoe_ipv4_udp_pay
tv_mac_pppoe_ipv4_udp_pay_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv4_udp_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/UDP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv4_udp_pay_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv4_udp_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/UDP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv4_udp_pay_drop_03 = {
    "name":"tv_mac_pppoe_ipv4_udp_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/UDP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tvs_mac_pppoe_ipv4_udp_pay = [
    tv_mac_pppoe_ipv4_udp_pay_in_queue_01,
    tv_mac_pppoe_ipv4_udp_pay_queue_region_02,
    tv_mac_pppoe_ipv4_udp_pay_drop_03
    ]

#test vector mac_pppoe_ipv4_tcp
tv_mac_pppoe_ipv4_tcp_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv4_tcp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/TCP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv4_tcp_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv4_tcp_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/TCP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv4_tcp_drop_03 = {
    "name":"tv_mac_pppoe_ipv4_tcp_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/TCP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tvs_mac_pppoe_ipv4_tcp = [
    tv_mac_pppoe_ipv4_tcp_in_queue_01,
    tv_mac_pppoe_ipv4_tcp_queue_region_02,
    tv_mac_pppoe_ipv4_tcp_drop_03
    ]

#test vector mac_pppoe_ipv4_sctp
tv_mac_pppoe_ipv4_sctp_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv4_sctp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/SCTP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv4_sctp_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv4_sctp_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/SCTP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv4_sctp_drop_03 = {
    "name":"tv_mac_pppoe_ipv4_sctp_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/SCTP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tvs_mac_pppoe_ipv4_sctp = [
    tv_mac_pppoe_ipv4_sctp_in_queue_01,
    tv_mac_pppoe_ipv4_sctp_queue_region_02,
    tv_mac_pppoe_ipv4_sctp_drop_03
    ]

#test vector mac_pppoe_ipv4_icmp
tv_mac_pppoe_ipv4_icmp_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv4_icmp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/ICMP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv4_icmp_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv4_icmp_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/ICMP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv4_icmp_drop_03 = {
    "name":"tv_mac_pppoe_ipv4_icmp_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/ICMP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tvs_mac_pppoe_ipv4_icmp = [
    tv_mac_pppoe_ipv4_icmp_in_queue_01,
    tv_mac_pppoe_ipv4_icmp_queue_region_02,
    tv_mac_pppoe_ipv4_icmp_drop_03
    ]

#test vector mac_pppoe_ipv6_frag
tv_mac_pppoe_ipv6_frag_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv6_frag_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_frag_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv6_frag_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_frag_drop_03 = {
    "name":"tv_mac_pppoe_ipv6_frag_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tvs_mac_pppoe_ipv6_frag = [
    tv_mac_pppoe_ipv6_frag_in_queue_01,
    tv_mac_pppoe_ipv6_frag_queue_region_02,
    tv_mac_pppoe_ipv6_frag_drop_03
    ]

#test vector mac_pppoe_ipv6_pay
tv_mac_pppoe_ipv6_pay_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv6_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_pay_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv6_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_pay_drop_03 = {
    "name":"tv_mac_pppoe_ipv6_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tvs_mac_pppoe_ipv6_pay = [
    tv_mac_pppoe_ipv6_pay_in_queue_01,
    tv_mac_pppoe_ipv6_pay_queue_region_02,
    tv_mac_pppoe_ipv6_pay_drop_03
    ]

#test vector mac_pppoe_ipv6_udp_pay
tv_mac_pppoe_ipv6_udp_pay_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv6_udp_pay_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/UDP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_udp_pay_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv6_udp_pay_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/UDP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_udp_pay_drop_03 = {
    "name":"tv_mac_pppoe_ipv6_udp_pay_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/UDP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tvs_mac_pppoe_ipv6_udp_pay = [
    tv_mac_pppoe_ipv6_udp_pay_in_queue_01,
    tv_mac_pppoe_ipv6_udp_pay_queue_region_02,
    tv_mac_pppoe_ipv6_udp_pay_drop_03
    ]

#test vector mac_pppoe_ipv6_tcp
tv_mac_pppoe_ipv6_tcp_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv6_tcp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/TCP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_tcp_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv6_tcp_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 4 5 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/TCP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3, 4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_tcp_drop_03 = {
    "name":"tv_mac_pppoe_ipv6_tcp_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/TCP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tvs_mac_pppoe_ipv6_tcp = [
    tv_mac_pppoe_ipv6_tcp_in_queue_01,
    tv_mac_pppoe_ipv6_tcp_queue_region_02,
    tv_mac_pppoe_ipv6_tcp_drop_03
    ]

#test vector mac_pppoe_ipv6_sctp
tv_mac_pppoe_ipv6_sctp_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv6_sctp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/SCTP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_sctp_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv6_sctp_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/SCTP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_sctp_drop_03 = {
    "name":"tv_mac_pppoe_ipv6_sctp_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/SCTP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tvs_mac_pppoe_ipv6_sctp = [
    tv_mac_pppoe_ipv6_sctp_in_queue_01,
    tv_mac_pppoe_ipv6_sctp_queue_region_02,
    tv_mac_pppoe_ipv6_sctp_drop_03
    ]

#test vector mac_pppoe_ipv6_icmpv6
tv_mac_pppoe_ipv6_icmpv6_in_queue_01 = {
    "name":"tv_mac_pppoe_ipv6_icmpv6_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/ICMP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":1}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_icmpv6_queue_region_02 = {
    "name":"tv_mac_pppoe_ipv6_icmpv6_queue_region_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/ICMP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_mac_pppoe_ipv6_icmpv6_drop_03 = {
    "name":"tv_mac_pppoe_ipv6_icmpv6_drop_03",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0057)/IPv6()/ICMP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tvs_mac_pppoe_ipv6_icmpv6 = [
    tv_mac_pppoe_ipv6_icmpv6_in_queue_01,
    tv_mac_pppoe_ipv6_icmpv6_queue_region_02,
    tv_mac_pppoe_ipv6_icmpv6_drop_03
    ]

#vxlan pipeline mode
#test vector mac_ipv4_vxlan_ipv4_frag_pipeline_mode
tv_mac_ipv4_vxlan_ipv4_frag_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_frag_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_ipv4_vxlan_ipv4_frag_pipeline_mode_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_frag_pipeline_mode_queue_region_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_ipv4_vxlan_ipv4_frag_pipeline_mode_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_frag_pipeline_mode_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":3}}
}

tvs_mac_ipv4_vxlan_ipv4_frag_pipeline_mode = [
    tv_mac_ipv4_vxlan_ipv4_frag_pipeline_mode_in_queue_01,
    tv_mac_ipv4_vxlan_ipv4_frag_pipeline_mode_queue_region_02,
    tv_mac_ipv4_vxlan_ipv4_frag_pipeline_mode_drop_03
    ]

#test vector mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode
tv_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=29)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode_queue_region_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=29)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=29)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode = [
    tv_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode_in_queue_01,
    tv_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode_queue_region_02,
    tv_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode_drop_03
    ]


#test vector mac_ipv4_vxlan_ipv4_tcp_pipeline_mode
tv_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=19,dport=23)/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=30)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode_queue_region_02 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode_queue_region_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=19,dport=23)/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=30)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode_drop_03 = {
    "name":"tv_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=19,dport=23)/Raw("x"*80)',
                               'Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=30)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode = [
    tv_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode_in_queue_01,
    tv_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode_queue_region_02,
    tv_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode_drop_03
    ]

#nvgre pipeline mode
#test vector mac_ipv4_nvgre_ipv4_frag_pipeline_mode
tv_mac_ipv4_nvgre_ipv4_frag_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_frag_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_ipv4_nvgre_ipv4_frag_pipeline_mode_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_frag_pipeline_mode_queue_region_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_ipv4_nvgre_ipv4_frag_pipeline_mode_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_frag_pipeline_mode_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":3}}
}

tvs_mac_ipv4_nvgre_ipv4_frag_pipeline_mode = [
    tv_mac_ipv4_nvgre_ipv4_frag_pipeline_mode_in_queue_01,
    tv_mac_ipv4_nvgre_ipv4_frag_pipeline_mode_queue_region_02,
    tv_mac_ipv4_nvgre_ipv4_frag_pipeline_mode_drop_03
    ]

#test vector mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode
tv_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw("x"*80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=100)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode_queue_region_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw("x"*80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=100)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw("x"*80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=100)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode = [
    tv_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode_in_queue_01,
    tv_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode_queue_region_02,
    tv_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode_drop_03
    ]

#test vector mac_ipv4_nvgre_ipv4_tcp_pipeline_mode
tv_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=3,dport=23)/Raw("x" * 80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=100)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode_queue_region_02 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode_queue_region_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=3,dport=23)/Raw("x" * 80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=100)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode_drop_03 = {
    "name":"tv_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=3,dport=23)/Raw("x" * 80)',
                               'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=100)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode = [
    tv_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode_in_queue_01,
    tv_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode_queue_region_02,
    tv_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode_drop_03
    ]

#non-tunnel pipeline mode
#test vector mac_ipv4_frag_pipeline_mode
tv_mac_ipv4_frag_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv4_frag_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=7,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_ipv4_frag_partial_fields_pipeline_mode_in_queue_02 = {
    "name":"tv_mac_ipv4_frag_partial_fields_pipeline_mode_in_queue_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":2}}

}

tv_mac_ipv4_frag_pipeline_mode_queue_region_03 = {
    "name":"tv_mac_ipv4_frag_pipeline_mode_queue_region_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=7,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_ipv4_frag_partial_fields_pipeline_mode_queue_region_04 = {
    "name":"tv_mac_ipv4_frag_partial_fields_pipeline_mode_queue_region_04",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_frag_pipeline_mode_drop_05 = {
    "name":"tv_mac_ipv4_frag_pipeline_mode_drop_05",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=7,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":3}}
}

tv_mac_ipv4_frag_partial_fields_pipeline_mode_drop_06 = {
    "name":"tv_mac_ipv4_frag_partial_fields_pipeline_mode_drop_06",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                            'Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_frag_pipeline_mode = [
    tv_mac_ipv4_frag_pipeline_mode_in_queue_01,
    tv_mac_ipv4_frag_partial_fields_pipeline_mode_in_queue_02,
    tv_mac_ipv4_frag_pipeline_mode_queue_region_03,
    tv_mac_ipv4_frag_partial_fields_pipeline_mode_queue_region_04,
    tv_mac_ipv4_frag_pipeline_mode_drop_05,
    tv_mac_ipv4_frag_partial_fields_pipeline_mode_drop_06
    ]

#test vector mac_ipv4_pay_pipeline_mode
tv_mac_ipv4_pay_pipeline_mode_tcp_in_queue_01 = {
    "name":"tv_mac_ipv4_pay_pipeline_mode_tcp_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv4_pay_pipeline_mode_udp_in_queue_02 = {
    "name":"tv_mac_ipv4_pay_pipeline_mode_udp_in_queue_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv4_pay_pipeline_mode_tcp_queue_region_03 = {
    "name":"tv_mac_ipv4_pay_pipeline_mode_tcp_queue_region_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv4_pay_pipeline_mode_udp_queue_region_04 = {
    "name":"tv_mac_ipv4_pay_pipeline_mode_udp_queue_region_04",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv4_pay_pipeline_mode_tcp_drop_05 = {
    "name":"tv_mac_ipv4_pay_pipeline_mode_tcp_drop_05",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv4_pay_pipeline_mode_udp_drop_06 = {
    "name":"tv_mac_ipv4_pay_pipeline_mode_udp_drop_06",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tvs_mac_ipv4_pay_pipeline_mode = [
    tv_mac_ipv4_pay_pipeline_mode_tcp_in_queue_01,
    tv_mac_ipv4_pay_pipeline_mode_udp_in_queue_02,
    tv_mac_ipv4_pay_pipeline_mode_tcp_queue_region_03,
    tv_mac_ipv4_pay_pipeline_mode_udp_queue_region_04,
    tv_mac_ipv4_pay_pipeline_mode_tcp_drop_05,
    tv_mac_ipv4_pay_pipeline_mode_udp_drop_06
    ]

#test vector mac_ipv4_udp_pay_pipeline_mode
tv_mac_ipv4_udp_pay_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv4_udp_pay_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=3)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_udp_pay_pipeline_mode_queue_region_02 = {
    "name":"tv_mac_ipv4_udp_pay_pipeline_mode_queue_region_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=3)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_udp_pay_pipeline_mode_drop_03 = {
    "name":"tv_mac_ipv4_udp_pay_pipeline_mode_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=3)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_udp_pay_pipeline_mode = [
    tv_mac_ipv4_udp_pay_pipeline_mode_in_queue_01,
    tv_mac_ipv4_udp_pay_pipeline_mode_queue_region_02,
    tv_mac_ipv4_udp_pay_pipeline_mode_drop_03
    ]

#test vector mac_ipv4_tcp_pipeline_mode
tv_mac_ipv4_tcp_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv4_tcp_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=5,dport=23)/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=7)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_tcp_pipeline_mode_queue_region_02 = {
    "name":"tv_mac_ipv4_tcp_pipeline_mode_queue_region_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=5,dport=23)/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=7)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv4_tcp_pipeline_mode_drop_03 = {
    "name":"tv_mac_ipv4_tcp_pipeline_mode_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=5,dport=23)/Raw("x"*80)',
                               'Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=7)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv4_tcp_pipeline_mode = [
    tv_mac_ipv4_tcp_pipeline_mode_in_queue_01,
    tv_mac_ipv4_tcp_pipeline_mode_queue_region_02,
    tv_mac_ipv4_tcp_pipeline_mode_drop_03
    ]

#test vector mac_ipv6_frag_pipeline_mode
tv_mac_ipv6_frag_srcipv6_dstipv6_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv6_frag_srcipv6_dstipv6_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 5 / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":5}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1514",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":5}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv6_frag_dstipv6_tc_pipeline_mode_in_queue_02 = {
    "name":"tv_mac_ipv6_frag_dstipv6_tc_pipeline_mode_in_queue_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions queue index 3 / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":3}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2027",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":3}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv6_frag_srcipv6_dstipv6_pipeline_mode_queue_region_03 = {
    "name":"tv_mac_ipv6_frag_srcipv6_dstipv6_pipeline_mode_queue_region_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1514",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv6_frag_dstipv6_tc_pipeline_mode_queue_region_04 = {
    "name":"tv_mac_ipv6_frag_dstipv6_tc_pipeline_mode_queue_region_04",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2027",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv6_frag_srcipv6_dstipv6_pipeline_mode_drop_05 = {
    "name":"tv_mac_ipv6_frag_srcipv6_dstipv6_pipeline_mode_drop_05",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1514",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv6_frag_dstipv6_tc_pipeline_mode_drop_06 = {
    "name":"tv_mac_ipv6_frag_dstipv6_tc_pipeline_mode_drop_06",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2027",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv6_frag_pipeline_mode = [
    tv_mac_ipv6_frag_srcipv6_dstipv6_pipeline_mode_in_queue_01,
    tv_mac_ipv6_frag_dstipv6_tc_pipeline_mode_in_queue_02,
    tv_mac_ipv6_frag_srcipv6_dstipv6_pipeline_mode_queue_region_03,
    tv_mac_ipv6_frag_dstipv6_tc_pipeline_mode_queue_region_04,
    tv_mac_ipv6_frag_srcipv6_dstipv6_pipeline_mode_drop_05,
    tv_mac_ipv6_frag_dstipv6_tc_pipeline_mode_drop_06
    ]

#test vector mac_ipv6_udp_pay_pipeline_mode
tv_mac_ipv6_udp_pay_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv6_udp_pay_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions queue index 5 / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":5}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=3,dport=23)/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=4)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":5}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv6_udp_pay_pipeline_mode_queue_region_02 = {
    "name":"tv_mac_ipv6_udp_pay_pipeline_mode_queue_region_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions rss queues 2 3 end / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[2, 3]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=3,dport=23)/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=4)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[2, 3]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv6_udp_pay_pipeline_mode_drop_03 = {
    "name":"tv_mac_ipv6_udp_pay_pipeline_mode_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=3,dport=23)/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=4)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv6_udp_pay_pipeline_mode = [
    tv_mac_ipv6_udp_pay_pipeline_mode_in_queue_01,
    tv_mac_ipv6_udp_pay_pipeline_mode_queue_region_02,
    tv_mac_ipv6_udp_pay_pipeline_mode_drop_03
    ]

#test vector mac_ipv6_tcp_pipeline_mode
tv_mac_ipv6_tcp_pipeline_mode_in_queue_01 = {
    "name":"tv_mac_ipv6_tcp_pipeline_mode_in_queue_01",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions queue index 4 / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":4}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=1,dport=23)/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":4}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv6_tcp_pipeline_mode_queue_region_02 = {
    "name":"tv_mac_ipv6_tcp_pipeline_mode_queue_region_02",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_queue_region,
                             "param":{"expect_port":0, "expect_queues":[4, 5]}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=1,dport=23)/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_queue_region_mismatched,
                                "param":{"expect_port":0, "expect_queues":[4, 5]}},
                  "expect_results":{"expect_pkts":2}}
}

tv_mac_ipv6_tcp_pipeline_mode_drop_03 = {
    "name":"tv_mac_ipv6_tcp_pipeline_mode_drop_03",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=1,dport=23)/Raw("x"*80)',
                               'Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":2}}
}

tvs_mac_ipv6_tcp_pipeline_mode = [
    tv_mac_ipv6_tcp_pipeline_mode_in_queue_01,
    tv_mac_ipv6_tcp_pipeline_mode_queue_region_02,
    tv_mac_ipv6_tcp_pipeline_mode_drop_03
    ]

tv_mac_ipv4_in_queue_01 = {
    "name":"tv_mac_ipv4_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions queue index 4 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":4}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.9",dst="192.168.6.12",tos=4,ttl=2)/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":4}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv4_drop_queue_02 = {
    "name":"tv_mac_ipv4_drop_queue_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.3 tos is 4 ttl is 2 / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.3",tos=4,ttl=2)/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.5.6",dst="192.168.5.15",tos=2,ttl=5)/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv4_udp_in_queue_01 = {
    "name":"tv_mac_ipv4_udp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions queue index 2 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":2}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.6.56",dst="192.168.5.83",tos=2,ttl=1)/UDP(sport=20,dport=33)/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":2}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv4_udp_drop_queue_02 = {
    "name":"tv_mac_ipv4_udp_drop_queue_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.3 tos is 4 / udp src is 25 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.3",tos=4)/UDP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:98")/IP(src="192.168.6.3",dst="192.168.8.5",tos=4)/UDP(sport=85,dport=62)/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv4_tcp_in_queue_01 = {
    "name":"tv_mac_ipv4_tcp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.32 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 6 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.32",tos=4)/TCP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":6}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.8.3",dst="192.168.15.26",tos=3)/UDP(sport=62,dport=88)/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":6}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv4_tcp_drop_queue_02 = {
    "name":"tv_mac_ipv4_tcp_drop_queue_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.5.6",dst="192.168.5.5",tos=8)/UDP(sport=55,dport=36)/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv6_in_queue_01 = {
    "name":"tv_mac_ipv6_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 7 / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":7}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="BCBC:910A:2222:5498:8475:1111:3900:8220", dst="ABAB:910A:2222:5498:8475:1111:3900:1520")/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":7}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv6_drop_queue_02 = {
    "name":"tv_mac_ipv6_drop_queue_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="BCBC:910A:2222:5498:8475:1111:3900:8220", dst="ABAB:910A:2222:5498:8475:1111:3900:1520")/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}


tv_mac_ipv6_frag_in_queue_01 = {
    "name":"tv_mac_ipv6_frag_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 7 / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":7}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="BCBC:910A:2222:5498:8475:1111:3900:8220", dst="ABAB:910A:2222:5498:8475:1111:3900:1520")/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":7}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv6_frag_drop_queue_02 = {
    "name":"tv_mac_ipv6_frag_drop_queue_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="BCBC:910A:2222:5498:8475:1111:3900:8220", dst="ABAB:910A:2222:5498:8475:1111:3900:1520")/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv6_udp_in_queue_01 = {
    "name":"tv_mac_ipv6_udp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1518 / udp src is 25 dst is 23 / end actions queue index 7 / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518")/UDP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":7}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="ABAB:910A:2222:5498:8475:1111:3900:1520")/UDP(sport=22,dport=12)/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":7}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv6_udp_drop_queue_02 = {
    "name":"tv_mac_ipv6_udp_drop_queue_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1518 / udp src is 25 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518")/UDP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="BCBC:910A:2222:5498:8475:1111:3900:8220")/UDP(sport=62,dport=11)/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv6_tcp_in_queue_01 = {
    "name":"tv_mac_ipv6_tcp_in_queue_01",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1518 / tcp src is 25 dst is 23 / end actions queue index 7 / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518")/TCP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_in_queue,
                             "param":{"expect_port":0, "expect_queues":7}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="ABAB:910A:2222:5498:8475:1111:3900:1520")/UDP(sport=22,dport=12)/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_in_queue_mismatched,
                                "param":{"expect_port":0, "expect_queues":7}},
                  "expect_results":{"expect_pkts":1}}
}

tv_mac_ipv6_tcp_drop_queue_02 = {
    "name":"tv_mac_ipv6_tcp_drop_queue_02",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1518 / tcp src is 25 dst is 23 / end actions drop / end",
    "matched":{"scapy_str":['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518")/TCP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_output_log_drop,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IPv6(src="BCBC:910A:2222:5498:8475:1111:3900:8220")/TCP(sport=62,dport=11)/("X"*480)'],
                  "check_func":{"func":rfc.check_output_log_drop_mismatched,
                                "param":{"expect_port":0, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":1}}
}

tvs_mac_ipv4_non_pipeline_mode = [
    tv_mac_ipv4_in_queue_01,
    tv_mac_ipv4_drop_queue_02
    ]

tvs_mac_ipv4_udp_non_pipeline_mode = [
    tv_mac_ipv4_udp_in_queue_01, 
    tv_mac_ipv4_udp_drop_queue_02 
    ]

tvs_mac_ipv4_tcp_non_pipeline_mode = [
    tv_mac_ipv4_tcp_in_queue_01,
    tv_mac_ipv4_tcp_drop_queue_02
    ]

tvs_mac_ipv6_non_pipeline_mode = [
    tv_mac_ipv6_in_queue_01,
    tv_mac_ipv6_drop_queue_02
    ]

tvs_mac_ipv6_frag_non_pipeline_mode = [
    tv_mac_ipv6_frag_in_queue_01, 
    tv_mac_ipv6_frag_drop_queue_02
    ]

tvs_mac_ipv6_udp_non_pipeline_mode = [
    tv_mac_ipv6_udp_in_queue_01,
    tv_mac_ipv6_udp_drop_queue_02
    ]

tvs_mac_ipv6_tcp_non_pipeline_mode = [
    tv_mac_ipv6_tcp_in_queue_01,
    tv_mac_ipv6_tcp_drop_queue_02
    ]

test_results = OrderedDict()

class SwitchFilterTest(TestCase):

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

        #copy the file with fdir rules to dut, to make the fdir table full and then test switch filter
        src_file = 'dep/testpmd_cmds_rte_flow_fdir_rules'
        self.dut_file_dir = '/tmp'
        self.dut.session.copy_file_to(src_file, self.dut_file_dir)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.kill_all()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()

    def create_testpmd_command(self):
        """
        Create testpmd command for non-pipeline mode
        """
        #Prepare testpmd EAL and parameters
        all_eal_param = self.dut.create_eal_parameters(ports=[0])
        command = "./%s/app/testpmd %s --log-level=\"ice,8\" -- -i %s" % (self.dut.target, all_eal_param, "--rxq=8 --txq=8 --cmdline-file=/tmp/testpmd_cmds_rte_flow_fdir_rules")
        return command

    def create_testpmd_command_pipeline_mode(self):
        """
        Create testpmd command for pipeline mode
        """
        #Prepare testpmd EAL and parameters
        all_eal_param = self.dut.create_eal_parameters(ports=[0], port_options={0:"pipeline-mode-support=1"})
        command = "./%s/app/testpmd %s --log-level=\"ice,8\" -- -i %s" % (self.dut.target, all_eal_param, "--rxq=8 --txq=8")
        return command

    def get_rule_number(self,outstring):
        """
        get the rule number.
        """
        result_scanner = r'Flow rule #(\d+) created'
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(outstring)
        rule_num = int(m.group(1))
        return rule_num

    def send_and_check_packets(self, dic, port):
        """
        general packets processing workflow.
        """
        #Specify the port to use
        dic["check_func"]["param"]["expect_port"] = port

        self.dut.send_expect("start", "testpmd> ", 15)
        time.sleep(2)

        #send packets
        for per_packet in dic["scapy_str"]:
            pkt = Packet(pkt_str=per_packet)
            pkt.send_pkt(self.tester, tx_port=self.__tx_iface, count=1)

        out = self.dut.send_expect("stop", "testpmd> ")

        result_flag, log_msg = dic["check_func"]["func"](out, dic["check_func"]["param"], dic["expect_results"])
        return result_flag, log_msg

    def send_packet_get_queue(self, dic):
        """
        general packets processing workflow.
        """
        self.dut.send_expect("start", "testpmd> ")
        # send packets
        for per_packet in dic["scapy_str"]:
            pkt = Packet(pkt_str=per_packet)
            pkt.send_pkt(self.tester, tx_port=self.__tx_iface, count=1)
        out = self.dut.send_expect("stop", "testpmd> ")
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
        self.verify(q_len & (q_len - 1) == 0, "defualt_queue length is not power of 2!")
        for q in default_queue:
            if q in queue_list:
                queue_list.remove(q)
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
        return set_queue_list

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

    def _rte_flow_validate_pattern(self, test_vectors, command, is_vxlan):

        global test_results

        out = self.dut.send_expect(command, "testpmd> ", 300)
        self.dut.send_expect("port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd", "testpmd> ", 15)
        if is_vxlan:
            self.dut.send_expect("rx_vxlan_port add 4789 0", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)
        time.sleep(2)

        overall_result = True
        test_results.clear()
        for tv in test_vectors:
            # get packet default_queue number
            mismatched_dic = tv["mismatched"]
            default_queue = self.send_packet_get_queue(mismatched_dic)

            # check if default_queue same with expect_queue
            expect_queue = tv["mismatched"]["check_func"]["param"]["expect_queues"]
            if expect_queue != "null":
                if isinstance(expect_queue, int):
                    eq_list = []
                    eq_list.append(expect_queue)
                elif isinstance(expect_queue, list):
                    eq_list = expect_queue
                recover_flag = list(set(eq_list) & set(default_queue))
            else:
                recover_flag = None

            # if default_queue has same one with expect_queue, recover rule
            if recover_flag:
                # exclude defult_queue number and get set_queue
                set_queue_list = self.get_available_queue_num(default_queue, eq_list)
                # recover rule command and check queue
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
            else:
                rule_command = tv["rte_flow_pattern"]

            pattern_name = tv["name"]
            test_results[pattern_name] = OrderedDict()

            out = self.dut.send_expect(rule_command, "testpmd> ", 15)  #create a rule
            #get the rule number
            rule_num = self.get_rule_number(out)

            #check whether the switch rule or fdir rule is created
            if "Succeeded to create (2) flow" not in out:
                result_flag = False
                log_msg = "The rule is not created as switch."
                overall_result = self.save_results(pattern_name, "rule", result_flag, log_msg, overall_result)
                self.dut.send_expect("flow destroy %d rule %d" % (self.dut_ports[0], rule_num), "testpmd> ")
                continue

            #check if the rule is in list
            out = self.dut.send_expect("flow list %d" % self.dut_ports[0], "testpmd> ", 15)
            rule_in_list_flag = rfc.check_rule_in_list_by_id(out, rule_num)   #check if the rule still in list
            if not rule_in_list_flag:
                result_flag = False
                log_msg = "Flow rule #%d is not in list." % rule_num
                overall_result = self.save_results(pattern_name, "rule", result_flag, log_msg, overall_result)
                self.dut.send_expect("flow destroy %d rule %d" % (self.dut_ports[0], rule_num), "testpmd> ")
                continue

            #matched part
            matched_dic = tv["matched"]
            result_flag, log_msg = self.send_and_check_packets(matched_dic, self.dut_ports[0])
            overall_result = self.save_results(pattern_name, "matched", result_flag, log_msg, overall_result)

            #mismatched part
            mismatched_dic = tv["mismatched"]
            if len(list(mismatched_dic.keys())) != 0:
                result_flag, log_msg = self.send_and_check_packets(mismatched_dic, self.dut_ports[0])
                overall_result = self.save_results(pattern_name, "mismatched", result_flag, log_msg, overall_result)

            self.dut.send_expect("flow destroy %d rule %d" % (self.dut_ports[0], rule_num), "testpmd> ")
            out = self.dut.send_expect("flow list %d" % self.dut_ports[0], "testpmd> ", 15)
            #check if the rule has been destroyed
            rule_in_list_flag = rfc.check_rule_in_list_by_id(out, rule_num)   #check if the rule still in list
            if rule_in_list_flag:
                result_flag = False
                log_msg = "Flow rule #%d still exists, not been destroyed." % rule_num
            else:
                #send matched packets, check the packets not to the corresponding queues
                check_destroy_dict = copy.deepcopy(matched_dic)
                check_destroy_dict["check_func"]["func"] = mismatched_dic["check_func"]["func"]
                result_flag, log_msg = self.send_and_check_packets(check_destroy_dict, self.dut_ports[0])
            overall_result = self.save_results(pattern_name, "destroy", result_flag, log_msg, overall_result)

        #check if the rules are all destroyed
        self.dut.send_expect("flow flush %d" % self.dut_ports[0], "testpmd> ")
        out = self.dut.send_expect("flow list %d" % self.dut_ports[0], "testpmd> ", 15)
        out_lines=out.splitlines()
        if len(out_lines) == 1:
            result_flag = True
            log_msg = ""
        else:
            result_flag = False
            log_msg = "flow flush failed, rules still exist."

        #save the result of executing the command "flow flush 0"
        pattern_name = "flow flush %d" % self.dut_ports[0]
        test_results[pattern_name] = OrderedDict()
        overall_result = self.save_results(pattern_name, "flush", result_flag, log_msg, overall_result)

        self.dut.send_expect("quit", "#")
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
        self.verify(overall_result == True, "Some test case failed.")

    #vxlan non-pipeline mode
    def test_mac_ipv4_vxlan_ipv4_frag(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_ipv4_frag, command, is_vxlan = True)

    def test_mac_ipv4_vxlan_ipv4_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_ipv4_pay, command, is_vxlan = True)

    def test_mac_ipv4_vxlan_ipv4_udp_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_ipv4_udp_pay, command, is_vxlan = True)

    def test_mac_ipv4_vxlan_ipv4_tcp(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_ipv4_tcp, command, is_vxlan = True)

    def test_mac_ipv4_vxlan_mac_ipv4_frag(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_mac_ipv4_frag, command, is_vxlan = True)

    def test_mac_ipv4_vxlan_mac_ipv4_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_mac_ipv4_pay, command, is_vxlan = True)

    def test_mac_ipv4_vxlan_mac_ipv4_udp_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_mac_ipv4_udp_pay, command, is_vxlan = True)

    def test_mac_ipv4_vxlan_mac_ipv4_tcp(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_mac_ipv4_tcp, command, is_vxlan = True)

    #nvgre non-pipeline mode
    def test_mac_ipv4_nvgre_ipv4_frag(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_ipv4_frag, command, is_vxlan = False)

    def test_mac_ipv4_nvgre_ipv4_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_ipv4_pay, command, is_vxlan = False)

    def test_mac_ipv4_nvgre_ipv4_udp_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_ipv4_udp_pay, command, is_vxlan = False)

    def test_mac_ipv4_nvgre_ipv4_tcp(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_ipv4_tcp, command, is_vxlan = False)

    def test_mac_ipv4_nvgre_mac_ipv4_frag(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_mac_ipv4_frag, command, is_vxlan = False)

    def test_mac_ipv4_nvgre_mac_ipv4_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_mac_ipv4_pay, command, is_vxlan = False)

    def test_mac_ipv4_nvgre_mac_ipv4_udp_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_mac_ipv4_udp_pay, command, is_vxlan = False)

    def test_mac_ipv4_nvgre_mac_ipv4_tcp(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_mac_ipv4_tcp, command, is_vxlan = False)

    #pppoed non-pipeline mode
    def test_mac_pppod_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppod_pay, command, is_vxlan = False)

    #pppoes non-pipeline mode
    def test_mac_pppoe_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_pay, command, is_vxlan = False)

    def non_support_test_mac_pppoe_ipv4_frag(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_frag, command, is_vxlan = False)

    def test_mac_pppoe_ipv4_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_pay, command, is_vxlan = False)

    def not_support_test_mac_pppoe_ipv4_udp_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_udp_pay, command, is_vxlan = False)

    def not_support_test_mac_pppoe_ipv4_tcp(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_tcp, command, is_vxlan = False)

    def not_support_test_mac_pppoe_ipv4_sctp(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_sctp, command, is_vxlan = False)

    def not_support_test_mac_pppoe_ipv4_icmp(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv4_icmp, command, is_vxlan = False)

    def not_support_test_mac_pppoe_ipv6_frag(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_frag, command, is_vxlan = False)

    def not_support_test_mac_pppoe_ipv6_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_pay, command, is_vxlan = False)

    def not_support_test_mac_pppoe_ipv6_udp_pay(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_udp_pay, command, is_vxlan = False)

    def not_support_test_mac_pppoe_ipv6_tcp(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_tcp, command, is_vxlan = False)

    def not_support_test_mac_pppoe_ipv6_sctp(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_sctp, command, is_vxlan = False)

    def not_support_test_mac_pppoe_ipv6_icmpv6(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_pppoe_ipv6_icmpv6, command, is_vxlan = False)

    #vxlan pipeline mode
    def test_mac_ipv4_vxlan_ipv4_frag_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_ipv4_frag_pipeline_mode, command, is_vxlan = True)

    def test_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_ipv4_udp_pay_pipeline_mode, command, is_vxlan = True)

    def test_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_vxlan_ipv4_tcp_pipeline_mode, command, is_vxlan = True)

    #nvgre pipeline mode
    def test_mac_ipv4_nvgre_ipv4_frag_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_ipv4_frag_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_ipv4_udp_pay_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_nvgre_ipv4_tcp_pipeline_mode, command, is_vxlan = False)

    #non-tunnel pipeline mode
    def test_mac_ipv4_frag_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_frag_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv4_pay_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_pay_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv4_udp_pay_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_udp_pay_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv4_tcp_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_tcp_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv6_frag_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv6_frag_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv6_udp_pay_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv6_udp_pay_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv6_tcp_pipeline_mode(self):
        command = self.create_testpmd_command_pipeline_mode()
        self._rte_flow_validate_pattern(tvs_mac_ipv6_tcp_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv4_non_pipeline_mode(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_non_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv4_udp_non_pipeline_mode(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_udp_non_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv4_tcp_non_pipeline_mode(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv4_tcp_non_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv6_non_pipeline_mode(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv6_non_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv6_frag_non_pipeline_mode(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv6_frag_non_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv6_udp_non_pipeline_mode(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv6_udp_non_pipeline_mode, command, is_vxlan = False)

    def test_mac_ipv6_tcp_non_pipeline_mode(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_ipv6_tcp_non_pipeline_mode, command, is_vxlan = False)

