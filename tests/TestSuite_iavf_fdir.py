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
from rte_flow_common import CVL_TXQ_RXQ_NUMBER
from multiprocessing import Process
from multiprocessing import Manager

from utils import GREEN, RED
import utils

MAC_IPV4_PAY = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=255, ttl=2, tos=4)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw("x" * 80)'],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.1.21", proto=255, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1, ttl=2, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=3, tos=4) / Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=9) / Raw("x" * 80)'
    ]
}

MAC_IPV4_PAY_protocol = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=17, ttl=2, tos=4)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=17, ttl=2, tos=4)/Raw("x" * 80)'],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", proto=1)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=6)/UDP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1)/TCP(sport=22,dport=23)/Raw("x" * 80)']
}

MAC_IPV4_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)'],
    "mismatch": [
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
    "mismatch": [
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
    "mismatch": [
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
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)'],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::1", nh=0, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=2, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=2, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=5)/("X"*480)']
}

MAC_IPV6_PAY_protocol = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=44, tc=1, hlim=2)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=44)/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/TCP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)'],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", nh=44)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=17)/TCP(sport=22,dport=23)/("X"*480)']
}

MAC_IPV6_UDP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)'],
    "mismatch": [
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
    "mismatch": [
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
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/SCTP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=21,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=24)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/("X"*480)']
}

MAC_IPV4_GTPU_EH = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/TCP(sport=22,dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6(nh=44)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6()/TCP(sport=22,dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6()/ICMP()/Raw("x"*20)'],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/SCTP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IPv6()/SCTP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x35)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/Raw("x"*20)']
}

MAC_IPV4_GTPU = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(nh=44)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/ICMP()/Raw("x"*20)'],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/SCTP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/SCTP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IP()/Raw("x"*20)']
}

MAC_IPV6_GTPU_EH = {
    "match": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP(frag=1)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/UDP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/ICMP()/Raw("x"*20)'],
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/ICMP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/TCP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/UDP()/Raw("x"*20)']
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
    "mismatch": [
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP()/Raw("x"*20)',
        'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw("x"*20)']
}

MAC_IPV4_L2TPv3 = {
    "match": [
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.3', proto=115)/L2TP(b'\\x00\\x00\\x00\\x11')/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.1.3', proto=115)/L2TP(b'\\x00\\x00\\x00\\x11')/Raw('x'*480)"],
    "mismatch": [
        "Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.3', proto=115)/L2TP(b'\\x00\\x00\\x00\\x12')/Raw('x'*480)"]
}

MAC_IPV6_L2TPv3 = {
    "match": [
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888',nh=115)/L2TP(b'\\x00\\x00\\x00\\x11')/Raw('x'*480)",
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:9999',nh=115)/L2TP(b'\\x00\\x00\\x00\\x11')/Raw('x'*480)"],
    "mismatch": [
        "Ether(dst='00:11:22:33:44:55')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888',nh=115)/L2TP(b'\\x00\\x00\\x00\\x12')/Raw('x'*480)"]
}

MAC_IPV4_ESP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",proto=50)/ESP(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3",proto=50)/ESP(spi=7)/Raw("x"*480)'],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",proto=50)/ESP(spi=17)/Raw("x"*480)']
}

MAC_IPV6_ESP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",nh=50)/ESP(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:9999",nh=50)/ESP(spi=7)/Raw("x"*480)'],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",nh=50)/ESP(spi=17)/Raw("x"*480)']
}

MAC_IPV4_AH = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",proto=51)/AH(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.3",proto=51)/AH(spi=7)/Raw("x"*480)'],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",proto=51)/AH(spi=17)/Raw("x"*480)']
}

MAC_IPV6_AH = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",nh=51)/AH(spi=7)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:9999",nh=51)/AH(spi=7)/Raw("x"*480)'],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",nh=51)/AH(spi=17)/Raw("x"*480)']
}

MAC_IPV4_NAT_T_ESP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20")/UDP(dport=4500)/ESP(spi=2)/Raw("x"*480)'],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.10.20")/UDP(dport=4500)/ESP(spi=2)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20")/UDP(dport=4500)/ESP(spi=12)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.20")/UDP(dport=4500)/ESP(spi=2)/Raw("x"*480)']
}

MAC_IPV6_NAT_T_ESP = {
    "match": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=2)/Raw("x"*480)'],
    "mismatch": [
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=12)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999")/UDP(dport=4500)/ESP(spi=2)/Raw("x"*480)',
        'Ether(dst="00:11:22:33:44:55")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=2)/Raw("x"*480)']
}

L2_Ethertype = [
    'Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x" *80)',
    'Ether(dst="00:11:22:33:44:55", type=0x8863)/IP()/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP(b\'\\x00\\x21\')/IP()/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:55", type=0x8864)/IP()/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:55")/ARP(pdst="192.168.1.1")',
    'Ether(dst="00:11:22:33:44:55", type=0x0806)/Raw("x" *80)',
    'Ether(dst="00:11:22:33:44:55",type=0x8100)',
    'Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)',
    'Ether(dst="00:11:22:33:44:55",type=0x88f7)/"\\x00\\x02"',
    'Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(label=0xee456)/IP()']

PFCP = [
    'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=22, dport=8805)/PFCP(S=0)',
    'Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=22, dport=8805)/PFCP(S=1, seid=123)',
    'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=22, dport=8805)/PFCP(S=0)',
    'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=22, dport=8805)/PFCP(S=1, seid=256)',
    'Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=22, dport=23)/Raw("x"*20)']

CREATE_2048_RULES_4_VFS = [
    'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.7.255", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.7.255", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.7.255", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)',
    'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.7.255", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw("x" * 80)']

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
        {"port_id": 0, "passthru": 1}]
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
        {"port_id": 0, "passthru": 1}]
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
        {"port_id": 0, "passthru": 1}]
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
        {"port_id": 0, "passthru": 1}]
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
        {"port_id": 0, "passthru": 1}]
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
        {"port_id": 0, "passthru": 1}]
}

tv_pfcp_queue_index = {
    "name": "test_pfcp_queue_index",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / end"],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "queue": 1},
        {"port_id": 0, "queue": 2},
        {"port_id": 0, "queue": 3},
        {"port_id": 0, "queue": 4},
        {"port_id": 0, "passthru": 1}]
}

tv_pfcp_queue_group = {
    "name": "test_pfcp_queue_group",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions rss queues 2 3 end / mark id 0 / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions rss queues 4 5 6 7 end / mark id 1 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark id 2 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions rss queues 3 4 5 6 end / mark id 3 / end"],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "queue": [4, 5, 6, 7], "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "queue": [3, 4, 5, 6], "mark_id": 3},
        {"port_id": 0, "passthru": 1}]
}

tv_pfcp_passthru = {
    "name": "test_pfcp_passthru",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions passthru / mark id 0 / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions passthru / mark id 1 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions passthru / mark id 2 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions passthru / mark id 3 / end"],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "passthru": 1, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "passthru": 1, "mark_id": 3},
        {"port_id": 0, "passthru": 1}]
}

tv_pfcp_mark_rss = {
    "name": "test_pfcp_mark_rss",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions mark / rss / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions mark id 1 / rss / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions mark id 2 / rss / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions mark id 3 / rss / end"],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "passthru": 1, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "passthru": 1, "mark_id": 3},
        {"port_id": 0, "passthru": 1}]
}

tv_pfcp_mark = {
    "name": "test_pfcp_mark",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions mark / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions mark id 1 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions mark id 2 / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions mark id 4294967294 / end"],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "queue": 0, "mark_id": 0},
        {"port_id": 0, "passthru": 1, "mark_id": 1},
        {"port_id": 0, "queue": 0, "mark_id": 2},
        {"port_id": 0, "passthru": 1, "mark_id": 4294967294},
        {"port_id": 0, "passthru": 1}]
}

tv_pfcp_drop = {
    "name": "test_pfcp_drop",
    "rule": [
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions drop / end",
        "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions drop / end"],
    "scapy_str": PFCP,
    "check_param": [
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "drop": 1},
        {"port_id": 0, "passthru": 1}]
}

tv_mac_ipv4_pay_queue_index = {
    "name": "test_mac_ipv4_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_pay_queue_group = {
    "name": "test_mac_ipv4_pay_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 1 end / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "queue": [0, 1]}
}

tv_mac_ipv4_pay_passthru = {
    "name": "test_mac_ipv4_pay_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "passthru": 1}
}

tv_mac_ipv4_pay_mark_rss = {
    "name": "test_mac_ipv4_pay_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv4_pay_mark = {
    "name": "test_mac_ipv4_pay_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv4_pay_drop = {
    "name": "test_mac_ipv4_pay_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / end",
    "scapy_str": MAC_IPV4_PAY,
    "check_param": {"port_id": 0, "drop":1}
}

tv_mac_ipv4_udp_queue_index = {
    "name": "test_mac_ipv4_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0}
}

tv_mac_ipv4_udp_drop = {
    "name": "test_mac_ipv4_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv4_udp_queue_group = {
    "name": "test_mac_ipv4_udp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions rss queues 1 2 3 4 end / mark id 4294967294 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 4294967294}
}

tv_mac_ipv4_udp_passthru = {
    "name": "test_mac_ipv4_udp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1}
}

tv_mac_ipv4_udp_mark_rss = {
    "name": "test_mac_ipv4_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark id 2 / rss / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2}
}

tv_mac_ipv4_udp_mark = {
    "name": "test_mac_ipv4_udp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark id 1 / end",
    "scapy_str": MAC_IPV4_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1}
}

tv_mac_ipv4_tcp_queue_index = {
    "name": "test_mac_ipv4_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 15 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "queue": 15}
}

tv_mac_ipv4_tcp_drop = {
    "name": "test_mac_ipv4_tcp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv4_tcp_queue_group = {
    "name": "test_mac_ipv4_tcp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 1}
}

tv_mac_ipv4_tcp_passthru = {
    "name": "test_mac_ipv4_tcp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions passthru / mark id 2 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2}
}

tv_mac_ipv4_tcp_mark_rss = {
    "name": "test_mac_ipv4_tcp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 0 / rss / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv4_tcp_mark = {
    "name": "test_mac_ipv4_tcp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 0 / end",
    "scapy_str": MAC_IPV4_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv4_sctp_queue_index = {
    "name": "test_mac_ipv4_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 tag is 1 / end actions queue index 0 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "queue": 0}
}

tv_mac_ipv4_sctp_drop = {
    "name": "test_mac_ipv4_sctp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions drop / mark / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv4_sctp_queue_group = {
    "name": "test_mac_ipv4_sctp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions rss queues 14 15 end / mark id 15 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "queue": [14, 15], "mark_id": 15}
}

tv_mac_ipv4_sctp_passthru = {
    "name": "test_mac_ipv4_sctp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions passthru / mark id 0 / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv4_sctp_mark_rss = {
    "name": "test_mac_ipv4_sctp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv4_sctp_mark = {
    "name": "test_mac_ipv4_sctp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions mark / end",
    "scapy_str": MAC_IPV4_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv6_pay_queue_index = {
    "name": "test_mac_ipv6_pay_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions queue index 15 / mark id 1 / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "queue": 15, "mark_id": 1}
}

tv_mac_ipv6_pay_drop = {
    "name": "test_mac_ipv6_pay_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions drop / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv6_pay_queue_group = {
    "name": "test_mac_ipv6_pay_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark id 2 / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "queue": [8, 9, 10, 11, 12, 13, 14, 15], "mark_id": 2}
}

tv_mac_ipv6_pay_passthru = {
    "name": "test_mac_ipv6_pay_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions passthru / mark id 3 / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 3}
}

tv_mac_ipv6_pay_mark_rss = {
    "name": "test_mac_ipv6_pay_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark id 4 / rss / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 4}
}

tv_mac_ipv6_pay_mark = {
    "name": "test_mac_ipv6_pay_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark id 5 / rss / end",
    "scapy_str": MAC_IPV6_PAY,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 5}
}

tv_mac_ipv6_udp_queue_index = {
    "name": "test_mac_ipv6_udp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 2 / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "queue": 2}
}

tv_mac_ipv6_udp_queue_group = {
    "name": "test_mac_ipv6_udp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss queues 1 2 end / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "queue": [1, 2]}
}

tv_mac_ipv6_udp_drop = {
    "name": "test_mac_ipv6_udp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv6_udp_passthru = {
    "name": "test_mac_ipv6_udp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions passthru / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1}
}

tv_mac_ipv6_udp_mark_rss = {
    "name": "test_mac_ipv6_udp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark / rss / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv6_udp_mark = {
    "name": "test_mac_ipv6_udp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark / end",
    "scapy_str": MAC_IPV6_UDP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv6_tcp_queue_index = {
    "name": "test_mac_ipv6_tcp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 2 / mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "queue": 2, "mark_id": 0}
}

tv_mac_ipv6_tcp_queue_group = {
    "name": "test_mac_ipv6_tcp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "queue": [2, 3], "mark_id": 0}
}

tv_mac_ipv6_tcp_drop = {
    "name": "test_mac_ipv6_tcp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv6_tcp_passthru = {
    "name": "test_mac_ipv6_tcp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions passthru / mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv6_tcp_mark_rss = {
    "name": "test_mac_ipv6_tcp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions mark / rss / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv6_tcp_mark = {
    "name": "test_mac_ipv6_tcp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions mark / end",
    "scapy_str": MAC_IPV6_TCP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0}
}

tv_mac_ipv6_sctp_queue_index = {
    "name": "test_mac_ipv6_sctp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions queue index 3 / mark id 0 / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "queue": 3, "mark_id": 0 }
}

tv_mac_ipv6_sctp_drop = {
    "name": "test_mac_ipv6_sctp_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions drop / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv6_sctp_queue_group = {
    "name": "test_mac_ipv6_sctp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions rss queues 12 13 end / mark id 0 / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "queue": [12, 13], "mark_id": 0}
}

tv_mac_ipv6_sctp_passthru = {
    "name": "test_mac_ipv6_sctp_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions passthru / mark id 0 / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 0 }
}

tv_mac_ipv6_sctp_mark_rss = {
    "name": "test_mac_ipv6_sctp_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 1 }
}

tv_mac_ipv6_sctp_mark = {
    "name": "test_mac_ipv6_sctp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions mark id 2 / end",
    "scapy_str": MAC_IPV6_SCTP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 2 }
}

