# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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
import os
import re
import time

import framework.utils as utils
import tests.rte_flow_common as rfc
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase, skip_unsupported_pkg
from framework.utils import GREEN, RED

MAC_IPV4_PAY = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=255, ttl=2, tos=4)/Raw("x" * 80)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.20",dst="192.168.0.22", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.1.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=3, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=9) / Raw("x" * 80)'
    ]
}

MAC_IPV4_PAY_SELECTED = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=17, ttl=2, tos=4)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=17, ttl=2, tos=4)/Raw("x" * 80)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", proto=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=6)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1)/TCP(sport=22,dport=23)/Raw("x" * 80)'
    ]
}

MAC_IPV4_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.19",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=21,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=24)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)']
}

MAC_IPV4_TCP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.19",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=21,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=24)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)']
}

MAC_IPV4_SCTP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw("x" * 80)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.19",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=21,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=24)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /SCTP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /SCTP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4)/Raw("x" * 80)']
}

MAC_IPV6_PAY = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:56")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::1", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=2, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=2, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=5)/("X"*480)']
}

MAC_IPV6_PAY_SELECTED = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=44, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment(id=1000)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=44)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment(id=1000)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)'],
    "unmatched": ['Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", nh=44)/("X"*480)',
                  'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
                  'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=17)/("X"*480)']
}

MAC_IPV6_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:56")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)']
}

MAC_IPV6_TCP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:56")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)']
}

MAC_IPV6_SCTP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:56")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/("X"*480)']
}

MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21", frag=1)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.20")/("X"*480)'
    ],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.22")',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.30", dst="192.168.0.21")',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IP(dst="192.168.0.21", src="192.168.0.20")/("X"*480)']
}

MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.20")/UDP(sport=22,dport=23)/("X"*480)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.23")/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IP(dst="192.168.0.21", src="192.168.0.20")/UDP(sport=22,dport=23)/("X"*480)'
    ]
}

MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.20")/TCP(sport=22,dport=23)/("X"*480)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.22")/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.23")/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IP(dst="192.168.0.21", src="192.168.0.20")/TCP(sport=22,dport=23)/("X"*480)']
}

MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.20")/SCTP(sport=22,dport=23)/("X"*480)'],
    "unmatched": [
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.22")/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.23")/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IP(dst="192.168.0.21", src="192.168.0.20")/SCTP(sport=22,dport=23)/("X"*480)']
}

MAC_IPV4_GTPU_EH = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/IPv6ExtHdrFragment(id=1000)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/Raw("x"*20)'],
    "unmatched": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']
}

MAC_IPV4_GTPU = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment(id=1000)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/Raw("x"*20)'],
    "unmatched": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IP()/Raw("x"*20)']
}

MAC_IPV6_GTPU_EH = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/ICMP()/Raw("x"*20)'],
    "unmatched": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/TCP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/UDP()/Raw("x"*20)']
}

MAC_IPV6_GTPU = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/ICMP()/Raw("x"*20)'],
    "unmatched": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw("x"*20)']
}

L2_Ethertype = [
    'Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x" *80)',
    'Ether(dst="00:11:22:33:44:55", type=0x8863)/IP()/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:55")/PPPoE(sessionid=3)/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:55", type=0x8864)/IP()/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:55")/ARP(pdst="192.168.1.1")',
    'Ether(dst="00:11:22:33:44:55", type=0x0806)/Raw("x" *80)',
    'Ether(dst="00:11:22:33:44:55",type=0x8100)',
    'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)',
    'Ether(dst="00:11:22:33:44:55",type=0x88f7)/"\\x00\\x02"',
    'Ether(dst="00:11:22:33:44:55",type=0x8847)']

MAC_IPV4_ESP = {
    "matched": [
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.20',dst='192.168.0.21',proto=50)/ESP(spi=7)/Raw('x'*480)",
    ],
    "unmatched": [
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.22',dst='192.168.0.21',proto=50)/ESP(spi=7)/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.20',dst='192.168.0.11',proto=50)/ESP(spi=7)/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.20',dst='192.168.0.21',proto=50)/ESP(spi=17)/Raw('x'*480)",
    ]
}

MAC_IPV6_ESP = {
    "matched": [
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::1',dst='2001::2',nh=50)/ESP(spi=7)/Raw('x'*480)",
    ],
    "unmatched": [
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888',dst='2001::2',nh=50)/ESP(spi=7)/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::1',dst='1111:2222:3333:4444:5555:6666:7777:9999',nh=50)/ESP(spi=7)/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::1',dst='2001::2',nh=50)/ESP(spi=17)/Raw('x'*480)",
    ]
}

MAC_IPV4_NAT_T_ESP = {
    "matched": [
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.20',dst='192.168.0.21')/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480)",
    ],
    "unmatched": [
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.22',dst='192.168.0.21')/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.20',dst='192.168.0.11')/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.20',dst='192.168.0.21')/UDP(dport=4500)/ESP(spi=77)/Raw('x'*480)",
    ]
}

MAC_IPV6_NAT_T_ESP = {
    "matched": [
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::1',dst='2001::2')/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480)",
    ],
    "unmatched": [
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::8',dst='2001::2')/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::1',dst='2001::9')/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='2001::1',dst='2001::2')/UDP(dport=4500)/ESP(spi=77)/Raw('x'*480)",
    ]
}

tv_mac_ipv4_pay_queue_index = {
    "name": "test_mac_ipv4_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_pay_rss_queues = {
    "name": "test_mac_ipv4_pay_rss_queues",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 2 3 end / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": [2, 3]}
}

tv_mac_ipv4_pay_passthru = {
    "name": "test_mac_ipv4_pay_passthru",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True}
}

