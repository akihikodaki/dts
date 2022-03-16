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
from framework.test_case import TestCase
from framework.utils import BLUE, GREEN, RED

vf1_mac = "00:01:23:45:67:89"

# send packets

MAC_IPV4_PAY_SRC_MAC = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2", frag=1)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="01:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="02:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="ff:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="01:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/ICMP()/Raw(load="x"*30)'
        % vf1_mac,
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:66:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:66", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2", frag=1)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:66:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:66", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:32:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="01:11:22:33:44:66", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/ICMP()/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_PAY_DST_MAC = {
    "match": [
        'Ether(src="00:02:00:00:00:01", dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)',
        'Ether(src="00:02:00:00:00:01", dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP()/Raw(load="x"*30)',
    ],
    "unmatch": [
        'Ether(src="00:02:00:00:00:01", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:02:00:00:00:01", dst="00:11:22:33:66:55")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)',
    ],
}

MAC_IPV4_PAY_SRC_IP = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.0", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2",frag=1)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.158", dst="192.168.0.2")/UDP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.255", dst="192.168.0.2")/TCP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.255", dst="192.168.0.2")/SCTP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.255", dst="192.168.0.2")/ICMP()/Raw(load="x"*30)'
        % vf1_mac,
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2",frag=1)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/UDP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/TCP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/SCTP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/ICMP()/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_PAY_DST_IP = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.0")/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.0",frag=1)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.158")/UDP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.255")/TCP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.255")/SCTP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.255")/ICMP()/Raw(load="x"*30)'
        % vf1_mac,
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.1.2")/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.1.2",frag=1)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.1.2")/UDP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.1.2")/TCP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.1.2")/SCTP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.1.2")/ICMP()/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_PAY_SRC_DST_IP = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.255", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.255", dst="192.168.0.2",frag=1)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.158", dst="192.168.255.2")/UDP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.0", dst="192.168.1.2")/TCP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.0", dst="192.168.1.2")/SCTP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.0", dst="192.168.1.2")/ICMP()/Raw(load="x"*30)'
        % vf1_mac,
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2",frag=1)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/UDP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/TCP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/SCTP()/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/ICMP()/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_PAY_SRC_DST_MAC_SRC_DST_IP = {
    "match": [
        'Ether(src="00:11:22:33:44:1b", dst="33:00:00:00:00:02")/IP(src="192.168.0.255", dst="192.168.0.2")/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:1b", dst="33:00:00:00:00:02")/IP(src="192.168.0.255", dst="192.168.0.2",frag=1)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:00", dst="33:00:00:00:00:03")/IP(src="192.168.0.158", dst="192.168.255.2")/UDP()/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:ff", dst="33:00:00:00:00:02")/IP(src="192.168.0.0", dst="192.168.1.2")/TCP()/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:ff", dst="33:00:00:00:00:02")/IP(src="192.168.0.0", dst="192.168.1.2")/SCTP()/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:ff", dst="33:00:00:00:00:02")/IP(src="192.168.0.0", dst="192.168.1.2")/ICMP()/Raw(load="x"*30)',
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:66:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2",frag=1)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:01")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP()/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.1.1", dst="192.168.0.2")/TCP()/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.3")/SCTP()/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.3")/ICMP()/Raw(load="x"*30)',
    ],
}

MAC_IPV4_TCP_SRC_MAC = {
    "match": [
        'Ether(src="00:11:22:33:44:54", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:57", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IPv6()/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_TCP_DST_MAC = {
    "match": [
        'Ether(src="00:02:00:00:00:01", dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)',
        'Ether(src="00:02:00:00:00:01", dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)',
    ],
    "unmatch": [
        'Ether(src="00:02:00:00:00:01", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:02:00:00:00:01", dst="00:11:22:33:66:55")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)',
    ],
}

MAC_IPV4_TCP_SRC_IP = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.0", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.3", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_TCP_DST_IP = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.14")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_TCP_SRC_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/TCP(sport=8012)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/TCP(sport=7985)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IPv6()/TCP(sport=8012)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/SCTP(sport=8012)/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_TCP_DST_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/TCP(dport=8012)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/TCP(dport=7985)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/UDP(dport=8012)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IPv6()/TCP(dport=8012)/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_TCP_SRC_DST_IP_SRC_DST_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.2", dst="192.168.255.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=7985,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=7985)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_TCP_SRC_DST_MAC_SRC_DST_IP_SRC_DST_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:66", dst="33:00:00:00:00:03")/IP(src="192.168.0.2", dst="192.168.255.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:66:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8010,dport=8017)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:01")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8010,dport=8017)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.1.1", dst="192.168.0.2")/TCP(sport=8010,dport=8017)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.3")/TCP(sport=8010,dport=8017)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=7985,dport=8017)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8010,dport=7985)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8010,dport=8017)/Raw(load="x"*30)',
    ],
}

MAC_IPV4_UDP_SRC_MAC = {
    "match": [
        'Ether(src="00:11:22:33:44:54", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:57", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IPv6()/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_UDP_DST_MAC = {
    "match": [
        'Ether(src="00:02:00:00:00:01", dst="00:11:22:33:44:55")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)',
        'Ether(src="00:02:00:00:00:01", dst="00:11:22:33:44:66")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)',
    ],
    "unmatch": [
        'Ether(src="00:02:00:00:00:01", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:02:00:00:00:01", dst="00:11:22:33:66:55")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)',
    ],
}

MAC_IPV4_UDP_SRC_IP = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.0", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.3", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_UDP_DST_IP = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.14")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_UDP_SRC_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/UDP(sport=8012)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/UDP(sport=7985)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IPv6()/UDP(sport=8012)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/SCTP(sport=8012)/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_UDP_DST_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/UDP(dport=8012)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/UDP(dport=7985)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/TCP(dport=8012)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IPv6()/UDP(dport=8012)/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_UDP_SRC_DST_IP_SRC_DST_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.2", dst="192.168.255.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=7985,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=7985)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_UDP_SRC_DST_MAC_SRC_DST_IP_SRC_DST_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:66", dst="33:00:00:00:00:02")/IP(src="192.168.0.2", dst="192.168.255.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:66:55", dst="33:00:00:00:00:03")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8010,dport=8017)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:01")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8010,dport=8017)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.1.1", dst="192.168.0.2")/UDP(sport=8010,dport=8017)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.3")/UDP(sport=8010,dport=8017)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=7985,dport=8017)/Raw(load="x"*30)',
        'Ether(src="00:11:22:33:44:55", dst="33:00:00:00:00:02")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8010,dport=7985)/Raw(load="x"*30)',
    ],
}

MAC_IPV4_SCTP_SRC_MAC = {
    "match": [
        'Ether(src="00:11:22:33:44:54", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:57", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IPv6()/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_SCTP_DST_MAC = {
    "match": [
        'Ether(src="00:02:00:00:00:01", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:02:00:00:00:01", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
}

MAC_IPV4_SCTP_SRC_IP = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.0", dst="192.168.0.2")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.3", dst="192.168.0.2")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_SCTP_DST_IP = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.14")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_SCTP_SRC_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/SCTP(sport=8012)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/SCTP(sport=7985)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IPv6()/SCTP(sport=8012)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/UDP(sport=8012)/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_SCTP_DST_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/SCTP(dport=8012)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/SCTP(dport=7985)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP()/UDP(dport=8012)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IPv6()/SCTP(dport=8012)/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_SCTP_SRC_DST_IP_SRC_DST_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.2", dst="192.168.255.2")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=7985,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=8012,dport=7985)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

