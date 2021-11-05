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

tv_actions_vf_id_0 = {
    "name":"tv_actions_vf_id_0",
    "rte_flow_pattern":"flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 0 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":0, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":0}},
    "mismatched":{}
}


tv_add_existing_rules_but_with_different_vfs = {
    "name":"tv_add_existing_rules_but_with_different_vfs",
    "rte_flow_pattern":["flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end",
                        "flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 2 / end"],
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":[1, 2], "expect_queues":"null"}},
               "expect_results":{"expect_pkts":[1, 1]}},
    "mismatched":{}
}

tv_add_two_rules_with_one_rule_input_set_included_in_the_other = {
    "name":"tv_add_two_rules_with_one_rule_input_set_included_in_the_other",
    "rte_flow_pattern":["flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 / end actions vf id 1 / end",
                        "flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 2 / end"],
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":[1, 2], "expect_queues":"null"}},
               "expect_results":{"expect_pkts":[1, 1]}},
    "mismatched":{}
}

tv_test_fwd_with_single_vf = {
    "name":"tv_test_fwd_with_single_vf",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_tx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":1}},
    "mismatched":{}
}

tv_test_fwd_with_multi_vfs = {
    "name":"tv_test_fwd_with_multi_vfs",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 1 / end",
    "matched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)'],
               "check_func":{"func":rfc.check_vf_rx_tx_packets_number,
                             "param":{"expect_port":[1, 2], "expect_queues":"null"}},
               "expect_results":{"expect_pkts":[1, 0]}},
    "mismatched":{}
}

#max vfs case: rte_flow_pattern and matched packets will be generated by code.
tv_max_vfs = {
    "name":"tv_max_vfs",
    "rte_flow_pattern":[],
    "matched":{"scapy_str":[],
               "check_func":{"func":rfc.check_kernel_vf_rx_packets_number,
                             "param":{"expect_port":list(range(1, 64)), "expect_queues":"null"}},
               "expect_results":{"expect_pkts":[1]*63}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.167.0.0")/TCP()/Raw("X"*480)'],
                  "check_func":{"func":rfc.check_kernel_vf_rx_packets_number,
                                "param":{"expect_port":list(range(1, 64)), "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":[1]*63}}
}

tv_max_field_vectors = {
    "name":"tv_max_field_vectors",
    "rte_flow_pattern":["flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end",
                        "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.2 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 / end actions vf id 1 / end",
                        "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.3 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp dst is 23 / end actions vf id 1 / end"],
    "matched":{"scapy_str":['Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)',
                            'Ether()/IP(dst="192.168.0.3")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":3}},
    "mismatched":{"scapy_str":['Ether()/IP(dst="192.168.0.5")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

#max rule number case: rte_flow_pattern and matched packets will be generated by code, and rte_flow_pattern will be writed to file.
tv_max_rule_number = {
    "name":"tv_max_rule_number",
    "rte_flow_pattern":[],
    "matched":{"scapy_str":[],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1}},
               "expect_results":{"expect_pkts":32563}},
    "mismatched":{"scapy_str":['Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.167.0.1")/TCP(sport=25,dport=23)/("X"*480)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1}},
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

tv_add_two_rules_with_different_input_set_same_vf_id = {
    "name":"tv_add_two_rules_with_different_input_set_same_vf_id",
    "rte_flow_pattern":["flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end",
                        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 1 / end"],
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=0)',
                            'Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=1)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":1, "expect_queues":"null"}},
               "expect_results":{"expect_pkts":2}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=0)',
                               'Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=1)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":1, "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":0}}
}

tv_add_two_rules_with_different_input_set_different_vf_id = {
    "name":"tv_add_two_rules_with_different_input_set_different_vf_id",
    "rte_flow_pattern":["flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end",
                        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 2 / end"],
    "matched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=0)',
                            'Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=1)'],
               "check_func":{"func":rfc.check_vf_rx_packets_number,
                             "param":{"expect_port":[1, 2], "expect_queues":"null"}},
               "expect_results":{"expect_pkts":[1, 1]}},
    "mismatched":{"scapy_str":['Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=0)',
                               'Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(S=1)'],
                  "check_func":{"func":rfc.check_vf_rx_packets_number,
                                "param":{"expect_port":[1, 2], "expect_queues":"null"}},
                  "expect_results":{"expect_pkts":[0, 0]}}
}

tv_mac_ipv4_drop = {
    "name": "tv_mac_ipv4_drop",
    "rte_flow_pattern": "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions drop / end",
    "matched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1")/Raw("x"*80)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 0}},
    "mismatched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2")/Raw("x"*80)'],
                "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 1}}
}

tv_mac_ipv4_mask_drop = {
    "name": "tv_mac_ipv4_drop",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 255.255.255.255 / end actions drop / end",
    "matched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP(dst="224.0.0.0")/TCP()/Raw("x"*80)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 0}},
    "mismatched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP(dst="128.0.0.0")/TCP()/Raw("x"*80)'],
                "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 1}}
}

tv_mac_nvgre_drop = {
    "name": "tv_mac_nvgre_drop",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end",
    "matched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 0}},
    "mismatched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.1")/NVGRE(TNI=1)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)'],
                "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 1}}
}