tv_mac_ipv4_pay_drop = {
    "name": "test_mac_ipv4_pay_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_pay_mark_rss = {
    "name": "test_mac_ipv4_pay_mark_rss",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv4_pay_mark = {
    "name": "test_mac_ipv4_pay_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_ipv4_pay = [tv_mac_ipv4_pay_queue_index, tv_mac_ipv4_pay_rss_queues, tv_mac_ipv4_pay_passthru,
                    tv_mac_ipv4_pay_drop, tv_mac_ipv4_pay_mark_rss, tv_mac_ipv4_pay_mark]

tv_mac_ipv4_udp_queue_index = {
    "name": "test_mac_ipv4_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 63 / mark id 0 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 63, "mark_id": 0}
}

tv_mac_ipv4_udp_rss_queues = {
    "name": "test_mac_ipv4_udp_rss_queues",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 4294967294 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": [0, 1, 2, 3], "mark_id": 4294967294}
}

tv_mac_ipv4_udp_passthru = {
    "name": "test_mac_ipv4_udp_passthru",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_udp_drop = {
    "name": "test_mac_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_udp_mark_rss = {
    "name": "test_mac_ipv4_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 2, "rss": True}
}

tv_mac_ipv4_udp_mark = {
    "name": "test_mac_ipv4_udp_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1}
}

vectors_ipv4_udp = [tv_mac_ipv4_udp_queue_index, tv_mac_ipv4_udp_rss_queues, tv_mac_ipv4_udp_passthru,
                    tv_mac_ipv4_udp_drop, tv_mac_ipv4_udp_mark_rss, tv_mac_ipv4_udp_mark]

tv_mac_ipv4_tcp_queue_index = {
    "name": "test_mac_ipv4_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 63 / mark id 0 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 63, "mark_id": 0}
}

tv_mac_ipv4_tcp_rss_queues = {
    "name": "test_mac_ipv4_tcp_rss_queues",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 4294967294 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": [0, 1, 2, 3], "mark_id": 4294967294}
}

tv_mac_ipv4_tcp_passthru = {
    "name": "test_mac_ipv4_tcp_passthru",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tcp_drop = {
    "name": "test_mac_ipv4_tcp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_tcp_mark_rss = {
    "name": "test_mac_ipv4_tcp_mark_rss",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 2, "rss": True}
}

tv_mac_ipv4_tcp_mark = {
    "name": "test_mac_ipv4_tcp_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1}
}

#vectors_ipv4_tcp = [tv_mac_ipv4_tcp_queue_index, tv_mac_ipv4_tcp_rss_queues, tv_mac_ipv4_tcp_passthru,
#                    tv_mac_ipv4_tcp_drop, tv_mac_ipv4_tcp_mark_rss, tv_mac_ipv4_tcp_mark]
vectors_ipv4_tcp = [tv_mac_ipv4_tcp_mark_rss]

tv_mac_ipv4_sctp_queue_index = {
    "name": "test_mac_ipv4_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions queue index 63 / mark id 0 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 63, "mark_id": 0}
}

tv_mac_ipv4_sctp_rss_queues = {
    "name": "test_mac_ipv4_sctp_rss_queues",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 4294967294 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": [0, 1, 2, 3], "mark_id": 4294967294}
}

tv_mac_ipv4_sctp_passthru = {
    "name": "test_mac_ipv4_sctp_passthru",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_sctp_drop = {
    "name": "test_mac_ipv4_sctp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_sctp_mark_rss = {
    "name": "test_mac_ipv4_sctp_mark_rss",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 2, "rss": True}
}

tv_mac_ipv4_sctp_mark = {
    "name": "test_mac_ipv4_sctp_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1}
}

vectors_ipv4_sctp = [tv_mac_ipv4_sctp_queue_index, tv_mac_ipv4_sctp_rss_queues, tv_mac_ipv4_sctp_passthru,
                     tv_mac_ipv4_sctp_drop, tv_mac_ipv4_sctp_mark_rss, tv_mac_ipv4_sctp_mark]

tv_mac_ipv6_pay_queue_index = {
    "name": "test_mac_ipv6_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions queue index 1 / mark / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0}
}

tv_mac_ipv6_pay_rss_queues = {
    "name": "test_mac_ipv6_pay_rss_queues",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions rss queues 56 57 58 59 60 61 62 63 end / mark / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": list(range(56, 64)), "mark_id": 0}
}

tv_mac_ipv6_pay_passthru = {
    "name": "test_mac_ipv6_pay_passthru",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions passthru / mark / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True, "mark_id": 0}
}

tv_mac_ipv6_pay_drop = {
    "name": "test_mac_ipv6_pay_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions drop / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_pay_mark_rss = {
    "name": "test_mac_ipv6_pay_mark_rss",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark / rss / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv6_pay_mark = {
    "name": "test_mac_ipv6_pay_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

vectors_ipv6_pay = [tv_mac_ipv6_pay_queue_index, tv_mac_ipv6_pay_rss_queues, tv_mac_ipv6_pay_passthru,
                    tv_mac_ipv6_pay_drop, tv_mac_ipv6_pay_mark_rss, tv_mac_ipv6_pay_mark]

tv_mac_ipv6_udp_queue_index = {
    "name": "test_mac_ipv6_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0}
}

tv_mac_ipv6_udp_rss_queues = {
    "name": "test_mac_ipv6_udp_rss_queues",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True}
}

tv_mac_ipv6_udp_passthru = {
    "name": "test_mac_ipv6_udp_passthru",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions passthru / mark / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv6_udp_drop = {
    "name": "test_mac_ipv6_udp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_udp_mark_rss = {
    "name": "test_mac_ipv6_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark / rss / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv6_udp_mark = {
    "name": "test_mac_ipv6_udp_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

vectors_ipv6_udp = [tv_mac_ipv6_udp_queue_index, tv_mac_ipv6_udp_rss_queues, tv_mac_ipv6_udp_passthru,
                    tv_mac_ipv6_udp_drop, tv_mac_ipv6_udp_mark_rss, tv_mac_ipv6_udp_mark]

tv_mac_ipv6_tcp_queue_index = {
    "name": "test_mac_ipv6_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0}
}

tv_mac_ipv6_tcp_rss_queues = {
    "name": "test_mac_ipv6_tcp_rss_queues",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions rss / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True}
}

tv_mac_ipv6_tcp_passthru = {
    "name": "test_mac_ipv6_tcp_passthru",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions passthru / mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv6_tcp_drop = {
    "name": "test_mac_ipv6_tcp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_tcp_mark_rss = {
    "name": "test_mac_ipv6_tcp_mark_rss",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions mark / rss / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv6_tcp_mark = {
    "name": "test_mac_ipv6_tcp_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

vectors_ipv6_tcp = [tv_mac_ipv6_tcp_queue_index, tv_mac_ipv6_tcp_rss_queues, tv_mac_ipv6_tcp_passthru,
                    tv_mac_ipv6_tcp_drop, tv_mac_ipv6_tcp_mark_rss, tv_mac_ipv6_tcp_mark]

tv_mac_ipv6_sctp_queue_index = {
    "name": "test_mac_ipv6_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions queue index 1 / mark / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0}
}

tv_mac_ipv6_sctp_rss_queues = {
    "name": "test_mac_ipv6_sctp_rss_queues",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions rss / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True}
}

tv_mac_ipv6_sctp_passthru = {
    "name": "test_mac_ipv6_sctp_passthru",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions passthru / mark / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv6_sctp_drop = {
    "name": "test_mac_ipv6_sctp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_sctp_mark_rss = {
    "name": "test_mac_ipv6_sctp_mark_rss",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions mark / rss / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv6_sctp_mark = {
    "name": "test_mac_ipv6_sctp_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions mark / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

vectors_ipv6_sctp = [tv_mac_ipv6_sctp_queue_index, tv_mac_ipv6_sctp_rss_queues, tv_mac_ipv6_sctp_passthru,
                     tv_mac_ipv6_sctp_drop, tv_mac_ipv6_sctp_mark_rss, tv_mac_ipv6_sctp_mark]

tv_mac_ipv4_tun_ipv4_pay_queue_index = {
    "name": "test_mac_ipv4_tun_ipv4_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_tun_ipv4_pay_passthru = {
    "name": "test_mac_ipv4_tun_ipv4_pay_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv4_tun_ipv4_pay_drop = {
    "name": "test_mac_ipv4_tun_ipv4_pay_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_tun_ipv4_pay_mark_rss = {
    "name": "test_mac_ipv4_tun_ipv4_pay_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv4_tun_ipv4_pay_mark = {
    "name": "test_mac_ipv4_tun_ipv4_pay_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

vectors_ipv4_tun_ipv4_pay = [tv_mac_ipv4_tun_ipv4_pay_queue_index,
                             tv_mac_ipv4_tun_ipv4_pay_passthru, tv_mac_ipv4_tun_ipv4_pay_drop,
                             tv_mac_ipv4_tun_ipv4_pay_mark_rss, tv_mac_ipv4_tun_ipv4_pay_mark]

tv_mac_ipv4_tun_ipv4_udp_queue_index = {
    "name": "test_mac_ipv4_tun_ipv4_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1}
}

tv_mac_ipv4_tun_ipv4_udp_rss_queues = {
    "name": "test_mac_ipv4_tun_ipv4_udp_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 38 39 40 41 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": list(range(38, 42)), "mark_id": 1}
}

tv_mac_ipv4_tun_ipv4_udp_passthru = {
    "name": "test_mac_ipv4_tun_ipv4_udp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_ipv4_udp_drop = {
    "name": "test_mac_ipv4_tun_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_tun_ipv4_udp_mark_rss = {
    "name": "test_mac_ipv4_tun_ipv4_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_ipv4_udp_mark = {
    "name": "test_mac_ipv4_tun_ipv4_udp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_ipv4_tun_ipv4_udp = [tv_mac_ipv4_tun_ipv4_udp_queue_index, tv_mac_ipv4_tun_ipv4_udp_rss_queues,
                             tv_mac_ipv4_tun_ipv4_udp_passthru, tv_mac_ipv4_tun_ipv4_udp_drop,
                             tv_mac_ipv4_tun_ipv4_udp_mark_rss, tv_mac_ipv4_tun_ipv4_udp_mark]

tv_mac_ipv4_tun_ipv4_tcp_queue_index = {
    "name": "test_mac_ipv4_tun_ipv4_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1}
}

tv_mac_ipv4_tun_ipv4_tcp_passthru = {
    "name": "test_mac_ipv4_tun_ipv4_tcp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_ipv4_tcp_drop = {
    "name": "test_mac_ipv4_tun_ipv4_tcp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_tun_ipv4_tcp_mark_rss = {
    "name": "test_mac_ipv4_tun_ipv4_tcp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_ipv4_tcp_mark = {
    "name": "test_mac_ipv4_tun_ipv4_tcp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_ipv4_tun_ipv4_tcp = [tv_mac_ipv4_tun_ipv4_tcp_queue_index,
                             tv_mac_ipv4_tun_ipv4_tcp_passthru, tv_mac_ipv4_tun_ipv4_tcp_drop,
                             tv_mac_ipv4_tun_ipv4_tcp_mark_rss, tv_mac_ipv4_tun_ipv4_tcp_mark]

tv_mac_ipv4_tun_ipv4_sctp_queue_index = {
    "name": "test_mac_ipv4_tun_ipv4_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1}
}

tv_mac_ipv4_tun_ipv4_sctp_passthru = {
    "name": "test_mac_ipv4_tun_ipv4_sctp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_ipv4_sctp_drop = {
    "name": "test_mac_ipv4_tun_ipv4_sctp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_tun_ipv4_sctp_mark_rss = {
    "name": "test_mac_ipv4_tun_ipv4_sctp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_ipv4_sctp_mark = {
    "name": "test_mac_ipv4_tun_ipv4_sctp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_ipv4_tun_ipv4_sctp = [tv_mac_ipv4_tun_ipv4_sctp_queue_index,
                              tv_mac_ipv4_tun_ipv4_sctp_passthru, tv_mac_ipv4_tun_ipv4_sctp_drop,
                              tv_mac_ipv4_tun_ipv4_sctp_mark_rss, tv_mac_ipv4_tun_ipv4_sctp_mark]

tv_mac_ipv4_tun_mac_ipv4_pay_queue_index = {
    "name": "test_mac_ipv4_tun_mac_ipv4_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 0 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 0}
}

tv_mac_ipv4_tun_mac_ipv4_pay_rss_queues = {
    "name": "test_mac_ipv4_tun_mac_ipv4_pay_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 0 1 end / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": [0, 1]}
}

tv_mac_ipv4_tun_mac_ipv4_pay_passthru = {
    "name": "test_mac_ipv4_tun_mac_ipv4_pay_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True}
}

tv_mac_ipv4_tun_mac_ipv4_pay_drop = {
    "name": "test_mac_ipv4_tun_mac_ipv4_pay_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_tun_mac_ipv4_pay_mark_rss = {
    "name": "test_mac_ipv4_tun_mac_ipv4_pay_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv4_tun_mac_ipv4_pay_mark = {
    "name": "test_mac_ipv4_tun_mac_ipv4_pay_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True, "mark_id": 0}
}

vectors_mac_ipv4_tun_mac_ipv4_pay = [tv_mac_ipv4_tun_mac_ipv4_pay_queue_index, tv_mac_ipv4_tun_mac_ipv4_pay_rss_queues,
                                     tv_mac_ipv4_tun_mac_ipv4_pay_passthru, tv_mac_ipv4_tun_mac_ipv4_pay_drop,
                                     tv_mac_ipv4_tun_mac_ipv4_pay_mark_rss, tv_mac_ipv4_tun_mac_ipv4_pay_mark]

tv_mac_ipv4_tun_mac_ipv4_udp_queue_index = {
    "name": "test_mac_ipv4_tun_mac_ipv4_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 15 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 15, "mark_id": 1}
}

tv_mac_ipv4_tun_mac_ipv4_udp_rss_queues = {
    "name": "test_mac_ipv4_tun_mac_ipv4_udp_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": [0, 1, 2, 3], "mark_id": 1}
}

tv_mac_ipv4_tun_mac_ipv4_udp_passthru = {
    "name": "test_mac_ipv4_tun_mac_ipv4_udp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_mac_ipv4_udp_drop = {
    "name": "test_mac_ipv4_tun_mac_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_tun_mac_ipv4_udp_mark_rss = {
    "name": "tv_mac_ipv4_tun_mac_ipv4_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_mac_ipv4_udp_mark = {
    "name": "tv_mac_ipv4_tun_mac_ipv4_udp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_mac_ipv4_tun_mac_ipv4_udp = [tv_mac_ipv4_tun_mac_ipv4_udp_queue_index, tv_mac_ipv4_tun_mac_ipv4_udp_rss_queues,
                                     tv_mac_ipv4_tun_mac_ipv4_udp_passthru, tv_mac_ipv4_tun_mac_ipv4_udp_drop,
                                     tv_mac_ipv4_tun_mac_ipv4_udp_mark_rss, tv_mac_ipv4_tun_mac_ipv4_udp_mark]

tv_mac_ipv4_tun_mac_ipv4_tcp_queue_index = {
    "name": "test_mac_ipv4_tun_mac_ipv4_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 15 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 15, "mark_id": 1}
}

tv_mac_ipv4_tun_mac_ipv4_tcp_rss_queues = {
    "name": "test_mac_ipv4_tun_mac_ipv4_tcp_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": [0, 1, 2, 3], "mark_id": 1}
}

tv_mac_ipv4_tun_mac_ipv4_tcp_passthru = {
    "name": "test_mac_ipv4_tun_mac_ipv4_tcp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_mac_ipv4_tcp_drop = {
    "name": "test_mac_ipv4_tun_mac_ipv4_tcp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_tun_mac_ipv4_tcp_mark_rss = {
    "name": "tv_mac_ipv4_tun_mac_ipv4_tcp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_mac_ipv4_tcp_mark = {
    "name": "tv_mac_ipv4_tun_mac_ipv4_tcp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_mac_ipv4_tun_mac_ipv4_tcp = [tv_mac_ipv4_tun_mac_ipv4_tcp_queue_index, tv_mac_ipv4_tun_mac_ipv4_tcp_rss_queues,
                                     tv_mac_ipv4_tun_mac_ipv4_tcp_passthru, tv_mac_ipv4_tun_mac_ipv4_tcp_drop,
                                     tv_mac_ipv4_tun_mac_ipv4_tcp_mark_rss, tv_mac_ipv4_tun_mac_ipv4_tcp_mark]

tv_mac_ipv4_tun_mac_ipv4_sctp_queue_index = {
    "name": "test_mac_ipv4_tun_mac_ipv4_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 15 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 15, "mark_id": 1}
}

tv_mac_ipv4_tun_mac_ipv4_sctp_rss_queues = {
    "name": "test_mac_ipv4_tun_mac_ipv4_sctp_rss_queues",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": [0, 1, 2, 3], "mark_id": 1}
}

tv_mac_ipv4_tun_mac_ipv4_sctp_passthru = {
    "name": "test_mac_ipv4_tun_mac_ipv4_sctp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_mac_ipv4_sctp_drop = {
    "name": "test_mac_ipv4_tun_mac_ipv4_sctp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions drop / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_tun_mac_ipv4_sctp_mark_rss = {
    "name": "test_mac_ipv4_tun_mac_ipv4_sctp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions rss / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_tun_mac_ipv4_sctp_mark = {
    "name": "tv_mac_ipv4_tun_mac_ipv4_sctp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_mac_ipv4_tun_mac_ipv4_sctp = [tv_mac_ipv4_tun_mac_ipv4_sctp_queue_index,
                                      tv_mac_ipv4_tun_mac_ipv4_sctp_rss_queues,
                                      tv_mac_ipv4_tun_mac_ipv4_sctp_passthru, tv_mac_ipv4_tun_mac_ipv4_sctp_drop,
                                      tv_mac_ipv4_tun_mac_ipv4_sctp_mark_rss, tv_mac_ipv4_tun_mac_ipv4_sctp_mark]

tv_mac_ipv4_gtpu_eh_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv4_gtpu_eh_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_eh_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_drop = {
    "name": "test_mac_ipv4_gtpu_eh_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_eh_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_mark = {
    "name": "tv_mac_ipv4_gtpu_eh_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_qfi_queue_index_mark = {
    "name": "test_mac_ipv4_gtpu_eh_qfi_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 3 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 3, "queue": 1}
}

tv_mac_ipv4_gtpu_eh_qfi_rss_queues_mark = {
    "name": "test_mac_ipv4_gtpu_eh_qfi_rss_queues_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / end actions rss queues 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1)/IP()/TCP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [2, 3]}
}

tv_mac_ipv4_gtpu_eh_4tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv4_gtpu_eh_4tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_eh_4tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_4tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_eh_4tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions queue index 10 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv4_gtpu_eh_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_eh_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_eh_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions queue index 10 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv4_gtpu_eh_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_eh_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_eh_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_mac_ipv4_gtpu_eh = [tv_mac_ipv4_gtpu_eh_queue_index, tv_mac_ipv4_gtpu_eh_queue_group,
                            tv_mac_ipv4_gtpu_eh_passthru, tv_mac_ipv4_gtpu_eh_drop,
                            tv_mac_ipv4_gtpu_eh_mark_rss, tv_mac_ipv4_gtpu_eh_mark,
                            tv_mac_ipv4_gtpu_eh_qfi_queue_index_mark, tv_mac_ipv4_gtpu_eh_qfi_rss_queues_mark,
			    tv_mac_ipv4_gtpu_eh_4tuple_queue_index, tv_mac_ipv4_gtpu_eh_4tuple_queue_group,
                            tv_mac_ipv4_gtpu_eh_4tuple_passthru, tv_mac_ipv4_gtpu_eh_4tuple_drop,
                            tv_mac_ipv4_gtpu_eh_4tuple_mark_rss,
                            tv_mac_ipv4_gtpu_eh_dstip_queue_index, tv_mac_ipv4_gtpu_eh_dstip_queue_group,
                            tv_mac_ipv4_gtpu_eh_dstip_passthru, tv_mac_ipv4_gtpu_eh_dstip_drop,
                            tv_mac_ipv4_gtpu_eh_dstip_mark_rss,
                            tv_mac_ipv4_gtpu_eh_srcip_queue_index, tv_mac_ipv4_gtpu_eh_srcip_queue_group,
                            tv_mac_ipv4_gtpu_eh_srcip_passthru, tv_mac_ipv4_gtpu_eh_srcip_drop,
                            tv_mac_ipv4_gtpu_eh_srcip_mark_rss]

tv_mac_ipv4_gtpu_queue_index = {
    "name": "test_mac_ipv4_gtpu_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions queue index 1 / mark / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "queue": 1}
}

tv_mac_ipv4_gtpu_queue_group = {
    "name": "test_mac_ipv4_gtpu_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 end / mark / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "queue": [0, 1]}
}

tv_mac_ipv4_gtpu_passthru = {
    "name": "test_mac_ipv4_gtpu_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions passthru / mark / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv4_gtpu_drop = {
    "name": "test_mac_ipv4_gtpu_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_mark_rss = {
    "name": "test_mac_ipv4_gtpu_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv4_gtpu_mark = {
    "name": "tv_mac_ipv4_gtpu_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv4_gtpu_3tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_3tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv4_gtpu_3tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_3tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_3tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_3tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_3tuple_drop = {
    "name": "test_mac_ipv4_gtpu_3tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_3tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_3tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions queue index 10 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv4_gtpu_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions queue index 10 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv4_gtpu_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_mac_ipv4_gtpu = [tv_mac_ipv4_gtpu_queue_index, tv_mac_ipv4_gtpu_queue_group,
                         tv_mac_ipv4_gtpu_passthru, tv_mac_ipv4_gtpu_drop,
                         tv_mac_ipv4_gtpu_mark_rss, tv_mac_ipv4_gtpu_mark,
			 tv_mac_ipv4_gtpu_3tuple_queue_index, tv_mac_ipv4_gtpu_3tuple_queue_group,
                         tv_mac_ipv4_gtpu_3tuple_passthru, tv_mac_ipv4_gtpu_3tuple_drop,
                         tv_mac_ipv4_gtpu_3tuple_mark_rss,
                         tv_mac_ipv4_gtpu_dstip_queue_index, tv_mac_ipv4_gtpu_dstip_queue_group,
                         tv_mac_ipv4_gtpu_dstip_passthru, tv_mac_ipv4_gtpu_dstip_drop,
                         tv_mac_ipv4_gtpu_dstip_mark_rss,
                         tv_mac_ipv4_gtpu_srcip_queue_index, tv_mac_ipv4_gtpu_srcip_queue_group,
                         tv_mac_ipv4_gtpu_srcip_passthru, tv_mac_ipv4_gtpu_srcip_drop,
                         tv_mac_ipv4_gtpu_srcip_mark_rss]

tv_mac_ipv6_gtpu_eh_4tuple_queue_index = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv6_gtpu_eh_4tuple_queue_group = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_eh_4tuple_passthru = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_4tuple_drop = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_eh_4tuple_mark_rss = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_dstip_queue_index = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions queue index 10 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv6_gtpu_eh_dstip_queue_group = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_eh_dstip_passthru = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_dstip_drop = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_eh_dstip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_srcip_queue_index = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions queue index 10 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv6_gtpu_eh_srcip_queue_group = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_eh_srcip_passthru = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_srcip_drop = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_eh_srcip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0, P=1, QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_mac_ipv6_gtpu_eh = [tv_mac_ipv6_gtpu_eh_4tuple_queue_index, tv_mac_ipv6_gtpu_eh_4tuple_queue_group,
                            tv_mac_ipv6_gtpu_eh_4tuple_passthru, tv_mac_ipv6_gtpu_eh_4tuple_drop,
                            tv_mac_ipv6_gtpu_eh_4tuple_mark_rss,
                            tv_mac_ipv6_gtpu_eh_dstip_queue_index, tv_mac_ipv6_gtpu_eh_dstip_queue_group,
                            tv_mac_ipv6_gtpu_eh_dstip_passthru, tv_mac_ipv6_gtpu_eh_dstip_drop,
                            tv_mac_ipv6_gtpu_eh_dstip_mark_rss,
                            tv_mac_ipv6_gtpu_eh_srcip_queue_index, tv_mac_ipv6_gtpu_eh_srcip_queue_group,
                            tv_mac_ipv6_gtpu_eh_srcip_passthru, tv_mac_ipv6_gtpu_eh_srcip_drop,
                            tv_mac_ipv6_gtpu_eh_srcip_mark_rss]

tv_mac_ipv6_gtpu_3tuple_queue_index = {
    "name": "test_mac_ipv6_gtpu_3tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions queue index 10 / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv6_gtpu_3tuple_queue_group = {
    "name": "test_mac_ipv6_gtpu_3tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_3tuple_passthru = {
    "name": "test_mac_ipv6_gtpu_3tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_3tuple_drop = {
    "name": "test_mac_ipv6_gtpu_3tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions drop / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_3tuple_mark_rss = {
    "name": "test_mac_ipv6_gtpu_3tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_dstip_queue_index = {
    "name": "test_mac_ipv6_gtpu_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions queue index 10 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv6_gtpu_dstip_queue_group = {
    "name": "test_mac_ipv6_gtpu_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_dstip_passthru = {
    "name": "test_mac_ipv6_gtpu_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_dstip_drop = {
    "name": "test_mac_ipv6_gtpu_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_dstip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_srcip_queue_index = {
    "name": "test_mac_ipv6_gtpu_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions queue index 10 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 10}
}

tv_mac_ipv6_gtpu_srcip_queue_group = {
    "name": "test_mac_ipv6_gtpu_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_srcip_passthru = {
    "name": "test_mac_ipv6_gtpu_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_srcip_drop = {
    "name": "test_mac_ipv6_gtpu_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_srcip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "unmatched":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

vectors_mac_ipv6_gtpu = [tv_mac_ipv6_gtpu_3tuple_queue_index, tv_mac_ipv6_gtpu_3tuple_queue_group,
                            tv_mac_ipv6_gtpu_3tuple_passthru, tv_mac_ipv6_gtpu_3tuple_drop,
                            tv_mac_ipv6_gtpu_3tuple_mark_rss,
                            tv_mac_ipv6_gtpu_dstip_queue_index, tv_mac_ipv6_gtpu_dstip_queue_group,
                            tv_mac_ipv6_gtpu_dstip_passthru, tv_mac_ipv6_gtpu_dstip_drop,
                            tv_mac_ipv6_gtpu_dstip_mark_rss,
                            tv_mac_ipv6_gtpu_srcip_queue_index, tv_mac_ipv6_gtpu_srcip_queue_group,
                            tv_mac_ipv6_gtpu_srcip_passthru, tv_mac_ipv6_gtpu_srcip_drop,
                            tv_mac_ipv6_gtpu_srcip_mark_rss]

tv_l2_ethertype_queue_index = {
    "name": "test_l2_ethertype_queue_index",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions queue index 1 / mark id 1 / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions queue index 2 / mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions queue index 3 / mark id 3 / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions queue index 4 / mark id 4 / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions queue index 5 / mark id 5 / end"],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "queue": 1, "mark_id": 1},
        {"port_id": 0, "queue": 1, "mark_id": 1},
        {"port_id": 0, "queue": 2, "mark_id": 2},
        {"port_id": 0, "queue": 2, "mark_id": 2},
        {"port_id": 0, "queue": 3, "mark_id": 3},
        {"port_id": 0, "queue": 3, "mark_id": 3},
        {"port_id": 0, "queue": 4, "mark_id": 4},
        {"port_id": 0, "queue": 4, "mark_id": 4},
        {"port_id": 0, "queue": 5, "mark_id": 5},
        {"port_id": 0, "queue": 0}]
}

tv_l2_ethertype_queue_group = {
    "name": "test_l2_ethertype_queue_group",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions rss queues 0 1 end / mark id 0 / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions rss queues 2 3 end / mark id 1 / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions rss queues 4 5 end / mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions rss queues 6 7 end / mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions rss queues 9 10 end / mark id 3 / end"],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 3},
        {"port_id": 0, "queue": 0}]
}

tv_l2_ethertype_passthru = {
    "name": "test_l2_ethertype_passthru",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions passthru / mark / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions passthru / mark id 1 / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions passthru / mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions passthru / mark id 3 / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions passthru / mark id 4 / end"],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 3},
        {"port_id": 0, "queue": 0, "mark_id": 3},
        {"port_id": 0, "queue": 0, "mark_id": 4},
        {"port_id": 0, "queue": 0}]
}

tv_l2_ethertype_mark_rss = {
    "name": "test_l2_ethertype_mark_rss",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions rss / mark id 0 / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions mark id 1 / rss / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions mark / rss / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions rss / mark / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions mark id 3 / rss / end"],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 3},
        {"port_id": 0, "queue": 0}]
}

tv_l2_ethertype_mark = {
    "name": "test_l2_ethertype_mark",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions mark id 0 / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions mark id 1 / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions mark id 2 / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions mark / end"],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": 0}]
}