MAC_IPV4_SCTP_SRC_DST_MAC_SRC_DST_IP_SRC_DST_PORT = {
    "match": [
        'Ether(src="00:11:22:33:44:66", dst="%s")/IP(src="192.168.0.2", dst="192.168.255.2")/SCTP(sport=8012,dport=8018)/Raw(load="x"*30)'
        % vf1_mac,
    ],
    "unmatch": [
        'Ether(src="00:11:22:33:66:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=8010,dport=8017)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.2")/SCTP(sport=8010,dport=8017)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/SCTP(sport=8010,dport=8017)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=7985,dport=8017)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=8010,dport=7985)/Raw(load="x"*30)'
        % vf1_mac,
        'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=8010,dport=8017)/Raw(load="x"*30)'
        % vf1_mac,
    ],
}

# test vectors

tv_mac_ipv4_pay_src_mac = {
    "name": "test_mac_ipv4_pay_src_mac",
    "rules": "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask 00:ff:ff:ff:ff:ff / ipv4 / end actions drop / end",
    "scapy_str": MAC_IPV4_PAY_SRC_MAC,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_pay_dst_mac = {
    "name": "test_mac_ipv4_pay_dst_mac",
    "rules": [
        "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 00:11:22:33:44:66 / ipv4 / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 00:11:22:33:66:55 / ipv4 / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / end actions drop / end",
    ],
    "scapy_str": MAC_IPV4_PAY_DST_MAC,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_pay_src_ip = {
    "name": "test_mac_ipv4_pay_src_ip",
    "rules": "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 / end actions drop / end",
    "scapy_str": MAC_IPV4_PAY_SRC_IP,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_pay_dst_ip = {
    "name": "test_mac_ipv4_pay_dst_ip",
    "rules": "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.0 / end actions drop / end",
    "scapy_str": MAC_IPV4_PAY_DST_IP,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_pay_src_dst_ip = {
    "name": "test_mac_ipv4_pay_src_dst_ip",
    "rules": "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / end actions drop / end",
    "scapy_str": MAC_IPV4_PAY_SRC_DST_IP,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_pay_src_dst_mac_src_dst_ip = {
    "name": "test_mac_ipv4_pay_src_dst_mac_src_dst_ip",
    "rules": [
        "flow create 0 ingress pattern eth dst is 33:00:00:00:00:01 / ipv4 / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 33:00:00:00:00:02 / ipv4 / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 33:00:00:00:00:03 / ipv4 / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 33:00:00:00:00:02 dst mask ff:ff:ff:ff:ff:fe / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / end actions drop / end",
    ],
    "scapy_str": MAC_IPV4_PAY_SRC_DST_MAC_SRC_DST_IP,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_tcp_src_mac = {
    "name": "test_mac_ipv4_tcp_src_mac",
    "rules": "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:fe / ipv4 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP_SRC_MAC,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_tcp_dst_mac = {
    "name": "test_mac_ipv4_tcp_dst_mac",
    "rules": [
        "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / tcp / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 00:11:22:33:44:66 / ipv4 / tcp / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 00:11:22:33:66:55 / ipv4 / tcp / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / tcp / end actions drop / end",
    ],
    "scapy_str": MAC_IPV4_TCP_DST_MAC,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_tcp_src_ip = {
    "name": "test_mac_ipv4_tcp_src_ip",
    "rules": "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP_SRC_IP,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_tcp_dst_ip = {
    "name": "test_mac_ipv4_tcp_dst_ip",
    "rules": "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.243 / tcp / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP_DST_IP,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_tcp_src_port = {
    "name": "test_mac_ipv4_tcp_src_port",
    "rules": "flow create 0 priority 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP_SRC_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_tcp_dst_port = {
    "name": "test_mac_ipv4_tcp_dst_port",
    "rules": "flow create 0 priority 0 ingress pattern eth / ipv4 / tcp dst spec 8010 dst mask 65520 / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP_DST_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_tcp_src_dst_ip_src_dst_port = {
    "name": "test_mac_ipv4_tcp_src_dst_ip_src_dst_port",
    "rules": "flow create 0 priority 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
    "scapy_str": MAC_IPV4_TCP_SRC_DST_IP_SRC_DST_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_tcp_src_dst_mac_src_dst_ip_src_dst_port = {
    "name": "test_mac_ipv4_tcp_src_dst_mac_src_dst_ip_src_dst_port",
    "rules": [
        "flow create 0 ingress pattern eth dst is 33:00:00:00:00:01 / ipv4 / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 33:00:00:00:00:02 / ipv4 / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 33:00:00:00:00:03 / ipv4 / end actions vf id 1 / end",
        "flow create 0 priority 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 33:00:00:00:00:02 dst mask ff:ff:ff:ff:ff:fe / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
    ],
    "scapy_str": MAC_IPV4_TCP_SRC_DST_MAC_SRC_DST_IP_SRC_DST_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_udp_src_mac = {
    "name": "test_mac_ipv4_udp_src_mac",
    "rules": "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:fe / ipv4 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP_SRC_MAC,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_udp_dst_mac = {
    "name": "test_mac_ipv4_udp_dst_mac",
    "rules": [
        "flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 / udp / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 00:11:22:33:44:66 / ipv4 / udp / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 00:11:22:33:66:55 / ipv4 / udp / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst spec 00:11:22:33:44:55 dst mask ff:ff:ff:ff:ff:00 / ipv4 / udp / end actions drop / end",
    ],
    "scapy_str": MAC_IPV4_UDP_DST_MAC,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_udp_src_ip = {
    "name": "test_mac_ipv4_udp_src_ip",
    "rules": "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP_SRC_IP,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_udp_dst_ip = {
    "name": "test_mac_ipv4_udp_dst_ip",
    "rules": "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.243 / udp / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP_DST_IP,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_udp_src_port = {
    "name": "test_mac_ipv4_udp_src_port",
    "rules": "flow create 0 priority 0 ingress pattern eth / ipv4 / udp src spec 8010 src mask 65520 / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP_SRC_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_udp_dst_port = {
    "name": "test_mac_ipv4_udp_dst_port",
    "rules": "flow create 0 priority 0 ingress pattern eth / ipv4 / udp dst spec 8010 dst mask 65520 / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP_DST_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_udp_src_dst_ip_src_dst_port = {
    "name": "test_mac_ipv4_udp_src_dst_ip_src_dst_port",
    "rules": "flow create 0 priority 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / udp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
    "scapy_str": MAC_IPV4_UDP_SRC_DST_IP_SRC_DST_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_udp_src_dst_mac_src_dst_ip_src_dst_port = {
    "name": "test_mac_ipv4_udp_src_dst_mac_src_dst_ip_src_dst_port",
    "rules": [
        "flow create 0 ingress pattern eth dst is 33:00:00:00:00:01 / ipv4 / udp / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 33:00:00:00:00:02 / ipv4 / udp / end actions vf id 1 / end",
        "flow create 0 ingress pattern eth dst is 33:00:00:00:00:03 / ipv4 / udp / end actions vf id 1 / end",
        "flow create 0 priority 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 33:00:00:00:00:03 dst mask ff:ff:ff:ff:ff:fe / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / udp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
    ],
    "scapy_str": MAC_IPV4_UDP_SRC_DST_MAC_SRC_DST_IP_SRC_DST_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_sctp_src_mac = {
    "name": "test_mac_ipv4_sctp_src_mac",
    "rules": "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:fe / ipv4 / sctp / end actions drop / end",
    "scapy_str": MAC_IPV4_SCTP_SRC_MAC,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_sctp_dst_mac = {
    "name": "test_mac_ipv4_sctp_dst_mac",
    "rules": [
        "flow create 0 ingress pattern eth dst spec %s dst mask ff:ff:ff:ff:ff:00 / ipv4 / sctp / end actions drop / end"
        % vf1_mac
    ],
    "scapy_str": MAC_IPV4_SCTP_DST_MAC,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_sctp_src_ip = {
    "name": "test_mac_ipv4_sctp_src_ip",
    "rules": "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / sctp / end actions drop / end",
    "scapy_str": MAC_IPV4_SCTP_SRC_IP,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_sctp_dst_ip = {
    "name": "test_mac_ipv4_sctp_dst_ip",
    "rules": "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.243 / sctp / end actions drop / end",
    "scapy_str": MAC_IPV4_SCTP_DST_IP,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_sctp_src_port = {
    "name": "test_mac_ipv4_sctp_src_port",
    "rules": "flow create 0 priority 0 ingress pattern eth / ipv4 / sctp src spec 8010 src mask 65520 / end actions drop / end",
    "scapy_str": MAC_IPV4_SCTP_SRC_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_sctp_dst_port = {
    "name": "test_mac_ipv4_sctp_dst_port",
    "rules": "flow create 0 priority 0 ingress pattern eth / ipv4 / sctp dst spec 8010 dst mask 65520 / end actions drop / end",
    "scapy_str": MAC_IPV4_SCTP_DST_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_sctp_src_dst_ip_src_dst_port = {
    "name": "test_mac_ipv4_sctp_src_dst_ip_src_dst_port",
    "rules": "flow create 0 priority 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / sctp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
    "scapy_str": MAC_IPV4_SCTP_SRC_DST_IP_SRC_DST_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}

tv_mac_ipv4_sctp_src_dst_mac_src_dst_ip_src_dst_port = {
    "name": "test_mac_ipv4_sctp_src_dst_mac_src_dst_ip_src_dst_port",
    "rules": [
        "flow create 0 priority 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec %s dst mask ff:ff:ff:ff:ff:fe / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / sctp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end"
        % vf1_mac
    ],
    "scapy_str": MAC_IPV4_SCTP_SRC_DST_MAC_SRC_DST_IP_SRC_DST_PORT,
    "check_param": {"port_id": 1, "drop": 1},
}


vectors_ipv4_pay_4ports = [
    tv_mac_ipv4_pay_src_ip,
    tv_mac_ipv4_pay_dst_ip,
    tv_mac_ipv4_pay_src_dst_ip,
]

vectors_ipv4_pay_2ports = [
    tv_mac_ipv4_pay_src_mac,
    tv_mac_ipv4_pay_dst_mac,
    tv_mac_ipv4_pay_src_ip,
    tv_mac_ipv4_pay_dst_ip,
    tv_mac_ipv4_pay_src_dst_mac_src_dst_ip,
]

vectors_ipv4_tcp_4ports = [
    tv_mac_ipv4_tcp_src_ip,
    tv_mac_ipv4_tcp_dst_ip,
    tv_mac_ipv4_tcp_src_port,
    tv_mac_ipv4_tcp_dst_port,
    tv_mac_ipv4_tcp_src_dst_ip_src_dst_port,
]

vectors_ipv4_tcp_2ports = [
    tv_mac_ipv4_tcp_src_mac,
    tv_mac_ipv4_tcp_dst_mac,
    tv_mac_ipv4_tcp_src_ip,
    tv_mac_ipv4_tcp_dst_ip,
    tv_mac_ipv4_tcp_src_port,
    tv_mac_ipv4_tcp_dst_port,
    tv_mac_ipv4_tcp_src_dst_mac_src_dst_ip_src_dst_port,
]

vectors_ipv4_udp_4ports = [
    tv_mac_ipv4_udp_src_ip,
    tv_mac_ipv4_udp_dst_ip,
    tv_mac_ipv4_udp_src_port,
    tv_mac_ipv4_udp_dst_port,
    tv_mac_ipv4_udp_src_dst_ip_src_dst_port,
]

vectors_ipv4_udp_2ports = [
    tv_mac_ipv4_udp_src_mac,
    tv_mac_ipv4_udp_dst_mac,
    tv_mac_ipv4_udp_src_ip,
    tv_mac_ipv4_udp_dst_ip,
    tv_mac_ipv4_udp_src_port,
    tv_mac_ipv4_udp_dst_port,
    tv_mac_ipv4_udp_src_dst_mac_src_dst_ip_src_dst_port,
]

vectors_ipv4_sctp_4ports = [
    tv_mac_ipv4_sctp_src_ip,
    tv_mac_ipv4_sctp_dst_ip,
    tv_mac_ipv4_sctp_src_port,
    tv_mac_ipv4_sctp_dst_port,
    tv_mac_ipv4_sctp_src_dst_ip_src_dst_port,
]

vectors_ipv4_sctp_2ports = [
    tv_mac_ipv4_sctp_src_mac,
    tv_mac_ipv4_sctp_dst_mac,
    tv_mac_ipv4_sctp_src_ip,
    tv_mac_ipv4_sctp_dst_ip,
    tv_mac_ipv4_sctp_src_port,
    tv_mac_ipv4_sctp_dst_port,
    tv_mac_ipv4_sctp_src_dst_mac_src_dst_ip_src_dst_port,
]


class CVLDCFACLFilterTest(TestCase):
    def bind_nics_driver(self, ports, driver=""):
        # modprobe vfio driver
        if driver == "vfio-pci":
            for port in ports:
                netdev = self.dut.ports_info[port]["port"]
                driver = netdev.get_nic_driver()
                if driver != "vfio-pci":
                    netdev.bind_driver(driver="vfio-pci")

        elif driver == "igb_uio":
            # igb_uio should insmod as default, no need to check
            for port in ports:
                netdev = self.dut.ports_info[port]["port"]
                driver = netdev.get_nic_driver()
                if driver != "igb_uio":
                    netdev.bind_driver(driver="igb_uio")
        else:
            for port in ports:
                netdev = self.dut.ports_info[port]["port"]
                driver_now = netdev.get_nic_driver()
                if driver == "":
                    driver = netdev.default_driver
                if driver != driver_now:
                    netdev.bind_driver(driver=driver)

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(
            self.nic in ["columbiaville_25g", "columbiaville_100g"], "nic is not CVL"
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        localPort0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_iface0 = self.tester.get_interface(localPort0)
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.pf1_intf = self.dut.ports_info[self.dut_ports[1]]["intf"]
        self.dut.send_expect("ifconfig %s up" % self.tester_iface0, "# ")
        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.testpmd_status = "close"
        # bind pf to kernel
        self.bind_nics_driver(self.dut_ports, driver="ice")
        # set vf driver
        self.vf_driver = "vfio-pci"
        self.dut.send_expect("modprobe uio", "# ")
        self.path = self.dut.apps_name["test-pmd"]
        self.setup_1pf_vfs_env()
        self.dut.send_expect("ifconfig %s up" % self.tester_iface0, "# ", 15)

        self.src_file_dir = "dep/"
        self.dut_file_dir = "/tmp/"

    def setup_1pf_vfs_env(self, pf_port=0, driver="default"):

        self.used_dut_port_0 = self.dut_ports[pf_port]
        # get PF interface name
        out = self.dut.send_expect("ethtool -i %s" % self.pf0_intf, "#")
        # generate 4 VFs on PF
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 4, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        self.vf0_pci = self.sriov_vfs_port_0[0].pci
        self.vf1_pci = self.sriov_vfs_port_0[1].pci
        # set VF0 as trust
        self.dut.send_expect("ip link set %s vf 0 trust on" % self.pf0_intf, "#")
        # set VF1 mac address
        self.dut.send_expect(
            "ip link set %s vf 1 mac %s" % (self.pf0_intf, vf1_mac), "# "
        )
        # bind VFs to dpdk driver
        for port in self.sriov_vfs_port_0:
            port.bind_driver(self.vf_driver)
        time.sleep(15)

    def set_up(self):
        """
        Run before each test case.
        """

    def create_testpmd_command(self, param):
        """
        Create testpmd command
        """
        # Prepare testpmd EAL and parameters
        all_eal_param = self.dut.create_eal_parameters(
            cores="1S/4C/1T",
            ports=[self.vf0_pci, self.vf1_pci],
            port_options={self.vf0_pci: "cap=dcf"},
        )
        command = self.path + all_eal_param + "--log-level='ice,7'" + " -- -i" + param
        return command

    def launch_testpmd(self, param=""):
        """
        launch testpmd with the command
        """
        time.sleep(5)
        command = self.create_testpmd_command(param)
        out = self.dut.send_expect(command, "testpmd> ", 20)
        self.testpmd_status = "running"
        self.dut.send_expect("set portlist 1", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)
        self.pmd_output.execute_cmd("start")
        return out

    def send_packets(self, packets):
        self.pkt.update_pkt(packets)
        tx_port = self.tester_iface0
        self.pkt.send_pkt(crb=self.tester, tx_port=tx_port)

    def send_pkts_getouput(self, pkts):
        """
        if pkt_info is True, we need to get packet infomation to check the RSS hash and FDIR.
        if pkt_info is False, we just need to get the packet number and queue number.
        """
        self.send_packets(pkts)
        time.sleep(1)
        out_info = self.dut.get_session_output(timeout=1)
        out_pkt = self.pmd_output.execute_cmd("stop", timeout=15)
        out = out_info + out_pkt
        self.pmd_output.execute_cmd("start")
        return out

    def create_acl_filter_rule(self, rules, session_name="", check_stats=True):
        """
        create acl filter rules
        """
        if session_name == "":
            session_name = self.dut
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        acl_rule = "Succeeded to create (4) flow"
        if isinstance(rules, list):
            for rule in rules:
                out = session_name.send_expect(rule, "testpmd> ")
                if acl_rule in out:
                    m = p.search(out)
                    if m:
                        rule_list.append(m.group(1))
                    else:
                        rule_list.append(False)
        else:
            out = session_name.send_expect(rules, "testpmd> ")
            if acl_rule in out:
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)

        if check_stats:
            self.verify(
                all(rule_list),
                "some rules not created successfully, result %s, rule %s"
                % (rule_list, rules),
            )
        else:
            self.verify(
                not any(rule_list),
                "all rules should create failed, result %s" % rule_list,
            )
        return rule_list

    def create_other_filter_rule(self, rules, session_name="", check_stats=True):
        """
        create switch or fdir filter rules
        """
        if session_name == "":
            session_name = self.dut
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        if isinstance(rules, list):
            for rule in rules:
                out = session_name.send_expect(rule, "testpmd> ")
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)

        else:
            out = session_name.send_expect(rules, "testpmd> ")
            m = p.search(out)
            if m:
                rule_list.append(m.group(1))
            else:
                rule_list.append(False)
        if check_stats:
            self.verify(
                all(rule_list),
                "some rules not created successfully, result %s, rule %s"
                % (rule_list, rules),
            )
        else:
            self.verify(
                not any(rule_list),
                "all rules should create failed, result %s" % rule_list,
            )
        return rule_list

    def check_filter_rule_list(
        self, port_id, rule_list, session_name="", need_verify=True
    ):
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
            self.verify(
                result == rule_list,
                "the rule list is not the same. expect %s, result %s"
                % (rule_list, result),
            )
        else:
            return result

    def destroy_acl_filter_rule(
        self, port_id, rule_list, session_name="", need_verify=True
    ):
        if session_name == "":
            session_name = self.dut
        p = re.compile(r"Flow rule #(\d+) destroyed")
        destroy_list = []
        if isinstance(rule_list, list):
            for i in rule_list:
                out = session_name.send_expect(
                    "flow destroy %s rule %s" % (port_id, i), "testpmd> ", 15
                )
                m = p.search(out)
                if m:
                    destroy_list.append(m.group(1))
                else:
                    destroy_list.append(False)
        else:
            out = session_name.send_expect(
                "flow destroy %s rule %s" % (port_id, rule_list), "testpmd> ", 15
            )
            m = p.search(out)
            if m:
                destroy_list.append(m.group(1))
            else:
                destroy_list.append(False)
            rule_list = [rule_list]
        if need_verify:
            self.verify(
                destroy_list == rule_list,
                "flow rule destroy failed, expect %s result %s"
                % (rule_list, destroy_list),
            )
        else:
            return destroy_list

    def common_process(self, vectors, launch_testpmd=True):

        if launch_testpmd:
            # launch testpmd
            self.launch_testpmd()

        test_results = {}
        for test_vector in vectors:
            try:
                self.dut.send_expect("flow flush 0", "testpmd> ", 120)

                # create a rule
                rule_list = self.create_acl_filter_rule(test_vector["rules"])
                # send and check match packets
                out1 = self.send_pkts_getouput(pkts=test_vector["scapy_str"]["match"])
                rfc.check_drop(
                    out1,
                    pkt_num=len(test_vector["scapy_str"]["match"]),
                    check_param=test_vector["check_param"],
                )
                # send and check mismatch packets
                out2 = self.send_pkts_getouput(pkts=test_vector["scapy_str"]["unmatch"])
                rfc.check_drop(
                    out2,
                    pkt_num=len(test_vector["scapy_str"]["unmatch"]),
                    check_param=test_vector["check_param"],
                    stats=False,
                )
                # destroy rule
                self.destroy_acl_filter_rule(0, rule_list)
                # send matched packets and check
                out3 = self.send_pkts_getouput(pkts=test_vector["scapy_str"]["match"])
                rfc.check_drop(
                    out3,
                    pkt_num=len(test_vector["scapy_str"]["match"]),
                    check_param=test_vector["check_param"],
                    stats=False,
                )
                test_results[test_vector["name"]] = True
                print((GREEN("case passed: %s" % test_vector["name"])))
            except Exception as e:
                print((RED(e)))
                test_results[test_vector["name"]] = False
                continue
        failed_cases = []
        for k, v in list(test_results.items()):
            if not v:
                failed_cases.append(k)
        self.verify(all(test_results.values()), "{} failed.".format(failed_cases))

    def test_mac_ipv4(self):
        if self.nic == "columbiaville_25g":
            self.common_process(vectors_ipv4_pay_4ports)
        else:
            self.common_process(vectors_ipv4_pay_2ports)

    def test_mac_ipv4_tcp(self):
        if self.nic == "columbiaville_25g":
            self.common_process(vectors_ipv4_tcp_4ports)
        else:
            self.common_process(vectors_ipv4_tcp_2ports)

    def test_mac_ipv4_udp(self):
        if self.nic == "columbiaville_25g":
            self.common_process(vectors_ipv4_udp_4ports)
        else:
            self.common_process(vectors_ipv4_udp_2ports)

    def test_mac_ipv4_sctp(self):
        if self.nic == "columbiaville_25g":
            self.common_process(vectors_ipv4_sctp_4ports)
        else:
            self.common_process(vectors_ipv4_sctp_2ports)

    def test_negative(self):
        """
        negative cases
        """
        out_testpmd = self.launch_testpmd()
        self.check_dcf_status(out_testpmd, stats=True)
        rules = {
            "inconsistent spec and mask": [
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 dst mask 255.255.255.0 / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 dst mask 65520 / end actions drop / end",
            ],
            "only spec/mask": [
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 src mask 255.255.255.0 / end actions drop / end",
                "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 / ipv4 / tcp / end actions drop / end",
                "flow create 0 ingress pattern eth src mask ff:ff:ff:ff:ff:00 / ipv4 / tcp / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 / tcp src mask 65520 / end actions drop / end",
            ],
            "all 0 mask": [
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 0.0.0.0 / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 / tcp dst spec 8010 dst mask 0 / end actions drop / end",
                "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask 00:00:00:00:00:00 / ipv4 / tcp / end actions drop / end",
            ],
            "acl rules": [
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 0.0.0.0 / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 0 / end actions drop / end",
                "flow create 0 ingress pattern eth src spec 00:11:22:33:44:55 src mask ff:ff:ff:ff:ff:00 dst spec 00:11:22:33:44:55 dst mask 00:00:00:00:00:00 / ipv4 / tcp / end actions drop / end",
            ],
            "full mask": [
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.255 dst spec 192.168.0.2 dst mask 255.255.255.255 / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.255 dst spec 192.168.1.2 dst mask 255.255.255.255 / tcp src spec 8010 src mask 65535 dst spec 8017 dst mask 65535 / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.2.1 src mask 255.255.255.255 dst spec 192.168.2.2 dst mask 255.255.255.0 / udp src spec 8010 src mask 65520 dst spec 8017 dst mask 65535 / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.2.1 src mask 255.255.255.255 dst spec 192.168.2.2 dst mask 255.255.255.255 / sctp src spec 8012 src mask 65535 dst spec 8018 dst mask 65535 / end actions drop / end",
            ],
        }
        # all the rules failed to be created
        self.create_acl_filter_rule(rules["only spec/mask"], check_stats=False)
        self.check_filter_rule_list(0, [])
        self.create_acl_filter_rule(rules["all 0 mask"], check_stats=False)
        self.check_filter_rule_list(0, [])
        # full mask rules are created as switch rules
        self.create_acl_filter_rule(rules["full mask"], check_stats=False)
        self.dut.send_expect("flow flush 0", "testpmd> ", 15)
        # inconsistent spec and mask rules
        rule_list1 = self.create_acl_filter_rule(
            rules["inconsistent spec and mask"], check_stats=True
        )
        self.check_filter_rule_list(0, rule_list1)
        packet1 = [
            'Ether(dst="%s")/IP(src="192.168.1.1",dst="0.0.0.0")/("X"*480)' % vf1_mac,
            'Ether(dst="%s")/IP(src="192.168.0.1",dst="192.168.0.2")/TCP(sport=22,dport=0)/("X"*480)'
            % vf1_mac,
        ]
        out1 = self.send_pkts_getouput(pkts=packet1)
        rfc.check_drop(
            out1, pkt_num=2, check_param={"port_id": 1, "drop": 1}, stats=True
        )
        self.dut.send_expect("flow flush 0", "testpmd> ", 15)
        # acl rules combined "0" mask and not "0" mask
        rule_list2 = self.create_acl_filter_rule(rules["acl rules"], check_stats=True)
        self.check_filter_rule_list(0, rule_list2)
        packet2 = [
            'Ether(dst="%s")/IP(src="192.168.0.1",dst="192.168.1.2")/("X"*480)'
            % vf1_mac,
            'Ether(dst="%s")/IP(src="192.168.1.1",dst="192.168.0.2")/TCP(sport=8012,dport=23)/("X"*480)'
            % vf1_mac,
            'Ether(src="00:11:22:33:44:55",dst="%s")/IP(src="192.168.1.1",dst="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)'
            % vf1_mac,
        ]
        out2 = self.send_pkts_getouput(pkts=packet2)
        rfc.check_drop(
            out2, pkt_num=3, check_param={"port_id": 1, "drop": 1}, stats=True
        )

    def test_max_entry_num_combined_pattern(self):
        """
        the max ACL entry number combined two patterns.
        """
        src_file = "max_entry_num"
        flows = open(self.src_file_dir + src_file, mode="w")
        count = 0
        for i in range(32):
            flows.write(
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.%d src mask 255.255.0.255 / end actions drop / end \n"
                % i
            )
            count = count + 1
        for i in range(128):
            flows.write(
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.%d src mask 255.255.254.255 / tcp / end actions drop / end \n"
                % i
            )
            count = count + 1
        flows.close()
        self.verify(count == 160, "failed to config 160 acl rules.")
        self.dut.session.copy_file_to(self.src_file_dir + src_file, self.dut_file_dir)

        # start testpmd with creating 512 ACL rules
        param = " --cmdline-file=%s" % (self.dut_file_dir + src_file)
        out_testpmd = self.launch_testpmd(param)
        self.check_dcf_status(out_testpmd, stats=True)
        rule_list = self.dut.send_expect("flow list 0", "testpmd> ", 15)
        self.verify("159" in rule_list, "160 rules failed to be created")

        # create one more ACl rule failed, it is created as a switch rule.
        rule = "flow create 0 ingress pattern eth / ipv4 src spec 192.168.2.255 src mask 255.255.254.255 / tcp / end actions drop / end"
        self.create_acl_filter_rule(rule, check_stats=False)

        # delete one ACL rule, create the rule again, it is created as an ACL rule successfully.
        self.dut.send_expect("flow destroy 0 rule 159", "testpmd> ", 15)
        rule_list = self.dut.send_expect("flow list 0", "testpmd> ", 15)
        self.verify("159" not in rule_list, "rule 159 is not deleted")
        self.create_acl_filter_rule(rule, check_stats=True)
        # delete the switch rule
        self.dut.send_expect("flow destroy 0 rule 160", "testpmd> ", 15)
        # send and check match packets
        packet = (
            'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.2.255", dst="192.168.0.2")/TCP(sport=22, dport=23)/Raw(load="x"*30)'
            % vf1_mac
        )
        out1 = self.send_pkts_getouput(pkts=packet)
        rfc.check_drop(
            out1, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=True
        )

        # delete all rules, send and check match packets
        self.dut.send_expect("flow flush 0", "testpmd> ", 15)
        out1 = self.send_pkts_getouput(pkts=packet)
        rfc.check_drop(
            out1, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=False
        )

    def test_max_entry_num(self):
        """
        the default entry number is 256
        """
        src_file = "max_entry_num"
        flows = open(self.src_file_dir + src_file, mode="w")
        count = 0
        for i in range(255):
            flows.write(
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.%d src mask 255.255.254.255 / tcp / end actions drop / end \n"
                % i
            )
            count = count + 1
        flows.close()
        self.verify(count == 255, "failed to config 255 acl rules.")
        self.dut.session.copy_file_to(self.src_file_dir + src_file, self.dut_file_dir)

        # start testpmd with creating 255 ACL rules
        param = " --cmdline-file=%s" % (self.dut_file_dir + src_file)
        out_testpmd = self.launch_testpmd(param)
        self.check_dcf_status(out_testpmd, stats=True)
        rule_list = self.dut.send_expect("flow list 0", "testpmd> ", 15)
        self.verify("254" in rule_list, "255 rules failed to be created")

        # create a switch rule
        rule = "flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.255 src mask 255.255.255.255 / tcp / end actions drop / end"
        self.create_other_filter_rule(rule, check_stats=True)

        # create the 256 ACl rule
        rule1 = "flow create 0 ingress pattern eth / ipv4 src spec 192.168.2.255 src mask 255.0.255.255 / tcp / end actions drop / end"
        self.create_acl_filter_rule(rule1, check_stats=True)
        rule_list = self.dut.send_expect("flow list 0", "testpmd> ", 15)
        self.verify("256" in rule_list, "the last ACL rule failed to be created")

        # send and check match packets
        packet1 = (
            'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.2.255", dst="192.168.0.2")/TCP(sport=22, dport=23)/Raw(load="x"*30)'
            % vf1_mac
        )
        out1 = self.send_pkts_getouput(pkts=packet1)
        rfc.check_drop(
            out1, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=True
        )

        # create one more ACl rule
        rule2 = "flow create 0 ingress pattern eth / ipv4 src spec 192.168.3.255 src mask 255.255.255.254 / tcp / end actions drop / end"
        self.create_acl_filter_rule(rule2, check_stats=False)
        # send and check match packets
        packet2 = (
            'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.3.255", dst="192.168.0.2")/TCP(sport=22, dport=23)/Raw(load="x"*30)'
            % vf1_mac
        )
        out2 = self.send_pkts_getouput(pkts=packet2)
        rfc.check_drop(
            out2, pkt_num=0, check_param={"port_id": 1, "drop": 1}, stats=False
        )

        # delete one rule, create the rule again, successfully.
        self.dut.send_expect("flow destroy 0 rule 256", "testpmd> ", 15)
        self.dut.send_expect("flow destroy 0 rule 257", "testpmd> ", 15)
        rule_list = self.dut.send_expect("flow list 0", "testpmd> ", 15)
        self.verify("256" not in rule_list, "rule 256 is not deleted")
        self.verify("257" not in rule_list, "rule 257 is not deleted")
        self.create_acl_filter_rule(rule2, check_stats=True)
        # send and check match packets
        out3 = self.send_pkts_getouput(pkts=packet2)
        rfc.check_drop(
            out3, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=True
        )

        # delete all rules, send and check match packets
        self.dut.send_expect("flow flush 0", "testpmd> ", 15)
        out4 = self.send_pkts_getouput(pkts=packet2)
        rfc.check_drop(
            out4, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=False
        )

    def test_max_entry_num_ipv4_other(self):
        """
        create ipv4-other rules, 64 rules can be created at most.
        """
        src_file = "max_entry_num_ipv4_other"
        flows = open(self.src_file_dir + src_file, mode="w")
        count = 0
        for i in range(63):
            flows.write(
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.254.255 dst spec 192.168.0.%d dst mask 255.255.254.255 / end actions drop / end \n"
                % i
            )
            count = count + 1
        flows.close()
        self.verify(count == 63, "failed to config 63 acl rules.")
        self.dut.session.copy_file_to(self.src_file_dir + src_file, self.dut_file_dir)

        # start testpmd with creating 64 ACL rules
        param = " --cmdline-file=%s" % (self.dut_file_dir + src_file)
        out_testpmd = self.launch_testpmd(param)
        self.check_dcf_status(out_testpmd, stats=True)
        rule_list = self.dut.send_expect("flow list 0", "testpmd> ", 15)
        self.verify("62" in rule_list, "63 rules failed to be created")

        # create one switch rule
        rule = "flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.254 dst spec 192.168.2.100 dst mask 255.255.255.255 / end actions drop / end"
        self.create_other_filter_rule(rule, check_stats=True)

        # create the 64th ACl rule
        rule1 = "flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.254 dst spec 192.168.0.127 dst mask 255.255.254.255 / end actions drop / end"
        self.create_acl_filter_rule(rule1, check_stats=True)

        # create one more ACl rule
        rule2 = "flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.254 dst spec 192.168.1.128 dst mask 255.255.254.255 / end actions drop / end"
        self.create_acl_filter_rule(rule2, check_stats=False)

        # delete one rule, create the rule again, successfully.
        self.dut.send_expect("flow destroy 0 rule 64", "testpmd> ", 15)
        rule_list = self.dut.send_expect("flow list 0", "testpmd> ", 15)
        self.verify("64" not in rule_list, "rule 64 is not deleted")
        self.create_acl_filter_rule(rule2, check_stats=True)
        # delete switch rule
        self.dut.send_expect("flow destroy 0 rule 65", "testpmd> ", 15)
        rule_list = self.dut.send_expect("flow list 0", "testpmd> ", 15)
        self.verify("65" not in rule_list, "rule 65 is not deleted")

        # send and check match packets
        packet = (
            'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.1.128")/Raw(load="x"*30)'
            % vf1_mac
        )
        out1 = self.send_pkts_getouput(pkts=packet)
        rfc.check_drop(
            out1, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=True
        )

        # delete all rules, send and check match packets
        self.dut.send_expect("flow flush 0", "testpmd> ", 60)
        out1 = self.send_pkts_getouput(pkts=packet)
        rfc.check_drop(
            out1, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=False
        )

    def test_multirules_diff_pattern_inputset(self):
        """
        create rules with different patterns or inputset step by step.
        """
        out_testpmd = self.launch_testpmd()
        self.check_dcf_status(out_testpmd, stats=True)
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.0.255 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.1.1 src mask 255.255.255.0 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.1 dst mask 255.255.255.0 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.2.3 src mask 255.255.0.255 / udp / end actions drop / end",
        ]
        packets = [
            'Ether(dst="%s")/IP(src="192.168.0.3", dst="192.168.0.2")/Raw(load="x"*30)'
            % vf1_mac,
            'Ether(dst="%s")/IP(src="192.168.3.1", dst="192.168.0.2")/Raw(load="x"*30)'
            % vf1_mac,
            'Ether(dst="%s")/IP(src="192.168.1.3", dst="192.168.0.2")/Raw(load="x"*30)'
            % vf1_mac,
            'Ether(dst="%s")/IP(src="192.168.3.3", dst="192.168.0.2")/Raw(load="x"*30)'
            % vf1_mac,
            'Ether(dst="%s")/IP(src="192.168.3.3", dst="192.168.1.2")/UDP(sport=8012, dport=8018)/Raw(load="x"*30)'
            % vf1_mac,
        ]

        self.create_acl_filter_rule(rules[0], check_stats=True)
        out_drop = self.send_pkts_getouput(pkts=packets[0])
        rfc.check_drop(
            out_drop, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=True
        )
        out_receive = self.send_pkts_getouput(pkts=packets[1:5])
        rfc.check_drop(
            out_receive, pkt_num=4, check_param={"port_id": 1, "drop": 1}, stats=False
        )

        # same input set field, same spec, different mask.
        self.create_acl_filter_rule(rules[1], check_stats=True)
        out_drop = self.send_pkts_getouput(pkts=packets[0:2])
        rfc.check_drop(
            out_drop, pkt_num=2, check_param={"port_id": 1, "drop": 1}, stats=True
        )
        out_receive = self.send_pkts_getouput(pkts=packets[2:5])
        rfc.check_drop(
            out_receive, pkt_num=3, check_param={"port_id": 1, "drop": 1}, stats=False
        )

        # same input set field, different spec, same mask.
        self.create_acl_filter_rule(rules[2], check_stats=True)
        out_drop = self.send_pkts_getouput(pkts=packets[0:3])
        rfc.check_drop(
            out_drop, pkt_num=3, check_param={"port_id": 1, "drop": 1}, stats=True
        )
        out_receive = self.send_pkts_getouput(pkts=packets[3:5])
        rfc.check_drop(
            out_receive, pkt_num=2, check_param={"port_id": 1, "drop": 1}, stats=False
        )

        # same pattern, different input set field.
        self.create_acl_filter_rule(rules[3], check_stats=True)
        out_drop = self.send_pkts_getouput(pkts=packets[0:4])
        rfc.check_drop(
            out_drop, pkt_num=4, check_param={"port_id": 1, "drop": 1}, stats=True
        )
        out_receive = self.send_pkts_getouput(pkts=packets[4])
        rfc.check_drop(
            out_receive, pkt_num=1, check_param={"port_id": 1, "drop": 1}, stats=False
        )

        # different pattern, same input set field.
        self.create_acl_filter_rule(rules[4], check_stats=True)
        out_drop = self.send_pkts_getouput(pkts=packets[0:5])
        rfc.check_drop(
            out_drop, pkt_num=5, check_param={"port_id": 1, "drop": 1}, stats=True
        )

    def test_multirules_all_pattern(self):
        """
        create multirules for all patterns
        """
        out_testpmd = self.launch_testpmd()
        self.check_dcf_status(out_testpmd, stats=True)
        rules = [
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.0 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 / tcp src spec 8010 src mask 65520 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 / tcp dst spec 8017 dst mask 65520 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / tcp / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.254 / tcp / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / tcp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 / udp src spec 8017 src mask 65520 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 / udp dst spec 8010 dst mask 65520 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.254.255 / udp / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.254.255 / udp / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / udp src spec 8017 src mask 65520 dst spec 8010 dst mask 65520 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.254 / sctp / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.2 dst mask 255.255.255.254 / sctp / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 / sctp src spec 8010 src mask 65520 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 / sctp dst spec 8010 dst mask 65520 / end actions drop / end",
            "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.1 src mask 255.255.255.0 dst spec 192.168.0.2 dst mask 255.255.0.255 / sctp src spec 8010 src mask 65520 dst spec 8017 dst mask 65520 / end actions drop / end",
        ]
        rule_list = self.create_acl_filter_rule(rules, check_stats=True)
        self.check_filter_rule_list(0, rule_list)
        packets = {
            "drop": [
                'Ether(dst="%s")/IP(src="192.168.0.3", dst="192.168.0.2")/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.1.2")/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=8012, dport=7985)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=7985, dport=8018)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.0.0", dst="192.168.1.2")/TCP(sport=7984, dport=7985)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.0.3")/TCP(sport=7984, dport=7985)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.0.3", dst="192.168.1.2")/TCP(sport=8012, dport=8018)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=8017, dport=7985)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=7985, dport=8012)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.0.3")/UDP(sport=7984, dport=7985)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.0.3", dst="192.168.1.2")/UDP(sport=7984, dport=7985)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.0.3", dst="192.168.1.2")/UDP(sport=8018, dport=8012)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.0.0", dst="192.168.0.3")/UDP(sport=8012, dport=8018)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=8012, dport=7985)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=7985, dport=8012)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.0.3")/SCTP(sport=7984, dport=7985)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.1.2")/SCTP(sport=7984, dport=7985)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.0.3", dst="192.168.1.2")/SCTP(sport=8012, dport=8018)/Raw(load="x"*30)'
                % vf1_mac,
            ],
            "receive": [
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.1.2")/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=8018, dport=8012)/Raw(load="x"*30)'
                % vf1_mac,
                'Ether(dst="%s")/IP(src="192.168.1.0", dst="192.168.1.3")/SCTP(sport=8017, dport=8018)/Raw(load="x"*30)'
                % vf1_mac,
            ],
        }
        out_drop = self.send_pkts_getouput(pkts=packets["drop"])
        rfc.check_drop(
            out_drop,
            pkt_num=len(packets["drop"]),
            check_param={"port_id": 1, "drop": 1},
            stats=True,
        )
        out_receive = self.send_pkts_getouput(pkts=packets["receive"])
        rfc.check_drop(
            out_receive,
            pkt_num=len(packets["receive"]),
            check_param={"port_id": 1, "drop": 1},
            stats=False,
        )

    def test_multi_rteflow_rules(self):
        """
        create switch, acl and fdir rules simultaneously.
        """
        param = " --rxq=16 --txq=16"
        out_testpmd = self.launch_testpmd(param)
        self.check_dcf_status(out_testpmd, stats=True)
        rules = {
            "switch": [
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.20 / tcp / end actions vf id 1 / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.20 / tcp / end actions vf id 1 / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.20 / tcp / end actions vf id 1 / end",
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.4 dst is 192.168.0.20 / tcp / end actions vf id 1 / end",
            ],
            "acl": [
                "flow create 0 ingress pattern eth / ipv4 src spec 192.168.0.2 src mask 255.255.255.254 / tcp / end actions drop / end",
                "flow create 0 ingress pattern eth / ipv4 dst spec 192.168.0.21 dst mask 255.255.0.255 / tcp / end actions drop / end",
            ],
            "fdir": [
                "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.20 / tcp src is 22 dst is 23 / end actions queue index 3 / mark / end",
                "flow create 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.20 / tcp src is 22 dst is 23 / end actions queue index 3 / mark / end",
                "flow create 1 ingress pattern eth / ipv4 src is 192.168.1.1 dst is 192.168.0.20 / tcp src is 22 dst is 23 / end actions queue index 3 / mark / end",
            ],
        }
        switch_rule_list = self.create_other_filter_rule(
            rules["switch"], check_stats=True
        )
        self.check_filter_rule_list(0, switch_rule_list)
        acl_rule_list = self.create_acl_filter_rule(rules["acl"], check_stats=True)
        self.check_filter_rule_list(0, switch_rule_list + acl_rule_list)
        fdir_rule_list = self.create_other_filter_rule(rules["fdir"], check_stats=True)
        self.check_filter_rule_list(1, fdir_rule_list)

        packets = {
            "drop": [
                'Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.2", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30)',
                'Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.3", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30)',
                'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw(load="x"*30)'
                % vf1_mac,
            ],
            "mark": [
                'Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.1", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30)',
                'Ether(src="00:11:22:33:44:55", dst="%s")/IP(src="192.168.1.1", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30)'
                % vf1_mac,
            ],
            "rss": [
                'Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.1", dst="192.168.0.20")/TCP(sport=32,dport=33)/Raw(load="x"*30)',
                'Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.4", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30)',
            ],
            "noreceived": 'Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.1.1", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30)',
        }

        out_drop = self.send_pkts_getouput(pkts=packets["drop"])
        rfc.check_drop(
            out_drop,
            pkt_num=len(packets["drop"]),
            check_param={"port_id": 1, "drop": 1},
            stats=True,
        )

        out_mark = self.send_pkts_getouput(pkts=packets["mark"])
        rfc.check_iavf_fdir_mark(
            out_mark,
            pkt_num=len(packets["mark"]),
            check_param={"port_id": 1, "queue": 3, "mark_id": 0},
        )

        out_rss = self.send_pkts_getouput(pkts=packets["rss"])
        rfc.check_iavf_fdir_mark(
            out_rss,
            pkt_num=len(packets["rss"]),
            check_param={"port_id": 1, "passthru": 1},
        )

        out_noreceived = self.send_pkts_getouput(pkts=packets["noreceived"])
        rfc.check_iavf_fdir_mark(
            out_noreceived, pkt_num=0, check_param={"port_id": 1, "passthru": 1}
        )

        self.dut.send_expect("flow destroy 0 rule 4", "testpmd> ", 15)

        packets = {
            "mark": 'Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.2", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30)',
            "rss": 'Ether(src="00:11:22:33:44:55", dst="00:01:23:45:67:88")/IP(src="192.168.0.3", dst="192.168.0.20")/TCP(sport=22,dport=23)/Raw(load="x"*30)',
        }

        out_mark = self.send_pkts_getouput(pkts=packets["mark"])
        rfc.check_iavf_fdir_mark(
            out_mark, pkt_num=1, check_param={"port_id": 1, "queue": 3, "mark_id": 0}
        )

        out_rss = self.send_pkts_getouput(pkts=packets["rss"])
        rfc.check_iavf_fdir_mark(
            out_rss, pkt_num=1, check_param={"port_id": 1, "passthru": 1}
        )

    def check_dcf_status(self, out_testpmd, stats=True):
        """
        check if request for DCF is accepted.
        """
        if stats:
            self.verify(
                "Failed to init DCF parent adapter" not in out_testpmd,
                "request for DCF is rejected.",
            )
            out_portinfo = self.dut.send_expect("show port info 0", "testpmd> ", 15)
            self.verify("net_ice_dcf" in out_portinfo, "request for DCF is rejected.")
        else:
            self.verify(
                "Failed to init DCF parent adapter" in out_testpmd,
                "request for DCF is accepted.",
            )
            out_portinfo = self.dut.send_expect("show port info 0", "testpmd> ", 15)
            self.verify(
                "net_ice_dcf" not in out_portinfo, "request for DCF is accepted."
            )

    def quit_testpmd(self):
        """
        quit testpmd
        """
        if self.testpmd_status != "close":
            # destroy all flow rules on DCF
            self.dut.send_expect("flow flush 0", "testpmd> ", 15)
            self.dut.send_expect("clear port stats all", "testpmd> ", 15)
            self.dut.send_expect("quit", "#", 30)
            # kill all DPDK application
            self.dut.kill_all()
        self.testpmd_status = "close"

    def test_mutually_exclusive(self):
        """
        DCF mode and any ACL filters (not added by DCF) shall be mutually exclusive
        """
        self.dut.kill_all()
        self.session_secondary = self.dut.new_session()

        # add ACL rule by kernel, reject request for DCF functionality
        self.add_acl_rule_not_by_dcf(self.pf0_intf, stats=True)
        out_testpmd = self.launch_testpmd()
        self.check_dcf_status(out_testpmd, stats=False)
        self.quit_testpmd()
        self.delete_acl_rule_not_added_by_dcf()
        out_testpmd = self.launch_testpmd()
        self.check_dcf_status(out_testpmd, stats=True)
        self.quit_testpmd()

        # add ACL rule by kernel, accept request for DCF functionality of another PF
        self.add_acl_rule_not_by_dcf(self.pf1_intf, stats=True)
        out_testpmd = self.launch_testpmd()
        self.check_dcf_status(out_testpmd, stats=True)
        self.quit_testpmd()
        self.delete_acl_rule_not_added_by_dcf()

        # ACL DCF mode is active, add ACL filters by way of host based configuration is rejected
        out_testpmd = self.launch_testpmd()
        self.check_dcf_status(out_testpmd, stats=True)
        self.add_acl_rule_not_by_dcf(self.pf0_intf, stats=False)
        self.quit_testpmd()
        self.add_acl_rule_not_by_dcf(self.pf0_intf, stats=True)
        self.delete_acl_rule_not_added_by_dcf()

        # ACL DCF mode is active, add ACL filters by way of host based configuration on another PF successfully
        out_testpmd = self.launch_testpmd()
        self.check_dcf_status(out_testpmd, stats=True)
        self.add_acl_rule_not_by_dcf(self.pf1_intf, stats=True)
        self.quit_testpmd()
        self.delete_acl_rule_not_added_by_dcf()

    def add_acl_rule_not_by_dcf(self, pf, stats=True):
        """
        use secondary session
        add acl rule by kernel command
        """
        if stats:
            self.session_secondary.send_expect(
                "ethtool -N %s flow-type tcp4 src-ip 192.168.10.0 m 0.255.255.255 dst-port 8000 m 0x00ff action -1"
                % pf,
                "# ",
            )
        else:
            error_info = "rmgr: Cannot insert RX class rule: No such file or directory"
            self.session_secondary.send_expect(
                "ethtool -N %s flow-type tcp4 src-ip 192.168.10.0 m 0.255.255.255 dst-port 8000 m 0x00ff action -1"
                % pf,
                error_info,
            )

    def delete_acl_rule_not_added_by_dcf(self):
        """
        delete all the acl rule added not by DCF
        """
        out_pf0 = self.dut.send_expect("ethtool -n %s" % (self.pf0_intf), "# ")
        out_pf1 = self.dut.send_expect("ethtool -n %s" % (self.pf1_intf), "# ")

        p = re.compile(r"Filter: (\d+)")
        m0 = p.search(out_pf0)
        m1 = p.search(out_pf1)
        if m0:
            self.dut.send_expect(
                "ethtool -N %s delete %d" % (self.pf0_intf, int(m0.group(1))), "# "
            )
            self.dut.send_expect("ethtool -n %s" % (self.pf0_intf), "Total 0 rules")
        if m1:
            self.dut.send_expect(
                "ethtool -N %s delete %d" % (self.pf1_intf, int(m1.group(1))), "# "
            )
            self.dut.send_expect("ethtool -n %s" % (self.pf1_intf), "Total 0 rules")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.quit_testpmd()
        if getattr(self, "session_secondary", None):
            self.dut.close_session(self.session_secondary)
        self.delete_acl_rule_not_added_by_dcf()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
