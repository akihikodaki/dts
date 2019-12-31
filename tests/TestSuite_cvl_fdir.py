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


import re
import time

from packet import Packet
from pmd_output import PmdOutput
from test_case import TestCase
import rte_flow_common as rfc

from utils import GREEN, RED
import utils

MAC_IPV4_PAY = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=255, ttl=2, tos=4)/Raw("x" * 80)'],
    "unmatch": [
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
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)'],
    "unmatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22") / Raw("x" * 80)'
    ]
}

MAC_IPV4_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)'],
    "unmatch": [
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
    "unmatch": [
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
    "unmatch": [
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
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=1, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=1, tc=1, hlim=2)/IPv6ExtHdrFragment(1000)/("X"*480)'],
    "unmatch": [
        'Ether(dst="00:11:22:33:44:56")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=1, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022", src="2001::2", nh=1, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::1", nh=1, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=2, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=1, tc=2, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=1, tc=1, hlim=5)/("X"*480)']
}

MAC_IPV6_PAY_SELECTED = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=1, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment(1000)/("X"*480)'],
    "unmatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)']
}

MAC_IPV6_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)'],
    "unmatch": [
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
    "unmatch": [
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
    "unmatch": [
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
    "unmatch": [
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
    "unmatch": [
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
    "unmatch": [
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
    "unmatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.22")/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.23")/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.1.15")/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IP(dst="192.168.0.21", src="192.168.0.20")/SCTP(sport=22,dport=23)/("X"*480)']
}

MAC_IPV4_GTPU_IPV4_PAY = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/ICMP()/Raw("x"*20)'],
    "unmatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/SCTP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw("x"*20)']
}

tv_mac_ipv4_pay_queue_index = {
    "name": "test_mac_ipv4_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_pay_selected_inputset_queue_index = {
    "name": "test_mac_ipv4_pay_selected_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_PAY_SELECTED,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_udp_queue_index = {
    "name": "test_mac_ipv4_upd_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_tcp_queue_index = {
    "name": "test_mac_ipv4_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 63 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 63}
}

tv_mac_ipv4_sctp_queue_index = {
    "name": "test_mac_ipv4_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 tag is 1 / end actions queue index 2 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 2}
}

tv_mac_ipv6_pay_queue_index = {
    "name": "test_mac_ipv6_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 1 hop is 2 tc is 1 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv6_pay_selected_inputset_queue_index = {
    "name": "test_mac_ipv6_pay_selected_inputset_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV6_PAY_SELECTED,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv6_udp_queue_index = {
    "name": "test_mac_ipv6_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv6_tcp_queue_index = {
    "name": "test_mac_ipv6_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv6_sctp_queue_index = {
    "name": "test_mac_ipv6_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_tun_ipv4_pay_queue_index = {
    "name": "test_mac_ipv4_tun_ipv4_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_tun_ipv4_udp_queue_index = {
    "name": "test_mac_ipv4_tun_ipv4_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_tun_ipv4_tcp_queue_index = {
    "name": "test_mac_ipv4_tun_ipv4_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_tun_ipv4_sctp_queue_index = {
    "name": "test_mac_ipv4_tun_ipv4_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_tun_mac_ipv4_pay_queue_index = {
    "name": "test_mac_ipv4_tun_mac_ipv4_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_tun_mac_ipv4_udp_queue_index = {
    "name": "test_mac_ipv4_tun_mac_ipv4_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_tun_mac_ipv4_tcp_queue_index = {
    "name": "test_mac_ipv4_tun_mac_ipv4_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_tun_mac_ipv4_sctp_queue_index = {
    "name": "test_mac_ipv4_tun_mac_ipv4_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_pay_drop = {
    "name": "test_mac_ipv4_pay_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_udp_drop = {
    "name": "test_mac_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_tcp_drop = {
    "name": "test_mac_ipv4_tcp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_sctp_drop = {
    "name": "test_mac_ipv4_sctp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv6_pay_drop = {
    "name": "test_mac_ipv6_pay_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 1 hop is 2 tc is 1 / end actions drop / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv6_udp_drop = {
    "name": "test_mac_ipv6_udp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}
tv_mac_ipv6_tcp_drop = {
    "name": "test_mac_ipv6_tcp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv6_sctp_drop = {
    "name": "test_mac_ipv6_sctp_drop",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_tun_ipv4_pay_drop = {
    "name": "test_mac_ipv4_tun_ipv4_pay_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_tun_ipv4_udp_drop = {
    "name": "test_mac_ipv4_tun_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_tun_ipv4_tcp_drop = {
    "name": "test_mac_ipv4_tun_ipv4_tcp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_tun_ipv4_sctp_drop = {
    "name": "test_mac_ipv4_tun_ipv4_sctp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_tun_mac_ipv4_pay_drop = {
    "name": "test_mac_ipv4_tun_mac_ipv4_pay_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_tun_mac_ipv4_udp_drop = {
    "name": "test_mac_ipv4_tun_mac_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_tun_mac_ipv4_tcp_drop = {
    "name": "test_mac_ipv4_tun_mac_ipv4_tcp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_tun_mac_ipv4_sctp_drop = {
    "name": "test_mac_ipv4_tun_mac_ipv4_sctp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_pay_queue_group = {
    "name": "test_mac_ipv4_pay_queue_group",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 1 end / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [0, 1]}
}

tv_mac_ipv4_udp_queue_group = {
    "name": "test_mac_ipv4_udp_queue_group",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions rss queues 1 2 3 4 end / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4]}
}

tv_mac_ipv4_tcp_queue_group = {
    "name": "test_mac_ipv4_tcp_queue_group",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions rss queues 56 57 58 59 60 61 62 63 end / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": range(56, 64)}
}

tv_mac_ipv4_sctp_queue_group = {
    "name": "test_mac_ipv4_sctp_queue_group",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 tag is 1 / end actions rss queues 0 1 2 3 end / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": range(4)}
}

tv_mac_ipv6_pay_queue_group = {
    "name": "test_mac_ipv6_pay_queue_group",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 1 hop is 2 tc is 1 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv6_udp_queue_group = {
    "name": "test_mac_ipv6_udp_queue_group",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv6_tcp_queue_group = {
    "name": "test_mac_ipv6_tcp_queue_group",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv6_sctp_queue_group = {
    "name": "test_mac_ipv6_sctp_queue_group",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv4_tun_ipv4_pay_queue_group = {
    "name": "test_mac_ipv4_tun_ipv4_pay_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 end / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": range(9, 25)}
}

tv_mac_ipv4_tun_ipv4_udp_queue_group = {
    "name": "test_mac_ipv4_tun_ipv4_udp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 38 39 40 41 end / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [38, 39, 40, 41]}
}

tv_mac_ipv4_tun_ipv4_tcp_queue_group = {
    "name": "test_mac_ipv4_tun_ipv4_tcp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv4_tun_ipv4_sctp_queue_group = {
    "name": "test_mac_ipv4_tun_ipv4_sctp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv4_tun_mac_ipv4_pay_queue_group = {
    "name": "test_mac_ipv4_tun_mac_ipv4_pay_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv4_tun_mac_ipv4_udp_queue_group = {
    "name": "test_mac_ipv4_tun_mac_ipv4_udp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv4_tun_mac_ipv4_tcp_queue_group = {
    "name": "test_mac_ipv4_tun_mac_ipv4_tcp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv4_tun_mac_ipv4_sctp_queue_group = {
    "name": "test_mac_ipv4_tun_mac_ipv4_sctp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv4_gtpu_ipv4_pay_queue_index = {
    "name": "test_mac_ipv4_gtpu_ipv4_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / ipv4 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_PAY,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_gtpu_ipv4_pay_drop = {
    "name": "test_mac_ipv4_gtpu_ipv4_pay_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / ipv4 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_PAY,
    "check_func": rfc.check_drop,
    "check_param": {"port_id": 0}
}

tv_mac_ipv4_gtpu_ipv4_pay_queue_group = {
    "name": "test_mac_ipv4_gtpu_ipv4_pay_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / ipv4 / end actions rss queues 0 1 end / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_PAY,
    "check_func": rfc.check_queue,
    "check_param": {"port_id": 0, "queue": [0, 1]}
}

tv_mac_ipv4_gtpu_ipv4_pay_mark_count_query = {
    "name": "test_mac_ipv4_gtpu_ipv4_pay_mark_count_query",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / ipv4 / end actions queue index 2 / mark id 2 / count / end",
    "scapy_str": MAC_IPV4_GTPU_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 2, "mark_id": 2,
                    "count": {"hits_set": 1, "hits": 5}, "mark": True}
}

tv_mac_ipv4_pay_queue_index_mark = {
    "name": "test_mac_ipv4_pay_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / mark id 0 / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0, "mark": True}
}

tv_mac_ipv4_udp_queue_index_mark = {
    "name": "test_mac_ipv4_udp_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 0 / mark id 1 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 0, "mark_id": 1, "mark": True}
}

tv_mac_ipv4_tcp_queue_index_mark = {
    "name": "test_mac_ipv4_tcp_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 4294967294 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 4294967294, "mark": True}
}

tv_mac_ipv4_sctp_queue_drop_mark = {
    "name": "test_mac_ipv4_sctp_queue_drop_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 tag is 1 / end actions drop / mark id 1 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "mark": True}
}

tv_mac_ipv6_pay_queue_index_mark = {
    "name": "test_mac_ipv6_pay_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 1 hop is 2 tc is 1 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1, "mark": True}
}

tv_mac_ipv6_udp_queue_index_mark = {
    "name": "test_mac_ipv6_udp_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1, "mark": True}
}

tv_mac_ipv6_tcp_queue_index_mark = {
    "name": "test_mac_ipv6_tcp_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1, "mark": True}
}

tv_mac_ipv6_sctp_queue_index_mark = {
    "name": "test_mac_ipv6_sctp_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1, "mark": True}
}

tv_mac_ipv4_tun_ipv4_pay_queue_index_mark = {
    "name": "test_mac_ipv4_tun_ipv4_pay_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1, "mark": True}
}

tv_mac_ipv4_tun_ipv4_udp_queue_group_mark = {
    "name": "test_mac_ipv4_tun_ipv4_udp_queue_group_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 1 2 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": [1, 2], "mark_id": 1, "mark": True}
}

tv_mac_ipv4_tun_ipv4_tcp_drop_mark = {
    "name": "test_mac_ipv4_tun_ipv4_tcp_drop_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "mark_id": 1, "mark": True}
}

tv_mac_ipv4_tun_ipv4_sctp_queue_index_mark = {
    "name": "test_mac_ipv4_tun_ipv4_sctp_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1, "mark": True}
}

tv_mac_ipv4_tun_mac_ipv4_pay_queue_index_mark = {
    "name": "test_mac_ipv4_tun_mac_ipv4_pay_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_PAY_MAC_IPV4_TUN_MAC_IPV4_PAY,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1, "mark": True}
}

tv_mac_ipv4_tun_mac_ipv4_udp_queue_index_mark = {
    "name": "test_mac_ipv4_tun_mac_ipv4_udp_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_UDP_MAC_IPV4_TUN_MAC_IPV4_UDP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1, "mark": True}
}

tv_mac_ipv4_tun_mac_ipv4_tcp_queue_index_mark = {
    "name": "test_mac_ipv4_tun_mac_ipv4_tcp_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_TCP_MAC_IPV4_TUN_MAC_IPV4_TCP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1, "mark": True}
}

tv_mac_ipv4_tun_mac_ipv4_sctp_queue_index_mark = {
    "name": "test_mac_ipv4_tun_mac_ipv4_sctp_queue_index_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_TUN_IPV4_SCTP_MAC_IPV4_TUN_MAC_IPV4_SCTP,
    "check_func": rfc.check_mark,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 1, "mark": True}
}

vectors_ipv4_pay = [tv_mac_ipv4_pay_queue_index, tv_mac_ipv4_pay_selected_inputset_queue_index,
                         tv_mac_ipv4_pay_drop, tv_mac_ipv4_pay_queue_group, tv_mac_ipv4_pay_queue_index_mark]

vectors_ipv4_udp = [tv_mac_ipv4_udp_drop, tv_mac_ipv4_udp_queue_group, tv_mac_ipv4_udp_queue_index_mark,
                         tv_mac_ipv4_udp_queue_index]

vectors_ipv4_tcp = [tv_mac_ipv4_tcp_drop, tv_mac_ipv4_tcp_queue_group, tv_mac_ipv4_tcp_queue_index,
                         tv_mac_ipv4_tcp_queue_index_mark]

vectors_ipv4_sctp = [tv_mac_ipv4_sctp_queue_drop_mark, tv_mac_ipv4_sctp_queue_group, tv_mac_ipv4_sctp_drop,
                          tv_mac_ipv4_sctp_queue_index]

vectors_ipv6_pay = [tv_mac_ipv6_pay_drop, tv_mac_ipv6_pay_queue_group, tv_mac_ipv6_pay_queue_index,
                         tv_mac_ipv6_pay_queue_index_mark, tv_mac_ipv6_pay_selected_inputset_queue_index]

vectors_ipv6_udp = [tv_mac_ipv6_udp_drop, tv_mac_ipv6_udp_queue_group, tv_mac_ipv6_udp_queue_index,
                         tv_mac_ipv6_udp_queue_index_mark]

vectors_ipv6_tcp = [tv_mac_ipv6_tcp_drop, tv_mac_ipv6_tcp_queue_group, tv_mac_ipv6_tcp_queue_index,
                         tv_mac_ipv6_tcp_queue_index_mark]

vectors_ipv6_sctp = [tv_mac_ipv6_sctp_queue_index_mark, tv_mac_ipv6_sctp_drop, tv_mac_ipv6_sctp_queue_group,
                          tv_mac_ipv6_sctp_queue_index]

vectors_ipv4_tun_ipv4 = [tv_mac_ipv4_tun_ipv4_pay_drop, tv_mac_ipv4_tun_ipv4_pay_queue_group,
                              tv_mac_ipv4_tun_ipv4_pay_queue_index, tv_mac_ipv4_tun_ipv4_pay_queue_index_mark,
                              tv_mac_ipv4_tun_ipv4_sctp_drop, tv_mac_ipv4_tun_ipv4_sctp_queue_group,
                              tv_mac_ipv4_tun_ipv4_sctp_queue_index, tv_mac_ipv4_tun_ipv4_sctp_queue_index_mark,
                              tv_mac_ipv4_tun_ipv4_tcp_drop, tv_mac_ipv4_tun_ipv4_tcp_drop_mark,
                              tv_mac_ipv4_tun_ipv4_tcp_queue_group, tv_mac_ipv4_tun_ipv4_tcp_queue_index,
                              tv_mac_ipv4_tun_ipv4_udp_drop, tv_mac_ipv4_tun_ipv4_udp_queue_group,
                              tv_mac_ipv4_tun_ipv4_udp_queue_group_mark, tv_mac_ipv4_tun_ipv4_udp_queue_index]

vectors_ipv4_tun_mac = [tv_mac_ipv4_tun_mac_ipv4_pay_queue_index_mark, tv_mac_ipv4_tun_mac_ipv4_pay_drop,
                             tv_mac_ipv4_tun_mac_ipv4_pay_queue_group, tv_mac_ipv4_tun_mac_ipv4_pay_queue_index,
                             tv_mac_ipv4_tun_mac_ipv4_sctp_drop, tv_mac_ipv4_tun_mac_ipv4_sctp_queue_group,
                             tv_mac_ipv4_tun_mac_ipv4_sctp_queue_index, tv_mac_ipv4_tun_mac_ipv4_sctp_queue_index_mark,
                             tv_mac_ipv4_tun_mac_ipv4_tcp_drop, tv_mac_ipv4_tun_mac_ipv4_tcp_queue_group,
                             tv_mac_ipv4_tun_mac_ipv4_tcp_queue_index, tv_mac_ipv4_tun_mac_ipv4_tcp_queue_index_mark,
                             tv_mac_ipv4_tun_mac_ipv4_udp_drop, tv_mac_ipv4_tun_mac_ipv4_udp_queue_group,
                             tv_mac_ipv4_tun_mac_ipv4_udp_queue_index, tv_mac_ipv4_tun_mac_ipv4_udp_queue_index_mark]

test_vectors_gtpu_ipv4_pay = [tv_mac_ipv4_gtpu_ipv4_pay_drop, tv_mac_ipv4_gtpu_ipv4_pay_mark_count_query,
                              tv_mac_ipv4_gtpu_ipv4_pay_queue_group, tv_mac_ipv4_gtpu_ipv4_pay_queue_index]


class TestCVLFdir(TestCase):

    def check_rule(self, port_id=0, stats=True, rule_list=None):
        out = self.dut.send_command("flow list %s" % port_id, timeout=2)
        p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
        m = p.search(out)
        if stats:
            self.verify(m, "flow rule on port %s is not existed" % port_id)
            if rule_list:
                p = re.compile("^(\d+)\s")
                li = out.splitlines()
                res = filter(bool, map(p.match, li))
                result = [i.group(1) for i in res]
                self.verify(sorted(result) == sorted(rule_list),
                            "check rule list failed. expect %s, result %s" % (rule_list, result))
        else:
            self.verify(not m, "flow rule on port %s is existed" % port_id)

    def destroy_rule(self, rule_id, port_id=0):
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
                count = 1 if not tv["check_param"].get("count") else tv["check_param"]["count"]
                port_id = tv["check_param"]["port_id"]
                mark = tv["check_param"].get("mark")
                # create rule
                rule_li = self.create_fdir_rule(tv["rule"], check_stats=True)
                # send and check match packets
                out1 = self.send_pkts_getouput(pkts=tv["scapy_str"]["match"], port_id=port_id,
                                               count=count, mark=mark)
                tv["check_func"](out1, pkt_num=len(tv["scapy_str"]["match"]), check_param=tv["check_param"])
                # send and check unmatch packets
                out2 = self.send_pkts_getouput(pkts=tv["scapy_str"]["unmatch"], port_id=port_id,
                                               count=count, mark=mark)
                tv["check_func"](out2, pkt_num=len(tv["scapy_str"]["unmatch"]), check_param=tv["check_param"],
                                 stats=False)
                if tv["check_param"].get("count"):
                    self.query_count(tv["check_param"]["count"]["hits_set"], tv["check_param"]["count"]["hits"],
                                     port_id=port_id,
                                     rule_id=rule_li[0])
                # list and destroy rule
                self.check_rule(port_id=tv["check_param"]["port_id"], rule_list=rule_li)
                self.destroy_rule(rule_id=rule_li, port_id=port_id)
                # send matched packet
                out3 = self.send_pkts_getouput(pkts=tv["scapy_str"]["match"], port_id=port_id,
                                               count=count, mark=mark)
                tv["check_func"](out3, pkt_num=len(tv["scapy_str"]["match"]), check_param=tv["check_param"],
                                 stats=False)
                # check not rule exists
                self.check_rule(port_id=port_id, stats=False)
                test_results[tv["name"]] = True
                print(GREEN("case passed: %s" % tv["name"]))
            except Exception as e:
                print(RED(e))
                test_results[tv["name"]] = False
                continue
        failed_cases = []
        for k, v in test_results.items():
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
        # specify a fixed rss-hash-key for cvl ether
        self.pmd_output.execute_cmd(
            "port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd")
        res = self.pmd_output.wait_link_status_up('all', timeout=15)
        self.verify(res is True, 'there have port link is down')

    def launch_testpmd_with_mark(self):
        self.pmd_output.start_testpmd(cores="1S/4C/1T",
                                      param="--portmask=%s --rxq=64 --txq=64 --port-topology=loop" % self.portMask,
                                      eal_param="-w %s,flow-mark-support=1 -w %s,flow-mark-support=1" % (
                                          self.pci0, self.pci1), socket=self.ports_socket)
        self.config_testpmd()

    def send_packets(self, packets, tx_port=None, count=1):
        self.pkt.update_pkt(packets)
        tx_port = self.tester_iface0 if not tx_port else tx_port
        self.pkt.send_pkt(crb=self.tester, tx_port=tx_port, count=count)

    def send_pkts_getouput(self, pkts, port_id=0, count=1, mark=None):
        tx_port = self.tester_iface0 if port_id == 0 else self.tester_iface1
        self.send_packets(pkts, tx_port=tx_port, count=count)
        time.sleep(1)
        if mark:
            out = (self.pmd_output.get_output(), self.pmd_output.execute_cmd("stop"))
        else:
            out = self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("start")
        return out

    def create_fdir_rule(self, rule, check_stats=None):
        # dpdk get a warning message(ice_interrupt_handler), it'll mess up output stream, testpmd> probably not be
        # print completely.
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        if isinstance(rule, list):
            for i in rule:
                out = self.dut.send_command(i, timeout=1)
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        elif isinstance(rule, str):
            out = self.dut.send_command(rule, timeout=1)
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

    def check_fdir_rule(self, port_id=0, stats=True, rule_list=None):
        out = self.dut.send_command("flow list %s" % port_id, timeout=2)
        p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
        if stats:
            self.verify(p.search(out), "flow rule on port %s is not existed" % port_id)
            if rule_list:
                p = re.compile("^(\d+)\s")
                li = out.splitlines()
                res = filter(bool, map(p.match, li))
                result = [i.group(1) for i in res]
                self.verify(sorted(result) == sorted(rule_list),
                            "check rule list failed. expect %s, result %s" % (rule_list, result))
        else:
            self.verify(not p.search(out), "flow rule on port %s is existed" % port_id)

    def destroy_fdir_rule(self, port_id=0, rule_id=None):
        if rule_id == None:
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

    def test_mac_ipv4_tun_ipv4(self):
        self._rte_flow_validate(vectors_ipv4_tun_ipv4)

    def test_mac_ipv4_tun_mac(self):
        self._rte_flow_validate(vectors_ipv4_tun_mac)

    def test_queue_index_wrong_parameters(self):
        rule1 = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 64 / end"
        self.create_fdir_rule(rule1, check_stats=False)
        rule2 = [
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end",
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 2 / end",
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / end"]
        res = self.create_fdir_rule(rule2)
        self.verify(res[0], "create fdir rule failed, result %s" % res)
        self.verify(not any(res[1:]), "created wrong fdir rule %s should fail" % rule2[1:])

    def test_queue_group_wrong_parameters(self):
        rule1 = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 1 2 end / end"
        rule2 = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 end / end"
        rule3 = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end"
        rule4 = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 63 64 end / end"
        rule5 = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 end / end"
        res = self.create_fdir_rule([rule1, rule2, rule3, rule4], check_stats=False)
        self.dut.send_command("stop", timeout=1)
        self.dut.send_command("port stop all", timeout=1)
        self.dut.send_command("port config all rxq 32", timeout=1)
        self.dut.send_command("port config all txq 32", timeout=2)
        self.dut.send_command("port start all", timeout=1)
        self.pmd_output.execute_cmd("start")
        res = self.create_fdir_rule(rule5, check_stats=False)
        self.dut.send_command("stop", timeout=1)
        self.dut.send_command("port stop all", timeout=1)
        self.dut.send_command("port config all rxq 64", timeout=1)
        self.dut.send_command("port config all txq 64", timeout=2)
        self.dut.send_command("port start all", timeout=1)
        self.pmd_output.execute_cmd("start")
        result = True
        try:
            self.create_fdir_rule(rule5, check_stats=True)
            out = self.send_pkts_getouput(pkts=MAC_IPV4_PAY["match"])
            rfc.check_queue(out, pkt_num=len(MAC_IPV4_PAY["match"]), check_param={"port_id": 0, "queue": range(64)})
            out = self.send_pkts_getouput(pkts=MAC_IPV4_PAY["unmatch"])
            rfc.check_queue(out, pkt_num=len(MAC_IPV4_PAY["unmatch"]), check_param={"port_id": 0, "queue": range(64)})
        except Exception as e:
            result = False
            print(RED("failed:" + str(e)))
        finally:
            # restore testpmd config to default, then verify results
            self.config_testpmd()
        self.verify(result, "check failed")

    def test_mac_ipv4_gtpu_ipv4_pay_teid_mark_count_query(self):
        rule = "flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / ipv4 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 end / mark id 100 / count / end"
        p_gtpu1 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03") / IP(src="192.168.0.20", dst="192.168.0.21") / UDP(dport=2152) / GTP_U_Header(gtp_type=255, teid=0x12345678) / GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35) / IP() / Raw("x" * 20)'
        p_gtpu2 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw("x"*20)'
        # create fdir rule
        rule_li = self.create_fdir_rule(rule, check_stats=True)
        out = self.send_pkts_getouput(pkts=p_gtpu1, port_id=1, mark=True)
        check_param = {"port_id": 1, "queue": range(64), "mark_id": 100}
        rfc.check_mark(out, pkt_num=1, check_param=check_param)

        out = self.send_pkts_getouput(pkts=p_gtpu2, port_id=1, mark=True)
        rfc.check_queue(out[1], pkt_num=1, check_param=check_param)
        mark_scanner = "FDIR matched ID=(0x\w+)"
        res = re.search(mark_scanner, out[0])
        self.verify(not res, "FDIR should not in %s" % out[0])
        self.query_count(1, 1, 1, 0)

        self.check_fdir_rule(port_id=1, stats=True)
        self.destroy_fdir_rule(port_id=1, rule_id=rule_li[0])
        # send matched packets
        out = self.send_pkts_getouput(pkts=p_gtpu1, port_id=1, mark=True)
        rfc.check_queue(out[1], pkt_num=1, check_param=check_param, stats=True)
        res = re.search(mark_scanner, out[0])
        self.verify(not res, "FDIR should not in %s" % out[0])
        self.check_fdir_rule(port_id=1, stats=False)

    def test_mac_ipv4_gtpu_ipv4_pay_qfi_mark_count_query(self):
        rule = "flow create 1 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / ipv4 / end actions drop / mark id 3 / count / end"
        p_gtpu1 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP()/Raw("x"*20)'
        p_gtpu2 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw("x"*20)'
        # create fdir rule
        res = self.create_fdir_rule(rule, check_stats=True)
        check_param = {"port_id": 1, "mark": True, "mark_id": 3}
        # send matched packet
        out = self.send_pkts_getouput(pkts=p_gtpu1, port_id=1, mark=True)
        rfc.check_mark(out, pkt_num=1, check_param=check_param, stats=True)
        # send unmatched packet
        out1 = self.send_pkts_getouput(pkts=p_gtpu2, port_id=1, mark=True)
        rfc.check_mark(out1, pkt_num=1, check_param=check_param, stats=False)
        self.query_count(1, 1, 1, 0)
        self.check_fdir_rule(port_id=1, stats=True, rule_list=res)
        self.destroy_fdir_rule(port_id=1, rule_id=0)
        # send matched packets
        out = self.send_pkts_getouput(p_gtpu1, port_id=1, mark=True)
        rfc.check_mark(out, pkt_num=1, check_param={"port_id": 1}, stats=False)
        self.check_fdir_rule(port_id=1, stats=False)

    def test_mac_ipv4_gtpu_ipv4_pay_multirules(self):
        rule1 = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / ipv4 / end actions queue index 1 / end"
        rule2 = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x35 / ipv4 / end actions queue index 2 / end"
        rule3 = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x1234567 / gtp_psc qfi is 0x35 / ipv4 / end actions queue index 3 / end"
        res = self.create_fdir_rule(rule=[rule1, rule2, rule3], check_stats=True)
        rule4 = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x1234567 / gtp_psc qfi is 0x35 / ipv4 / end actions queue index 3 / end"
        rule5 = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x1234567 / gtp_psc qfi is 0x35 / ipv4 / end actions queue index 4 / end"
        rule6 = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x1234567 / gtp_psc qfi is 0x75 / ipv4 / end actions queue index 4 / end"
        res2 = self.create_fdir_rule(rule=[rule4, rule5, rule6], check_stats=False)
        rule7 = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x1234567 / gtp_psc qfi is 0x34 / ipv4 / end actions queue index 3 / end"
        res3 = self.create_fdir_rule(rule7, check_stats=True)
        p_gtpu1 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw("x"*20)'
        p_gtpu2 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw("x"*20)'
        p_gtpu3 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw("x"*20)'
        p_gtpu4 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw("x"*20)'
        p_gtpu5 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x36)/IP()/Raw("x"*20)'
        out1 = self.send_pkts_getouput(p_gtpu1)
        rfc.check_queue(out1, pkt_num=1, check_param={"queue": 1})
        out2 = self.send_pkts_getouput(p_gtpu2)
        rfc.check_queue(out2, pkt_num=1, check_param={"queue": 3})
        out3 = self.send_pkts_getouput(p_gtpu3)
        rfc.check_queue(out3, pkt_num=1, check_param={"queue": 2})
        out4 = self.send_pkts_getouput(p_gtpu4)
        rfc.check_queue(out4, pkt_num=1, check_param={"queue": 3})
        out5 = self.send_pkts_getouput(p_gtpu5)
        rfc.check_queue(out5, pkt_num=1, check_param={"queue": [1, 2, 3]}, stats=False)
        res.extend(res3)
        self.check_fdir_rule(port_id=0, stats=True, rule_list=res)
        self.dut.send_command("flow flush 0", timeout=1)
        out1 = self.send_pkts_getouput(p_gtpu1)
        rfc.check_queue(out1, pkt_num=1, check_param={"queue": 1}, stats=False)
        out2 = self.send_pkts_getouput(p_gtpu2)
        rfc.check_queue(out2, pkt_num=1, check_param={"queue": 3}, stats=False)
        out3 = self.send_pkts_getouput(p_gtpu3)
        rfc.check_queue(out3, pkt_num=1, check_param={"queue": 2}, stats=False)
        out4 = self.send_pkts_getouput(p_gtpu4)
        rfc.check_queue(out4, pkt_num=1, check_param={"queue": 3}, stats=False)

    def test_mac_ipv4_gtpu_ipv4_pay_two_ports(self):
        rule1 = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / ipv4 / end actions queue index 1 / end'
        rule2 = 'flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / ipv4 / end actions queue index 1 / end'
        rule3 = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x35 / ipv4 / end actions queue index 2 / end'
        rule4 = 'flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x35 / ipv4 / end actions queue index 3 / end'
        rule5 = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / ipv4 / end actions queue index 1 / end'
        rule6 = 'flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / ipv4 / end actions queue index 2 / end'

        p_gtpu1 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw("x"*20)'
        p_gtpu2 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw("x"*20)'
        p_gtpu3 = 'Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw("x"*20)'
        res1 = self.create_fdir_rule([rule1, rule2], check_stats=True)
        out1 = self.send_pkts_getouput(p_gtpu1)
        rfc.check_queue(out1, pkt_num=1, check_param={"queue": 1})
        out2 = self.send_pkts_getouput(p_gtpu1, port_id=1)
        rfc.check_queue(out2, pkt_num=1, check_param={"port_id": 1, "queue": 1})

        res2 = self.create_fdir_rule([rule3, rule4], check_stats=True)
        out1 = self.send_pkts_getouput(p_gtpu2)
        rfc.check_queue(out1, pkt_num=1, check_param={"queue": 2})
        out2 = self.send_pkts_getouput(p_gtpu2, port_id=1)
        rfc.check_queue(out2, pkt_num=1, check_param={"port_id": 1, "queue": 3})

        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("flow flush 1", timeout=1)

        res3 = self.create_fdir_rule([rule5, rule6])
        self.verify(all(res3), "rules should be create seccess, result is %s" % res3)
        out1 = self.send_pkts_getouput(p_gtpu3)
        rfc.check_queue(out1, pkt_num=1, check_param={"queue": 1}, stats=False)
        out2 = self.send_pkts_getouput(p_gtpu3, port_id=1)
        rfc.check_queue(out2, pkt_num=1, check_param={"port_id": 1, "queue": 2}, stats=True)

        self.check_fdir_rule(port_id=0, rule_list=res3[0])
        self.check_fdir_rule(port_id=1, rule_list=res3[1])

        self.destroy_fdir_rule(0, 0)
        self.destroy_fdir_rule(1, 0)

        out1 = self.send_pkts_getouput([p_gtpu1, p_gtpu2])
        rfc.check_queue(out1, pkt_num=2, check_param={"port_id": 0, "queue": [1, 2]}, stats=False)
        out2 = self.send_pkts_getouput([p_gtpu1, p_gtpu2, p_gtpu3], port_id=1)
        rfc.check_queue(out2, pkt_num=3, check_param={"port_id": 1, "queue": [1, 2, 3]}, stats=False)

        self.check_fdir_rule(0, stats=False)
        self.check_fdir_rule(1, stats=False)

    def test_mac_ipv4_gtpu_ipv4_pay_wrong_parameters(self):
        rule1 = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x100 / ipv4 / end actions queue index 1 / end'
        rule2 = 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc qfi is 0x5 / ipv4 / end actions queue index 2 / end'
        self.create_fdir_rule([rule1, rule2], check_stats=False)
        self.check_fdir_rule(0, stats=False)

    def test_count_query_identifier_share(self):
        rule1 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions queue index 1 / count identifier 0x1234 shared on / end'
        rule2 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / end actions queue index 2 / count identifier 0x1234 shared on / end'
        rule3 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 / end actions queue index 3 / count identifier 0x1234 shared off / end'
        rule4 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.4 / end actions queue index 4 / count identifier 0x1234 / end'
        rule5 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.5 / end actions queue index 5 / count shared on / end'
        rule6 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.6 / end actions drop / count shared on / end'
        rule7 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.0.7 / end actions drop / count identifier 0x1235 shared on / end'

        pkt1 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.21") / Raw("x" * 80)'
        pkt2 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.21") / Raw("x" * 80)'
        pkt3 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.21") / Raw("x" * 80)'
        pkt4 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4",dst="192.168.0.21") / Raw("x" * 80)'
        pkt5 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.5",dst="192.168.0.21") / Raw("x" * 80)'
        pkt6 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.6",dst="192.168.0.21") / Raw("x" * 80)'
        pkt7 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.21") / Raw("x" * 80)'

        res = self.create_fdir_rule([rule1, rule2, rule3, rule4, rule5, rule6, rule7])
        self.verify(all(res), "create rules failed, result: %s" % res)
        out1 = self.send_pkts_getouput(pkt1, count=10)
        rfc.check_queue(out1, pkt_num=10, check_param={"queue": 1}, stats=True)
        out2 = self.send_pkts_getouput(pkt2, count=10)
        rfc.check_queue(out2, pkt_num=10, check_param={"queue": 2}, stats=True)
        out3 = self.send_pkts_getouput(pkt3, count=10)
        rfc.check_queue(out3, pkt_num=10, check_param={"queue": 3}, stats=True)
        out4 = self.send_pkts_getouput(pkt4, count=10)
        rfc.check_queue(out4, pkt_num=10, check_param={"queue": 4}, stats=True)
        out5 = self.send_pkts_getouput(pkt5, count=10)
        rfc.check_queue(out5, pkt_num=10, check_param={"queue": 5}, stats=True)
        out6 = self.send_pkts_getouput(pkt6, count=10)
        rfc.check_drop(out6, pkt_num=10, check_param={"port_id": 0})
        out7 = self.send_pkts_getouput(pkt7, count=10)
        rfc.check_drop(out7, pkt_num=10, check_param={"port_id": 0})

        self.query_count(1, 20, 0, 0)
        self.query_count(1, 20, 0, 1)
        self.query_count(1, 10, 0, 2)
        self.query_count(1, 10, 0, 3)
        self.query_count(1, 20, 0, 4)
        self.query_count(1, 20, 0, 5)
        self.query_count(1, 10, 0, 6)

        self.check_fdir_rule(0, stats=True, rule_list=res)
        self.dut.send_command("flow flush 0", timeout=1)
        out = self.send_pkts_getouput(pkts=[pkt1, pkt2, pkt3, pkt4, pkt5])
        rfc.check_queue(out, pkt_num=5, check_param={"port_id": 0, "queue": range(1, 6)}, stats=False)
        out6 = self.send_pkts_getouput(pkt6, count=10)
        rfc.check_drop(out6, pkt_num=10, check_param={"port_id": 0}, stats=False)
        out7 = self.send_pkts_getouput(pkt7, count=10)
        rfc.check_drop(out7, pkt_num=10, check_param={"port_id": 0}, stats=False)

        self.check_fdir_rule(stats=False)

    def test_multi_patterns_count_query(self):
        rule1 = 'flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / count / end'
        rule2 = 'flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / count / end'
        rule3 = 'flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions rss queues 62 63 end / count / end'
        rule4 = 'flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / count / end'
        rule5 = 'flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 3 / count / end'
        rule6 = 'flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 / tcp dst is 23 / end actions queue index 4 / count / end'
        rule7 = 'flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 5 / count / end'

        pkt1 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /TCP(sport=22, dport=23)/ Raw("x" * 80)'
        pkt2 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22, dport=23)/ Raw("x" * 80)'
        pkt3 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /SCTP(sport=22, dport=23)/ Raw("x" * 80)'
        pkt4 = 'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=1, tc=1, hlim=2)/("X"*480)'
        pkt5 = 'Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=4790)/VXLAN(flags=0xc)/IP(dst="192.168.0.21", src="192.168.0.20")/UDP(sport=22,dport=23)/("X"*480)'
        pkt6 = 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20")/TCP(dport=23)/("X"*480)'
        pkt7 = 'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP(sport=22,dport=23)/("X"*480)'

        res = self.create_fdir_rule(rule=[rule1, rule2, rule3, rule4, rule5, rule6, rule7], check_stats=True)
        self.verify(all(res), "create rules failed, result %s" % res)
        out = self.send_pkts_getouput(pkts=pkt1, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"queue": 1}, stats=True)
        out = self.send_pkts_getouput(pkts=pkt2, count=10)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 0})
        out = self.send_pkts_getouput(pkts=pkt3, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"queue": [62, 63]}, stats=True)
        out = self.send_pkts_getouput(pkts=pkt4, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"queue": 1}, stats=True)
        out = self.send_pkts_getouput(pkts=pkt5, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"queue": 3}, stats=True)
        out = self.send_pkts_getouput(pkts=pkt6, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"queue": 4}, stats=True)
        out = self.send_pkts_getouput(pkts=pkt7, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"queue": 5}, stats=True)

        for i in range(7):
            self.query_count(1, 10, port_id=0, rule_id=i)
        self.check_fdir_rule(port_id=0, stats=True, rule_list=res)

        self.dut.send_command("flow flush 0", timeout=1)
        out = self.send_pkts_getouput(pkts=pkt1, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"queue": 1}, stats=False)
        out = self.send_pkts_getouput(pkts=pkt2, count=10)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 0}, stats=False)
        out = self.send_pkts_getouput(pkts=pkt3, count=1)
        rfc.check_queue(out, pkt_num=1, check_param={"queue": [62, 63]}, stats=False)
        out = self.send_pkts_getouput(pkts=[pkt4, pkt5, pkt6, pkt7], count=1)
        rfc.check_queue(out, pkt_num=4, check_param={"queue": [1, 3, 4, 5]}, stats=False)
        self.check_fdir_rule(stats=False)

    def test_two_ports_multi_patterns_count_query(self):
        rules = [
            'flow create 1 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 255  tos is 4 / end actions queue index 1 / count / end',
            'flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions rss queues 6 7 end / count / end',
            'flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss queues 6 7 end / count / end',
            'flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 2 / count / end',
            'flow create 1 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / count / end',
            'flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions drop / count / end',
            'flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / count / end'
        ]
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", ttl=2, tos=4)/TCP(sport=22,dport=23)/Raw(load="X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=1, tc=1, hlim=2)/("X"*480)',
            'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", ttl=2, tos=4)/TCP(sport=22,dport=23)/Raw(load="X"*480)'
        ]
        res = self.create_fdir_rule(rule=rules, check_stats=True)
        out = self.send_pkts_getouput(pkts[0], port_id=1, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"port_id": 1, "queue": 1}, stats=True)
        out = self.send_pkts_getouput(pkts[1:3], port_id=1, count=10)
        rfc.check_queue(out, pkt_num=20, check_param={"port_id": 1, "queue": [6, 7]}, stats=True)
        out = self.send_pkts_getouput(pkts[3], port_id=1, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"port_id": 1, "queue": 2}, stats=True)
        out = self.send_pkts_getouput(pkts[4], port_id=1, count=10)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 1})
        out = self.send_pkts_getouput(pkts[5], count=10)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 0})
        out = self.send_pkts_getouput(pkts[6], count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"port_id": 0, "queue": 1}, stats=True)
        out = self.send_pkts_getouput(pkts[7], port_id=1, count=10)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 1}, stats=False)

        for i in range(5):
            self.query_count(1, 10, 1, i)
        for i in range(2):
            self.query_count(1, 10, 0, i)
        self.check_fdir_rule(port_id=0, stats=True, rule_list=res[0:2])
        self.check_fdir_rule(port_id=1, stats=True, rule_list=res[2:])

        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("flow flush 1", timeout=1)

        out = self.send_pkts_getouput(pkts[0], port_id=1, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"port_id": 1, "queue": 1}, stats=False)
        out = self.send_pkts_getouput(pkts[1:3], port_id=1, count=10)
        rfc.check_queue(out, pkt_num=20, check_param={"port_id": 1, "queue": [6, 7]}, stats=False)
        out = self.send_pkts_getouput(pkts[3], port_id=1, count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"port_id": 1, "queue": 2}, stats=False)
        out = self.send_pkts_getouput(pkts[4], port_id=1, count=10)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 1}, stats=False)
        out = self.send_pkts_getouput(pkts[5], count=10)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 0}, stats=False)
        out = self.send_pkts_getouput(pkts[6], count=10)
        rfc.check_queue(out, pkt_num=10, check_param={"port_id": 0, "queue": 1}, stats=False)
        out = self.send_pkts_getouput(pkts[7], port_id=0, count=10)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 0}, stats=False)
        self.check_fdir_rule(0, stats=False)
        self.check_fdir_rule(1, stats=False)

    def test_multirules_mark(self):
        rules = [
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 2 / mark id 1 / end",
            "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions queue index 1 / mark id 2 / count / end"]

        pkt1 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)'
        pkt2 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw("x" * 80)'
        pkt3 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw("x" * 80)'

        res = self.create_fdir_rule(rules, check_stats=True)

        out1 = self.send_pkts_getouput(pkt1, mark=True)
        rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=True)

        out2 = self.send_pkts_getouput(pkt2, mark=True)
        rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 2}, stats=True)

        out3 = self.send_pkts_getouput(pkt3, mark=True)
        rfc.check_mark(out3, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 1}, stats=True)

        self.query_count(1, 1, port_id=0, rule_id=2)
        self.check_fdir_rule(0, stats=True, rule_list=res)
        self.destroy_fdir_rule(port_id=0, rule_id=0)

        out1 = self.send_pkts_getouput(pkt1, mark=True)
        rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=False)

        self.check_fdir_rule(0, stats=True, rule_list=res[1:])
        out2 = self.send_pkts_getouput(pkt2, mark=True)
        rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 2}, stats=True)

        out3 = self.send_pkts_getouput(pkt3, mark=True)
        rfc.check_mark(out3, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 1}, stats=True)

        self.query_count(1, 2, port_id=0, rule_id=2)
        self.dut.send_command("flow flush 0", timeout=1)

        out1 = self.send_pkts_getouput(pkt1, mark=True)
        rfc.check_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=False)

        out2 = self.send_pkts_getouput(pkt2, mark=True)
        rfc.check_mark(out2, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 2}, stats=False)

        out3 = self.send_pkts_getouput(pkt3, mark=True)
        rfc.check_mark(out3, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 1}, stats=False)

        self.check_fdir_rule(stats=False)

    def test_mark_wrong_parameters(self):
        rule = "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark id 4294967296 / end"
        self.create_fdir_rule(rule=rule, check_stats=False)
        self.check_fdir_rule(stats=False)

    def test_pattern_conflict_flow(self):
        rule1 = "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / end actions queue index 1 / end"
        self.create_fdir_rule(rule=rule1, check_stats=True)
        pkt1 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)'
        pkt2 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22, dport=23)/ Raw("x" * 80)'
        out1 = self.send_pkts_getouput(pkts=[pkt1, pkt2])
        rfc.check_queue(out1, pkt_num=2, check_param={"port_id": 0, "queue": 1}, stats=True)

        rule2 = "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 2 / end"
        self.create_fdir_rule(rule=rule2, check_stats=True)
        out2 = self.send_pkts_getouput(pkt1)
        rfc.check_queue(out2, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=True)

        out3 = self.send_pkts_getouput(pkt2)
        rfc.check_queue(out3, pkt_num=1, check_param={"port_id": 0, "queue": 2}, stats=True)

        self.dut.send_command("flow flush 0", timeout=1)

        self.create_fdir_rule(rule=rule2, check_stats=True)
        out4 = self.send_pkts_getouput(pkt2)
        rfc.check_queue(out4, pkt_num=1, check_param={"port_id": 0, "queue": 2}, stats=True)

        self.create_fdir_rule(rule=rule1, check_stats=True)
        out5 = self.send_pkts_getouput(pkt2)
        rfc.check_queue(out5, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=True)

    def test_max_count(self):
        pattern = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.{} / end actions drop / count / end"
        rules = [pattern.format(i) for i in range(1, 256)] + [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 / end actions drop / count / end"]
        res = self.create_fdir_rule(rules, check_stats=True)

        rule2 = 'flow create 0 ingress pattern eth / ipv4 src is 192.168.1.2 / end actions drop / count / end'
        res2 = self.create_fdir_rule(rule2, check_stats=False)

        pkt = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1",dst="192.168.0.21") / Raw("x" * 80)'
        out = self.send_pkts_getouput(pkt, count=10)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 0}, stats=True)
        self.query_count(1, 10, port_id=0, rule_id=255)
        self.check_fdir_rule(0, stats=True, rule_list=res)
        self.dut.send_command("flow flush 0", timeout=1)
        out = self.send_pkts_getouput(pkt, count=10)
        rfc.check_drop(out, pkt_num=10, check_param={"port_id": 0}, stats=False)
        self.check_fdir_rule(stats=False)
        self.dut.send_command("stop", timeout=2)
        self.dut.send_command("quit", timeout=2)
        self.launch_testpmd_with_mark()

    def tear_down(self):
        # destroy all flow rule on port 0
        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("flow flush 1", timeout=1)
        self.dut.send_command("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")

    def tear_down_all(self):
        self.dut.kill_all()