tv_l2_ethertype_drop = {
    "name": "test_l2_ethertype_drop",
    "rule": [
        "flow create 0 ingress pattern eth type is 0x8863 / end actions drop / end",
        "flow create 0 ingress pattern eth type is 0x8864 / end actions drop / end",
        "flow create 0 ingress pattern eth type is 0x0806 / end actions drop / end",
        "flow create 0 ingress pattern eth type is 0x8100 / end actions drop / end",
        "flow create 0 ingress pattern eth type is 0x88f7 / end actions drop / end"],
    "scapy_str": L2_Ethertype,
    "check_param": [
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "queue": 0}]
}

vectors_l2_ethertype = [tv_l2_ethertype_queue_index,
                        tv_l2_ethertype_queue_group,
                        tv_l2_ethertype_passthru,
                        tv_l2_ethertype_drop,
                        tv_l2_ethertype_mark_rss,
                        tv_l2_ethertype_mark]

tv_mac_ipv4_esp_queue_index = {
    "name": "tv_mac_ipv4_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": {"match": MAC_IPV4_ESP['matched'],
                  "unmatched": MAC_IPV4_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 7, "queue": 13}
}

tv_mac_ipv4_esp_queue_group = {
    "name": "tv_mac_ipv4_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": {"match": MAC_IPV4_ESP['matched'],
                  "unmatched": MAC_IPV4_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 6, "queue": [1, 2, 3, 4]}
}

tv_mac_ipv4_esp_passthru = {
    "name": "tv_mac_ipv4_esp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions passthru / mark id 1 / end",
    "scapy_str": {"match": MAC_IPV4_ESP['matched'],
                  "unmatched": MAC_IPV4_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True, "mark_id": 1}
}

