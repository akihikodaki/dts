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

from test_case import TestCase, skip_unsupported_pkg, check_supported_nic
from pmd_output import PmdOutput
from packet import Packet
from utils import BLUE, RED, GREEN
import rte_flow_common as rfc

import os

tv_mac_pay = {
    "name":"tv_mac_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth src is 00:00:00:00:00:01 dst is 00:11:22:33:44:55 type is 0x0800 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="00:00:00:00:00:01",dst="00:11:22:33:44:55")/IP()/Raw("x" *80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="00:00:00:00:00:02",dst="00:11:22:33:44:55")/IP()/Raw("x" *80)',
                               'Ether(src="00:00:00:00:00:01",dst="00:11:22:33:44:54")/IP()/Raw("x" *80)',
                               'Ether(src="00:00:00:00:00:01",dst="00:11:22:33:44:55")/IPv6()/Raw("x" *80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_frag = {
    "name":"tv_mac_ipv4_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2,frag=5)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2,frag=5)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4",dst="192.168.0.2",tos=4,ttl=2,frag=5)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.5",tos=4,ttl=2,frag=5)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=2,frag=5)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3,frag=5)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_pay = {
    "name":"tv_mac_ipv4_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 6 tos is 4 ttl is 2 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.5",tos=4,ttl=2)/TCP()/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=2)/TCP()/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP()/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/UDP()/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_udp_pay = {
    "name":"tv_mac_ipv4_udp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.5",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.7",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=3)/UDP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=9)/UDP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=30,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=19)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_tcp_pay = {
    "name":"tv_mac_ipv4_tcp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.5",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.7",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=3)/TCP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=9)/TCP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=30,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=19)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_igmp = {
    "name":"tv_mac_ipv4_igmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 proto is 0x02 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/IP()/IGMP()/Raw("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw("X"*480)',
                               'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/Raw("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv6_srcip_dstip = {
    "name":"tv_mac_ipv6_srcip_dstip",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
                            'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
                               'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/("X"*480)',
                               'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
                               'Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv6_dstip_tc = {
    "name":"tv_mac_ipv6_dstip_tc",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/("X"*480)',
                            'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv6_udp_pay = {
    "name":"tv_mac_ipv6_udp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/UDP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=7)/UDP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=30,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=19)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv6_tcp = {
    "name":"tv_mac_ipv6_tcp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/TCP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=7)/TCP(sport=25,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=30,dport=23)/("X"*480)',
                               'Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=19)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_nvgre_ipv4_pay = {
    "name":"tv_mac_ipv4_nvgre_ipv4_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_nvgre_ipv4_udp_pay = {
    "name":"tv_mac_ipv4_nvgre_ipv4_udp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.5", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.7")/UDP(sport=50,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_nvgre_ipv4_tcp = {
    "name":"tv_mac_ipv4_nvgre_ipv4_tcp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.5", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=20,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=39)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_nvgre_mac_ipv4_pay = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_nvgre_mac_ipv4_udp_pay = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_udp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a2")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw("x"*80)]',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_nvgre_mac_ipv4_tcp = {
    "name":"tv_mac_ipv4_nvgre_mac_ipv4_tcp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a2")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.5", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw("x"*80)',
                               'Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_ip_multicast = {
    "name":"tv_ip_multicast",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="239.0.0.0")/TCP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="128.0.0.0")/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_l2_multicast = {
    "name":"tv_l2_multicast",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst spec 01:00:5e:00:00:00 dst mask ff:ff:ff:80:00:00 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="01:00:5e:7f:00:00")/IP()/TCP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="01:00:5e:ff:00:00")/IP()/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_ethertype_filter_pppod = {
    "name":"tv_ethertype_filter_pppod",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8863 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x" *80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x" *80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_ethertype_filter_pppoe = {
    "name":"tv_ethertype_filter_pppoe",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x8864 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_ethertype_filter_ipv6 = {
    "name":"tv_ethertype_filter_ipv6",
    "rte_flow_pattern":"flow create 0 ingress pattern eth type is 0x86dd / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", tc=3)/TCP(dport=23)/("X"*480)',
                            'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", tc=3)/TCP(dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/IP()/TCP(dport=23)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_udp_port_filter_dhcp_discovery = {
    "name":"tv_udp_port_filter_dhcp_discovery",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp src is 68 dst is 67 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=68,dport=67)/BOOTP(chaddr="3c:fd:fe:b2:43:90")/DHCP(options=[("message-type","discover"),"end"])/Raw("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=63,dport=67)/BOOTP(chaddr="3c:fd:fe:b2:43:90")/DHCP(options=[("message-type","discover"),"end"])/Raw("X"*480)',
                               'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=68,dport=69)/BOOTP(chaddr="3c:fd:fe:b2:43:90")/DHCP(options=[("message-type","discover"),"end"])/Raw("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_udp_port_filter_dhcp_offer = {
    "name":"tv_udp_port_filter_dhcp_offer",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp src is 67 dst is 68 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=67,dport=68)/BOOTP(chaddr="3c:fd:fe:b2:43:90",yiaddr="192.168.1.0")/DHCP(options=[("message-type","offer"),"end"])/Raw("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=63,dport=68)/BOOTP(chaddr="3c:fd:fe:b2:43:90",yiaddr="192.168.1.0")/DHCP(options=[("message-type","offer"),"end"])/Raw("X"*480)',
                               'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=67,dport=63)/BOOTP(chaddr="3c:fd:fe:b2:43:90",yiaddr="192.168.1.0")/DHCP(options=[("message-type","offer"),"end"])/Raw("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_udp_port_filter_vxlan = {
    "name":"tv_udp_port_filter_vxlan",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp dst is 4789 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/TCP()/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_filter = {
    "name":"tv_mac_vlan_filter",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_vlan_filter = {
    "name":"tv_vlan_filter",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_l2tpv3 = {
    "name":"tv_mac_ipv4_l2tpv3",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":["Ether(dst='00:11:22:33:44:12')/IP(src='192.168.0.2', proto=115)/L2TP(b'\\x00\\x00\\x00\\x01')/('X'*480)"],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":["Ether(dst='00:11:22:33:44:12')/IP(src='192.168.0.2', proto=115)/L2TP(b'\\x00\\x00\\x00\\x02')/('X'*480)",
                               "Ether(dst='00:11:22:33:44:12')/IP(src='192.168.1.2', proto=115)/L2TP(b'\\x00\\x00\\x00\\x01')/('X'*480)",
                               "Ether(dst='00:11:22:33:44:12')/IP(dst='192.168.0.2', proto=115)/L2TP(b'\\x00\\x00\\x00\\x01')/('X'*480)"],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv6_l2tpv3 = {
    "name":"tv_mac_ipv6_l2tpv3",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / l2tpv3oip session_id is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":["Ether(dst='00:11:22:33:44:13')/IPv6(dst='1111:2222:3333:4444:5555:6666:7777:8888', nh=115)/L2TP(b'\\x00\\x00\\x00\\x01')/('X'*480)"],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":["Ether(dst='00:11:22:33:44:13')/IPv6(dst='1111:2222:3333:4444:5555:6666:7777:8888', nh=115)/L2TP(b'\\x00\\x00\\x00\\x02')/('X'*480)",
                               "Ether(dst='00:11:22:33:44:13')/IPv6(dst='1111:2222:3333:4444:5555:6666:7777:9999', nh=115)/L2TP(b'\\x00\\x00\\x00\\x01')/('X'*480)",
                               "Ether(dst='00:11:22:33:44:13')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888', nh=115)/L2TP(b'\\x00\\x00\\x00\\x01')/('X'*480)"],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_esp = {
    "name":"tv_mac_ipv4_esp",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=50)/ESP(spi=1)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:22")/IP(src="192.168.0.2", proto=50)/ESP(spi=2)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:22")/IP(src="192.168.1.2", proto=50)/ESP(spi=1)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IP(dst="192.168.0.2", proto=50)/ESP(spi=1)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv6_esp = {
    "name":"tv_mac_ipv6_esp",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / esp spi is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=50)/ESP(spi=1)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=50)/ESP(spi=2)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999", nh=50)/ESP(spi=1)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", nh=50)/ESP(spi=1)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_ah = {
    "name":"tv_mac_ipv4_ah",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=51)/AH(spi=1)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=51)/AH(spi=2)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IP(src="192.168.10.2", proto=51)/AH(spi=1)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IP(dst="192.168.0.2", proto=51)/AH(spi=1)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv6_ah = {
    "name":"tv_mac_ipv6_ah",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / ah spi is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=51)/AH(spi=1)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=51)/AH(spi=2)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999", nh=51)/AH(spi=1)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", nh=51)/AH(spi=1)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_nat_t_esp = {
    "name":"tv_mac_ipv4_nat_t_esp",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / udp / esp spi is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2")/UDP(dport=4500)/ESP(spi=1)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2")/UDP(dport=4500)/ESP(spi=2)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IP(src="192.168.1.2")/UDP(dport=4500)/ESP(spi=1)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IP(dst="192.168.0.2")/UDP(dport=4500)/ESP(spi=1)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv6_nat_t_esp = {
    "name":"tv_mac_ipv6_nat_t_esp",
    "rte_flow_pattern":"flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / udp / esp spi is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=1)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=2)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999")/UDP(dport=4500)/ESP(spi=1)/("X"*480)',
                               'Ether(dst="00:11:22:33:44:13")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=1)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_pfcp_node = {
    "name":"tv_mac_ipv4_pfcp_node",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=0)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=1)',
                               'Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=0)',
                               'Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=1)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv4_pfcp_session = {
    "name":"tv_mac_ipv4_pfcp_session",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=1)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=0)',
                               'Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=0)',
                               'Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=1)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv6_pfcp_node = {
    "name":"tv_mac_ipv6_pfcp_node",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=0)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=0)',
                               'Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=1)',
                               'Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=1)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_ipv6_pfcp_session = {
    "name":"tv_mac_ipv6_pfcp_session",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=1)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=0)',
                               'Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=1)',
                               'Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=0)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id = {
    "name":"tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id = {
    "name":"tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv4_pay_session_id_proto_id = {
    "name":"tv_mac_pppoe_ipv4_pay_session_id_proto_id",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv6_pay_session_id_proto_id = {
    "name":"tv_mac_pppoe_ipv6_pay_session_id_proto_id",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x00\\x57\')/IPv6()/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv4_pay_ip_address = {
    "name":"tv_mac_pppoe_ipv4_pay_ip_address",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv4_udp_pay = {
    "name":"tv_mac_pppoe_ipv4_udp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port = {
    "name":"tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv4_tcp_pay = {
    "name":"tv_mac_pppoe_ipv4_tcp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port = {
    "name":"tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv6_pay_ip_address = {
    "name":"tv_mac_pppoe_ipv6_pay_ip_address",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv6_udp_pay = {
    "name":"tv_mac_pppoe_ipv6_udp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port = {
    "name":"tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv6_tcp_pay = {
    "name":"tv_mac_pppoe_ipv6_tcp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port = {
    "name":"tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv4_pay_ip_address = {
    "name":"tv_mac_vlan_pppoe_ipv4_pay_ip_address",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv4_udp_pay = {
    "name":"tv_mac_vlan_pppoe_ipv4_udp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port = {
    "name":"tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv4_tcp_pay = {
    "name":"tv_mac_vlan_pppoe_ipv4_tcp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port = {
    "name":"tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv6_pay_ip_address = {
    "name":"tv_mac_vlan_pppoe_ipv6_pay_ip_address",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)',
                               'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv6_udp_pay = {
    "name":"tv_mac_vlan_pppoe_ipv6_udp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port = {
    "name":"tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv6_tcp_pay = {
    "name":"tv_mac_vlan_pppoe_ipv6_tcp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port = {
    "name":"tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x57\')/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_lcp_pay = {
    "name":"tv_mac_pppoe_lcp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_pppoe_ipcp_pay = {
    "name":"tv_mac_pppoe_ipcp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_lcp_pay = {
    "name":"tv_mac_vlan_pppoe_lcp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\xc0\\x21\')/PPP_LCP()/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_mac_vlan_pppoe_ipcp_pay = {
    "name":"tv_mac_vlan_pppoe_ipcp_pay",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{"scapy_str":['Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(b\'\\x80\\x21\')/PPP_IPCP()/Raw("x" * 80)',
                               'Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}


class CVLDCFFlowPriorityTest(TestCase):
    supported_nic = ['columbiaville_100g', 'columbiaville_25g', 'columbiaville_25gx2']

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

    @check_supported_nic(supported_nic)
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
        #bind pf to kernel
        self.bind_nics_driver(self.dut_ports, driver="ice")

        #set vf driver
        self.vf_driver = 'vfio-pci'
        self.dut.send_expect('modprobe vfio-pci', '#')
        self.path = self.dut.apps_name['test-pmd']

    def setup_1pf_vfs_env(self, pf_port=0, driver='default'):

        self.used_dut_port_0 = self.dut_ports[pf_port]
        #get PF interface name
        self.pf0_intf = self.dut.ports_info[self.used_dut_port_0]['intf']
        self.dut.send_expect('ethtool --set-priv-flags %s vf-vlan-prune-disable on' % self.pf0_intf, '#')
        #generate 4 VFs on PF
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 4, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]['vfs_port']
        #set VF0 as trust
        self.dut.send_expect('ip link set %s vf 0 trust on' % self.pf0_intf, '#')
        #bind VFs to dpdk driver
        for port in self.sriov_vfs_port_0:
            port.bind_driver(self.vf_driver)
        time.sleep(5)

    def set_up(self):
        """
        Run before each test case.
        """
        #Switch's recpri resource cannot be released,so need to reload ice driver to release it, this is a known issue of ND
        self.dut.send_expect("rmmod ice","#",30)
        self.dut.send_expect("modprobe ice","#",30)
  
    def create_testpmd_command(self):
        """
        Create testpmd command
        """
        #Prepare testpmd EAL and parameters
        vf0_pci = self.sriov_vfs_port_0[0].pci
        vf1_pci = self.sriov_vfs_port_0[1].pci
        vf2_pci = self.sriov_vfs_port_0[2].pci
        vf3_pci = self.sriov_vfs_port_0[3].pci
        all_eal_param = self.dut.create_eal_parameters(cores='1S/4C/1T',ports=[vf0_pci, vf1_pci, vf2_pci, vf3_pci], port_options={vf0_pci:"cap=dcf"})
        command = self.path + all_eal_param + " -- -i"
        return command

    def launch_testpmd(self):
        """
        launch testpmd with the command
        """
        command = self.create_testpmd_command()
        out = self.dut.send_expect(command, "testpmd> ", 15)
        self.testpmd_status = "running"
        #self.dut.send_expect("set portlist 1", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)

    def send_and_check_packets(self, dic, session_name="", tx_iface=""):
        """
        general packets processing workflow.
        """
        if session_name == "":
            session_name = self.dut
        if tx_iface == "":
            tx_iface = self.__tx_iface
        session_name.send_expect("start", "testpmd> ", 15)
        time.sleep(2)
        #send packets
        self.pkt.update_pkt(dic["scapy_str"])
        self.pkt.send_pkt(self.tester, tx_port=tx_iface, count=1, timeout=370)
        time.sleep(3)
        out = session_name.send_expect("stop", "testpmd> ", 15)
        dic["check_func"]["func"](out, dic["check_func"]["param"], dic["expect_results"])

    def validate_switch_filter_rule(self, rte_flow_pattern, session_name="", check_stats=True):
        """
        validate switch filter rules
        """
        if session_name == "":
            session_name = self.dut
        p = "Flow rule validated"
        rule_list = []
        if isinstance(rte_flow_pattern, list):
            for rule in rte_flow_pattern:
                length = len(rule)
                rule_rep = rule[0:5] + "validate" + rule[11:length]
                out = session_name.send_expect(rule_rep, "testpmd> ")  #validate a rule
                if (p in out) and ("Failed" not in out):
                    rule_list.append(True)
                else:
                    rule_list.append(False)
        elif isinstance(rte_flow_pattern, str):
            length = len(rte_flow_pattern)
            rule_rep = rte_flow_pattern[0:5] + "validate" + rte_flow_pattern[11:length]
            out = session_name.send_expect(rule_rep, "testpmd> ")  #validate a rule
            if (p in out) and ("Failed" not in out):
                rule_list.append(True)
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            self.verify(all(rule_list), "some rules not validated successfully, result %s, rule %s" % (rule_list, rte_flow_pattern))
        else:
            self.verify(not any(rule_list), "all rules should not validate successfully, result %s, rule %s" % (rule_list, rte_flow_pattern))

    def create_switch_filter_rule(self, rte_flow_pattern, session_name="", check_stats=True):
        """
        create switch filter rules
        """
        if session_name == "":
            session_name = self.dut
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        if isinstance(rte_flow_pattern, list):
            for rule in rte_flow_pattern:
                out = session_name.send_expect(rule, "testpmd> ")  #create a rule
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        else:
            out = session_name.send_expect(rte_flow_pattern, "testpmd> ")  #create a rule
            m = p.search(out)
            if m:
                rule_list.append(m.group(1))
            else:
                rule_list.append(False)
        if check_stats:
            self.verify(all(rule_list), "some rules not created successfully, result %s, rule %s" % (rule_list, rte_flow_pattern))
        else:
            self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        return rule_list

    def check_switch_filter_rule_list(self, port_id, rule_list, session_name="", need_verify=True):
        """
        check the rules in list identical to ones in rule_list
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
            self.verify(result == rule_list,
                    "the rule list is not the same. expect %s, result %s" % (rule_list, result))
        else:
            return result

    def destroy_switch_filter_rule(self, port_id, rule_list, session_name="", need_verify=True):
        if session_name == "":
            session_name = self.dut
        p = re.compile(r"Flow rule #(\d+) destroyed")
        destroy_list = []
        if isinstance(rule_list, list):
            for i in rule_list:
                out = session_name.send_expect("flow destroy %s rule %s" % (port_id, i), "testpmd> ", 15)
                m = p.search(out)
                if m:
                    destroy_list.append(m.group(1))
                else:
                    destroy_list.append(False)
        else:
            out = session_name.send_expect("flow destroy %s rule %s" % (port_id, rule_list), "testpmd> ", 15)
            m = p.search(out)
            if m:
                destroy_list.append(m.group(1))
            else:
                destroy_list.append(False)
            rule_list = [rule_list]
        if need_verify:
            self.verify(destroy_list == rule_list, "flow rule destroy failed, expect %s result %s" % (rule_list, destroy_list))
        else:
            return destroy_list

    def _rte_flow_validate_pattern(self, test_vector, launch_testpmd=True):
        
        #launch testpmd
        if launch_testpmd:
            self.launch_testpmd()
        #add priority for rules
        rte_flow_pattern=test_vector["rte_flow_pattern"]
        length= len(rte_flow_pattern)
        rule1=rte_flow_pattern[0:14] + "priority 0" + rte_flow_pattern[13:length]
        rule2=rte_flow_pattern[0:14] + "priority 1" + rte_flow_pattern[13:length-7]+ "2" + rte_flow_pattern[length-6:length]
        rte_flow=[rule1, rule2]
        #validate 2 rule
        self.validate_switch_filter_rule(rte_flow)
        #create 2 rule
        rule_list = self.create_switch_filter_rule(rte_flow)
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        matched_dic = test_vector["matched"]
        matched_dic["check_func"]["param"]["expect_port"]=2
        self.send_and_check_packets(matched_dic)
        #send mismatched packets and check
        mismatched_dic = test_vector["mismatched"]
        mismatched_dic["check_func"]["param"]["expect_port"]=[1,2]
        mismatched_dic["expect_results"]["expect_pkts"]=[0,0]
        self.send_and_check_packets(mismatched_dic)
        #destroy rule with priority 1
        self.destroy_switch_filter_rule(0, rule_list[1])
        self.check_switch_filter_rule_list(0, ['0'])
        #send matched packets and check
        destroy_dict1 = copy.deepcopy(matched_dic)
        destroy_dict1["check_func"]["param"]["expect_port"]=1
        self.send_and_check_packets(destroy_dict1)
        #recreate rule with priority 1
        self.create_switch_filter_rule(rte_flow[1])
        self.check_switch_filter_rule_list(0, rule_list)
        #destroy rule with priority 0
        self.destroy_switch_filter_rule(0, rule_list[0])
        self.check_switch_filter_rule_list(0, ['1'])
        #send matched packets and check
        destroy_dict2 = copy.deepcopy(matched_dic)
        self.send_and_check_packets(destroy_dict2)
        #destroy rule with priority 1 and check
        self.destroy_switch_filter_rule(0, rule_list[1])
        self.check_switch_filter_rule_list(0, [])
        destroy_dict3 = copy.deepcopy(matched_dic)
        if isinstance(destroy_dict3["expect_results"]["expect_pkts"], list):
            destroy_dict3["expect_results"]["expect_pkts"] = [0]*len(destroy_dict3["expect_results"]["expect_pkts"])
        else:
            destroy_dict3["expect_results"]["expect_pkts"] = 0
        self.send_and_check_packets(destroy_dict3)

    
    def test_mac_ipv4_frag(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_frag)

    def test_mac_ipv4_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_pay)

    def test_mac_ipv4_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_udp_pay)

    def test_mac_ipv4_tcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_tcp_pay)

    def test_mac_ipv4_igmp(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_igmp)

    def test_mac_ipv6_srcip_dstip(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv6_srcip_dstip)

    def test_mac_ipv6_dstip_tc(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv6_dstip_tc)

    def test_mac_ipv6_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv6_udp_pay)

    def test_mac_ipv6_tcp(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv6_tcp)

    def test_mac_ipv4_nvgre_ipv4_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_nvgre_ipv4_pay)

    def test_mac_ipv4_nvgre_ipv4_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_nvgre_ipv4_udp_pay)

    def test_mac_ipv4_nvgre_ipv4_tcp(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_nvgre_ipv4_tcp)

    def test_mac_ipv4_nvgre_mac_ipv4_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_nvgre_mac_ipv4_pay)

    def test_mac_ipv4_nvgre_mac_ipv4_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_nvgre_mac_ipv4_udp_pay)

    def test_mac_ipv4_nvgre_mac_ipv4_tcp(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_nvgre_mac_ipv4_tcp)

    def test_ip_multicast(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_ip_multicast)

    def test_l2_multicast(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_l2_multicast)

    def test_ethertype_filter_pppod(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_ethertype_filter_pppod)

    def test_ethertype_filter_pppoe(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_ethertype_filter_pppoe)

    def test_ethertype_filter_ipv6(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_ethertype_filter_ipv6)

    def test_udp_port_filter_dhcp_discovery(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_udp_port_filter_dhcp_discovery)

    def test_udp_port_filter_dhcp_offer(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_udp_port_filter_dhcp_offer)

    def test_udp_port_filter_vxlan(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_udp_port_filter_vxlan)

    def test_mac_vlan_filter(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_filter)

    def test_vlan_filter(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_vlan_filter)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_ipv4_l2tpv3(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_l2tpv3)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_ipv6_l2tpv3(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv6_l2tpv3)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv4_esp(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_esp)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv6_esp(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv6_esp)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv4_ah(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_ah)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv6_ah(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv6_ah)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv4_nat_t_esp(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_nat_t_esp)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv6_nat_t_esp(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv6_nat_t_esp)
    
    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_ipv4_pfcp_node(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_pfcp_node)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_ipv4_pfcp_session(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv4_pfcp_session)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_ipv6_pfcp_node(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv6_pfcp_node)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_ipv6_pfcp_session(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_ipv6_pfcp_session)
    
    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv4_pay_session_id_proto_id(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_pay_session_id_proto_id)
    
    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv6_pay_session_id_proto_id(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_pay_session_id_proto_id)
    
    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv4_pay_session_id_proto_id(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_pay_session_id_proto_id)
    
    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv6_pay_session_id_proto_id(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_pay_session_id_proto_id)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv4_pay_ip_address(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_pay_ip_address)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv4_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_udp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv4_udp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_udp_pay_non_src_dst_port)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv4_tcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_tcp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv4_tcp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv4_tcp_pay_non_src_dst_port)
    
    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv6_pay_ip_address(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_pay_ip_address)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv6_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_udp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv6_udp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_udp_pay_non_src_dst_port)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv6_tcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_tcp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipv6_tcp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipv6_tcp_pay_non_src_dst_port)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv4_pay_ip_address(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_pay_ip_address)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv4_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_udp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_udp_pay_non_src_dst_port)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv4_tcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_tcp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv4_tcp_pay_non_src_dst_port)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv6_pay_ip_address(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_pay_ip_address)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv6_udp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_udp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_udp_pay_non_src_dst_port)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv6_tcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_tcp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipv6_tcp_pay_non_src_dst_port)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_lcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_lcp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_pppoe_ipcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pppoe_ipcp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_lcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_lcp_pay)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_vlan_pppoe_ipcp_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_vlan_pppoe_ipcp_pay)

    def test_negative_case(self):
        self.setup_1pf_vfs_env()
        #launch testpmd
        self.launch_testpmd()
        negative_rule=["flow create 0 priority 2 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 1 / end",
                       "flow create 0 priority a ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 1 / end",
                       "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 4 / end"]
        self.create_switch_filter_rule(negative_rule, check_stats=False)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_exclusive_case(self):
        self.setup_1pf_vfs_env()

        #subcase 1: same pattern/input set/action different priority
        self.launch_testpmd()
        rule=["flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 2 / end",
                   "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 2 / end"]
        rule_list=self.create_switch_filter_rule(rule)
        #self.check_switch_filter_rule_list(0, rule_list)
        matched_dic = {"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)'],
                       "check_func":{"func":rfc.check_vf_rx_packets_number,
                                     "param":{"expect_port":2, "expect_queue":"null"}},
                       "expect_results":{"expect_pkts":1}}
        self.send_and_check_packets(matched_dic)
        self.dut.send_expect("flow flush 0", "testpmd> ", 15)
        self.dut.send_expect("clear port stats all", "testpmd> ", 15)
        self.dut.send_expect("quit", "#", 15)

        #subcase 2: same pattern/input set/priority different action
        self.launch_testpmd()
        rule=["flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 1 / end",
                   "flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 2 / end"]
        rule_list=self.create_switch_filter_rule(rule)
        self.check_switch_filter_rule_list(0, rule_list)
        matched_dic = {"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)'],
                       "check_func":{"func":rfc.check_vf_rx_packets_number,
                                     "param":{"expect_port":[1,2], "expect_queue":"null"}},
                       "expect_results":{"expect_pkts":[1,1]}}
        self.send_and_check_packets(matched_dic)
        self.dut.send_expect("flow flush 0", "testpmd> ", 15)
        self.dut.send_expect("clear port stats all", "testpmd> ", 15)
        self.dut.send_expect("quit", "#", 15)

        #subcase 3: some rules overlap
        self.launch_testpmd()
        rule=["flow create 0 priority 0 ingress pattern eth / vlan / vlan / pppoes / pppoe_proto_id is 0x21 / end actions vf id 1 / end",
                   "flow create 0 priority 0 ingress pattern eth / vlan / vlan tci is 2 / end actions vf id 1 / end",
                   "flow create 0 priority 1 ingress pattern eth / vlan / vlan / pppoes seid is 1 / ipv4 / end actions vf id 2 / end",
                   "flow create 0 priority 1 ingress pattern eth dst is 00:00:00:01:03:03 / vlan / vlan / end actions vf id 2 / end",
                   "flow create 0 priority 1 ingress pattern eth dst is 00:00:00:01:03:03 / end actions vf id 3 / end",
                   "flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / vlan tci is 2 / end actions vf id 3 / end"]
        rule_list=self.create_switch_filter_rule(rule)
        self.check_switch_filter_rule_list(0, rule_list)
        matched_dic = {"scapy_str":['Ether(dst="00:00:00:01:03:03")/Dot1Q(vlan=1)/Dot1Q(vlan=2)/Raw("x"*480)'],
                       "check_func":{"func":rfc.check_vf_rx_packets_number,
                                     "param":{"expect_port":[2,3], "expect_queue":"null"}},
                       "expect_results":{"expect_pkts":[1,1]}}
        self.send_and_check_packets(matched_dic)
        self.dut.send_expect("flow destroy 0 rule 5", "testpmd> ", 15)
        self.send_and_check_packets(matched_dic)
        self.dut.send_expect("flow destroy 0 rule 4", "testpmd> ", 15)
        matched_dic["check_func"]["param"]["expect_port"]=2
        matched_dic["expect_results"]["expect_pkts"]=1
        self.send_and_check_packets(matched_dic)
        self.dut.send_expect("flow destroy 0 rule 3", "testpmd> ", 15)
        matched_dic["check_func"]["param"]["expect_port"]=1
        matched_dic["expect_results"]["expect_pkts"]=1
        self.send_and_check_packets(matched_dic)
        self.dut.send_expect("flow destroy 0 rule 1", "testpmd> ", 15)
        matched_dic["expect_results"]["expect_pkts"]=0
        self.send_and_check_packets(matched_dic)
        matched_dic = {"scapy_str":['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)'],
                       "check_func":{"func":rfc.check_vf_rx_packets_number,
                                     "param":{"expect_port":2, "expect_queue":"null"}},
                       "expect_results":{"expect_pkts":1}}
        self.send_and_check_packets(matched_dic)
        self.dut.send_expect("flow destroy 0 rule 2", "testpmd> ", 15)
        matched_dic["check_func"]["param"]["expect_port"]=1
        self.send_and_check_packets(matched_dic)
        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ", 15)
        matched_dic["expect_results"]["expect_pkts"]=0
        self.send_and_check_packets(matched_dic)

    def tear_down(self):
        """
        Run after each test case.
        """
        if self.testpmd_status != "close":
            # destroy all flow rules on DCF
            self.dut.send_expect("flow flush 0", "testpmd> ", 15)
            self.dut.send_expect("clear port stats all", "testpmd> ", 15)
            self.dut.send_expect("quit", "#", 15)
            #kill all DPDK application
            self.dut.kill_all()
            # destroy vfs
            for port_id in self.dut_ports:
                self.dut.destroy_sriov_vfs_by_port(port_id)
        self.testpmd_status = "close"
        if getattr(self, 'session_secondary', None):
            self.dut.close_session(self.session_secondary)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()