tv_mac_ipv4_gtpu_eh_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "queue": 1}
}

tv_mac_ipv4_gtpu_eh_drop = {
    "name": "test_mac_ipv4_gtpu_eh_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv4_gtpu_eh_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 2 3 end / mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 0}
}

tv_mac_ipv4_gtpu_eh_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1}
}

tv_mac_ipv4_gtpu_eh_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark / rss / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 0}
}

tv_mac_ipv4_gtpu_eh_mark = {
    "name": "test_mac_ipv4_gtpu_eh_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 0}
}

tv_mac_ipv4_gtpu_queue_index = {
    "name": "test_mac_ipv4_gtpu_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions queue index 1 / mark id 0 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "queue": 1, "mark_id": 0}
}

tv_mac_ipv4_gtpu_drop = {
    "name": "test_mac_ipv4_gtpu_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "drop": 1}
}

tv_mac_ipv4_gtpu_queue_group = {
    "name": "test_mac_ipv4_gtpu_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions rss queues 1 2 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1}
}

tv_mac_ipv4_gtpu_passthru = {
    "name": "test_mac_ipv4_gtpu_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions passthru / mark id 2 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 2}
}

tv_mac_ipv4_gtpu_mark_rss = {
    "name": "test_mac_ipv4_gtpu_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark id 3 / rss / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 3}
}

tv_mac_ipv4_gtpu_mark = {
    "name": "test_mac_ipv4_gtpu_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark id 4 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 4}
}

tv_mac_ipv4_gtpu_eh_4tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv4_gtpu_eh_4tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_eh_4tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_4tuple_drop = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_eh_4tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_4tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV4_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv4_gtpu_eh_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_eh_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_eh_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv4_gtpu_eh_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_eh_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_eh_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_eh_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_eh_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_3tuple_queue_index = {
    "name": "test_mac_ipv4_gtpu_3tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv4_gtpu_3tuple_queue_group = {
    "name": "test_mac_ipv4_gtpu_3tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_3tuple_passthru = {
    "name": "test_mac_ipv4_gtpu_3tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_3tuple_drop = {
    "name": "test_mac_ipv4_gtpu_3tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions drop / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_3tuple_mark_rss = {
    "name": "test_mac_ipv4_gtpu_3tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV4_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_dstip_queue_index = {
    "name": "test_mac_ipv4_gtpu_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv4_gtpu_dstip_queue_group = {
    "name": "test_mac_ipv4_gtpu_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_dstip_passthru = {
    "name": "test_mac_ipv4_gtpu_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_dstip_drop = {
    "name": "test_mac_ipv4_gtpu_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_dstip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_srcip_queue_index = {
    "name": "test_mac_ipv4_gtpu_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv4_gtpu_srcip_queue_group = {
    "name": "test_mac_ipv4_gtpu_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv4_gtpu_srcip_passthru = {
    "name": "test_mac_ipv4_gtpu_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_gtpu_srcip_drop = {
    "name": "test_mac_ipv4_gtpu_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv4_gtpu_srcip_mark_rss = {
    "name": "test_mac_ipv4_gtpu_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/UDP()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_4tuple_queue_index = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv6_gtpu_eh_4tuple_queue_group = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_eh_4tuple_passthru = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_4tuple_drop = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_eh_4tuple_mark_rss = {
    "name": "test_mac_ipv6_gtpu_eh_4tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV6_GTPU_EH,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_dstip_queue_index = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv6_gtpu_eh_dstip_queue_group = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_eh_dstip_passthru = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_dstip_drop = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_eh_dstip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_eh_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_srcip_queue_index = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv6_gtpu_eh_srcip_queue_group = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_eh_srcip_passthru = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_eh_srcip_drop = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_eh_srcip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_eh_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=0,P=1,QFI=0x35)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=0,P=1,QFI=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_3tuple_queue_index = {
    "name": "test_mac_ipv6_gtpu_3tuple_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions queue index 1 / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv6_gtpu_3tuple_queue_group = {
    "name": "test_mac_ipv6_gtpu_3tuple_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_3tuple_passthru = {
    "name": "test_mac_ipv6_gtpu_3tuple_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions passthru / mark id 1 / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_3tuple_drop = {
    "name": "test_mac_ipv6_gtpu_3tuple_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions drop / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_3tuple_mark_rss = {
    "name": "test_mac_ipv6_gtpu_3tuple_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions mark id 1 / rss / end",
    "scapy_str": MAC_IPV6_GTPU,
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_dstip_queue_index = {
    "name": "test_mac_ipv6_gtpu_dstip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv6_gtpu_dstip_queue_group = {
    "name": "test_mac_ipv6_gtpu_dstip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_dstip_passthru = {
    "name": "test_mac_ipv6_gtpu_dstip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_dstip_drop = {
    "name": "test_mac_ipv6_gtpu_dstip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_dstip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_dstip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_srcip_queue_index = {
    "name": "test_mac_ipv6_gtpu_srcip_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions queue index 1 / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": 1}
}

tv_mac_ipv6_gtpu_srcip_queue_group = {
    "name": "test_mac_ipv6_gtpu_srcip_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "queue": [0, 1, 2, 3]}
}