tv_mac_ipv4_esp_drop = {
    "name": "tv_mac_ipv4_esp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions drop / end",
    "scapy_str": {"match": MAC_IPV4_ESP['matched'],
                  "unmatched": MAC_IPV4_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv4_esp_mark_rss = {
    "name": "tv_mac_ipv4_esp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions mark id 2 / rss / end",
    "scapy_str": {"match": MAC_IPV4_ESP['matched'],
                  "unmatched": MAC_IPV4_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 2, "rss": True}
}

tv_mac_ipv4_esp_mark = {
    "name": "tv_mac_ipv4_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions mark id 15 / end",
    "scapy_str": {"match": MAC_IPV4_ESP['matched'],
                  "unmatched": MAC_IPV4_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 15}
}

vectors_mac_ipv4_esp = [
    tv_mac_ipv4_esp_queue_index,
    tv_mac_ipv4_esp_queue_group,
    tv_mac_ipv4_esp_passthru,
    tv_mac_ipv4_esp_drop,
    tv_mac_ipv4_esp_mark_rss,
    tv_mac_ipv4_esp_mark,
]

tv_mac_ipv6_esp_queue_index = {
    "name": "tv_mac_ipv6_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": {"match": MAC_IPV6_ESP['matched'],
                  "unmatched": MAC_IPV6_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 7, "queue": 13}
}

tv_mac_ipv6_esp_queue_group = {
    "name": "tv_mac_ipv6_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": {"match": MAC_IPV6_ESP['matched'],
                  "unmatched": MAC_IPV6_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 6, "queue": [1, 2, 3, 4]}
}

tv_mac_ipv6_esp_passthru = {
    "name": "tv_mac_ipv6_esp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions passthru / mark id 1 / end",
    "scapy_str": {"match": MAC_IPV6_ESP['matched'],
                  "unmatched": MAC_IPV6_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True, "mark_id": 1}
}

tv_mac_ipv6_esp_drop = {
    "name": "tv_mac_ipv6_esp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions drop / end",
    "scapy_str": {"match": MAC_IPV6_ESP['matched'],
                  "unmatched": MAC_IPV6_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv6_esp_mark_rss = {
    "name": "tv_mac_ipv6_esp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions mark / rss / end",
    "scapy_str": {"match": MAC_IPV6_ESP['matched'],
                  "unmatched": MAC_IPV6_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 0, "rss": True}
}

tv_mac_ipv6_esp_mark = {
    "name": "tv_mac_ipv6_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / esp spi is 7 / end actions mark id 15 / end",
    "scapy_str": {"match": MAC_IPV6_ESP['matched'],
                  "unmatched": MAC_IPV6_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 15}
}

vectors_mac_ipv6_esp = [
    tv_mac_ipv6_esp_queue_index,
    tv_mac_ipv6_esp_queue_group,
    tv_mac_ipv6_esp_passthru,
    tv_mac_ipv6_esp_drop,
    tv_mac_ipv6_esp_mark_rss,
    tv_mac_ipv6_esp_mark,
]

tv_mac_ipv4_nat_t_esp_queue_index = {
    "name": "tv_mac_ipv4_nat_t_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": {"match": MAC_IPV4_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV4_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 7, "queue": 13}
}

tv_mac_ipv4_nat_t_esp_queue_group = {
    "name": "tv_mac_ipv4_nat_t_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": {"match": MAC_IPV4_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV4_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 6, "queue": [1, 2, 3, 4]}
}

tv_mac_ipv4_nat_t_esp_passthru = {
    "name": "tv_mac_ipv4_nat_t_esp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions passthru / mark id 1 / end",
    "scapy_str": {"match": MAC_IPV4_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV4_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True, "mark_id": 1}
}

tv_mac_ipv4_nat_t_esp_drop = {
    "name": "tv_mac_ipv4_nat_t_esp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions drop / end",
    "scapy_str": {"match": MAC_IPV4_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV4_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv4_nat_t_esp_mark_rss = {
    "name": "tv_mac_ipv4_nat_t_esp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions mark id 2 / rss / end",
    "scapy_str": {"match": MAC_IPV4_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV4_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 2, "rss": True}
}

tv_mac_ipv4_nat_t_esp_mark = {
    "name": "tv_mac_ipv4_nat_t_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions mark id 15 / end",
    "scapy_str": {"match": MAC_IPV4_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV4_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 15}
}

vectors_mac_ipv4_nat_t_esp = [
    tv_mac_ipv4_nat_t_esp_queue_index,
    tv_mac_ipv4_nat_t_esp_queue_group,
    tv_mac_ipv4_nat_t_esp_passthru,
    tv_mac_ipv4_nat_t_esp_drop,
    tv_mac_ipv4_nat_t_esp_mark_rss,
    tv_mac_ipv4_nat_t_esp_mark,
]

tv_mac_ipv6_nat_t_esp_queue_index = {
    "name": "tv_mac_ipv6_nat_t_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": {"match": MAC_IPV6_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV6_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 7, "queue": 13}
}

tv_mac_ipv6_nat_t_esp_queue_group = {
    "name": "tv_mac_ipv6_nat_t_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": {"match": MAC_IPV6_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV6_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 6, "queue": [1, 2, 3, 4]}
}

tv_mac_ipv6_nat_t_esp_passthru = {
    "name": "tv_mac_ipv6_nat_t_esp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions passthru / mark id 1 / end",
    "scapy_str": {"match": MAC_IPV6_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV6_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "rss": True, "mark_id": 1}
}

tv_mac_ipv6_nat_t_esp_drop = {
    "name": "tv_mac_ipv6_nat_t_esp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions drop / end",
    "scapy_str": {"match": MAC_IPV6_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV6_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv6_nat_t_esp_mark_rss = {
    "name": "tv_mac_ipv6_nat_t_esp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions mark id 2 / rss / end",
    "scapy_str": {"match": MAC_IPV6_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV6_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 2, "rss": True}
}

tv_mac_ipv6_nat_t_esp_mark = {
    "name": "tv_mac_ipv6_nat_t_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions mark id 15 / end",
    "scapy_str": {"match": MAC_IPV6_NAT_T_ESP['matched'],
                  "unmatched": MAC_IPV6_NAT_T_ESP['unmatched'],
                  },
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 15}
}

vectors_mac_ipv6_nat_t_esp = [
    tv_mac_ipv6_nat_t_esp_queue_index,
    tv_mac_ipv6_nat_t_esp_queue_group,
    tv_mac_ipv6_nat_t_esp_passthru,
    tv_mac_ipv6_nat_t_esp_drop,
    tv_mac_ipv6_nat_t_esp_mark_rss,
    tv_mac_ipv6_nat_t_esp_mark,
]

class TestCVLFdir(TestCase):

    def query_count(self, hits_set, hits, port_id=0, rule_id=0):
        out = self.dut.send_command("flow query %s %s count" % (port_id, rule_id), timeout=1)
        p = re.compile("hits_set:\s(\d+).*hits:\s(\d+)", re.DOTALL)
        m = p.search(out)
        res_hits_set = int(m.group(1))
        res_hits = int(m.group(2))
        self.verify(res_hits_set == hits_set,
                    "hits_set number check failed. expect: %d, result: %d" % (hits_set, res_hits_set))
        self.verify(res_hits == hits, "hits number check failed. expect: %d, result: %d" % (hits, res_hits))

    def _rte_flow_validate(self, vectors):
        test_results = {}
        for tv in vectors:
            try:
                count = 1
                port_id = tv["check_param"]["port_id"] if tv["check_param"].get("port_id") is not None else 0
                drop = tv["check_param"].get("drop")
                # create rule
                rule_li = self.create_fdir_rule(tv["rule"], check_stats=True)
                # send and check match packets
                out1 = self.send_pkts_getouput(pkts=tv["scapy_str"]["match"], port_id=port_id,
                                               count=count, drop=drop)
                matched_queue = tv["check_func"](out1, pkt_num=len(tv["scapy_str"]["match"]),
                                                 check_param=tv["check_param"])
                # send and check unmatched packets
                out2 = self.send_pkts_getouput(pkts=tv["scapy_str"]["unmatched"], port_id=port_id,
                                               count=count, drop=drop)
                tv["check_func"](out2, pkt_num=len(tv["scapy_str"]["unmatched"]), check_param=tv["check_param"],
                                 stats=False)
                if tv["check_param"].get("count"):
                    self.query_count(tv["check_param"]["count"]["hits_set"], tv["check_param"]["count"]["hits"],
                                     port_id=port_id,
                                     rule_id=rule_li[0])
                # list and destroy rule
                self.check_fdir_rule(port_id=tv["check_param"]["port_id"], rule_list=rule_li)
                self.destroy_fdir_rule(rule_id=rule_li, port_id=port_id)
                # send matched packet
                out3 = self.send_pkts_getouput(pkts=tv["scapy_str"]["match"], port_id=port_id,
                                               count=count, drop=drop)
                matched_queue2 = tv["check_func"](out3, pkt_num=len(tv["scapy_str"]["match"]),
                                                  check_param=tv["check_param"],
                                                  stats=False)
                if tv["check_param"].get("rss"):
                    self.verify(matched_queue == matched_queue2 and None not in matched_queue,
                                "send twice matched packet, received in deferent queues")
                # check not rule exists
                self.check_fdir_rule(port_id=port_id, stats=False)
                test_results[tv["name"]] = True
                self.logger.info((GREEN("case passed: %s" % tv["name"])))
            except Exception as e:
                self.logger.warning((RED(e)))
                self.dut.send_command("flow flush 0", timeout=1)
                self.dut.send_command("flow flush 1", timeout=1)
                test_results[tv["name"]] = False
                self.logger.info((GREEN("case failed: %s" % tv["name"])))
                continue
        failed_cases = []
        for k, v in list(test_results.items()):
            if not v:
                failed_cases.append(k)
        self.verify(all(test_results.values()), "{} failed.".format(failed_cases))

    def _multirules_process(self, vectors, port_id=0):
        # create rules on only one port
        test_results = {}
        rule_li = []
        for tv in vectors:
            try:
                port_id = port_id
                pkts=tv["scapy_str"]
                check_param=tv["check_param"]
                self.destroy_fdir_rule(rule_id=rule_li, port_id=port_id)

                # validate rules and create rules
                rule_li = self.create_fdir_rule(tv["rule"], check_stats=True)

                for i in range(len(pkts)):
                    port_id = check_param[i]["port_id"]
                    out = self.send_pkts_getouput(pkts=pkts[i], drop=check_param[i].get("drop"))
                    rfc.check_mark(out, pkt_num=1, check_param=check_param[i])
                test_results[tv["name"]] = True
                print((GREEN("case passed: %s" % tv["name"])))
            except Exception as e:
                print((RED(e)))
                test_results[tv["name"]] = False
                continue
        failed_cases = []
        for k, v in list(test_results.items()):
            if not v:
                failed_cases.append(k)
        self.verify(all(test_results.values()), "{} failed.".format(failed_cases))

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
        self.portMask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.dut_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.dut_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_iface0 = self.tester.get_interface(self.dut_port0)
        self.tester_iface1 = self.tester.get_interface(self.dut_port1)
        self.pci0 = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.pci1 = self.dut.ports_info[self.dut_ports[1]]['pci']

        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        pf_pci = [self.dut.ports_info[0]['pci']]
        out = self.pmd_output.start_testpmd('default', ports=pf_pci,eal_param='--log-level=ice,7')
        self.dut.send_expect("quit", "# ")
        self.max_rule_num = self.pmd_output.get_max_rule_number(self, out)
        self.launch_testpmd_with_mark()

    def set_up(self):
        """
        Run before each test case.
        """
        self.pmd_output.execute_cmd("start")

    def config_testpmd(self):
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("port config 0 udp_tunnel_port add vxlan 4789")
        self.pmd_output.execute_cmd("port config 1 udp_tunnel_port add vxlan 4789")
        self.pmd_output.execute_cmd("port config all rss all")
        # specify a fixed rss-hash-key for cvl ether
        self.pmd_output.execute_cmd(
            "port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd")
        self.pmd_output.execute_cmd(
            "port config 1 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd")
        res = self.pmd_output.wait_link_status_up('all', timeout=15)
        self.verify(res is True, 'there have port link is down')

    def launch_testpmd_with_mark(self, rxq=64, txq=64):
        self.pmd_output.start_testpmd(cores="1S/4C/1T",
                                      param="--portmask=%s --rxq=%d --txq=%d --port-topology=loop" % (
                                          self.portMask, rxq, txq),
                                      eal_param="-a %s -a %s --log-level=ice,7" % (
                                          self.pci0, self.pci1), socket=self.ports_socket)
        self.config_testpmd()

    def send_packets(self, packets, tx_port=None, count=1):
        self.pkt.update_pkt(packets)
        tx_port = self.tester_iface0 if not tx_port else tx_port
        self.pkt.send_pkt(crb=self.tester, tx_port=tx_port, count=count)

    def send_pkts_getouput(self, pkts, port_id=0, count=1, drop=False):
        tx_port = self.tester_iface0 if port_id == 0 else self.tester_iface1

        time.sleep(1)
        if drop:
            self.pmd_output.execute_cmd("clear port stats all")
            time.sleep(0.5)
            self.send_packets(pkts, tx_port=tx_port, count=count)
            out = self.pmd_output.execute_cmd("stop")
            self.pmd_output.execute_cmd("start")
        else:
            self.send_packets(pkts, tx_port=tx_port, count=count)
            out = self.pmd_output.get_output()
        return out

    def create_fdir_rule(self, rule: (list, str), check_stats=None, msg=None, validate=True):
        if validate:
            if isinstance(rule, list):
                validate_rule = [i.replace('create', 'validate') for i in rule]
            else:
                validate_rule = rule.replace('create', 'validate')
            self.validate_fdir_rule(validate_rule, check_stats=check_stats)
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        if isinstance(rule, list):
            for i in rule:
                out = self.pmd_output.execute_cmd(i, timeout=1)
                if msg:
                    self.verify(msg in out, "failed: expect %s in %s" % (msg, out))
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        elif isinstance(rule, str):
            out = self.pmd_output.execute_cmd(rule, timeout=1)
            if msg:
                self.verify(msg in out, "failed: expect %s in %s" % (msg, out))
            m = p.search(out)
            if m:
                rule_list.append(m.group(1))
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            self.verify(all(rule_list), "some rules create failed, result %s" % rule_list)
        elif check_stats == False:
            self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        return rule_list

    def validate_fdir_rule(self, rule, check_stats=True, check_msg=None):
        flag = 'Flow rule validated'
        if isinstance(rule, str):
            out = self.pmd_output.execute_cmd(rule, timeout=1)
            if check_stats:
                self.verify(flag in out.strip(), "rule %s validated failed, result %s" % (rule, out))
            else:
                if check_msg:
                    self.verify(flag not in out.strip() and check_msg in out.strip(),
                                "rule %s validate should failed with msg: %s, but result %s" % (rule, check_msg, out))
                else:
                    self.verify(flag not in out.strip(), "rule %s validate should failed, result %s" % (rule, out))
        elif isinstance(rule, list):
            for r in rule:
                out = self.pmd_output.execute_cmd(r, timeout=1)
                if check_stats:
                    self.verify(flag in out.strip(), "rule %s validated failed, result %s" % (r, out))
                else:
                    if not check_msg:
                        self.verify(flag not in out.strip(), "rule %s validate should failed, result %s" % (r, out))
                    else:
                        self.verify(flag not in out.strip() and check_msg in out.strip(),
                                    "rule %s should validate failed with msg: %s, but result %s" % (
                                        r, check_msg, out))

    def check_fdir_rule(self, port_id=0, stats=True, rule_list=None):
        out = self.pmd_output.execute_cmd("flow list %s" % port_id)
        p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
        matched = p.search(out)
        if stats:
            self.verify(matched, "flow rule on port %s is not existed" % port_id)
            if rule_list:
                p = re.compile("^(\d+)\s")
                li = out.splitlines()
                res = list(filter(bool, list(map(p.match, li))))
                result = [i.group(1) for i in res]
                self.verify(sorted(result) == sorted(rule_list),
                            "check rule list failed. expect %s, result %s" % (rule_list, result))
        else:
            self.verify(not matched, "flow rule on port %s is existed" % port_id)

    def destroy_fdir_rule(self, port_id=0, rule_id=None):
        if rule_id is None:
            rule_id = 0
        if isinstance(rule_id, list):
            for i in rule_id:
                out = self.dut.send_command("flow destroy %s rule %s" % (port_id, i), timeout=1)
                p = re.compile(r"Flow rule #(\d+) destroyed")
                m = p.search(out)
                self.verify(m, "flow rule %s delete failed" % rule_id)
        else:
            out = self.dut.send_command("flow destroy %s rule %s" % (port_id, rule_id), timeout=1)
            p = re.compile(r"Flow rule #(\d+) destroyed")
            m = p.search(out)
            self.verify(m, "flow rule %s delete failed" % rule_id)

    def test_flow_validation(self):
        rule = "flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end"
        self.validate_fdir_rule(rule)
        rules3 = [
            'flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark / count / end',
            'flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 0 1 end / mark id 1 / count identifier 0x1234 shared on / end',
            'flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark id 2 / count identifier 0x34 shared off / end',
            'flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark id 3 / rss / count shared on / end',
            'flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / count shared off / end']
        self.validate_fdir_rule(rules3)
        self.check_fdir_rule(stats=False)

    def test_negative_validation(self):
        # dpdk now supoort only count action
        # self.validate_fdir_rule(
        #    'flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions count / end',
        #    check_stats=False, check_msg='Invalid argument')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / and actions end',
            check_stats=False, check_msg='Bad arguments')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 2 3 end / rss / end',
            check_stats=False, check_msg='error')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / mark id 4294967296 / end',
            check_stats=False, check_msg='Bad arguments')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tc is 4 / end actions queue index 1 / end',
            check_stats=False, check_msg='Bad arguments')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 64 / end',
            check_stats=False, check_msg='Invalid argument')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end',
            check_stats=False, check_msg='Invalid argument')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 end / end',
            check_stats=False, check_msg='Invalid argument')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues end / end',
            check_stats=False, check_msg='Invalid argument')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end',
            check_stats=False, check_msg='Invalid argument')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 63 64 end / end',
            check_stats=False, check_msg='Invalid argument')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x100 / end actions queue index 1 / end',
            check_stats=False, check_msg='Bad arguments')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc qfi is 0x5 / end actions queue index 2 / end',
            check_stats=False, check_msg='Bad arguments')
        self.validate_fdir_rule(
            'flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / end actions queue index 1 / end',
            check_stats=False, check_msg='Bad arguments')
        # need run for os default pkg
        # self.validate_fdir_rule(
        #     'flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end',
        #     check_stats=False, check_msg='Bad arguments')
        self.validate_fdir_rule(
            'flow validate 2 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end',
            check_stats=False, check_msg='No such device')
        self.check_fdir_rule(stats=False)

    def test_mac_ipv4_pay_protocal(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 1 / end actions queue index 1 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 17 / end actions passthru / mark id 3 / end"]
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        pkt1 = 'Ether(dst="00:11:22:33:44:55") / IP(src="192.168.0.20", dst="192.168.0.21", proto=1) / Raw("x" * 80)'
        pkt2 = 'Ether(dst="00:11:22:33:44:55") / IP(src="192.168.0.20", dst="192.168.0.21", frag=1, proto=1) / Raw("x" * 80)'
        pkt3 = 'Ether(dst="00:11:22:33:44:55") / IP(src="192.168.0.20", dst="192.168.0.21", ttl=2, tos=4) / UDP(sport=22, dport=23) / Raw("x" * 80)'
        pkt4 = 'Ether(dst="00:11:22:33:44:55") / IP(src="192.168.0.20", dst="192.168.0.21", frag=1, ttl=2, tos=4) / UDP(sport=22, dport=23) / Raw("x" * 80)'
        pkt5 = 'Ether(dst="00:11:22:33:44:55") / IP(src="192.168.0.20", dst="192.168.0.21", proto=17, ttl=2, tos=4) / Raw("x" * 80)'
        pkt6 = 'Ether(dst="00:11:22:33:44:55") / IP(src="192.168.0.20", dst="192.168.0.21", frag=1, proto=17, ttl=2, tos=4) / Raw("x" * 80)'

        out = self.send_pkts_getouput([pkt1, pkt2])
        port_id = 0
        p = re.compile(r'port\s+%s/queue(.+?):\s+received\s+(\d+)\s+packets.*?FDIR matched ID=(\S+)' % port_id, re.S)
        res = p.findall(out)
        pkt_num = sum([int(i[1]) for i in res])
        pkt_queue = set([int(i[0]) for i in res])
        pkt_mark_id = set([i[2] for i in res])
        self.verify(pkt_num == 2, "received pkts %s, expect 2" % pkt_num)
        self.verify(all([i == 1 for i in pkt_queue]), "wrong received queue %s, expect 1" % pkt_queue)
        self.verify(all([i == '0x1' for i in pkt_mark_id]), "wrong received mark id %s, expect 0x1" % pkt_mark_id)

        out2 = self.send_pkts_getouput([pkt3, pkt4, pkt5, pkt6])
        res = p.findall(out2)
        pkt_num = sum([int(i[1]) for i in res])
        pkt_mark_id = set([i[2] for i in res])
        self.verify(pkt_num == 4, "received pkts %s, expect 4" % pkt_num)
        rfc.verify_directed_by_rss(out2)
        self.verify(all([i == '0x3' for i in pkt_mark_id]), "wrong received mark id %s, expect 0x1" % pkt_mark_id)

        pkt7 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", proto=1) / Raw("x" * 80)'
        pkt8 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=6) / Raw("x" * 80)'
        pkt9 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/ Raw("x" * 80)'
        pkt10 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1)/TCP(sport=22,dport=23)/ Raw("x" * 80)'

        out3 = self.send_pkts_getouput([pkt7, pkt8, pkt9, pkt10])
        fdir_scanner = re.compile("FDIR matched ID=(0x\w+)")
        p2 = re.compile(r"port\s+%s/queue\s+(\d+):\s+received\s+(\d+)\s+packets" % port_id)
        res = p2.findall(out3)
        pkt_num = sum([int(i[1]) for i in res])
        self.verify(pkt_num == 4, "received pkts %s, expect 4" % pkt_num)
        self.verify(not fdir_scanner.search(out3), "should not FDIR matched ID included in output: %s" % out3)

        self.check_fdir_rule(port_id=port_id, rule_list=rule_li)
        self.destroy_fdir_rule(rule_id=rule_li)

        out = self.send_pkts_getouput([pkt1, pkt2, pkt3, pkt4, pkt5, pkt6])
        res = p2.findall(out)
        pkt_num = sum([int(i[1]) for i in res])
        self.verify(pkt_num == 6, "received pkts %s, expect 6" % pkt_num)
        self.verify(not fdir_scanner.search(out3), "should not FDIR matched ID included in output: %s" % out3)
        self.check_fdir_rule(stats=False)

    def test_mac_ipv6_pay_protocal(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 44 / end actions rss queues 5 6 end / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 6 / end actions mark id 2 / rss / end"]
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        pkt1 = 'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010", nh=44, tc=1, hlim=2)/("X"*480)'
        pkt2 = 'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/IPv6ExtHdrFragment(b"1000")/("X"*480)'
        pkt3 = 'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010", nh=44)/TCP(sport=22,dport=23)/("X"*480)'
        pkt4 = 'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/IPv6ExtHdrFragment(b"1000")/TCP(sport=22,dport=23)/("X"*480)'
        pkt5 = 'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/("X"*480)'
        pkt6 = 'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)'

        out = self.send_pkts_getouput([pkt1, pkt2, pkt3, pkt4])
        port_id = 0
        p = re.compile(r'port\s+%s/queue(.+?):\s+received\s+(\d+)\s+packets.*?FDIR matched ID=(\S+)' % port_id, re.S)
        res = p.findall(out)
        pkt_num = sum([int(i[1]) for i in res])
        pkt_queue = set([int(i[0]) for i in res])
        pkt_mark_id = set([i[2] for i in res])
        self.verify(pkt_num == 4, "received pkts %s, expect 4" % pkt_num)
        self.verify(all([i in [5, 6] for i in pkt_queue]), "wrong received queue %s, expect 5 or 6]" % pkt_queue)
        self.verify(all([i == '0x1' for i in pkt_mark_id]), "wrong received mark id %s, expect 0x1" % pkt_mark_id)

        out2 = self.send_pkts_getouput([pkt5, pkt6])
        res = p.findall(out2)
        pkt_num = sum([int(i[1]) for i in res])
        pkt_mark_id = set([i[2] for i in res])
        self.verify(pkt_num == 2, "received pkts %s, expect 2" % pkt_num)
        rfc.verify_directed_by_rss(out2)
        self.verify(all([i == '0x2' for i in pkt_mark_id]), "wrong received mark id %s, expect 0x2" % pkt_mark_id)

        pkt8 = 'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)'
        pkt9 = 'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=17)/("X"*480)'

        out3 = self.send_pkts_getouput([pkt8, pkt9])
        fdir_scanner = re.compile("FDIR matched ID=(0x\w+)")
        p2 = re.compile(r"port\s+%s/queue\s+(\d+):\s+received\s+(\d+)\s+packets" % port_id)
        res = p2.findall(out3)
        pkt_num = sum([int(i[1]) for i in res])
        self.verify(pkt_num == 2, "received pkts %s, expect 3" % pkt_num)
        self.verify(not fdir_scanner.search(out3), "should not FDIR matched ID included in output: %s" % out3)

        self.check_fdir_rule(port_id=port_id, rule_list=rule_li)
        self.destroy_fdir_rule(rule_id=rule_li)

        out = self.send_pkts_getouput([pkt1, pkt2, pkt3, pkt4, pkt5, pkt6])
        res = p2.findall(out)
        pkt_num = sum([int(i[1]) for i in res])
        self.verify(pkt_num == 6, "received pkts %s, expect 6" % pkt_num)
        self.verify(not fdir_scanner.search(out3), "should not FDIR matched ID included in output: %s" % out3)
        self.check_fdir_rule(stats=False)

    def test_invalid_parameters_of_queue_index(self):
        rule = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 64 / end"
        out = self.dut.send_command(rule, timeout=1)
        self.verify("error" in out, "failed with output: %s" % out)
        self.check_fdir_rule(port_id=0, stats=False)

    def test_invalid_parameters_of_rss_queues(self):
        rule1 = [
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end",
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 end / end",
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues end / end"]
        self.create_fdir_rule(rule=rule1, check_stats=False, msg='error')
        rule2 = 'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end'
        self.create_fdir_rule(rule2, check_stats=False, msg='error')
        rule3 = 'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 63 64 end / end'
        self.create_fdir_rule(rule3, check_stats=False, msg='error')
        try:
            # restart testpmd
            self.dut.send_expect("quit", "# ")
            self.dut.kill_all()
            self.launch_testpmd_with_mark(rxq=7, txq=7)
            self.pmd_output.execute_cmd("start")
            rule4 = 'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 proto is 255 / end actions rss queues 0 1 2 3 4 5 6 7 end / end'
            self.create_fdir_rule(rule4, check_stats=False)
            self.check_fdir_rule(port_id=0, stats=False)
            # restart testpmd
            self.dut.send_expect("quit", "# ")
            self.dut.kill_all()
            self.launch_testpmd_with_mark(rxq=8, txq=8)
            self.pmd_output.execute_cmd("start")
            self.create_fdir_rule(rule4, check_stats=True)
            out = self.send_pkts_getouput(pkts=MAC_IPV4_PAY['match'])
            rfc.check_mark(out, pkt_num=len(MAC_IPV4_PAY['match']), check_param={"port_id": 0, "queue": list(range(8))},
                           stats=True)
            out2 = self.send_pkts_getouput(pkts=MAC_IPV4_PAY['unmatched'])
            rfc.check_mark(out2, pkt_num=len(MAC_IPV4_PAY['unmatched']),
                           check_param={"port_id": 0, "queue": list(range(8))}, stats=True)
        except Exception as e:
            raise Exception(e)
        finally:
            self.dut.kill_all()
            self.launch_testpmd_with_mark()

    def test_invalid_parameters_of_input_set(self):
        rule = [
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x100 / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc qfi is 0x5 / end actions queue index 2 / end",
            "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / end actions queue index 1 / end"
        ]
        self.create_fdir_rule(rule, check_stats=False, msg="Bad arguments")
        self.check_fdir_rule(stats=False)

    def test_invalid_parameters_of_mark_id(self):
        rule = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark id 4294967296 / end"
        self.create_fdir_rule(rule, check_stats=False, msg="Bad arguments")
        self.check_fdir_rule(stats=False)

    def test_duplicated_rules(self):
        rule = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end"
        rule_li = self.create_fdir_rule(rule, check_stats=True)
        self.create_fdir_rule(rule, check_stats=False, msg="Rule already exists!: File exists", validate=False)
        self.check_fdir_rule(stats=True, rule_list=rule_li)

    def test_conflicted_rules(self):
        rule1 = [
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / mark / end']
        rule_li = self.create_fdir_rule(rule1, check_stats=True)
        rule2 = [
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 2 / end",
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions drop / end",
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 2 / mark / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions rss queues 2 3 end / mark / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 3 / mark / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 3 / mark / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2021 / end actions mark / end',
            'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end']
        self.create_fdir_rule(rule2[0:4], check_stats=False, msg="Rule already exists!: File exists", validate=False)
        self.create_fdir_rule(rule2[4:7], check_stats=False, msg="error", validate=False)
        self.create_fdir_rule(rule2[7:], check_stats=False, msg="Invalid input set: Invalid argument", validate=False)
        self.check_fdir_rule(stats=True, rule_list=rule_li)

    def test_conflicted_actions(self):
        rule1 = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / rss queues 2 3 end / end"
        self.create_fdir_rule(rule1, check_stats=False, msg="error")
        self.check_fdir_rule(stats=False)

    def test_void_action(self):
        rule = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions end"
        self.create_fdir_rule(rule, check_stats=False)
        self.check_fdir_rule(stats=False)

    def _test_unsupported_action(self):
        # now dpdk has already support only count action, so this case need update or abandon
        rule = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions count / end"
        self.create_fdir_rule(rule, check_stats=False, msg="Invalid input action: Invalid argument")
        self.check_fdir_rule(stats=False)

    def test_delete_a_nonexistent_rule(self):
        self.check_fdir_rule(stats=False)
        out = self.pmd_output.execute_cmd("flow destroy 0 rule 0")
        self.verify(not "error" in out, "failed, destroy non-existent rule should not raise error")
        self.check_fdir_rule(stats=False)
        out = self.pmd_output.execute_cmd("flow flush 0")
        self.verify(not "error" in out, "failed, flush non-existent rule should not raise error")
        self.check_fdir_rule(stats=False)

    def test_unsupported_input_set_field(self):
        rule = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tc is 2 / end actions queue index 1 / end"
        self.create_fdir_rule(rule, check_stats=False, msg="Bad arguments")
        self.check_fdir_rule(stats=False)

    def test_invalid_port(self):
        rule = "flow create 2 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / end"
        self.create_fdir_rule(rule, check_stats=False, msg="No such device: No such device")
        out = self.pmd_output.execute_cmd("flow list 2")
        self.verify("Invalid port 2" in out, "expect Invalid port 2 in %s" % out)

    def _test_unsupported_pattern(self):
        # only test with OS default package
        rule = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end"
        self.create_fdir_rule(rule, check_stats=False)
        self.check_fdir_rule(stats=False)

    def test_conflict_patterns(self):
        fdir_flag = "ice_flow_create(): Succeeded to create (1) flow"
        switch_flag = "ice_flow_create(): Succeeded to create (2) flow"
        pkts = ['Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22, dport=23)/ Raw("x" * 80)']
        rule1 = 'flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / end actions queue index 1 / end'
        out = self.pmd_output.execute_cmd(rule1)
        self.verify(fdir_flag in out, "fdir rule should be created")
        out = self.send_pkts_getouput(pkts=pkts)
        rfc.check_mark(out, pkt_num=2, check_param={"port_id": 0, "queue": 1}, stats=True)

        rule2 = "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 2 / end"
        out = self.pmd_output.execute_cmd(rule2)
        self.verify(switch_flag in out, "switch rule should be created")
        out = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=True)
        out = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 2}, stats=True)

        self.pmd_output.execute_cmd('flow flush 0')
        out = self.pmd_output.execute_cmd(rule2)
        self.verify(fdir_flag in out, "fdir rule should be created")
        out = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 2}, stats=True)
        out = self.pmd_output.execute_cmd(rule1)
        self.verify(switch_flag in out, "switch rule should be created")
        out = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=True)

    def test_count_for_1_rule(self):
        rule = ["flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / count / end",
                "flow create 1 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions count / end"]
        rule_li = self.create_fdir_rule(rule, check_stats=True)
        out = self.send_pkts_getouput(pkts=MAC_IPV4_PAY['match'])
        rfc.check_mark(out, pkt_num=len(MAC_IPV4_PAY['match']), check_param={"port_id": 0, "queue": 1},
                       stats=True)
        out = self.send_pkts_getouput(port_id=1, pkts=MAC_IPV4_PAY['match'])
        rfc.check_mark(out, pkt_num=len(MAC_IPV4_PAY['match']), check_param={"port_id": 1, "rss": True},
                       stats=True)

        out = self.send_pkts_getouput(pkts=MAC_IPV4_PAY['unmatched'])
        rfc.check_mark(out, pkt_num=len(MAC_IPV4_PAY['unmatched']), check_param={"port_id": 0, "rss": True},
                       stats=False)
        out = self.send_pkts_getouput(port_id=1, pkts=MAC_IPV4_PAY['unmatched'])
        rfc.check_mark(out, pkt_num=len(MAC_IPV4_PAY['unmatched']), check_param={"port_id": 1, "rss": True},
                       stats=False)
        self.query_count(1, 2, 0, 0)
        self.query_count(1, 2, 1, 0)
        self.check_fdir_rule(port_id=0, stats=True, rule_list=['0'])
        self.check_fdir_rule(port_id=1, stats=True, rule_list=['0'])
        self.destroy_fdir_rule(0, ['0'])
        self.destroy_fdir_rule(1, ['0'])
        out = self.send_pkts_getouput(pkts=MAC_IPV4_PAY['match'])
        rfc.check_mark(out, pkt_num=len(MAC_IPV4_PAY['match']), check_param={"port_id": 0, "rss": True},
                       stats=False)
        out = self.send_pkts_getouput(port_id=1, pkts=MAC_IPV4_PAY['match'])
        rfc.check_mark(out, pkt_num=len(MAC_IPV4_PAY['match']), check_param={"port_id": 0, "rss": True},
                       stats=False)
        self.check_fdir_rule(stats=False)
        self.check_fdir_rule(port_id=1, stats=False)
        out = self.pmd_output.execute_cmd("flow query 0 0 count")
        self.verify("Flow rule #0 not found" in out, "query should failed")
        out = self.pmd_output.execute_cmd("flow query 1 0 count")
        self.verify("Flow rule #0 not found" in out, "query should failed")

    def test_count_query_identifier_share(self):
        rule1 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions queue index 1 / count identifier 0x1234 shared on / end'
        rule2 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / end actions rss queues 2 3 end / count identifier 0x1234 shared on / end'
        rule3 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 / end actions passthru / mark / count identifier 0x1234 shared off / end'
        rule4 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.4 / end actions mark id 1 / rss / count identifier 0x1234 / end'
        rule5 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.5 / end actions queue index 5 / count shared on / end'
        rule6 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.6 / end actions drop / count shared on / end'
        rule7 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.7 / end actions drop / count identifier 0x1235 shared on / end'
        rule8 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.8 / end actions rss / count / end'

        pkt1 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.21") / Raw("x" * 80)'
        pkt2 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.21") / Raw("x" * 80)'
        pkt3 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.21") / Raw("x" * 80)'
        pkt4 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4",dst="192.168.0.21") / Raw("x" * 80)'
        pkt5 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.5",dst="192.168.0.21") / Raw("x" * 80)'
        pkt6 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.6",dst="192.168.0.21") / Raw("x" * 80)'
        pkt7 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.21") / Raw("x" * 80)'
        pkt8 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.8",dst="192.168.0.21") / Raw("x" * 80)'

        res = self.create_fdir_rule([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8], check_stats=True)
        self.verify(all(res), "create rules failed, result: %s" % res)
        out1 = self.send_pkts_getouput(pkt1, count=10)
        rfc.check_mark(out1, pkt_num=10, check_param={"queue": 1}, stats=True)
        out2 = self.send_pkts_getouput(pkt2, count=10)
        rfc.check_mark(out2, pkt_num=10, check_param={"queue": [2, 3]}, stats=True)
        out3 = self.send_pkts_getouput(pkt3, count=10)
        rfc.check_mark(out3, pkt_num=10, check_param={"mark_id": 0, "rss": True}, stats=True)
        out4 = self.send_pkts_getouput(pkt4, count=10)
        rfc.check_mark(out4, pkt_num=10, check_param={"mark_id": 1, "rss": True}, stats=True)
        out5 = self.send_pkts_getouput(pkt5, count=10)
        rfc.check_mark(out5, pkt_num=10, check_param={"queue": 5}, stats=True)
        out6 = self.send_pkts_getouput(pkt6, count=10, drop=True)
        rfc.check_drop(out6, pkt_num=10, check_param={"port_id": 0})
        out7 = self.send_pkts_getouput(pkt7, count=10, drop=True)
        rfc.check_drop(out7, pkt_num=10, check_param={"port_id": 0})
        out8 = self.send_pkts_getouput(pkt8, count=10)
        rfc.check_mark(out8, pkt_num=10, check_param={"rss": True}, stats=True)

        self.query_count(1, 20, 0, 0)
        self.query_count(1, 20, 0, 1)
        self.query_count(1, 10, 0, 2)
        self.query_count(1, 10, 0, 3)
        self.query_count(1, 20, 0, 4)
        self.query_count(1, 20, 0, 5)
        self.query_count(1, 10, 0, 6)
        self.query_count(1, 10, 0, 7)

        self.check_fdir_rule(0, stats=True, rule_list=res)
        self.dut.send_command("flow flush 0", timeout=1)
        self.check_fdir_rule(stats=False)

        self.send_pkts_getouput(pkts=[pkt1, pkt2, pkt3, pkt4, pkt5, pkt6, pkt7, pkt8])
        out = self.pmd_output.execute_cmd("flow query 0 0 count")
        self.verify("Flow rule #0 not found" in out, "query should failed")

    @skip_unsupported_pkg('os default')
    def test_multi_patterns_mark_count_query(self):
        rule1 = 'flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / count / end'
        rule2 = 'flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / mark id 1 / count / end'
        rule3 = 'flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions rss queues 62 63 end / mark id 2 / count / end'
        rule4 = 'flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / mark id 3 / count / end'
        rule5 = 'flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 3 / mark id 4 / count / end'
        rule6 = 'flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 / tcp dst is 23 / end actions queue index 4 / count / mark id 5 / end'
        rule7 = 'flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 5 / mark id 6 / count / end'
        rule8 = 'flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 \
    32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 end / mark id 100 / count / end'

        pkt1 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /TCP(sport=22, dport=23)/ Raw("x" * 80)'
        pkt2 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22, dport=23)/ Raw("x" * 80)'
        pkt3 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /SCTP(sport=22, dport=23)/ Raw("x" * 80)'
        pkt4 = 'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=1, tc=1, hlim=2)/("X"*480)'
        pkt5 = 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=4790)/VXLAN(flags=0xc)/IP(dst="192.168.0.21", src="192.168.0.20")/UDP(sport=22,dport=23)/("X"*480)'
        pkt6 = 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20")/TCP(dport=23)/("X"*480)'
        pkt7 = 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP(sport=22,dport=23)/("X"*480)'
        pkt8 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)'

        res = self.create_fdir_rule(rule=[rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8], check_stats=True)
        self.verify(all(res), "create rules failed, result %s" % res)
        out = self.send_pkts_getouput(pkts=pkt1, count=10)
        rfc.check_mark(out, pkt_num=10, check_param={"queue": 1, "mark_id": 0}, stats=True)
        out = self.send_pkts_getouput(pkts=pkt2, count=10, drop=True)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 0})
        out = self.send_pkts_getouput(pkts=pkt3, count=10)
        rfc.check_mark(out, pkt_num=10, check_param={"queue": [62, 63], "mark_id": 2}, stats=True)
        out = self.send_pkts_getouput(pkts=pkt4, count=10)
        rfc.check_mark(out, pkt_num=10, check_param={"queue": 1, "mark_id": 3}, stats=True)
        out = self.send_pkts_getouput(pkts=pkt5, count=10)
        rfc.check_mark(out, pkt_num=10, check_param={"queue": 3, "mark_id": 4}, stats=True)
        out = self.send_pkts_getouput(pkts=pkt6, count=10)
        rfc.check_mark(out, pkt_num=10, check_param={"queue": 4, "mark_id": 5}, stats=True)
        out = self.send_pkts_getouput(pkts=pkt7, count=10)
        rfc.check_mark(out, pkt_num=10, check_param={"queue": 5, "mark_id": 6}, stats=True)
        out = self.send_pkts_getouput(port_id=1, pkts=pkt8, count=10)
        rfc.check_mark(out, pkt_num=10, check_param={"port_id": 1, "rss": True, "mark_id": 100}, stats=True)

        for i in range(7):
            self.query_count(1, 10, port_id=0, rule_id=i)
        self.query_count(1, 10, port_id=1, rule_id=0)
        self.check_fdir_rule(port_id=0, stats=True, rule_list=res[:-1])
        self.dut.send_command("flow flush 0", timeout=1)
        self.check_fdir_rule(stats=False)

        self.send_pkts_getouput(pkts=[pkt1, pkt2, pkt3, pkt4, pkt5, pkt6, pkt7, pkt8])
        out = self.pmd_output.execute_cmd("flow query 0 0 count")
        self.verify("Flow rule #0 not found" in out, "query should failed")

    def test_max_count_number(self):
        pattern = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.{} / end actions drop / count / end"
        rules = [pattern.format(i) for i in range(1, 256)] + [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 / end actions drop / count / end"]
        res = self.create_fdir_rule(rules, check_stats=True)

        rule2 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.1.2 / end actions drop / count / end'
        self.create_fdir_rule(rule2, check_stats=False, msg="No free counter found", validate=False)

        pkt = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1",dst="192.168.0.21") / Raw("x" * 80)'
        out = self.send_pkts_getouput(pkt, count=10, drop=True)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 0}, stats=True)
        self.query_count(1, 10, port_id=0, rule_id=255)
        self.check_fdir_rule(0, stats=True, rule_list=res)
        self.dut.send_command("flow flush 0", timeout=1)
        out = self.send_pkts_getouput(pkt, count=10, drop=True)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 0}, stats=False)
        self.check_fdir_rule(stats=False)
        self.dut.send_command("stop", timeout=2)
        self.dut.send_command("quit", timeout=2)
        self.launch_testpmd_with_mark()

    @skip_unsupported_pkg('os default')
    def test_same_rule_on_two_ports(self):
        rule = [
            'flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark / end',
            'flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark / end']
        self.create_fdir_rule(rule=rule, check_stats=True)
        p_gtpu1 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP()/Raw("x"*20)'
        out1 = self.send_pkts_getouput(pkts=p_gtpu1, port_id=0)
        rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 0}, stats=True)
        out2 = self.send_pkts_getouput(pkts=p_gtpu1, port_id=1)
        rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 1, "queue": 1, "mark_id": 0}, stats=True)
        self.check_fdir_rule(port_id=0, stats=True, rule_list=['0'])
        self.check_fdir_rule(port_id=1, stats=True, rule_list=['0'])
        self.destroy_fdir_rule(port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)
        self.check_fdir_rule(port_id=1, stats=True, rule_list=['0'])
        out1 = self.send_pkts_getouput(pkts=p_gtpu1, port_id=0)
        rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "queue": 1, "rss": True}, stats=False)
        out2 = self.send_pkts_getouput(pkts=p_gtpu1, port_id=1)
        rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 1, "queue": 1, "mark_id": 0}, stats=True)
        self.destroy_fdir_rule(port_id=1)
        self.check_fdir_rule(port_id=0, stats=False)
        self.check_fdir_rule(port_id=1, stats=False)
        out1 = self.send_pkts_getouput(pkts=p_gtpu1, port_id=0)
        rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "queue": 1, "rss": True}, stats=False)
        out2 = self.send_pkts_getouput(pkts=p_gtpu1, port_id=1)
        rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 1, "queue": 1, "rss": True}, stats=False)

    def test_same_intput_set_different_actions_on_two_ports(self):
        rule = [
            'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end',
            'flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / mark id 1 / end']
        self.create_fdir_rule(rule=rule, check_stats=True)
        pkt = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)'
        out1 = self.send_pkts_getouput(pkts=pkt, port_id=0)
        rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 1}, stats=True)
        out2 = self.send_pkts_getouput(pkts=pkt, port_id=1)
        rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 1, "queue": [2, 3], "mark_id": 1}, stats=True)
        self.pmd_output.execute_cmd('flow flush 0')
        self.pmd_output.execute_cmd('flow flush 1')
        self.check_fdir_rule(0, False)
        self.check_fdir_rule(1, False)
        out1 = self.send_pkts_getouput(pkts=pkt, port_id=0)
        rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "queue": 1, "rss": True}, stats=False)
        out2 = self.send_pkts_getouput(pkts=pkt, port_id=1)
        rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 1, "queue": [2, 3], "rss": True}, stats=False)

    @skip_unsupported_pkg('os default')
    def test_two_ports_multi_patterns_count_query(self):
        rules = [
            'flow create 1 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 255  tos is 4 / end actions queue index 1 / mark id 1 / count identifier 0x1234 shared on / end',
            'flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions rss queues 6 7 end / mark id 2 / count identifier 0x1234 shared on / end',
            'flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss queues 6 7 end / mark id 1 / count / end',
            'flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 2 / mark / count / end',
            'flow create 1 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / count / end',
            'flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions drop / count / end',
            'flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / mark id 1 / count identifier 0x1234 shared on / end']
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", ttl=2, tos=4)/TCP(sport=22,dport=23)/Raw(load="X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", ttl=2, tos=4)/TCP(sport=22,dport=23)/Raw(load="X"*480)']

        self.create_fdir_rule(rule=rules, check_stats=True)

        out1 = self.send_pkts_getouput(pkts[0], port_id=1, count=10)
        rfc.check_mark(out1, pkt_num=10, check_param={"port_id": 1, "queue": 1, "mark_id": 1})
        out2 = self.send_pkts_getouput(pkts[1], port_id=1, count=10)
        rfc.check_mark(out2, pkt_num=10, check_param={"port_id": 1, "queue": [6, 7], "mark_id": 2})
        out3 = self.send_pkts_getouput(pkts[2], port_id=1, count=10)
        rfc.check_mark(out3, pkt_num=10, check_param={"port_id": 1, "queue": [6, 7], "mark_id": 1})
        out4 = self.send_pkts_getouput(pkts[3], port_id=1, count=10)
        rfc.check_mark(out4, pkt_num=10, check_param={"port_id": 1, "queue": 2, "mark_id": 0})
        out5 = self.send_pkts_getouput(pkts[4], port_id=1, count=10, drop=True)
        rfc.check_mark(out5, pkt_num=10, check_param={"port_id": 1, "drop": True})
        out6 = self.send_pkts_getouput(pkts[5], port_id=0, count=10, drop=True)
        rfc.check_mark(out6, pkt_num=10, check_param={"port_id": 0, "drop": True})
        out7 = self.send_pkts_getouput(pkts[6], port_id=0, count=10)
        rfc.check_mark(out7, pkt_num=10, check_param={"port_id": 0, "queue": 1, "mark_id": 1})
        out8 = self.send_pkts_getouput(pkts[7], port_id=1, count=10)
        rfc.check_mark(out8, pkt_num=10, check_param={"port_id": 1})
        self.query_count(1, 20, 1, 0)
        self.query_count(1, 20, 1, 1)
        self.query_count(1, 10, 1, 2)
        self.query_count(1, 10, 1, 3)
        self.query_count(1, 10, 1, 4)
        self.query_count(1, 10, 0, 0)
        self.query_count(1, 10, 0, 1)
        self.check_fdir_rule(port_id=1, stats=True, rule_list=list(map(str, range(5))))
        self.check_fdir_rule(port_id=0, stats=True, rule_list=list(map(str, range(2))))
        self.pmd_output.execute_cmd("flow flush 0")
        self.pmd_output.execute_cmd("flow flush 1")
        out1 = self.send_pkts_getouput(pkts=pkts[:5].append(pkts[7]), port_id=1, count=10)
        rfc.check_mark(out1, pkt_num=60, check_param={"port_id": 1}, stats=False)
        out2 = self.send_pkts_getouput(pkts=pkts[5:7], port_id=0, count=10)
        rfc.check_mark(out2, pkt_num=20, check_param={"port_id": 0}, stats=False)
        self.check_fdir_rule(port_id=0, stats=False)
        self.check_fdir_rule(port_id=1, stats=False)
        for i in range(5):
            out = self.pmd_output.execute_cmd("flow query %s %s count" % (1, i))
            self.verify("Flow rule #%s not found" % i in out, "expect not rule found, result %s" % out)
        for i in range(2):
            out = self.pmd_output.execute_cmd("flow query %s %s count" % (0, i))
            self.verify("Flow rule #%s not found" % i in out, "expect not rule found, result %s" % out)

    def test_port_stop_start_reset(self):
        rule = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark / end"
        rule_li = self.create_fdir_rule(rule=rule, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=True, rule_list=rule_li)
        pkt = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") / Raw("x" * 80)'
        out1 = self.send_pkts_getouput(pkts=pkt, port_id=0, count=1)
        rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 0}, stats=True)
        self.pmd_output.execute_cmd("port stop 0")
        self.pmd_output.execute_cmd("port start 0")
        self.check_fdir_rule(port_id=0, stats=True, rule_list=rule_li)
        out2 = self.send_pkts_getouput(pkts=pkt, port_id=0, count=1)
        rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 0}, stats=True)
        rule2 = 'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.22 dst is 192.168.0.23 / end actions queue index 2 / mark id 1 / end'
        rule_li2 = self.create_fdir_rule(rule=rule2, check_stats=True)
        self.check_fdir_rule(rule_list=rule_li+rule_li2)
        out3 = self.send_pkts_getouput(pkts='Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22",dst="192.168.0.23") / Raw("x" * 80)', port_id=0, count=1)
        rfc.check_mark(out3, pkt_num=1, check_param={"port_id": 0, "queue": 2, "mark_id": 1}, stats=True)

    def test_delete_rules(self):
        rules = [
            'flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end',
            'flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 24 / end actions queue index 2 / mark / end',
            'flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 25 / end actions queue index 3 / mark / end']
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.56.0",dst="192.1.0.0",tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.56.0",dst="192.1.0.0",tos=4)/TCP(sport=22,dport=24)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.56.0",dst="192.1.0.0",tos=4)/TCP(sport=22,dport=25)/Raw("x" * 80)']
        queues = [1, 2, 3]

        for i in range(3):
            rule_li = self.create_fdir_rule(rule=rules, check_stats=True)
            rule_li2 = copy.copy(rule_li)
            pkts2 = copy.copy(pkts)
            queues2 = copy.copy(queues)
            self.check_fdir_rule(rule_list=rule_li)
            out1 = self.send_pkts_getouput(pkts=pkts[0], port_id=0, count=1)
            rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 0}, stats=True)
            out2 = self.send_pkts_getouput(pkts=pkts[1], port_id=0, count=1)
            rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 0, "queue": 2, "mark_id": 0}, stats=True)
            out3 = self.send_pkts_getouput(pkts=pkts[2], port_id=0, count=1)
            rfc.check_mark(out3, pkt_num=1, check_param={"port_id": 0, "queue": 3, "mark_id": 0}, stats=True)
            self.destroy_fdir_rule(port_id=0, rule_id=i)
            rule_li2.pop(i)
            pkts2.pop(i)
            queues2.pop(i)
            self.check_fdir_rule(rule_list=rule_li2)
            out1 = self.send_pkts_getouput(pkts=pkts[i], port_id=0, count=1)
            rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "queue": queues[i], "mark_id": 0}, stats=False)
            out2 = self.send_pkts_getouput(pkts=pkts2[0], port_id=0, count=1)
            rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 0, "queue": queues2[0], "mark_id": 0}, stats=True)
            out3 = self.send_pkts_getouput(pkts=pkts2[1], port_id=0, count=1)
            rfc.check_mark(out3, pkt_num=1, check_param={"port_id": 0, "queue": queues2[1], "mark_id": 0}, stats=True)
            self.pmd_output.execute_cmd("flow flush 0")
            out1 = self.send_pkts_getouput(pkts=pkts[0], port_id=0, count=1)
            rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 0}, stats=False)
            out2 = self.send_pkts_getouput(pkts=pkts[1], port_id=0, count=1)
            rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 0, "queue": 2, "mark_id": 0}, stats=False)
            out3 = self.send_pkts_getouput(pkts=pkts[2], port_id=0, count=1)
            rfc.check_mark(out3, pkt_num=1, check_param={"port_id": 0, "queue": 3, "mark_id": 0}, stats=False)

    def test_max_rules(self):
        rule_pattern = "flow create 0 ingress pattern eth / ipv4 src is 192.168.100.20 dst is 192.168.%d.%d / end actions queue index 1 / mark / end"
        rules = list()
        pkt_pattern = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.100.20",dst="192.168.%d.%d")/Raw("x" * 80)'
        pkts2 = list()
        # each pf can create 1024 rules at least in 2 ports card
        # each pf can create 512 rules at least in 4 ports card
        # and there are 14k rules shared by pfs and vfs
        # so 1 pf and 2 vfs can create 15360 rules at most on 2 ports card
        # 1 pf and 2 vfs can create 14848 rules at most on 4 ports card
        count = int(self.max_rule_num/256)
        rule_li = list(map(str, range(self.max_rule_num)))
        pkts = ['Ether(dst="00:11:22:33:44:55")/IP(src="192.168.100.20",dst="192.168.0.0")/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.100.20",dst="192.168.%s.255")/Raw("x" * 80)'%(count-1)]
        for i in range(count):
            for j in range(256):
                rules.append(rule_pattern % (i, j))
                pkts2.append(pkt_pattern % (i, j))
        cmd_path = '/tmp/test_max_rules'
        cmd_li = map(lambda x: x + os.linesep, rules)
        with open(cmd_path, 'w') as f:
            f.writelines(cmd_li)
        self.pmd_output.execute_cmd("stop")
        self.dut.send_command("quit", timeout=2)
        self.dut.session.copy_file_to(cmd_path, cmd_path)
        try:
            out = self.pmd_output.start_testpmd(cores="1S/4C/1T",
                                                param="--portmask=%s --rxq=%d --txq=%d --port-topology=loop --cmdline-file=%s" % (
                                                    self.portMask, 64, 64, cmd_path),
                                                eal_param="-a %s -a %s --log-level='ice,7'" % (
                                                    self.pci0, self.pci1), socket=self.ports_socket)
            self.verify('Failed to create flow' not in out, "create some rule failed")
            self.config_testpmd()
            self.pmd_output.execute_cmd('start')
            rule = "flow create 0 ingress pattern eth / ipv4 src is 192.168.100.20 dst is 192.168.65.0 / end actions queue index 1 / mark / end"
            self.create_fdir_rule(rule=rule, check_stats=False, msg='Failed to create flow', validate=False)
            self.check_fdir_rule(port_id=0, stats=True, rule_list=rule_li)
            out1 = self.send_pkts_getouput(pkts=pkts, port_id=0, count=1)
            rfc.check_mark(out1, pkt_num=2, check_param={"port_id": 0, "queue": 1, "mark_id": 0}, stats=True)
            self.pmd_output.execute_cmd("flow flush 0")
            self.check_fdir_rule(port_id=0, stats=False)
            out = self.send_pkts_getouput(pkts=pkts2, port_id=0, count=1)
            rfc.check_mark(out, pkt_num=len(pkts2), check_param={"port_id": 0, "mark_id": 0}, stats=False)
        except Exception as e:
            raise Exception(e)
        finally:
            self.dut.kill_all()
            self.launch_testpmd_with_mark()

    def test_mac_ipv4_pay(self):
        self._rte_flow_validate(vectors_ipv4_pay)

    def test_mac_ipv4_udp(self):
        self._rte_flow_validate(vectors_ipv4_udp)

    def test_mac_ipv4_tcp(self):
        self._rte_flow_validate(vectors_ipv4_tcp)

    def test_mac_ipv4_sctp(self):
        self._rte_flow_validate((vectors_ipv4_sctp))

    def test_mac_ipv6_pay(self):
        self._rte_flow_validate(vectors_ipv6_pay)

    def test_mac_ipv6_udp(self):
        self._rte_flow_validate(vectors_ipv6_udp)

    def test_mac_ipv6_tcp(self):
        self._rte_flow_validate(vectors_ipv6_tcp)

    def test_mac_ipv6_sctp(self):
        self._rte_flow_validate(vectors_ipv6_sctp)

    def test_mac_ipv4_tun_ipv4_pay(self):
        self._rte_flow_validate(vectors_ipv4_tun_ipv4_pay)

    def test_mac_ipv4_tun_ipv4_udp(self):
        self._rte_flow_validate(vectors_ipv4_tun_ipv4_udp)

    def test_mac_ipv4_tun_ipv4_tcp(self):
        self._rte_flow_validate(vectors_ipv4_tun_ipv4_tcp)

    def test_mac_ipv4_tun_ipv4_sctp(self):
        self._rte_flow_validate(vectors_ipv4_tun_ipv4_sctp)

    def test_mac_ipv4_tun_mac_ipv4_pay(self):
        self._rte_flow_validate(vectors_mac_ipv4_tun_mac_ipv4_pay)

    def test_mac_ipv4_tun_mac_ipv4_udp(self):
        self._rte_flow_validate(vectors_mac_ipv4_tun_mac_ipv4_udp)

    def test_mac_ipv4_tun_mac_ipv4_tcp(self):
        self._rte_flow_validate(vectors_mac_ipv4_tun_mac_ipv4_tcp)

    def test_mac_ipv4_tun_mac_ipv4_sctp(self):
        self._rte_flow_validate(vectors_mac_ipv4_tun_mac_ipv4_sctp)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv4_gtpu_eh(self):
        self._rte_flow_validate(vectors_mac_ipv4_gtpu_eh)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv4_gtpu(self):
        self._rte_flow_validate(vectors_mac_ipv4_gtpu)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv6_gtpu_eh(self):
        self._rte_flow_validate(vectors_mac_ipv6_gtpu_eh)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv6_gtpu(self):
        self._rte_flow_validate(vectors_mac_ipv6_gtpu)

    def test_l2_ethertype(self):
        self._multirules_process(vectors_l2_ethertype)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv4_esp(self):
        self._rte_flow_validate(vectors_mac_ipv4_esp)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv6_esp(self):
        self._rte_flow_validate(vectors_mac_ipv6_esp)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv4_nat_t_esp(self):
        self._rte_flow_validate(vectors_mac_ipv4_nat_t_esp)

    @skip_unsupported_pkg('os default')
    def test_mac_ipv6_nat_t_esp(self):
        self._rte_flow_validate(vectors_mac_ipv6_nat_t_esp)

    def test_unsupported_ethertype(self):
        rule = ['flow create 0 ingress pattern eth type is 0x0800 / end actions queue index 1 / end',
                'flow create 0 ingress pattern eth type is 0x86dd / end actions queue index 1 / end']
        self.create_fdir_rule(rule, check_stats=True, msg="Succeeded to create (2) flow")
        self.check_fdir_rule(stats=True)

    def tear_down(self):
        # destroy all flow rule on port 0
        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("flow flush 1", timeout=1)
        self.dut.send_command("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")

    def tear_down_all(self):
        self.dut.kill_all()