tv_mac_ppoes_drop = {
    "name": "tv_mac_ppoes_drop",
    "rte_flow_pattern": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end",
    "matched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b"\\x00\\x21")/IP()/Raw("x" * 80)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 0}},
    "mismatched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=2)/PPP(b"\\x00\\x21")/IP()/Raw("x" * 80)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 1}}
}

tv_mac_pfcp_drop = {
    "name": "tv_mac_pfcp_drop",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions drop / end",
    "matched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=8805)/PFCP(S=0)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 0}},
    "mismatched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=8805)/PFCP(S=1)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 1}}
}

tv_mac_vlan_drop = {
    "name": "tv_mac_vlan_drop",
    "rte_flow_pattern": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions drop / end",
    "matched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*80)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 0}},
    "mismatched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*80)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 1}}
}

tv_mac_l2tp_drop = {
    "name": "tv_mac_l2tp_drop",
    "rte_flow_pattern": "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions drop / end",
    "matched": {"scapy_str": ["Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.2', proto=115)/L2TP(b'\\x00\\x00\\x00\\x01')/('X'*480)"],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 0}},
    "mismatched": {"scapy_str": ["Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.2', proto=115)/L2TP(b'\\x00\\x00\\x00\\x02')/('X'*480)"],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 1}}
}

tv_mac_esp_drop = {
    "name": "tv_mac_l2tp_drop",
    "rte_flow_pattern": "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions drop / end",
    "matched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2", proto=50)/ESP(spi=1)/("X"*480)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 0}},
    "mismatched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2", proto=50)/ESP(spi=2)/("X"*480)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 1}}
}

tv_mac_blend_pkg_drop = {
    "name": "tv_mac_blend_pkg_drop",
    "rte_flow_pattern": ["flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions drop / end",
                         "flow create 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 255.255.255.255 / end actions drop / end",
                         "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.3 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end",
                         "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end",
                         "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions drop / end",
                         "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions drop / end",
                         "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.4 / l2tpv3oip session_id is 1 / end actions drop / end",
                         "flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.5 / esp spi is 1 / end actions drop / end"],
    "matched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1")/Raw("x"*80)',
                              'Ether(dst="00:11:22:33:44:55")/IP(dst="224.0.0.0")/TCP()/Raw("x"*80)',
                              'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.3")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b"\\x00\\x21")/IP()/Raw("X" * 80)',
                              'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=8805)/PFCP(S=0)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*80)',
                              'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4", proto=115)/L2TP(b"\\x00\\x00\\x00\\x01")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.5", proto=50)/ESP(spi=1)/("X"*80)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 0}},
    "mismatched": {"scapy_str": ['Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.6")/Raw("x"*80)',
                                 'Ether(dst="00:11:22:33:44:55")/IP(dst="128.0.0.0")/TCP()/Raw("x"*80)',
                                 'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.8")/NVGRE(TNI=1)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)',
                                 'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=2)/PPP(b"\\x00\\x21")/IP()/Raw("x" * 80)',
                                 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=8805)/PFCP(S=1)',
                                 'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2)/IP(src="192.168.0.9",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*80)',
                                 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.10", proto=115)/L2TP(b"\\x00\\x00\\x00\\x02")/("X"*480)',
                                 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.11", proto=50)/ESP(spi=2)/("X"*80)'],
               "check_func": {"func": rfc.check_vf_rx_packets_number,
                             "param": {"expect_port": 1, "expect_queues": "null"}},
               "expect_results": {"expect_pkts": 8}}
}