tv_mac_ipv6_gtpu_srcip_passthru = {
    "name": "test_mac_ipv6_gtpu_srcip_passthru",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions passthru / mark id 1 / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv6_gtpu_srcip_drop = {
    "name": "test_mac_ipv6_gtpu_srcip_drop",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions drop / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_param": {"port_id": 0, "drop": True}
}

tv_mac_ipv6_gtpu_srcip_mark_rss = {
    "name": "test_mac_ipv6_gtpu_srcip_mark_rss",
    "rule": "flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions mark id 1 / rss / end",
    "scapy_str": {"match":
        [
            'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)'],
        "mismatch":
            [
                'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw("x"*20)']},
    "check_param": {"port_id": 0, "mark_id": 1, "rss": True}
}

tv_mac_ipv4_l2tpv3_queue_index = {
    "name": "test_mac_ipv4_l2tpv3_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV4_L2TPv3,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7}
}

tv_mac_ipv4_l2tpv3_queue_group = {
    "name": "test_mac_ipv4_l2tpv3_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV4_L2TPv3,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6}
}

tv_mac_ipv4_l2tpv3_mark = {
    "name": "test_mac_ipv4_l2tpv3_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV4_L2TPv3,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15}
}

tv_mac_ipv6_l2tpv3_queue_index = {
    "name": "test_mac_ipv6_l2tpv3_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 17 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV6_L2TPv3,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7}
}

tv_mac_ipv6_l2tpv3_queue_group = {
    "name": "test_mac_ipv6_l2tpv3_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 17 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV6_L2TPv3,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6}
}

tv_mac_ipv6_l2tpv3_mark = {
    "name": "test_mac_ipv6_l2tpv3_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 17 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV6_L2TPv3,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15}
}

tv_mac_ipv4_esp_queue_index = {
    "name": "test_mac_ipv4_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / esp spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV4_ESP,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7}
}

tv_mac_ipv4_esp_queue_group = {
    "name": "test_mac_ipv4_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV4_ESP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6}
}

tv_mac_ipv4_esp_mark = {
    "name": "test_mac_ipv4_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / esp spi is 7 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV4_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15}
}

tv_mac_ipv6_esp_queue_index = {
    "name": "test_mac_ipv6_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 / esp spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV6_ESP,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7}
}

tv_mac_ipv6_esp_queue_group = {
    "name": "test_mac_ipv6_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV6_ESP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6}
}

tv_mac_ipv6_esp_mark = {
    "name": "test_mac_ipv6_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 / esp spi is 7 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV6_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15}
}

tv_mac_ipv4_ah_queue_index = {
    "name": "test_mac_ipv4_ah_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 / ah spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV4_AH,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7}
}

tv_mac_ipv4_ah_queue_group = {
    "name": "test_mac_ipv4_ah_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 / ah spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV4_AH,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6}
}

tv_mac_ipv4_ah_mark = {
    "name": "test_mac_ipv4_ah_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 / ah spi is 7 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV4_AH,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15}
}

tv_mac_ipv6_ah_queue_index = {
    "name": "test_mac_ipv6_ah_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ah spi is 7 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV6_AH,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7}
}

tv_mac_ipv6_ah_queue_group = {
    "name": "test_mac_ipv6_ah_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ah spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV6_AH,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6}
}

tv_mac_ipv6_ah_mark = {
    "name": "test_mac_ipv6_ah_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 / ah spi is 7 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV6_AH,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15}
}

tv_mac_ipv4_nat_t_esp_queue_index = {
    "name": "test_mac_ipv4_nat_t_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / esp spi is 2 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV4_NAT_T_ESP,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7}
}

tv_mac_ipv4_nat_t_esp_queue_group = {
    "name": "test_mac_ipv4_nat_t_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / esp spi is 2 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV4_NAT_T_ESP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6}
}

tv_mac_ipv4_nat_t_esp_mark = {
    "name": "test_mac_ipv4_nat_t_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / esp spi is 2 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV4_NAT_T_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15}
}

tv_mac_ipv6_nat_t_esp_queue_index = {
    "name": "test_mac_ipv6_nat_t_esp_queue_index",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / udp / esp spi is 2 / end actions queue index 13 / mark id 7 / end",
    "scapy_str": MAC_IPV6_NAT_T_ESP,
    "check_param": {"port_id": 0, "queue": 13, "mark_id": 7}
}

tv_mac_ipv6_nat_t_esp_queue_group = {
    "name": "test_mac_ipv6_nat_t_esp_queue_group",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / udp / esp spi is 2 / end actions rss queues 1 2 3 4 end / mark id 6 / end",
    "scapy_str": MAC_IPV6_NAT_T_ESP,
    "check_param": {"port_id": 0, "queue": [1, 2, 3, 4], "mark_id": 6}
}

tv_mac_ipv6_nat_t_esp_mark = {
    "name": "test_mac_ipv6_nat_t_esp_mark",
    "rule": "flow create 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / udp / esp spi is 2 / end actions mark id 15 / end",
    "scapy_str": MAC_IPV6_NAT_T_ESP,
    "check_param": {"port_id": 0, "passthru": 1, "mark_id": 15}
}

vectors_ipv4_pay = [tv_mac_ipv4_pay_queue_index, tv_mac_ipv4_pay_mark_rss,tv_mac_ipv4_pay_passthru,
                         tv_mac_ipv4_pay_drop, tv_mac_ipv4_pay_queue_group, tv_mac_ipv4_pay_mark]

vectors_ipv4_udp = [tv_mac_ipv4_udp_drop, tv_mac_ipv4_udp_queue_group, tv_mac_ipv4_udp_queue_index,
                         tv_mac_ipv4_udp_mark_rss, tv_mac_ipv4_udp_passthru, tv_mac_ipv4_udp_mark]

vectors_ipv4_tcp = [tv_mac_ipv4_tcp_drop, tv_mac_ipv4_tcp_queue_group, tv_mac_ipv4_tcp_queue_index,
                         tv_mac_ipv4_tcp_mark_rss, tv_mac_ipv4_tcp_passthru, tv_mac_ipv4_tcp_mark]

vectors_ipv4_sctp = [tv_mac_ipv4_sctp_drop, tv_mac_ipv4_sctp_queue_group, tv_mac_ipv4_sctp_queue_index,
                         tv_mac_ipv4_sctp_passthru, tv_mac_ipv4_sctp_mark_rss, tv_mac_ipv4_sctp_mark]

vectors_ipv6_pay = [tv_mac_ipv6_pay_drop, tv_mac_ipv6_pay_queue_group, tv_mac_ipv6_pay_queue_index,
                         tv_mac_ipv6_pay_mark_rss, tv_mac_ipv6_pay_passthru, tv_mac_ipv6_pay_mark]

vectors_ipv6_udp = [tv_mac_ipv6_udp_drop, tv_mac_ipv6_udp_queue_group, tv_mac_ipv6_udp_queue_index,
                         tv_mac_ipv6_udp_passthru, tv_mac_ipv6_udp_mark_rss, tv_mac_ipv6_udp_mark]

vectors_ipv6_tcp = [tv_mac_ipv6_tcp_drop, tv_mac_ipv6_tcp_queue_group, tv_mac_ipv6_tcp_queue_index,
                         tv_mac_ipv6_tcp_mark_rss, tv_mac_ipv6_tcp_passthru, tv_mac_ipv6_tcp_mark]

vectors_ipv6_sctp = [tv_mac_ipv6_sctp_queue_index, tv_mac_ipv6_sctp_drop, tv_mac_ipv6_sctp_queue_group,
                          tv_mac_ipv6_sctp_passthru, tv_mac_ipv6_sctp_mark_rss, tv_mac_ipv6_sctp_mark]

vectors_ipv4_gtpu_eh = [tv_mac_ipv4_gtpu_eh_drop, tv_mac_ipv4_gtpu_eh_mark_rss, tv_mac_ipv4_gtpu_eh_queue_index,
                        tv_mac_ipv4_gtpu_eh_queue_group, tv_mac_ipv4_gtpu_eh_passthru, tv_mac_ipv4_gtpu_eh_mark,
                        tv_mac_ipv4_gtpu_eh_4tuple_queue_index, tv_mac_ipv4_gtpu_eh_4tuple_queue_group,
                        tv_mac_ipv4_gtpu_eh_4tuple_passthru, tv_mac_ipv4_gtpu_eh_4tuple_drop,
                        tv_mac_ipv4_gtpu_eh_4tuple_mark_rss,
                        tv_mac_ipv4_gtpu_eh_dstip_queue_index, tv_mac_ipv4_gtpu_eh_dstip_queue_group,
                        tv_mac_ipv4_gtpu_eh_dstip_passthru, tv_mac_ipv4_gtpu_eh_dstip_drop,
                        tv_mac_ipv4_gtpu_eh_dstip_mark_rss,
                        tv_mac_ipv4_gtpu_eh_srcip_queue_index, tv_mac_ipv4_gtpu_eh_srcip_queue_group,
                        tv_mac_ipv4_gtpu_eh_srcip_passthru, tv_mac_ipv4_gtpu_eh_srcip_drop,
                        tv_mac_ipv4_gtpu_eh_srcip_mark_rss]

vectors_ipv4_gtpu = [tv_mac_ipv4_gtpu_drop, tv_mac_ipv4_gtpu_mark_rss, tv_mac_ipv4_gtpu_queue_index,
                     tv_mac_ipv4_gtpu_queue_group, tv_mac_ipv4_gtpu_passthru, tv_mac_ipv4_gtpu_mark,
                     tv_mac_ipv4_gtpu_3tuple_queue_index, tv_mac_ipv4_gtpu_3tuple_queue_group,
                     tv_mac_ipv4_gtpu_3tuple_passthru, tv_mac_ipv4_gtpu_3tuple_drop,
                     tv_mac_ipv4_gtpu_3tuple_mark_rss,
                     tv_mac_ipv4_gtpu_dstip_queue_index, tv_mac_ipv4_gtpu_dstip_queue_group,
                     tv_mac_ipv4_gtpu_dstip_passthru, tv_mac_ipv4_gtpu_dstip_drop,
                     tv_mac_ipv4_gtpu_dstip_mark_rss,
                     tv_mac_ipv4_gtpu_srcip_queue_index, tv_mac_ipv4_gtpu_srcip_queue_group,
                     tv_mac_ipv4_gtpu_srcip_passthru, tv_mac_ipv4_gtpu_srcip_drop,
                     tv_mac_ipv4_gtpu_srcip_mark_rss]

vectors_ipv6_gtpu_eh = [tv_mac_ipv6_gtpu_eh_4tuple_queue_index, tv_mac_ipv6_gtpu_eh_4tuple_queue_group,
                        tv_mac_ipv6_gtpu_eh_4tuple_passthru, tv_mac_ipv6_gtpu_eh_4tuple_drop,
                        tv_mac_ipv6_gtpu_eh_4tuple_mark_rss,
                        tv_mac_ipv6_gtpu_eh_dstip_queue_index, tv_mac_ipv6_gtpu_eh_dstip_queue_group,
                        tv_mac_ipv6_gtpu_eh_dstip_passthru, tv_mac_ipv6_gtpu_eh_dstip_drop,
                        tv_mac_ipv6_gtpu_eh_dstip_mark_rss,
                        tv_mac_ipv6_gtpu_eh_srcip_queue_index, tv_mac_ipv6_gtpu_eh_srcip_queue_group,
                        tv_mac_ipv6_gtpu_eh_srcip_passthru, tv_mac_ipv6_gtpu_eh_srcip_drop,
                        tv_mac_ipv6_gtpu_eh_srcip_mark_rss]

vectors_ipv6_gtpu = [tv_mac_ipv6_gtpu_3tuple_queue_index, tv_mac_ipv6_gtpu_3tuple_queue_group,
                     tv_mac_ipv6_gtpu_3tuple_passthru, tv_mac_ipv6_gtpu_3tuple_drop,
                     tv_mac_ipv6_gtpu_3tuple_mark_rss,
                     tv_mac_ipv6_gtpu_dstip_queue_index, tv_mac_ipv6_gtpu_dstip_queue_group,
                     tv_mac_ipv6_gtpu_dstip_passthru, tv_mac_ipv6_gtpu_dstip_drop,
                     tv_mac_ipv6_gtpu_dstip_mark_rss,
                     tv_mac_ipv6_gtpu_srcip_queue_index, tv_mac_ipv6_gtpu_srcip_queue_group,
                     tv_mac_ipv6_gtpu_srcip_passthru, tv_mac_ipv6_gtpu_srcip_drop,
                     tv_mac_ipv6_gtpu_srcip_mark_rss]

vectors_pfcp = [tv_pfcp_queue_index, tv_pfcp_queue_group, tv_pfcp_passthru, tv_pfcp_drop,
                     tv_pfcp_mark, tv_pfcp_mark_rss]

vectors_l2_ethertype = [tv_l2_ethertype_drop, tv_l2_ethertype_queue_index, tv_l2_ethertype_queue_group,
                             tv_l2_ethertype_passthru, tv_l2_ethertype_mark, tv_l2_ethertype_mark_rss]

vectors_ipv4_l2tpv3 = [tv_mac_ipv4_l2tpv3_queue_index, tv_mac_ipv4_l2tpv3_queue_group, tv_mac_ipv4_l2tpv3_mark]

vectors_ipv6_l2tpv3 = [tv_mac_ipv6_l2tpv3_queue_index, tv_mac_ipv6_l2tpv3_queue_group, tv_mac_ipv6_l2tpv3_mark]

vectors_ipv4_esp = [tv_mac_ipv4_esp_queue_index, tv_mac_ipv4_esp_queue_group, tv_mac_ipv4_esp_mark]

vectors_ipv6_esp = [tv_mac_ipv6_esp_queue_index, tv_mac_ipv6_esp_queue_group, tv_mac_ipv6_esp_mark]

vectors_ipv4_ah = [tv_mac_ipv4_ah_queue_index, tv_mac_ipv4_ah_queue_group, tv_mac_ipv4_ah_mark]

vectors_ipv6_ah = [tv_mac_ipv6_ah_queue_index, tv_mac_ipv6_ah_queue_group, tv_mac_ipv6_ah_mark]

vectors_ipv4_nat_t_esp = [tv_mac_ipv4_nat_t_esp_queue_index, tv_mac_ipv4_nat_t_esp_queue_group, tv_mac_ipv4_nat_t_esp_mark]

vectors_ipv6_nat_t_esp = [tv_mac_ipv6_nat_t_esp_queue_index, tv_mac_ipv6_nat_t_esp_queue_group, tv_mac_ipv6_nat_t_esp_mark]

class TestIAVFFdir(TestCase):

    def rte_flow_process(self, vectors):
        test_results = {}
        for tv in vectors:
            try:
                port_id = tv["check_param"]["port_id"]
                self.dut.send_expect("flow flush %d" % port_id, "testpmd> ", 120)

                # validate rule
                self.validate_fdir_rule(tv["rule"], check_stats=True)
                self.check_fdir_rule(port_id=port_id, stats=False)

                # create rule
                rule_li = self.create_fdir_rule(tv["rule"], check_stats=True)
                if "gtpu_eh" in tv["name"]:
                    gtpu_rss = [
                        "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end"]
                    gtpu_rss_rule_li = self.create_fdir_rule(gtpu_rss, check_stats=True)

                # send and check match packets
                out1 = self.send_pkts_getouput(pkts=tv["scapy_str"]["match"])
                rfc.check_iavf_fdir_mark(out1, pkt_num=len(tv["scapy_str"]["match"]), check_param=tv["check_param"])
                # send and check mismatch packets
                out2 = self.send_pkts_getouput(pkts=tv["scapy_str"]["mismatch"])
                rfc.check_iavf_fdir_mark(out2, pkt_num=len(tv["scapy_str"]["mismatch"]), check_param=tv["check_param"],
                                 stats=False)
                # list and destroy rule
                if "gtpu_eh" in tv["name"]:
                    self.check_fdir_rule(port_id=port_id, rule_list=rule_li+gtpu_rss_rule_li)
                else:
                    self.check_fdir_rule(port_id=port_id, rule_list=rule_li)
                self.destroy_fdir_rule(rule_id=rule_li, port_id=port_id)
                # send matched packet
                out3 = self.send_pkts_getouput(pkts=tv["scapy_str"]["match"])
                rfc.check_iavf_fdir_mark(out3, pkt_num=len(tv["scapy_str"]["match"]), check_param=tv["check_param"],
                                 stats=False)
                # check not rule exists
                if "gtpu_eh" in tv["name"]:
                    self.check_fdir_rule(port_id=port_id, rule_list=gtpu_rss_rule_li)
                else:
                    self.check_fdir_rule(port_id=port_id, stats=False)
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

    def multirules_process(self, vectors, port_id=0):
        # create rules on only one port
        test_results = {}
        rule_li = []
        for tv in vectors:
            try:
                port_id = port_id
                pkts=tv["scapy_str"]
                check_param=tv["check_param"]
                self.destroy_fdir_rule(rule_id=rule_li, port_id=port_id)
                # validate rules
                self.validate_fdir_rule(tv["rule"], check_stats=True)

                # create rules
                rule_li = self.create_fdir_rule(tv["rule"], check_stats=True)

                for i in range(len(pkts)):
                    port_id = check_param[i]["port_id"]
                    out = self.send_pkts_getouput(pkts=pkts[i])
                    rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param=check_param[i])
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
        self.verify(cores is not None, "Insufficient cores for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        localPort0 = self.tester.get_local_port(self.dut_ports[0])
        localPort1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_iface0 = self.tester.get_interface(localPort0)
        self.tester_iface1 = self.tester.get_interface(localPort1)
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf1_intf = self.dut.ports_info[self.dut_ports[1]]['intf']
        self.pf0_mac = self.dut.get_mac_address(0)
        self.pf1_mac = self.dut.get_mac_address(1)

        #bind pf to kernel
        for port in self.dut_ports:
            netdev = self.dut.ports_info[port]['port']
            netdev.bind_driver(driver='ice')

        #set vf driver
        self.vf_driver = 'vfio-pci'
        self.dut.send_expect('modprobe vfio-pci', '#')
        self.suite_config = rfc.get_suite_config(self)

        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.path = self.dut.apps_name['test-pmd']

        self.src_file_dir = 'dep/'
        self.dut_file_dir = '/tmp/'
        self.cvlq_num = CVL_TXQ_RXQ_NUMBER

    def set_up(self):
        """
        Run before each test case.
        """
        self.re_load_ice_driver()
        time.sleep(1)
        self.setup_2pf_4vf_env()
        time.sleep(1)
        self.launch_testpmd()

    def setup_2pf_4vf_env(self, driver='default'):

        #get PF interface name
        self.used_dut_port_0 = self.dut_ports[0]
        self.used_dut_port_1 = self.dut_ports[1]

        #generate 2 VFs on PF
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 2, driver=driver)
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_1, 2, driver=driver)
        self.sriov_vfs_pf0 = self.dut.ports_info[self.used_dut_port_0]['vfs_port']
        self.sriov_vfs_pf1 = self.dut.ports_info[self.used_dut_port_1]['vfs_port']

        self.dut.send_expect('ip link set %s vf 0 mac 00:11:22:33:44:55' % self.pf0_intf, '#')
        self.dut.send_expect('ip link set %s vf 1 mac 00:11:22:33:44:66' % self.pf0_intf, '#')
        self.dut.send_expect('ip link set %s vf 0 mac 00:11:22:33:44:77' % self.pf1_intf, '#')
        self.dut.send_expect('ip link set %s vf 1 mac 00:11:22:33:44:88' % self.pf1_intf, '#')

        #bind VF0 and VF1 to dpdk driver
        try:
            for vf_port in self.sriov_vfs_pf0:
                vf_port.bind_driver(self.vf_driver)
            for vf_port in self.sriov_vfs_pf1:
                vf_port.bind_driver(self.vf_driver)

        except Exception as e:
            self.destroy_env()
            raise Exception(e)
        out = self.dut.send_expect('./usertools/dpdk-devbind.py -s', '#')
        print(out)

    def setup_npf_nvf_env(self, pf_num=2, vf_num=2, driver='default'):

        #get PF interface name
        self.used_dut_port_0 = self.dut_ports[0]
        self.used_dut_port_1 = self.dut_ports[1]
        try:
            # generate vf on pf
            if pf_num == 1:
                self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, vf_num, driver=driver)
                self.sriov_vfs_pf0 = self.dut.ports_info[self.used_dut_port_0]['vfs_port']
                #bind VF0 and VF1 to dpdk driver
                for vf_port in self.sriov_vfs_pf0:
                    vf_port.bind_driver(self.vf_driver)
            else:
                self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, vf_num, driver=driver)
                self.dut.generate_sriov_vfs_by_port(self.used_dut_port_1, vf_num, driver=driver)
                self.sriov_vfs_pf0 = self.dut.ports_info[self.used_dut_port_0]['vfs_port']
                self.sriov_vfs_pf1 = self.dut.ports_info[self.used_dut_port_1]['vfs_port']
                for vf_port in self.sriov_vfs_pf0:
                    vf_port.bind_driver(self.vf_driver)
                for vf_port in self.sriov_vfs_pf1:
                    vf_port.bind_driver(self.vf_driver)

        except Exception as e:
            self.destroy_env()
            raise Exception(e)
        out = self.dut.send_expect('./usertools/dpdk-devbind.py -s', '#')
        print(out)

    def destroy_env(self):
        """
        This is to stop testpmd and destroy 1pf and 2vfs environment.
        """
        self.dut.send_expect("quit", "# ", 60)
        time.sleep(2)
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[1])

    def re_load_ice_driver(self):
        """
        remove and reload the ice driver
        """
        self.dut.send_expect("rmmod ice", "# ", 40)
        ice_driver_file_location = self.suite_config["ice_driver_file_location"]
        self.dut.send_expect("insmod %s" % ice_driver_file_location, "# ")
        self.dut.send_expect("ifconfig %s up" % self.pf0_intf, "# ", 15)
        self.dut.send_expect("ifconfig %s up" % self.pf1_intf, "# ", 15)

    def config_testpmd(self):
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        # specify a fixed rss-hash-key for cvl ether
        self.pmd_output.execute_cmd(
            "port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd")
        self.pmd_output.execute_cmd(
            "port config 1 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd")
        res = self.pmd_output.wait_link_status_up('all', timeout=15)
        self.verify(res is True, 'there have port link is down')
        self.pmd_output.execute_cmd("start")

    def launch_testpmd(self):
        self.pmd_output.start_testpmd(cores="1S/4C/1T",
                                      param="--rxq={} --txq={}".format(self.cvlq_num, self.cvlq_num),
                                      eal_param="-w %s -w %s" % (
                                           self.sriov_vfs_pf0[0].pci,self.sriov_vfs_pf0[1].pci),
                                      socket=self.ports_socket)
        self.config_testpmd()

    def send_packets(self, packets, pf_id=0):
        self.pkt.update_pkt(packets)
        tx_port = self.tester_iface0 if pf_id == 0 else self.tester_iface1
        self.pkt.send_pkt(crb=self.tester, tx_port=tx_port)

    def send_pkts_getouput(self, pkts, pf_id=0):
        """
        if pkt_info is True, we need to get packet infomation to check the RSS hash and FDIR.
        if pkt_info is False, we just need to get the packet number and queue number.
        """
        self.send_packets(pkts, pf_id)
        time.sleep(1)
        out_info = self.dut.get_session_output(timeout=1)
        out_pkt = self.pmd_output.execute_cmd("stop")
        out = out_info + out_pkt
        self.pmd_output.execute_cmd("start")
        return out

    def validate_fdir_rule(self, rule, check_stats=None):
        # validate rule.
        p = "Flow rule validated"
        rule_list = []
        if isinstance(rule, list):
            for i in rule:
                length = len(i)
                rule_rep = i[0:5] + "validate" + i[11:length]
                out = self.pmd_output.execute_cmd(rule_rep)
                if (p in out) and ("Failed" not in out):
                    rule_list.append(True)
                else:
                    rule_list.append(False)
        elif isinstance(rule, str):
            length = len(rule)
            rule_rep = rule[0:5] + "validate" + rule[11:length]
            out = self.pmd_output.execute_cmd(rule_rep)
            if (p in out) and ("Failed" not in out):
                rule_list.append(True)
            else:
                rule_list.append(False)
        else:
            raise Exception("unsupported rule type, only accept list or str")
        if check_stats:
            self.verify(all(rule_list), "some rules validate failed, result %s" % rule_list)
        elif check_stats == False:
            self.verify(not any(rule_list), "all rules should validate failed, result %s" % rule_list)

    def create_fdir_rule(self, rule, check_stats=None):
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        if isinstance(rule, list):
            for i in rule:
                out = self.pmd_output.execute_cmd(i)
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        elif isinstance(rule, str):
            out = self.pmd_output.execute_cmd(rule)
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

    def destroy_fdir_rule(self, rule_id, port_id=0):
        if isinstance(rule_id, list):
            for i in rule_id:
                out = self.pmd_output.execute_cmd("flow destroy %s rule %s" % (port_id, i))
                p = re.compile(r"Flow rule #(\d+) destroyed")
                m = p.search(out)
                self.verify(m, "flow rule %s delete failed" % rule_id)
        else:
            out = self.pmd_output.execute_cmd("flow destroy %s rule %s" % (port_id, rule_id))
            p = re.compile(r"Flow rule #(\d+) destroyed")
            m = p.search(out)
            self.verify(m, "flow rule %s delete failed" % rule_id)

    def check_fdir_rule(self, port_id=0, stats=True, rule_list=None):
        out = self.pmd_output.execute_cmd("flow list %s" % port_id)
        p = re.compile(r"ID\s+Group\s+Prio\s+Attr\s+Rule")
        if stats:
            self.verify(p.search(out), "flow rule on port %s is not existed" % port_id)
            if rule_list:
                p = re.compile("^(\d+)\s")
                li = out.splitlines()
                res = list(filter(bool, list(map(p.match, li))))
                result = [i.group(1) for i in res]
                self.verify(sorted(result) == sorted(rule_list),
                            "check rule list failed. expect %s, result %s" % (rule_list, result))
        else:
            self.verify(not p.search(out), "flow rule on port %s is existed" % port_id)

    def check_rule_number(self, port_id=0, num=0):
        out = self.dut.send_command("flow list %s" % port_id, timeout=30)
        result_scanner = r'\d*.*?\d*.*?\d*.*?=>*'
        scanner = re.compile(result_scanner, re.DOTALL)
        li = scanner.findall(out)
        if num == 0:
            self.verify(not li, "there should be no rule listed")
        else:
            print(len(li))
            self.verify(len(li) == num, "the amount of rules is wrong.")
        return out

    def test_mac_ipv4_pay(self):
        self.rte_flow_process(vectors_ipv4_pay)

    def test_mac_ipv4_udp(self):
        self.rte_flow_process(vectors_ipv4_udp)

    def test_mac_ipv4_tcp(self):
        self.rte_flow_process(vectors_ipv4_tcp)

    def test_mac_ipv4_sctp(self):
        self.rte_flow_process(vectors_ipv4_sctp)

    def test_mac_ipv6_pay(self):
        self.rte_flow_process(vectors_ipv6_pay)

    def test_mac_ipv6_udp(self):
        self.rte_flow_process(vectors_ipv6_udp)

    def test_mac_ipv6_tcp(self):
        self.rte_flow_process(vectors_ipv6_tcp)

    def test_mac_ipv6_sctp(self):
        self.rte_flow_process(vectors_ipv6_sctp)

    def test_mac_ipv4_gtpu_eh(self):
        self.rte_flow_process(vectors_ipv4_gtpu_eh)

    def test_mac_ipv4_gtpu(self):
        self.rte_flow_process(vectors_ipv4_gtpu)

    def test_mac_ipv6_gtpu_eh(self):
        self.rte_flow_process(vectors_ipv6_gtpu_eh)

    def test_mac_ipv6_gtpu(self):
        self.rte_flow_process(vectors_ipv6_gtpu)

    def test_mac_ipv4_l2tpv3(self):
        self.rte_flow_process(vectors_ipv4_l2tpv3)

    def test_mac_ipv6_l2tpv3(self):
        self.rte_flow_process(vectors_ipv6_l2tpv3)

    def test_mac_ipv4_esp(self):
        self.rte_flow_process(vectors_ipv4_esp)

    def test_mac_ipv6_esp(self):
        self.rte_flow_process(vectors_ipv6_esp)

    def test_mac_ipv4_ah(self):
        self.rte_flow_process(vectors_ipv4_ah)

    def test_mac_ipv6_ah(self):
        self.rte_flow_process(vectors_ipv6_ah)

    def test_mac_ipv4_nat_t_esp(self):
        self.rte_flow_process(vectors_ipv4_nat_t_esp)

    def test_mac_ipv6_nat_t_esp(self):
        self.rte_flow_process(vectors_ipv6_nat_t_esp)

    def test_mac_ipv4_protocol(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 1 / end actions queue index 1 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 17 / end actions passthru / mark id 3 / end"]

        #validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        #create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # pkt1 and pkt2 in "match" match rule 0, pkt3-6 match rule 1.
        out1 = self.send_pkts_getouput(MAC_IPV4_PAY_protocol["match"][0:2])
        rfc.check_iavf_fdir_mark(out1, pkt_num=2, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=True)

        out2 = self.send_pkts_getouput(MAC_IPV4_PAY_protocol["match"][2:6])
        rfc.check_iavf_fdir_mark(out2, pkt_num=4, check_param={"port_id": 0, "mark_id": 3, "passthru": 1}, stats=True)

        # send mismatched packets:
        out3 = self.send_pkts_getouput(MAC_IPV4_PAY_protocol["mismatch"])
        rfc.check_iavf_fdir_mark(out3, pkt_num=4, check_param={"port_id": 0, "passthru": 1}, stats=False)

        # destroy the rules and check there is no rule listed.
        self.destroy_fdir_rule(rule_id=rule_li, port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)

        # send matched packet
        out4 = self.send_pkts_getouput(MAC_IPV4_PAY_protocol["match"])
        rfc.check_iavf_fdir_mark(out4, pkt_num=6, check_param={"port_id": 0, "passthru": 1}, stats=False)

    def test_mac_ipv6_protocol(self):
        rules = [
            "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 44 / end actions rss queues 5 6 end / mark id 0 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 6 / end actions mark id 2 / rss / end"]

        # validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        # create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # pkt1-4 in "match" match rule 0, pkt5-6 match rule 1.
        out1 = self.send_pkts_getouput(MAC_IPV6_PAY_protocol["match"][0:4])
        rfc.check_iavf_fdir_mark(out1, pkt_num=4, check_param={"port_id": 0, "mark_id": 0, "queue": [5, 6]}, stats=True)

        out2 = self.send_pkts_getouput(MAC_IPV6_PAY_protocol["match"][4:6])
        rfc.check_iavf_fdir_mark(out2, pkt_num=2, check_param={"port_id": 0, "mark_id": 2, "passthru": 1}, stats=True)

        # send mismatched packets:
        out3 = self.send_pkts_getouput(MAC_IPV6_PAY_protocol["mismatch"])
        rfc.check_iavf_fdir_mark(out3, pkt_num=3, check_param={"port_id": 0, "passthru": 1}, stats=False)

        # destroy the rules and check there is no rule listed.
        self.destroy_fdir_rule(rule_id=rule_li, port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)

        # send matched packet
        out4 = self.send_pkts_getouput(MAC_IPV6_PAY_protocol["match"])
        rfc.check_iavf_fdir_mark(out4, pkt_num=6, check_param={"port_id": 0, "passthru": 1}, stats=False)

    def test_mac_ipv4_gtpu_eh_without_teid(self):
        rules = ["flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end", \
                 "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 3 / end"]
        MAC_IPV4_GTPU_EH_WITHOUT_TEID = {
            "match": 'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTPPDUSessionContainer(type=1,P=1,QFI=0x34)/IP()/TCP()/Raw("x"*20)',
            "mismatch": 'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTPPDUSessionContainer(type=1,P=1,QFI=0x35)/IP()/TCP()/Raw("x"*20)'
        }
        # validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        # create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # send matched packet
        out1 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_TEID["match"])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 1}, stats=True)

        # send mismatched packets:
        out2 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_TEID["mismatch"])
        rfc.check_iavf_fdir_mark(out2, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=False)

        # destroy the rules and check there is no rule listed.
        self.destroy_fdir_rule(rule_id=rule_li, port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)

        open_rss_rule = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end"
        rule_li = self.create_fdir_rule(open_rss_rule, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # send matched packet
        out3 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_TEID["match"])
        rfc.check_iavf_fdir_mark(out3, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=False)

    def test_mac_ipv4_gtpu_eh_without_qfi(self):
        rules = ["flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end", \
                 "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / end actions rss queues 2 3 end / mark id 1 / end"]
        MAC_IPV4_GTPU_EH_WITHOUT_QFI = {
            "match": 'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer(type=1, P=1)/IP()/UDP()/Raw("x"*20)',
            "mismatch": 'Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTPPDUSessionContainer(type=1, P=1)/IP()/UDP()/Raw("x"*20)'
        }
        # validate rules
        self.validate_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=False)

        # create rules
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # send matched packet
        out1 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_QFI["match"])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": [2, 3]}, stats=True)

        # send mismatched packets:
        out2 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_QFI["mismatch"])
        rfc.check_iavf_fdir_mark(out2, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=False)

        # destroy the rules and check there is no rule listed.
        self.destroy_fdir_rule(rule_id=rule_li, port_id=0)
        self.check_fdir_rule(port_id=0, stats=False)

        open_rss_rule = "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end"
        rule_li = self.create_fdir_rule(open_rss_rule, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)

        # send matched packet
        out3 = self.send_pkts_getouput(MAC_IPV4_GTPU_EH_WITHOUT_QFI["match"])
        rfc.check_iavf_fdir_mark(out3, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=False)

    def test_pfcp(self):
        # open the RSS function for PFCP session packet.
        out = self.pmd_output.execute_cmd("flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end")
        self.verify("Flow rule #0 created" in out, "failed to enable RSS function for MAC_IPV4_PFCP session packet")
        out = self.pmd_output.execute_cmd("flow create 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end")
        self.verify("Flow rule #1 created" in out, "failed to enable RSS function for MAC_IPV6_PFCP session packet")
        self.multirules_process(vectors_pfcp)

    def test_l2_ethertype(self):
        self.multirules_process(vectors_l2_ethertype)

    def test_negative_case(self):
        """
        negative cases
        """
        rules = {
            "invalid parameters of queue index" : "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 16 / end",
            "invalid parameters of rss queues" : [
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 end / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues end / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 15 16 end / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 end / end"],
            "invalid mark id" : "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / mark id 4294967296 / end",
            "invalid parameters of GTPU input set" : [
                "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x100 / end actions queue index 1 / end",
                "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc qfi is 0x5 / end actions queue index 2 / end",
                "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / end actions queue index 1 / end"],
            "unsupported type of L2 ethertype" : [
                "flow create 0 ingress pattern eth type is 0x0800 / end actions queue index 1 / end",
                "flow create 0 ingress pattern eth type is 0x86dd / end actions queue index 1 / end"],
            "conflicted actions" : "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / rss queues 2 3 end / end",
            "void action" : "flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions end",
            "unsupported action" : "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions count / end",
            "unsupported input set field" : "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tc is 2 / end actions queue index 1 / end",
            "void input set value" : "flow create 0 ingress pattern eth / ipv4 / end actions queue index 1 / end",
            "invalid port" : "flow create 2 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end"
        }
        # all the rules failed to create and validate
        self.validate_fdir_rule(rules["invalid parameters of queue index"], check_stats=False)
        self.create_fdir_rule(rules["invalid parameters of queue index"], check_stats=False)
        self.validate_fdir_rule(rules["invalid parameters of rss queues"], check_stats=False)
        self.create_fdir_rule(rules["invalid parameters of rss queues"], check_stats=False)
        self.validate_fdir_rule(rules["invalid parameters of GTPU input set"], check_stats=False)
        self.create_fdir_rule(rules["invalid parameters of GTPU input set"], check_stats=False)
        self.validate_fdir_rule(rules["unsupported type of L2 ethertype"], check_stats=False)
        self.create_fdir_rule(rules["unsupported type of L2 ethertype"], check_stats=False)
        self.validate_fdir_rule(rules["conflicted actions"], check_stats=False)
        self.create_fdir_rule(rules["conflicted actions"], check_stats=False)
        self.validate_fdir_rule(rules["void action"], check_stats=False)
        self.create_fdir_rule(rules["void action"], check_stats=False)
        self.validate_fdir_rule(rules["unsupported input set field"], check_stats=False)
        self.create_fdir_rule(rules["unsupported input set field"], check_stats=False)
        self.validate_fdir_rule(rules["void input set value"], check_stats=False)
        self.create_fdir_rule(rules["void input set value"], check_stats=False)
        self.validate_fdir_rule(rules["invalid port"], check_stats=False)
        self.create_fdir_rule(rules["invalid port"], check_stats=False)

        # check there is no rule listed
        self.check_fdir_rule(port_id=0, stats=False)
        self.check_fdir_rule(port_id=1, stats=False)

        # duplicated rules
        rule = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end"
        self.create_fdir_rule(rule, check_stats=True)
        self.create_fdir_rule(rule, check_stats=False)
        self.pmd_output.execute_cmd("flow destroy 0 rule 0")

        # conflict rules
        rule = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end"
        self.create_fdir_rule(rule, check_stats=True)
        rule1 = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 2 / end"
        self.create_fdir_rule(rule1, check_stats=False)
        rule2 = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions drop / end"
        self.create_fdir_rule(rule2, check_stats=False)
        self.pmd_output.execute_cmd("flow destroy 0 rule 0", timeout=1)

        # delete a non-existent rule
        out1 = self.pmd_output.execute_cmd("flow destroy 0 rule 0")
        self.verify("error" not in out1, "there shouldn't report error message")
        out2 = self.pmd_output.execute_cmd("flow destroy 2 rule 0")
        self.verify("Invalid port" in out2, "there should report error message")
        out3 = self.pmd_output.execute_cmd("flow flush 2")
        self.verify("Invalid port" in out3, "port 2 doesn't exist.")
        out4 = self.pmd_output.execute_cmd("flow list 2")
        self.verify("Invalid port" in out4, "port 2 doesn't exist.")

        self.check_fdir_rule(port_id=0, stats=False)
        self.check_fdir_rule(port_id=1, stats=False)

    def test_unsupported_pattern_with_OS_package(self):
        """
        Create GTPU rule, PFCP rule, L2 Ethertype rule, l2tpv3 rule and esp rule with OS default package
        """
        rule = ["flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / end",
                "flow create 0 ingress pattern eth type is 0x8863 / end actions queue index 1 / mark id 1 / end",
                "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions rss queues 1 2 end / mark id 6 / end",
                "flow create 0 ingress pattern eth / ipv6 / udp / esp spi is 6 / end actions rss queues 1 2 end / mark id 6 / end"]
        self.destroy_env()
        os_package_location = self.suite_config["os_default_package_file_location"]
        comms_package_location = self.suite_config["comms_package_file_location"]
        package_location = self.suite_config["package_file_location"]
        self.dut.send_expect("cp %s %s" % (os_package_location, package_location), "# ")
        self.re_load_ice_driver()
        self.setup_2pf_4vf_env()
        self.launch_testpmd()

        self.validate_fdir_rule(rule, check_stats=False)
        self.create_fdir_rule(rule, check_stats=False)
        self.check_fdir_rule(port_id=0, stats=False)

        self.destroy_env()
        self.dut.send_expect("cp %s %s" % (comms_package_location, package_location), "# ")
        self.re_load_ice_driver()
        self.setup_2pf_4vf_env()

    def test_create_same_rule_on_pf_vf(self):
        """
        create same rules on pf and vf, no conflict
        """
        self.dut.kill_all()
        self.session_secondary = self.dut.new_session()
        self.session_third = self.dut.new_session()

        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end"]
        pkts = {
            "matched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)'],
            "mismatched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)'],
            "pf": [
                'Ether(dst="%s")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)' % self.pf0_mac,
                'Ether(dst="%s")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)' % self.pf1_mac]
        }
        out_pf0 = self.dut.send_expect("ethtool -N %s flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1" % self.pf0_intf, "# ")
        out_pf1 = self.dut.send_expect("ethtool -N %s flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1" % self.pf1_intf, "# ")
        p = re.compile(r"Added rule with ID (\d+)")
        m0 = p.search(out_pf0)
        m1 = p.search(out_pf1)

        eal_param = "-c 0xf -n 6 -w %s -w %s --file-prefix=pf0" % (self.sriov_vfs_pf0[0].pci,self.sriov_vfs_pf0[1].pci)
        command = self.path + eal_param + " -- -i --rxq=%s --txq=%s" % (self.cvlq_num, self.cvlq_num)
        self.dut.send_expect(command, "testpmd> ", 300)
        self.config_testpmd()

        eal_param = "-c 0xf0 -n 6 -w %s -w %s --file-prefix=pf1" % (self.sriov_vfs_pf1[0].pci,self.sriov_vfs_pf1[1].pci)
        command = self.path + eal_param + " -- -i --rxq=%s --txq=%s" % (self.cvlq_num, self.cvlq_num)
        self.session_secondary.send_expect(command, "testpmd> ", 300)
        #self.session_secondary.config_testpmd()
        self.session_secondary.send_expect("set fwd rxonly", "testpmd> ")
        self.session_secondary.send_expect("set verbose 1", "testpmd> ")
        # specify a fixed rss-hash-key for cvl ether
        self.session_secondary.send_expect(
            "port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd", "testpmd> ")
        self.session_secondary.send_expect(
            "port config 1 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd", "testpmd> ")
        self.session_secondary.send_expect("start", "testpmd> ")

        self.create_fdir_rule(rules, check_stats=True)
        self.session_secondary.send_expect("flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end", "created")
        self.session_secondary.send_expect("flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end", "created")

        # confirm pf link is up
        self.session_third.send_expect("ifconfig %s up" % self.pf0_intf, "# ", 15)
        self.session_third.send_expect("ifconfig %s up" % self.pf1_intf, "# ", 15)
        time.sleep(1)

        # send matched packets
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0))
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1))
        self.tester.scapy_execute()
        time.sleep(1)
        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify("rx_queue_1_packets: 1" in out_pf0, "the packet is not redirected to expected queue of pf0")
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify("rx_queue_1_packets: 1" in out_pf1, "the packet is not redirected to expected queue of pf1")

        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=True)
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=True)

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf10, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=True)

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf11, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=True)

        #send mismatched packets
        out_vf00 = self.send_pkts_getouput(pkts["mismatched"][0])
        rfc.check_iavf_fdir_mark(out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=False)
        out_vf01 = self.send_pkts_getouput(pkts["mismatched"][1])
        rfc.check_iavf_fdir_mark(out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=False)

        self.send_packets(pkts["mismatched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf10, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=False)

        self.send_packets(pkts["mismatched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf11, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=False)

        # flush all the rules
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.dut.send_expect("flow flush 1", "testpmd> ")
        self.session_secondary.send_expect("flow flush 0", "testpmd> ")
        self.session_secondary.send_expect("flow flush 1", "testpmd> ")

        self.session_third.send_expect("ethtool -N %s delete %d" % (self.pf0_intf, int(m0.group(1))), "# ")
        self.session_third.send_expect("ethtool -N %s delete %d" % (self.pf1_intf, int(m1.group(1))), "# ")
        self.session_third.send_expect("ethtool -n %s" % (self.pf0_intf), "Total 0 rules")
        self.session_third.send_expect("ethtool -n %s" % (self.pf1_intf), "Total 0 rules")

        # send matched packets
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0))
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1))
        self.tester.scapy_execute()

        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify("rx_queue_1_packets: 1" in out_pf0, "the packet is redirected to expected queue of pf0")
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify("rx_queue_1_packets: 1" in out_pf1, "the packet is redirected to expected queue of pf1")

        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=False)
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=False)

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf10, pkt_num=1, check_param={"port_id": 0, "queue": 1}, stats=False)

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf11, pkt_num=1, check_param={"port_id": 1, "queue": 1}, stats=False)

        self.dut.close_session(self.session_secondary)
        self.dut.close_session(self.session_third)

    def test_create_same_input_diff_action_on_pf_vf(self):
        """
        create same input set but different action rules on pf and vf, no conflict.
        """
        self.dut.kill_all()
        self.session_secondary = self.dut.new_session()
        self.session_third = self.dut.new_session()

        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 3 4 end / mark / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end"]
        pkts = {
            "matched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)'],
            "mismatched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)'],
            "pf": [
                'Ether(dst="%s")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)' % self.pf0_mac,
                'Ether(dst="%s")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)' % self.pf1_mac]
        }
        out_pf0 = self.dut.send_expect("ethtool -N %s flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1" % self.pf0_intf, "# ")
        out_pf1 = self.dut.send_expect("ethtool -N %s flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 2" % self.pf1_intf, "# ")
        p = re.compile(r"Added rule with ID (\d+)")
        m0 = p.search(out_pf0)
        m1 = p.search(out_pf1)

        eal_param = "-c 0xf -n 6 -w %s -w %s --file-prefix=pf0" % (self.sriov_vfs_pf0[0].pci,self.sriov_vfs_pf0[1].pci)
        command = self.path + eal_param + " -- -i --rxq=%s --txq=%s" % (self.cvlq_num, self.cvlq_num)
        self.dut.send_expect(command, "testpmd> ", 300)
        self.config_testpmd()

        eal_param = "-c 0xf0 -n 6 -w %s -w %s --file-prefix=pf1" % (self.sriov_vfs_pf1[0].pci,self.sriov_vfs_pf1[1].pci)
        command = self.path + eal_param + " -- -i --rxq=%s --txq=%s" % (self.cvlq_num, self.cvlq_num)
        self.session_secondary.send_expect(command, "testpmd> ", 300)
        #self.session_secondary.config_testpmd()
        self.session_secondary.send_expect("set fwd rxonly", "testpmd> ")
        self.session_secondary.send_expect("set verbose 1", "testpmd> ")
        # specify a fixed rss-hash-key for cvl ether
        self.session_secondary.send_expect(
            "port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd", "testpmd> ")
        self.session_secondary.send_expect(
            "port config 1 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd", "testpmd> ")
        self.session_secondary.send_expect("start", "testpmd> ")

        self.create_fdir_rule(rules[:2], check_stats=True)
        self.session_secondary.send_expect(rules[2], "created")
        self.session_secondary.send_expect(rules[3], "created")

        # confirm pf link is up
        self.session_third.send_expect("ifconfig %s up" % self.pf0_intf, "# ", 15)
        self.session_third.send_expect("ifconfig %s up" % self.pf1_intf, "# ", 15)
        time.sleep(1)

        # send matched packets
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0))
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1))
        self.tester.scapy_execute()
        time.sleep(1)
        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify("rx_queue_1_packets: 1" in out_pf0, "the packet is not redirected to expected queue of pf0")
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify("rx_queue_2_packets: 1" in out_pf1, "the packet is not redirected to expected queue of pf1")

        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 1}, stats=True)
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": [3, 4], "mark_id": 0}, stats=True)

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf10, pkt_num=1, check_param={"port_id": 0, "drop": 1}, stats=True)

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf11, pkt_num=1, check_param={"port_id": 1, "passthru": 1, "mark_id": 1}, stats=True)

        #send mismatched packets
        out_vf00 = self.send_pkts_getouput(pkts["mismatched"][0])
        rfc.check_iavf_fdir_mark(out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 1}, stats=False)
        out_vf01 = self.send_pkts_getouput(pkts["mismatched"][1])
        rfc.check_iavf_fdir_mark(out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": [3, 4], "mark_id": 0}, stats=False)

        self.send_packets(pkts["mismatched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf10, pkt_num=1, check_param={"port_id": 0, "drop": 1}, stats=False)

        self.send_packets(pkts["mismatched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf11, pkt_num=1, check_param={"port_id": 1, "passthru": 1, "mark_id": 1}, stats=False)

        # flush all the rules
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.dut.send_expect("flow flush 1", "testpmd> ")
        self.session_secondary.send_expect("flow flush 0", "testpmd> ")
        self.session_secondary.send_expect("flow flush 1", "testpmd> ")

        self.session_third.send_expect("ethtool -N %s delete %d" % (self.pf0_intf, int(m0.group(1))), "# ")
        self.session_third.send_expect("ethtool -N %s delete %d" % (self.pf1_intf, int(m1.group(1))), "# ")
        self.session_third.send_expect("ethtool -n %s" % (self.pf0_intf), "Total 0 rules")
        self.session_third.send_expect("ethtool -n %s" % (self.pf1_intf), "Total 0 rules")

        # send matched packets
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0))
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1))
        self.tester.scapy_execute()

        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify("rx_queue_1_packets: 1" in out_pf0, "the packet is redirected to expected queue of pf0")
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify("rx_queue_2_packets: 1" in out_pf1, "the packet is redirected to expected queue of pf1")

        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 1}, stats=False)
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": [3, 4], "mark_id": 0}, stats=False)

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf10, pkt_num=1, check_param={"port_id": 0, "drop": 1}, stats=False)

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf11, pkt_num=1, check_param={"port_id": 1, "passthru": 1, "mark_id": 1}, stats=False)

        self.dut.close_session(self.session_secondary)
        self.dut.close_session(self.session_third)

    def test_create_diff_input_diff_action_on_pf_vf(self):
        """
        create different rules on pf and vf
        """
        self.dut.kill_all()
        self.session_secondary = self.dut.new_session()
        self.session_third = self.dut.new_session()

        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.22 dst is 192.168.0.23 / udp src is 22 dst is 23 / end actions queue index 6 / mark / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.22 dst is 192.168.0.23 / udp src is 22 dst is 23 / end actions queue index 6 / mark id 1 / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.22 dst is 192.168.0.23 tos is 4 / tcp src is 22 dst is 23 / end actions drop / end"]
        pkts = {
            "matched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.22",dst="192.168.0.23")/UDP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.22",dst="192.168.0.23")/UDP(sport=22,dport=23)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.22",dst="192.168.0.23",tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)'],
            "mismatched": [
                'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
                'Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)'],
            "pf": [
                'Ether(dst="%s")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)' % self.pf0_mac,
                'Ether(dst="%s")/IP(src="192.168.0.22",dst="192.168.0.23")/UDP(sport=22,dport=23)/Raw("x" * 80)' % self.pf1_mac]
        }
        out_pf0 = self.dut.send_expect("ethtool -N %s flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1" % self.pf0_intf, "# ")
        out_pf1 = self.dut.send_expect("ethtool -N %s flow-type udp4 src-ip 192.168.0.22 dst-ip 192.168.0.23 src-port 22 dst-port 23 action -1" % self.pf1_intf, "# ")
        p = re.compile(r"Added rule with ID (\d+)")
        m0 = p.search(out_pf0)
        m1 = p.search(out_pf1)

        eal_param = "-c 0xf -n 6 -w %s -w %s --file-prefix=pf0" % (self.sriov_vfs_pf0[0].pci,self.sriov_vfs_pf0[1].pci)
        command = self.path + eal_param + " -- -i --rxq=%s --txq=%s" % (self.cvlq_num, self.cvlq_num)
        self.dut.send_expect(command, "testpmd> ", 300)
        self.config_testpmd()

        eal_param = "-c 0xf0 -n 6 -w %s -w %s --file-prefix=pf1" % (self.sriov_vfs_pf1[0].pci,self.sriov_vfs_pf1[1].pci)
        command = self.path + eal_param + " -- -i --rxq=%s --txq=%s" % (self.cvlq_num, self.cvlq_num)
        self.session_secondary.send_expect(command, "testpmd> ", 300)
        #self.session_secondary.config_testpmd()
        self.session_secondary.send_expect("set fwd rxonly", "testpmd> ")
        self.session_secondary.send_expect("set verbose 1", "testpmd> ")
        # specify a fixed rss-hash-key for cvl ether
        self.session_secondary.send_expect(
            "port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd", "testpmd> ")
        self.session_secondary.send_expect(
            "port config 1 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd", "testpmd> ")
        self.session_secondary.send_expect("start", "testpmd> ")

        self.create_fdir_rule(rules[:2], check_stats=True)
        self.session_secondary.send_expect(rules[2], "created")
        self.session_secondary.send_expect(rules[3], "created")

        # confirm pf link is up
        self.session_third.send_expect("ifconfig %s up" % self.pf0_intf, "# ", 15)
        self.session_third.send_expect("ifconfig %s up" % self.pf1_intf, "# ", 15)
        time.sleep(1)

        # send matched packets
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0))
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1))
        self.tester.scapy_execute()
        time.sleep(1)

        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify("rx_queue_1_packets: 1" in out_pf0, "the packet is not redirected to expected queue of pf0")
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify("rx_dropped: 1" in out_pf1, "the packet is not dropped pf1")

        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": [2, 3]}, stats=True)
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": 6, "mark_id": 0}, stats=True)

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf10, pkt_num=1, check_param={"port_id": 0, "queue": 6, "mark_id": 1}, stats=True)

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf11, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=True)

        #send mismatched packets
        out_vf00 = self.send_pkts_getouput(pkts["mismatched"][0])
        rfc.check_iavf_fdir_mark(out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": [2, 3]}, stats=False)
        out_vf01 = self.send_pkts_getouput(pkts["mismatched"][1])
        rfc.check_iavf_fdir_mark(out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": 6, "mark_id": 0}, stats=False)

        self.send_packets(pkts["mismatched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf10, pkt_num=1, check_param={"port_id": 0, "queue": 6, "mark_id": 1}, stats=False)

        self.send_packets(pkts["mismatched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf11, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=False)

        # flush all the rules
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.dut.send_expect("flow flush 1", "testpmd> ")
        self.session_secondary.send_expect("flow flush 0", "testpmd> ")
        self.session_secondary.send_expect("flow flush 1", "testpmd> ")

        self.session_third.send_expect("ethtool -N %s delete %d" % (self.pf0_intf, int(m0.group(1))), "# ")
        self.session_third.send_expect("ethtool -N %s delete %d" % (self.pf1_intf, int(m1.group(1))), "# ")
        self.session_third.send_expect("ethtool -n %s" % (self.pf0_intf), "Total 0 rules")
        self.session_third.send_expect("ethtool -n %s" % (self.pf1_intf), "Total 0 rules")

        # send matched packets
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][0], self.tester_iface0))
        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkts["pf"][1], self.tester_iface1))
        self.tester.scapy_execute()

        out_pf0 = self.session_third.send_expect("ethtool -S %s" % self.pf0_intf, "# ")
        self.verify("rx_queue_1_packets: 1" in out_pf0, "the rule is not destroyed")
        out_pf1 = self.session_third.send_expect("ethtool -S %s" % self.pf1_intf, "# ")
        self.verify("rx_dropped: 1" in out_pf1, "the packet is dropped by pf1")

        #send mismatched packets
        out_vf00 = self.send_pkts_getouput(pkts["matched"][0])
        rfc.check_iavf_fdir_mark(out_vf00, pkt_num=1, check_param={"port_id": 0, "queue": [2, 3]}, stats=False)
        out_vf01 = self.send_pkts_getouput(pkts["matched"][1])
        rfc.check_iavf_fdir_mark(out_vf01, pkt_num=1, check_param={"port_id": 1, "queue": 6, "mark_id": 0}, stats=False)

        self.send_packets(pkts["matched"][2], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf10 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf10, pkt_num=1, check_param={"port_id": 0, "queue": 6, "mark_id": 1}, stats=False)

        self.send_packets(pkts["matched"][3], pf_id=1)
        out_info = self.session_secondary.get_session_before(timeout=2)
        out_pkt = self.session_secondary.send_expect("stop", "testpmd> ")
        out_vf11 = out_info + out_pkt
        self.session_secondary.send_expect("start", "testpmd> ")
        rfc.check_iavf_fdir_mark(out_vf11, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=False)

        self.dut.close_session(self.session_secondary)
        self.dut.close_session(self.session_third)

    def test_maxnum_128_profiles(self):
        """
        There are 128 profiles in total.
        each pf apply for 8 profiles when kernel driver init, 4 for non-tunnel packet, 4 for tunnel packet.
        profile 0 and profile 1 are default profile for specific packet.
        design case with 2*100G card, so only 110 profiles can be used for vf.
        """
        nex_cnt = 0
        self.destroy_env()
        self.setup_npf_nvf_env(pf_num=1,vf_num=16)

        if len(self.dut_ports) == 4:
            nex_cnt = 94 // 8
        elif len(self.dut_ports) == 2:
            nex_cnt = 110 // 8
        else:
            self.verify(False, 'The number of ports is not supported')

        self.dut.send_expect("ip link set {} vf {} mac 00:11:22:33:44:55".format(self.pf0_intf, nex_cnt), '#')
        command = self.path + " -c f -n 6 -- -i --rxq=4 --txq=4"
        self.dut.send_expect(command, "testpmd> ", 360)
        self.config_testpmd()

        for port_id in range(nex_cnt):
            rules = [
                "flow create %d ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end" % port_id,
                "flow create %d ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end" % port_id,
                "flow create %d ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / mark / end" % port_id,
                "flow create %d ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end" % port_id,
                "flow create %d ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end" % port_id,
                "flow create %d ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / sctp src is 22 dst is 23 / end actions queue index 1 / mark / end" % port_id,
                "flow create %d ingress pattern eth type is 0x8863 / end actions queue index 1 / mark id 1 / end" % port_id,
                "flow create %d ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 2 / end" % port_id]
            self.create_fdir_rule(rules, check_stats=True)

        rules = [
            "flow create {} ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end".format(nex_cnt),
            "flow create {} ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end".format(nex_cnt),
            "flow create {} ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / mark / end".format(nex_cnt),
            "flow create {} ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end".format(nex_cnt),
            "flow create {} ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end".format(nex_cnt),
            "flow create {} ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / sctp src is 22 dst is 23 / end actions queue index 1 / mark / end".format(nex_cnt)]
        self.create_fdir_rule(rules, check_stats=True)

        rule = "flow create {} ingress pattern eth type is 0x8863 / end actions queue index 1 / mark id 1 / end".format(nex_cnt)
        self.create_fdir_rule(rule, check_stats=False)
        pkt1 = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22, dport=23)/ Raw("x" * 80)'
        out = self.send_pkts_getouput(pkts=pkt1)
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": nex_cnt, "mark_id": 0, "queue": 1}, stats=True)
        pkt2 = 'Ether(dst="00:11:22:33:44:55", type=0x8863)/IP()/Raw("x" * 80)'
        out = self.send_pkts_getouput(pkts=pkt2)
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": nex_cnt, "mark_id": 1, "queue": 1}, stats=False)

        self.dut.send_expect("flow flush {}".format(nex_cnt), "testpmd> ")
        self.check_fdir_rule(port_id=(nex_cnt), stats=False)
        out = self.send_pkts_getouput(pkts=pkt1)
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": nex_cnt, "mark_id": 0, "queue": 1}, stats=False)

        self.create_fdir_rule(rule, check_stats=True)
        out = self.send_pkts_getouput(pkts=pkt2)
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": nex_cnt, "mark_id": 1, "queue": 1}, stats=True)

    def test_stress_port_stop_start(self):
        """
        Rules can take effect after port stop/start
        """
        rule = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark / end"
        pkt = 'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") / Raw("x" * 80)'
        self.create_fdir_rule(rule, check_stats=True)
        out = self.send_pkts_getouput(pkts=pkt)
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 1}, stats=True)
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.check_fdir_rule(port_id=0, rule_list=['0'])
        out = self.send_pkts_getouput(pkts=pkt)
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 1}, stats=True)

    def test_stress_delete_rules(self):
        """
        delete 1st/2nd/last rule won't affect other rules
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 24 / end actions queue index 2 / mark id 2 / end",
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 25 / end actions queue index 3 / mark id 3 / end"]
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=25)/Raw("x" * 80)']

        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)
        out_0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out_0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=True)
        out_1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out_1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=True)
        out_2 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(out_2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=True)

        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ")
        out_0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out_0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=False)
        out_1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out_1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=True)
        out_2 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(out_2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=True)
        self.dut.send_expect("flow flush 0", "testpmd> ")

        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)
        self.dut.send_expect("flow destroy 0 rule 1", "testpmd> ")
        out_0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out_0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=True)
        out_1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out_1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=False)
        out_2 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(out_2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=True)
        self.dut.send_expect("flow flush 0", "testpmd> ")

        rule_li = self.create_fdir_rule(rules, check_stats=True)
        self.check_fdir_rule(port_id=0, rule_list=rule_li)
        self.dut.send_expect("flow destroy 0 rule 2", "testpmd> ")
        out_0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out_0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=True)
        out_1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out_1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=True)
        out_2 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(out_2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=False)
        self.dut.send_expect("flow flush 0", "testpmd> ")

        out_0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out_0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=False)
        out_1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out_1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=False)
        out_2 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(out_2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=False)

    def test_stress_vf_port_reset_add_new_rule(self):
        """
        vf reset, the origin rule can't take effect,
        then add a new rule which can take effect.
        relaunch testpmd, create same rules, can take effect.
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end"]
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)']
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 1}, stats=True)
        # reset vf
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port reset 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        # check the rule of port0 is still listed, but doesn't take effect.
        self.check_fdir_rule(port_id=0, rule_list=['0'])
        self.check_fdir_rule(port_id=1, rule_list=['0'])
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 1}, stats=True)
        # create the rule again
        self.create_fdir_rule(rules[0], check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 1}, stats=True)
        # relaunch testpmd, and create the rules, check matched packets.
        self.dut.send_expect("quit", "# ")
        self.launch_testpmd()
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 1}, stats=True)

    def test_stress_vf_port_reset_delete_rule(self):
        """
        vf reset, the origin rule can't take effect,
        then delete the rule which can't take effect without core dump,
        relaunch testpmd, create same rules, can take effect.
        """
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark / end"]
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)']
        rule_li = self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 6}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 6}, stats=True)
        # reset vf
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port reset 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        # check the rule of port0 is still listed, but doesn't take effect.
        self.check_fdir_rule(port_id=0, rule_list=['0'])
        self.check_fdir_rule(port_id=1, rule_list=['0'])
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 6}, stats=True)
        # delete the rules
        self.dut.send_expect("flow destroy 0 rule 0", "Invalid flow destroy")
        self.destroy_fdir_rule(rule_id='0', port_id=1)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 6}, stats=False)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 6}, stats=False)
        # relaunch testpmd, and create the rules, check matched packets.
        self.dut.send_expect("quit", "# ")
        self.launch_testpmd()
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 6}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 6}, stats=True)

    def test_stress_pf_reset_vf_add_new_rule(self):
        """
        pf trigger vf reset, the origin rule can't take effect,
        then add a new rule which can take effect.
        relaunch testpmd, create same rules, can take effect.
        """
        self.session_secondary = self.dut.new_session()
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end"]
        new_rule = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.1 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark id 1 / end"
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.0",dst="192.1.0.1", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)']
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 1}, stats=True)

        self.session_secondary.send_expect("ip link set %s vf 0 mac 00:11:22:33:44:56" % self.pf0_intf, "# ")
        out = self.dut.session.get_session_before(timeout=2)
        self.verify("Port 0: reset event" in out, "failed to reset vf0")
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port reset 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        out0 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 1}, stats=True)

        # create a new rule, the packet patch the rule can be redirected to queue 6 with mark ID 1.
        self.create_fdir_rule(new_rule, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[3])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 6}, stats=True)
        # relaunch testpmd, and create the rules, check matched packets.
        self.dut.send_expect("quit", "# ")
        self.launch_testpmd()
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 1}, stats=True)
        self.dut.send_expect("quit", "# ")
        self.session_secondary.send_expect("ip link set %s vf 0 mac 00:11:22:33:44:55" % self.pf0_intf, "# ")
        self.dut.close_session(self.session_secondary)

    def test_stress_pf_reset_vf_delete_rule(self):
        """
        pf trigger vf reset, the origin rule can't take effect,
        then delete the rule which can't take effect without core dump,
        relaunch testpmd, create same rules, can take effect.
        """
        self.session_secondary = self.dut.new_session()
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark / end",
            "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark / end"]
        pkts = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw("x" * 80)']
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[0])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 6}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 6}, stats=True)

        self.session_secondary.send_expect("ip link set %s vf 0 mac 00:11:22:33:44:56" % self.pf0_intf, "# ")
        out = self.dut.session.get_session_before(timeout=2)
        self.verify("Port 0: reset event" in out, "failed to reset vf0")
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port reset 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        out0 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "passthru": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 6}, stats=True)
        # delete the rules
        self.dut.send_expect("flow destroy 0 rule 0", "Invalid flow destroy")
        self.destroy_fdir_rule(rule_id='0', port_id=1)
        out0 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 6}, stats=False)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 6}, stats=False)

        # relaunch testpmd, and create the rules, check matched packets.
        self.dut.send_expect("quit", "# ")
        self.launch_testpmd()
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts[2])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 0, "queue": 6}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts[1])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 1, "mark_id": 0, "queue": 6}, stats=True)
        self.dut.send_expect("quit", "# ")
        self.session_secondary.send_expect("ip link set %s vf 0 mac 00:11:22:33:44:55" % self.pf0_intf, "# ")
        self.dut.close_session(self.session_secondary)

    def checksum_enablehw(self, port, hw):
        """
        set checksum parameters
        """
        self.dut.send_expect("set fwd csum", "testpmd>")
        self.dut.send_expect("port stop all", "testpmd>")
        self.dut.send_expect("csum set ip %s %d" % (hw, port), "testpmd>")
        self.dut.send_expect("csum set udp %s %d" %(hw, port), "testpmd>")
        self.dut.send_expect("port start all", "testpmd>")
        self.dut.send_expect("start", "testpmd>")

    def get_chksum_values(self, packets_expected):
        """
        Validate the checksum flags.
        """
        checksum_pattern = re.compile("chksum.*=.*(0x[0-9a-z]+)")

        chksum = dict()

        self.tester.send_expect("scapy", ">>> ")
        self.tester.send_expect("import sys", ">>> ")
        self.tester.send_expect("sys.path.append('./dep')", ">>> ")
        self.tester.send_expect("from pfcp import PFCP",  ">>> ")

        for packet_type in list(packets_expected.keys()):
            self.tester.send_expect("p = %s" % packets_expected[packet_type], ">>>")
            out = self.tester.send_command("p.show2()", timeout=1)
            chksums = checksum_pattern.findall(out)
            chksum[packet_type] = chksums

        self.tester.send_expect("exit()", "#")
        return chksum

    def checksum_validate(self, packets_sent, packets_expected):
        """
        Validate the checksum.
        """
        tx_interface = self.tester_iface0
        rx_interface = self.tester_iface0

        sniff_src = "00:11:22:33:44:55"
        result = dict()
        pkt = Packet()
        chksum = self.get_chksum_values(packets_expected)
        self.inst = self.tester.tcpdump_sniff_packets(intf=rx_interface, count=len(packets_sent),
                filters=[{'layer': 'ether', 'config': {'src': sniff_src}}])
        for packet_type in list(packets_sent.keys()):
            pkt.append_pkt(packets_sent[packet_type])
        pkt.send_pkt(crb=self.tester, tx_port=tx_interface, count=1)

        p = self.tester.load_tcpdump_sniff_packets(self.inst)
        nr_packets = len(p)
        print(p)
        packets_received = [p[i].sprintf("%IP.chksum%;%TCP.chksum%;%UDP.chksum%;%SCTP.chksum%") for i in range(nr_packets)]
        print(len(packets_sent), len(packets_received))
        self.verify(len(packets_sent)*1 == len(packets_received), "Unexpected Packets Drop")
        i = 0
        for packet_received in packets_received:
            ip_checksum, tcp_checksum, udp_checksum, sctp_checksum = packet_received.split(';')
            if udp_checksum != '??':
                packet_type = 'UDP'
                l4_checksum = udp_checksum
            if i == 0 or i == 2:
                packet_type = packet_type + '/PFCP_NODE'
            else:
                packet_type = packet_type + '/PFCP_SESSION'

            if ip_checksum != '??':
                packet_type = 'IP/' + packet_type
                if chksum[packet_type] != [ip_checksum, l4_checksum]:
                    result[packet_type] = packet_type + " checksum error"
            else:
                packet_type = 'IPv6/' + packet_type
                if chksum[packet_type] != [l4_checksum]:
                    result[packet_type] = packet_type + " checksum error"
            i = i + 1
        return (result, p)

    def set_vlan(self, vlan, port, strip, rx_tx="rx"):
        """
        set rx_vlan and tx_vlan
        """
        self.dut.send_expect("vlan set filter on %d" % port, "testpmd> ", 20)
        self.dut.send_expect("vlan set strip %s %d" % (strip, port), "testpmd> ", 20)
        self.dut.send_expect("rx_vlan add %d %d" % (vlan, port), "testpmd> ", 20)
        self.dut.send_expect("set verbose 1", "testpmd> ", 20)

        if rx_tx == "tx":
            self.dut.send_expect("port stop %d" % port, "testpmd> ", 20)
            self.dut.send_expect("tx_vlan set %d %d" % (port, vlan), "testpmd> ", 20)
            self.dut.send_expect("port start %d" % port, "testpmd> ", 20)
            self.dut.send_expect("set fwd mac", "testpmd> ", 20)

    def get_tcpdump_package(self, pkts):
        """
        return vlan id of tcpdump packets
        """
        vlans = []
        for i in range(len(pkts)):
            vlan = pkts.strip_element_vlan("vlan", p_index=i)
            print("vlan is:", vlan)
            vlans.append(vlan)
        return vlans

    def test_pfcp_vlan_strip_on_hw_checksum(self):
        """
        Set PFCP FDIR rules
        Enable HW checksum offload.
        Enable vlan filter and receipt of VLAN packets with VLAN Tag Identifier 1 on port 0.
        Disable vlan strip.
        Send packet with incorrect checksum,
        can rx it and report the checksum error,
        verify forwarded packets have correct checksum.
        """
        rules = ["flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / mark id 1 / end",
                 "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / mark id 2 / end",
                 "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / mark id 3 / end",
                 "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / mark id 4 / end"]

        self.dut.send_expect("quit", "# ")
        self.pmd_output.start_testpmd(cores="1S/4C/1T",
                                      param="--rxq={} --txq={} --enable-rx-cksum --port-topology=loop".format(self.cvlq_num, self.cvlq_num),
                                      eal_param="-w %s" % self.sriov_vfs_pf0[0].pci,
                                      socket=self.ports_socket)
        vlan = 51
        mac = "00:11:22:33:44:55"
        sndIP = '10.0.0.1'
        sndIPv6 = '::1'
        pkts_sent = {'IP/UDP/PFCP_NODE': 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s", chksum=0xf)/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=0)/("X"*46)' % (mac, sndIP),
                     'IP/UDP/PFCP_SESSION': 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s", chksum=0xf)/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=1)/("X"*46)' % (mac, sndIP),
                     'IPv6/UDP/PFCP_NODE': 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=0)/("X"*46)' % (mac, sndIPv6),
                     'IPv6/UDP/PFCP_SESSION': 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=1)/("X"*46)' % (mac, sndIPv6)}

        expIP = sndIP
        expIPv6 = sndIPv6
        pkts_ref = {'IP/UDP/PFCP_NODE': 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)' % (mac, expIP),
                    'IP/UDP/PFCP_SESSION': 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)' % (mac, expIP),
                    'IPv6/UDP/PFCP_NODE': 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)' % (mac, expIPv6),
                    'IPv6/UDP/PFCP_SESSION': 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)' % (mac, expIPv6)}

        self.checksum_enablehw(port=0, hw="hw")

        self.set_vlan(vlan=vlan, port=0, strip="on")
        out_info = self.dut.send_expect("show port info 0", "testpmd> ", 20)
        self.verify("strip on" in out_info, "Wrong strip:" + out_info)

        # send packets and check the checksum value
        result = self.checksum_validate(pkts_sent, pkts_ref)
        # validate vlan in the tcpdumped packets
        out_dump = self.get_tcpdump_package(result[1])
        self.verify(len(out_dump), "Forwarded vlan packet not received!!!")
        self.verify(vlan not in out_dump, "Wrong vlan:" + str(out_dump))

        # Validate checksum on the receive packet
        out_testpmd = self.dut.send_expect("stop", "testpmd> ")
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out_testpmd)
        bad_l4csum = self.pmd_output.get_pmd_value("Bad-l4csum:", out_testpmd)
        self.verify(bad_ipcsum == 2, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 4, "Bad-l4csum check error")
        self.dut.send_expect("start", "testpmd> ")

        # check fdir rule take effect
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=True)
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=True)
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out3, pkt_num=1, check_param={"port_id": 0, "mark_id": 4, "queue": 4}, stats=True)

        # destroy the rules and check there is no rule listed.
        self.dut.send_expect("flow flush 0", "testpmd> ", 20)
        self.check_fdir_rule(port_id=0, stats=False)

        # check no rules existing
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=False)
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=False)
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=False)
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out3, pkt_num=1, check_param={"port_id": 0, "mark_id": 4, "queue": 4}, stats=False)

        # send packets and check the checksum value
        result = self.checksum_validate(pkts_sent, pkts_ref)
        # validate vlan in the tcpdumped packets
        out_dump = self.get_tcpdump_package(result[1])
        self.verify(len(out_dump), "Forwarded vlan packet not received!!!")
        self.verify(vlan not in out_dump, "Wrong vlan:" + str(out_dump))

        # Validate checksum on the receive packet
        out_testpmd = self.dut.send_expect("stop", "testpmd> ")
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out_testpmd)
        bad_l4csum = self.pmd_output.get_pmd_value("Bad-l4csum:", out_testpmd)
        self.verify(bad_ipcsum == 2, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 4, "Bad-l4csum check error")

    def test_pfcp_vlan_strip_off_sw_checksum(self):
        """
        Set PFCP FDIR rules
        Enable SW checksum offload.
        Enable vlan filter and receipt of VLAN packets with VLAN Tag Identifier 1 on port 0.
        Disable vlan strip.
        Send packet with incorrect checksum,
        can rx it and report the checksum error,
        verify forwarded packets have correct checksum.
        """
        rules = ["flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / mark id 1 / end",
                 "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / mark id 2 / end",
                 "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / mark id 3 / end",
                 "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / mark id 4 / end"]

        self.dut.send_expect("quit", "# ")
        self.pmd_output.start_testpmd(cores="1S/4C/1T",
                                      param="--rxq={} --txq={} --enable-rx-cksum --port-topology=loop".format(self.cvlq_num, self.cvlq_num),
                                      eal_param="-w %s" % self.sriov_vfs_pf0[0].pci,
                                      socket=self.ports_socket)
        vlan = 51
        mac = "00:11:22:33:44:55"
        sndIP = '10.0.0.1'
        sndIPv6 = '::1'
        pkts_sent = {'IP/UDP/PFCP_NODE': 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s", chksum=0xf)/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=0)/("X"*46)' % (mac, sndIP),
                'IP/UDP/PFCP_SESSION': 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s", chksum=0xf)/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=1)/("X"*46)' % (mac, sndIP),
                'IPv6/UDP/PFCP_NODE': 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=0)/("X"*46)' % (mac, sndIPv6),
                'IPv6/UDP/PFCP_SESSION': 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(S=1)/("X"*46)' % (mac, sndIPv6)}

        expIP = sndIP
        expIPv6 = sndIPv6
        pkts_ref = {'IP/UDP/PFCP_NODE': 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)' % (mac, expIP),
                    'IP/UDP/PFCP_SESSION': 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)' % (mac, expIP),
                    'IPv6/UDP/PFCP_NODE': 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)' % (mac, expIPv6),
                    'IPv6/UDP/PFCP_SESSION': 'Ether(src="%s", dst="52:00:00:00:00:00")/Dot1Q(vlan=51)/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)' % (mac, expIPv6)}

        self.checksum_enablehw(port=0, hw="sw")

        self.set_vlan(vlan=vlan, port=0, strip="off")
        out_info = self.dut.send_expect("show port info 0", "testpmd> ", 20)
        self.verify("strip off" in out_info, "Wrong strip:" + out_info)

        result = self.checksum_validate(pkts_sent, pkts_ref)

        out_dump = self.get_tcpdump_package(result[1])
        self.verify(len(out_dump), "Forwarded vlan packet not received!!!")
        self.verify(vlan in out_dump, "Wrong vlan:" + str(out_dump))

        # Validate checksum on the receive packet
        out_testpmd = self.dut.send_expect("stop", "testpmd> ")
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out_testpmd)
        bad_l4csum = self.pmd_output.get_pmd_value("Bad-l4csum:", out_testpmd)
        self.verify(bad_ipcsum == 2, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 4, "Bad-l4csum check error")
        self.dut.send_expect("start", "testpmd> ")

        # check fdir rule take effect
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=True)
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=True)
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out3, pkt_num=1, check_param={"port_id": 0, "mark_id": 4, "queue": 4}, stats=True)

        # destroy the rules and check there is no rule listed.
        self.dut.send_expect("flow flush 0", "testpmd> ", 20)
        self.check_fdir_rule(port_id=0, stats=False)

        # check no rules existing
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=False)
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=False)
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=False)
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out3, pkt_num=1, check_param={"port_id": 0, "mark_id": 4, "queue": 4}, stats=False)

        result = self.checksum_validate(pkts_sent, pkts_ref)

        out_dump = self.get_tcpdump_package(result[1])
        self.verify(len(out_dump), "Forwarded vlan packet not received!!!")
        self.verify(vlan in out_dump, "Wrong vlan:" + str(out_dump))

        # Validate checksum on the receive packet
        out_testpmd = self.dut.send_expect("stop", "testpmd> ")
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out_testpmd)
        bad_l4csum = self.pmd_output.get_pmd_value("Bad-l4csum:", out_testpmd)
        self.verify(bad_ipcsum == 2, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 4, "Bad-l4csum check error")

    def test_pfcp_vlan_insert_on(self):
        """
        Set PFCP FDIR rules
        Enable vlan filter and insert VLAN Tag Identifier 1 to vlan packet sent from port 0
        """
        rules = ["flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / mark id 1 / end",
                 "flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / mark id 2 / end",
                 "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / mark id 3 / end",
                 "flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / mark id 4 / end"]

        self.dut.send_expect("quit", "# ")
        self.pmd_output.start_testpmd(cores="1S/4C/1T",
                                      param="--rxq={} --txq={} --enable-rx-cksum --port-topology=loop".format(self.cvlq_num, self.cvlq_num),
                                      eal_param="-w %s" % self.sriov_vfs_pf0[0].pci,
                                      socket=self.ports_socket)
        vlan = 51
        mac = "00:11:22:33:44:55"
        sndIP = '10.0.0.1'
        sndIPv6 = '::1'
        pkt = Packet()
        pkts_sent = {'IP/UDP/PFCP_NODE': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)' % (mac, sndIP),
                     'IP/UDP/PFCP_SESSION': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)' % (mac, sndIP),
                     'IPv6/UDP/PFCP_NODE': 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=0)/("X"*46)' % (mac, sndIPv6),
                     'IPv6/UDP/PFCP_SESSION': 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/UDP(sport=22, dport=8805)/PFCP(S=1)/("X"*46)' % (mac, sndIPv6)}

        self.set_vlan(vlan=vlan, port=0, strip="off", rx_tx="tx")
        self.dut.send_expect("start", "testpmd> ")

        tx_interface = self.tester_iface0
        rx_interface = self.tester_iface0

        dmac = "00:11:22:33:44:55"
        smac = self.pf1_mac
        inst = self.tester.tcpdump_sniff_packets(rx_interface)

        for packet_type in list(pkts_sent.keys()):
            pkt.append_pkt(pkts_sent[packet_type])
        pkt.send_pkt(crb=self.tester, tx_port=tx_interface, count=1)

        p = self.tester.load_tcpdump_sniff_packets(inst)

        out = self.get_tcpdump_package(p)
        self.verify(vlan in out, "Vlan not found:" + str(out))
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        # check fdir rule take effect
        self.create_fdir_rule(rules, check_stats=True)
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=True)
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=True)
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=True)
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out3, pkt_num=1, check_param={"port_id": 0, "mark_id": 4, "queue": 4}, stats=True)

        # destroy the rules and check there is no rule listed.
        self.dut.send_expect("flow flush 0", "testpmd> ", 20)
        self.check_fdir_rule(port_id=0, stats=False)

        # check no rules existing
        out0 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out0, pkt_num=1, check_param={"port_id": 0, "mark_id": 1, "queue": 1}, stats=False)
        out1 = self.send_pkts_getouput(pkts=pkts_sent["IP/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out1, pkt_num=1, check_param={"port_id": 0, "mark_id": 2, "queue": 2}, stats=False)
        out2 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_NODE"])
        rfc.check_iavf_fdir_mark(out2, pkt_num=1, check_param={"port_id": 0, "mark_id": 3, "queue": 3}, stats=False)
        out3 = self.send_pkts_getouput(pkts=pkts_sent["IPv6/UDP/PFCP_SESSION"])
        rfc.check_iavf_fdir_mark(out3, pkt_num=1, check_param={"port_id": 0, "mark_id": 4, "queue": 4}, stats=False)

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop all", "testpmd> ")
        self.dut.send_expect("tx_vlan reset 0", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ")
        self.dut.send_expect("stop", "testpmd> ", 30)

    def test_check_profile_delete(self):
        pkt_ipv4_pay_ipv6_pay = [
            'Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x" * 80)',
            'Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1, hlim=2)/("X"*480)']

        rule_ipv4_tcp_ipv6_udp = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 2 / mark id 2 / end"
        ]
        # create rules
        self.create_fdir_rule(rule_ipv4_tcp_ipv6_udp, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=True)
        out = self.send_pkts_getouput(pkt_ipv4_pay_ipv6_pay)
        rfc.verify_iavf_fdir_directed_by_rss(out, stats=True)

        self.pmd_output.execute_cmd("flow flush 0")
        rule_ipv4_other_ipv6_other = [
            "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 3 / mark id 3 / end",
            "flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / end actions queue index 4 / mark id 4 / end"
        ]
        self.create_fdir_rule(rule_ipv4_other_ipv6_other, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=True)
        out = self.send_pkts_getouput(pkt_ipv4_pay_ipv6_pay)
        rfc.check_iavf_fdir_mark(out, pkt_num=2, check_param={"port_id": 0, "mark_id": [3, 4], "queue": [3, 4]}, stats=True)

        self.pmd_output.execute_cmd("flow flush 0")
        self.create_fdir_rule(rule_ipv4_tcp_ipv6_udp, check_stats=True)
        self.check_fdir_rule(port_id=0, stats=True)
        out = self.send_pkts_getouput(pkt_ipv4_pay_ipv6_pay)
        rfc.verify_iavf_fdir_directed_by_rss(out, stats=True)

    def tear_down(self):
        # destroy all flow rule on port 0
        self.dut.kill_all()
        self.destroy_env()
        if getattr(self, 'session_secondary', None):
            self.dut.close_session(self.session_secondary)
        if getattr(self, 'session_third', None):
            self.dut.close_session(self.session_third)

    def tear_down_all(self):
        self.dut.kill_all()
        self.destroy_env()