sv_mac_test_drop_action = [
    tv_mac_ipv4_drop,
    tv_mac_ipv4_mask_drop,
    tv_mac_nvgre_drop,
    tv_mac_ppoes_drop,
    tv_mac_pfcp_drop,
    tv_mac_vlan_drop,
    tv_mac_l2tp_drop,
    tv_mac_esp_drop,
    tv_mac_blend_pkg_drop
]

class CVLDCFSwitchFilterTest(TestCase):
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
        self.used_dut_port_0 = self.dut_ports[0]
        self.pf0_intf = self.dut.ports_info[self.used_dut_port_0]['intf']
        self.__tx_iface = self.tester.get_interface(localPort)
        self.pkt = Packet()
        self.testpmd_status = "close"
        #bind pf to kernel
        self.bind_nics_driver(self.dut_ports, driver="ice")
        # get priv-flags default stats
        self.flag = 'vf-vlan-pruning'
        self.default_stats = self.dut.get_priv_flags_state(self.pf0_intf, self.flag)

        #set vf driver
        self.vf_driver = 'vfio-pci'
        self.dut.send_expect('modprobe vfio-pci', '#')
        self.path = self.dut.apps_name['test-pmd']

    def setup_1pf_vfs_env(self, pf_port=0, driver='default'):

        self.used_dut_port_0 = self.dut_ports[pf_port]
        #get PF interface name
        self.pf0_intf = self.dut.ports_info[self.used_dut_port_0]['intf']
        out = self.dut.send_expect('ethtool -i %s' % self.pf0_intf, '#')
        if self.default_stats:
            self.dut.send_expect('ethtool --set-priv-flags %s %s off' % (self.pf0_intf, self.flag), "# ")
        #generate 4 VFs on PF
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 4, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]['vfs_port']
        #set VF0 as trust
        self.dut.send_expect('ip link set %s vf 0 trust on' % self.pf0_intf, '#')
        #bind VFs to dpdk driver
        for port in self.sriov_vfs_port_0:
            port.bind_driver(self.vf_driver)
        time.sleep(5)

    def reload_ice(self):
        self.dut.send_expect("rmmod ice", "# ", 15)
        self.dut.send_expect("modprobe ice", "# ", 15)

    def set_up(self):
        """
        Run before each test case.
        """
        self.reload_ice()

    def create_testpmd_command(self):
        """
        Create testpmd command
        """
        #Prepare testpmd EAL and parameters
        vf0_pci = self.sriov_vfs_port_0[0].pci
        vf1_pci = self.sriov_vfs_port_0[1].pci
        all_eal_param = self.dut.create_eal_parameters(cores='1S/4C/1T',ports=[vf0_pci, vf1_pci], port_options={vf0_pci:"cap=dcf"})
        command = self.path + all_eal_param + " -- -i"
        return command

    def launch_testpmd(self):
        """
        launch testpmd with the command
        """
        command = self.create_testpmd_command()
        out = self.dut.send_expect(command, "testpmd> ", 15)
        self.testpmd_status = "running"
        self.dut.send_expect("set portlist 1", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)

    def send_packets(self, dic, session_name="", tx_iface=""):
        """
        send packets.
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
        out = session_name.send_expect("stop", "testpmd> ")
        return out

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

    def send_and_get_packets_bg(self, dic, session_name="", tx_iface=""):
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
        pkt = Packet()
        pkt.update_pkt(dic["scapy_str"])
        pkt.send_pkt_bg(self.tester, tx_port=tx_iface, count=1, loop=0, timeout=370)
        time.sleep(3)
        out = session_name.send_expect("stop", "testpmd> ", 15)
        results = dic["check_func"]["func"](out, dic["check_func"]["param"], dic["expect_results"], False)
        return results

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

    def get_kernel_vf_log(self, vf_intfs, session_name):
        """
        get the log of each kernel vf in list vf_intfs
        """
        out_vfs = []
        for intf in vf_intfs:
            out = session_name.send_expect('ifconfig %s' % intf, '#')
            out_vfs.append(out)
        return out_vfs

    def _rte_flow_validate_pattern(self, test_vector, launch_testpmd=True):

        if launch_testpmd:
            #launch testpmd
            self.launch_testpmd()
        #validate a rule
        self.validate_switch_filter_rule(test_vector["rte_flow_pattern"])
        #create a rule
        rule_list = self.create_switch_filter_rule(test_vector["rte_flow_pattern"])   #create a rule
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        matched_dic = test_vector["matched"]
        self.send_and_check_packets(matched_dic)
        #send mismatched packets and check
        mismatched_dic = test_vector["mismatched"]
        self.send_and_check_packets(mismatched_dic)
        #destroy rule and send matched packets
        self.destroy_switch_filter_rule(0, rule_list)
        self.check_switch_filter_rule_list(0, [])
        #send matched packets and check
        destroy_dict = copy.deepcopy(matched_dic)
        if isinstance(destroy_dict["expect_results"]["expect_pkts"], list):
            destroy_dict["expect_results"]["expect_pkts"] = [0]*len(destroy_dict["expect_results"]["expect_pkts"])
        else:
            destroy_dict["expect_results"]["expect_pkts"] = 0
        self.send_and_check_packets(destroy_dict)

    def test_mac_pay(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_mac_pay)

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

    def test_negative_case(self):
        """
        negative cases
        """
        #set up 4 vfs on 1 pf environment
        self.setup_1pf_vfs_env()
        #launch testpmd
        self.launch_testpmd()
        rules = {
            "cannot create rule on vf 1": "flow create 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end",
            "unsupported input set": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 tos is 4 / end actions vf id 1 / end",
            "invalid vf id": "flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 5 / end",
            "void action": "flow create 0 ingress pattern eth / ipv4 / udp src is 25 dst is 23 / end actions end",
            "void input set value": "flow create 0 ingress pattern eth / ipv4 / end actions vf id 1 end"
        }
        # cannot create rule on vf 1
        self.validate_switch_filter_rule(rules["cannot create rule on vf 1"], check_stats=False)
        self.check_switch_filter_rule_list(1, [])
        self.create_switch_filter_rule(rules["cannot create rule on vf 1"], check_stats=False)
        self.check_switch_filter_rule_list(1, [])

        # unsupported input set
        self.validate_switch_filter_rule(rules["unsupported input set"], check_stats=False)
        self.check_switch_filter_rule_list(0, [])
        self.create_switch_filter_rule(rules["unsupported input set"], check_stats=False)
        self.check_switch_filter_rule_list(0, [])

        # duplicated rues
        rule = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions vf id 1 / end"
        rule_list = self.create_switch_filter_rule(rule)   #create a rule
        self.check_switch_filter_rule_list(0, rule_list)
        self.create_switch_filter_rule(rule, check_stats=False)
        self.check_switch_filter_rule_list(0, rule_list)
        self.destroy_switch_filter_rule(0, rule_list)

        # void action
        self.validate_switch_filter_rule(rules["void action"], check_stats=False)
        self.check_switch_filter_rule_list(0, [])
        self.create_switch_filter_rule(rules["void action"], check_stats=False)
        self.check_switch_filter_rule_list(0, [])

        # void input set value
        self.validate_switch_filter_rule(rules["void input set value"], check_stats=False)
        self.check_switch_filter_rule_list(0, [])
        self.create_switch_filter_rule(rules["void input set value"], check_stats=False)
        self.check_switch_filter_rule_list(0, [])

        # invalid vf id
        # self.validate_switch_filter_rule(rules["invalid vf id"], check_stats=False)
        # self.check_switch_filter_rule_list(0, [])
        self.create_switch_filter_rule(rules["invalid vf id"], check_stats=False)
        self.check_switch_filter_rule_list(0, [])

        # delete non-existing rule
        #check no rule in the list
        self.check_switch_filter_rule_list(0, [])
        #destroy rule 0
        out = self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ", timeout=15)
        self.verify("Fail" not in out, "Destroy failed.")
        #flush rules
        out = self.dut.send_expect("flow flush 0", "testpmd> ", timeout=15)
        self.verify("Fail" not in out, "Destroy failed.")

        # add long switch rule
        rule = "flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 tc is 3 / end actions vf id 1 / end"
        self.validate_switch_filter_rule(rule, check_stats=False)
        self.check_switch_filter_rule_list(0, [])
        self.create_switch_filter_rule(rule, check_stats=False)
        self.check_switch_filter_rule_list(0, [])
        #create MAC_IPV6_UDP_PAY rule, and check the rule will not be affected by the long rule failure
        self._rte_flow_validate_pattern(tv_mac_ipv6_udp_pay, launch_testpmd=False)

    @skip_unsupported_pkg(['comms', 'wireless'])
    def test_unsupported_pattern_in_os_default(self):
        """
        test with os default package
        """
        #set up 4 vfs on 1 pf environment
        self.setup_1pf_vfs_env()
        #launch testpmd
        self.launch_testpmd()
        rules = [
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions vf id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions vf id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions vf id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / udp / esp spi is 1 / end actions vf id 1 / end"
        ]
        self.validate_switch_filter_rule(rules, check_stats=False)
        self.check_switch_filter_rule_list(0, [])
        self.create_switch_filter_rule(rules, check_stats=False)
        self.check_switch_filter_rule_list(0, [])

        self.dut.send_expect("flow flush 0", "testpmd> ", 300)
        self.dut.send_expect("quit", "#")
        self.testpmd_status = "close"
        # destroy vfs
        for port_id in self.dut_ports:
            self.dut.destroy_sriov_vfs_by_port(port_id)

    def test_add_existing_rules_but_with_different_vfs(self):
        #set up 4 vfs on 1 pf environment
        self.setup_1pf_vfs_env()
        #launch testpmd
        vf0_pci = self.sriov_vfs_port_0[0].pci
        vf1_pci = self.sriov_vfs_port_0[1].pci
        vf2_pci = self.sriov_vfs_port_0[2].pci
        all_eal_param = self.dut.create_eal_parameters(cores="1S/4C/1T", ports=[vf0_pci, vf1_pci, vf2_pci], port_options={vf0_pci:"cap=dcf"})
        command = self.path + all_eal_param + " -- -i"
        out = self.dut.send_expect(command, "testpmd> ", 15)
        self.testpmd_status = "running"
        self.dut.send_expect("set portlist 1,2", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)
        #create rules with same pattern but to different vfs
        rule_list = self.create_switch_filter_rule(tv_add_existing_rules_but_with_different_vfs["rte_flow_pattern"])
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        matched_dic = tv_add_existing_rules_but_with_different_vfs["matched"]
        self.send_and_check_packets(matched_dic)
        #destroy rule 0 and send matched packets
        self.destroy_switch_filter_rule(0, rule_list[0])
        rule_list.pop(0)
        #check only rule 1 exists in the list
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        destroy_dict = copy.deepcopy(matched_dic)
        destroy_dict["expect_results"]["expect_pkts"][0] = 0
        self.send_and_check_packets(destroy_dict)
        #destroy rule 1 and send matched packets
        self.destroy_switch_filter_rule(0, rule_list[0])
        rule_list.pop(0)
        #check no rule exists in the list
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        destroy_dict["expect_results"]["expect_pkts"][1] = 0
        self.send_and_check_packets(destroy_dict)

    def test_add_existing_rules_with_the_same_vfs(self):
        #set up 4 vfs on 1 pf environment
        self.setup_1pf_vfs_env()
        #launch testpmd
        self.launch_testpmd()
        #create a rule
        rule = "flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end"
        rule_list = self.create_switch_filter_rule(rule)   #create a rule
        self.check_switch_filter_rule_list(0, rule_list)
        #create the same rule
        self.create_switch_filter_rule(rule, check_stats=False)   #create a rule
        self.check_switch_filter_rule_list(0, rule_list)

    def test_add_two_rules_with_one_rule_input_set_included_in_the_other(self):
        #set up 4 vfs on 1 pf environment
        self.setup_1pf_vfs_env()
        #launch testpmd
        vf0_pci = self.sriov_vfs_port_0[0].pci
        vf1_pci = self.sriov_vfs_port_0[1].pci
        vf2_pci = self.sriov_vfs_port_0[2].pci
        all_eal_param = self.dut.create_eal_parameters(cores="1S/4C/1T", ports=[vf0_pci, vf1_pci, vf2_pci], port_options={vf0_pci:"cap=dcf"})
        command = self.path + all_eal_param + " -- -i"
        out = self.dut.send_expect(command, "testpmd> ", 15)
        self.testpmd_status = "running"
        self.dut.send_expect("set portlist 1,2", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)
        #create rules with one rule's input set included in the other
        rule_list = self.create_switch_filter_rule(tv_add_two_rules_with_one_rule_input_set_included_in_the_other["rte_flow_pattern"])
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        matched_dic = tv_add_two_rules_with_one_rule_input_set_included_in_the_other["matched"]
        self.send_and_check_packets(matched_dic)
        #send packet that only matches rule 0 but not rule 1
        matched_dic_1 = copy.deepcopy(matched_dic)
        matched_dic_1["scapy_str"].clear()
        matched_dic_1["scapy_str"].append('Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.3")/("X"*480)')
        matched_dic_1["expect_results"]["expect_pkts"][1] = 0
        self.send_and_check_packets(matched_dic_1)
        #destroy rule 0 and send matched packets
        self.destroy_switch_filter_rule(0, rule_list[0])
        rule_list.pop(0)
        #check only rule 1 exists in the list
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        destroy_dict = copy.deepcopy(matched_dic)
        destroy_dict["expect_results"]["expect_pkts"][0] = 0
        self.send_and_check_packets(destroy_dict)
        #destroy rule 1 and send matched packets
        self.destroy_switch_filter_rule(0, rule_list[0])
        rule_list.pop(0)
        #check no rule exists in the list
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        destroy_dict["expect_results"]["expect_pkts"][1] = 0
        self.send_and_check_packets(destroy_dict)

    def test_fwd_with_single_vf(self):
        #set up 4 vfs on 1 pf environment
        self.setup_1pf_vfs_env()
        #launch testpmd
        command = self.create_testpmd_command()
        out = self.dut.send_expect(command, "testpmd> ", 15)
        self.testpmd_status = "running"
        self.dut.send_expect("set portlist 1", "testpmd> ", 15)
        self.dut.send_expect("set fwd mac", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)
        #create a rule
        rule_list = self.create_switch_filter_rule(tv_test_fwd_with_single_vf["rte_flow_pattern"])   #create a rule
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check the vf received the packet and forwarded it
        matched_dic = tv_test_fwd_with_single_vf["matched"]
        #one vf, the rx packets are equal to tx packets
        tx_dic = copy.deepcopy(matched_dic)
        out = self.send_packets(matched_dic)
        matched_dic["check_func"]["func"](out, matched_dic["check_func"]["param"], matched_dic["expect_results"], tx_dic["check_func"]["param"], tx_dic["expect_results"])

    def test_fwd_with_multi_vfs(self):
        #set up 4 vfs on 1 pf environment
        self.setup_1pf_vfs_env()
        #launch testpmd
        vf0_pci = self.sriov_vfs_port_0[0].pci
        vf1_pci = self.sriov_vfs_port_0[1].pci
        vf2_pci = self.sriov_vfs_port_0[2].pci
        all_eal_param = self.dut.create_eal_parameters(cores="1S/4C/1T", ports=[vf0_pci, vf1_pci, vf2_pci], port_options={vf0_pci:"cap=dcf"})
        command = self.path + all_eal_param + " -- -i"
        out = self.dut.send_expect(command, "testpmd> ", 15)
        self.testpmd_status = "running"
        self.dut.send_expect("set portlist 1,2", "testpmd> ", 15)
        self.dut.send_expect("set fwd mac", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)
        #create a rule
        rule_list = self.create_switch_filter_rule(tv_test_fwd_with_multi_vfs["rte_flow_pattern"])
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check vf1 received the packet and forwarded to vf2
        matched_dic = tv_test_fwd_with_multi_vfs["matched"]
        #tx packets number on vf2
        tx_dic = copy.deepcopy(matched_dic)
        tx_dic["expect_results"]["expect_pkts"][0] = matched_dic["expect_results"]["expect_pkts"][1]
        tx_dic["expect_results"]["expect_pkts"][1] = matched_dic["expect_results"]["expect_pkts"][0]
        out = self.send_packets(matched_dic)
        matched_dic["check_func"]["func"](out, matched_dic["check_func"]["param"], matched_dic["expect_results"], tx_dic["check_func"]["param"], tx_dic["expect_results"])

    def test_max_vfs(self):
        # get max vfs number
        max_vf_number = int(256/(len(self.dut_ports)))
        #set up max_vf_number vfs on 1 pf environment
        self.used_dut_port_0 = self.dut_ports[0]
        self.pf0_intf = self.dut.ports_info[self.used_dut_port_0]['intf']
        out = self.dut.send_expect('ethtool -i %s' % self.pf0_intf, '#')
        #generate max_vf_number VFs on PF0
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, max_vf_number, driver='default')
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port_0]['vfs_port']

        for port in self.sriov_vfs_port:
            port.bind_driver('iavf')
        #sort the vf interfaces and pcis by pcis
        vfs = {}
        for vf_port in self.sriov_vfs_port:
            vfs[vf_port.pci] = vf_port.intf_name
        vfs_sort = sorted(vfs.items(), key=lambda item:item[0])
        vf_pci = [key for key,value in vfs_sort]
        vf_intf = [value for key,value in vfs_sort]
        #start the max_vf_number VFs in the kernel
        for intf in vf_intf:
            self.dut.send_expect('ifconfig %s up' % intf, '#')
        self.dut.send_expect('ip link set %s vf 0 trust on' % self.pf0_intf, '#')
        self.dut.send_expect('./usertools/dpdk-devbind.py -b %s %s' % (self.vf_driver, vf_pci[0]), '# ')
        time.sleep(5)
        vf_intf.pop(0)
        #launch testpmd
        vf0_pci = vf_pci[0]
        all_eal_param = self.dut.create_eal_parameters(cores="1S/4C/1T", ports=[vf0_pci], port_options={vf0_pci:"cap=dcf"})
        command = self.path + all_eal_param + " -- -i"
        out = self.dut.send_expect(command, "testpmd> ", 15)
        self.testpmd_status = "running"
        #generate max_vf_number-1 rules to each vf and matched packets
        for i in range(1,max_vf_number):
            rte_flow_pattern = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.%d / tcp / end actions vf id %d / end" % (i, i)
            tv_max_vfs["rte_flow_pattern"].append(rte_flow_pattern)
            matched_scapy_str = 'Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.%d")/TCP()/Raw("X"*480)' % i
            tv_max_vfs["matched"]["scapy_str"].append(matched_scapy_str)
        out = self.dut.send_expect("show port info all", "testpmd> ", 15)
        #create max_vf_number-1 rules
        rule_list = self.create_switch_filter_rule(tv_max_vfs["rte_flow_pattern"])
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        tv_max_vfs["matched"]["check_func"]["param"]["expect_port"] = list(range(1, max_vf_number))
        tv_max_vfs["matched"]["expect_results"]["expect_pkts"] = [1]*(max_vf_number-1)
        matched_dic = tv_max_vfs["matched"]
        out = self.send_packets(matched_dic)
        #check the max_vf_number-1 packets received by each vf
        self.session_secondary = self.dut.new_session(suite="session_secondary")
        #get the log of each kernel vf
        out_vfs = self.get_kernel_vf_log(vf_intf, self.session_secondary)
        matched_dic["check_func"]["func"](out_vfs, matched_dic["expect_results"]["expect_pkts"])
        #send mismatched packets and check
        tv_max_vfs["mismatched"]["check_func"]["param"]["expect_port"] = list(range(1, max_vf_number))
        tv_max_vfs["mismatched"]["expect_results"]["expect_pkts"] = [1]*(max_vf_number-1)
        mismatched_dic = tv_max_vfs["mismatched"]
        out = self.send_packets(mismatched_dic)
        #get the log of each kernel vf
        out_vfs = self.get_kernel_vf_log(vf_intf, self.session_secondary)
        # kernel vf will not clear the statistics automatically, the rx packets number is the same
        mismatched_dic["check_func"]["func"](out_vfs, mismatched_dic["expect_results"]["expect_pkts"])
        #destroy rules and send matched packets
        self.destroy_switch_filter_rule(0, rule_list)
        self.check_switch_filter_rule_list(0, [])
        #send matched packets and check
        destroy_dict = copy.deepcopy(matched_dic)
        out = self.send_packets(destroy_dict)
        # check the packets are not to any vf, and the statistics in each kernel vf are still the same.
        out_vfs = self.get_kernel_vf_log(vf_intf, self.session_secondary)
        #the kernel vf will not clear the statistics automatically, the rx packets number is still the same
        destroy_dict["check_func"]["func"](out_vfs, destroy_dict["expect_results"]["expect_pkts"])

    def test_max_field_vectors(self):
        #set up 4 vfs on 1 pf environment
        self.setup_1pf_vfs_env()
        #launch testpmd
        self.launch_testpmd()
        #create 3 nvgre rules, which have run out of field vectors
        rule_list = self.create_switch_filter_rule(tv_max_field_vectors["rte_flow_pattern"])   #create a rule
        self.check_switch_filter_rule_list(0, rule_list)
        #create a rule, check the rule can not be created successfully
        rule = "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.10 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a1  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions vf id 1 / end"
        self.create_switch_filter_rule(rule, check_stats=False)
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        matched_dic = tv_max_field_vectors["matched"]
        self.send_and_check_packets(matched_dic)
        #send mismatched packets and check
        mismatched_dic = tv_max_field_vectors["mismatched"]
        self.send_and_check_packets(mismatched_dic)
        #destroy rules and send matched packets
        self.destroy_switch_filter_rule(0, rule_list)
        self.check_switch_filter_rule_list(0, [])
        #send matched packets and check
        destroy_dict = copy.deepcopy(matched_dic)
        destroy_dict["expect_results"]["expect_pkts"] = 0
        self.send_and_check_packets(destroy_dict)

    def test_dcf_stop_start(self):
        #set up 4 vfs on 1 pf environment
        self.setup_1pf_vfs_env()
        #launch testpmd
        self.launch_testpmd()
        #create MAC_IPV4_UDP_PAY rule
        rule_list = self.create_switch_filter_rule(tv_mac_ipv4_udp_pay["rte_flow_pattern"])   #create a rule
        self.check_switch_filter_rule_list(0, rule_list)
        #send matched packets and check
        matched_dic = tv_mac_ipv4_udp_pay["matched"]
        self.send_and_check_packets(matched_dic)
        #stop the DCF, then start the DCF
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        #send matched packets, port 1 can not receive the packets.
        destroy_dict = copy.deepcopy(matched_dic)
        destroy_dict['expect_results'] = {"expect_pkts":0}
        self.send_and_check_packets(destroy_dict)

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
    def test_add_two_rules_with_different_input_set_same_vf_id(self):
        self.setup_1pf_vfs_env()
        self._rte_flow_validate_pattern(tv_add_two_rules_with_different_input_set_same_vf_id)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_add_two_rules_with_different_input_set_different_vf_id(self):
        #set up 4 vfs on 1 pf environment
        self.setup_1pf_vfs_env()
        #launch testpmd
        vf0_pci = self.sriov_vfs_port_0[0].pci
        vf1_pci = self.sriov_vfs_port_0[1].pci
        vf2_pci = self.sriov_vfs_port_0[2].pci
        all_eal_param = self.dut.create_eal_parameters(cores="1S/4C/1T", ports=[vf0_pci, vf1_pci, vf2_pci], port_options={vf0_pci:"cap=dcf"})
        command = self.path + all_eal_param + " -- -i"
        out = self.dut.send_expect(command, "testpmd> ", 15)
        self.testpmd_status = "running"
        self.dut.send_expect("set portlist 1,2", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)
        self._rte_flow_validate_pattern(tv_add_two_rules_with_different_input_set_different_vf_id, False)

    @skip_unsupported_pkg(['os default', 'wireless'])
    def test_mac_drop_action(self):
        self.setup_1pf_vfs_env()
        self.dut.send_expect('ip link set %s vf 1 mac "00:11:22:33:44:55"' % self.pf0_intf, '# ')
        self.launch_testpmd()
        for pattern in sv_mac_test_drop_action:
            # validate a rule
            self.validate_switch_filter_rule(pattern["rte_flow_pattern"])
            # create a rule
            rule_list = self.create_switch_filter_rule(pattern["rte_flow_pattern"])  # create a rule
            self.check_switch_filter_rule_list(0, rule_list)
            # send matched packets and check
            matched_dic = pattern["matched"]
            self.send_and_check_packets(matched_dic)
            # send mismatched packets and check
            mismatched_dic = pattern["mismatched"]
            self.send_and_check_packets(mismatched_dic)
            # destroy rule and send matched packets
            self.destroy_switch_filter_rule(0, rule_list)
            self.check_switch_filter_rule_list(0, [])
            # send matched packets and check
            destroy_dict = copy.deepcopy(matched_dic)
            destroy_dict["expect_results"]["expect_pkts"] = len(pattern["matched"]["scapy_str"])
            self.send_and_check_packets(destroy_dict)
            self.dut.send_expect("flow flush 0", "testpmd> ", 15)
            self.dut.send_expect("clear port stats all", "testpmd> ", 15)

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
        if self.default_stats:
            self.dut.send_expect('ethtool --set-priv-flags %s %s %s' % (self.pf0_intf, self.flag, self.default_stats), "# ")
