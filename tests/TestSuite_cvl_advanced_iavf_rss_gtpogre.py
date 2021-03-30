# BSD LICENSE
#
# Copyright(c)2021 Intel Corporation. All rights reserved.
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
import time
from packet import Packet
from pmd_output import PmdOutput
from test_case import TestCase
from rte_flow_common import RssProcessing

mac_ipv4_gtpu_ipv4_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
}

mac_ipv4_gtpu_ipv4_l3src_changed_pkt = eval(str(mac_ipv4_gtpu_ipv4_basic).replace('192.168.0.2', '192.168.1.2'))
mac_ipv4_gtpu_ipv4_l3dst_changed_pkt = eval(str(mac_ipv4_gtpu_ipv4_basic).replace('192.168.0.1', '192.168.1.1'))

mac_ipv4_gtpu_ipv4_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv4_l3src_only = eval(str(mac_ipv4_gtpu_ipv4_l3dst_only)
                                     .replace('mac_ipv4_gtpu_ipv4_l3dst', 'mac_ipv4_gtpu_ipv4_l3src')
                                     .replace('l3-dst-only', 'l3-src-only')
                                     .replace('check_hash_same', 'hash_check_different')
                                     .replace('check_hash_different', 'check_hash_same')
                                     .replace('hash_check_different', 'check_hash_different'))
mac_ipv4_gtpu_ipv4_all = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_different',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv4_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_basic['gtpogre-ipv4-nonfrag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv4_toeplitz = [mac_ipv4_gtpu_ipv4_l3dst_only, mac_ipv4_gtpu_ipv4_l3src_only,
                               mac_ipv4_gtpu_ipv4_all, mac_ipv4_gtpu_ipv4_gtpu]

mac_ipv4_gtpu_ipv4_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2", frag=6)/("X"*480)',
            'action': {'save_hash': 'gtpogre-ipv4-frag'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1", frag=6)/("X"*480)',
            'action': {'check_no_hash_or_different': 'gtpogre-ipv4-frag'},
        },
    ],
}

mac_ipv4_gtpu_ipv6_symmetric = eval(str(mac_ipv4_gtpu_ipv4_symmetric).replace('IPv6', 'IPv61')
                                    .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                    .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                    .replace(', frag=6)', ')/IPv6ExtHdrFragment()')
                                    .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                    .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                    .replace('gtpu / ipv4', 'gtpu / ipv6').replace('types ipv4', 'types ipv6')
                                    )

mac_ipv4_gtpu_ipv4_udp_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': {'save_hash': 'basic_with_rule'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_no_hash_or_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_no_hash_or_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_no_hash_or_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_no_hash_or_different',
        },
    ],
}

mac_ipv4_gtpu_ipv6_udp_symmetric = eval(str(mac_ipv4_gtpu_ipv4_udp_symmetric).replace('IPv6', 'IPv61')
                                        .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                        .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                        .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                        .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                        .replace('gtpu / ipv4', 'gtpu / ipv6').replace('types ipv4-udp', 'types ipv6-udp')
                                        )

mac_ipv4_gtpu_ipv4_tcp_symmetric = eval(str(mac_ipv4_gtpu_ipv4_udp_symmetric).replace('TCP(', 'TCP1(')
                                        .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                        .replace('udp / end', 'tcp / end ').replace('ipv4-udp', 'ipv4-tcp')
                                        .replace('udp_symmetric', 'tcp_symmetric'))

mac_ipv4_gtpu_ipv6_tcp_symmetric = eval(str(mac_ipv4_gtpu_ipv4_tcp_symmetric).replace('IPv6', 'IPv61')
                                        .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                        .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                        .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                        .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                        .replace('gtpu / ipv4', 'gtpu / ipv6').replace('types ipv4-tcp', 'types ipv6-tcp')
                                        )

mac_ipv4_gtpu_eh_dl_ipv4_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)',
            'action': {'save_hash': 'gtpogre-ipv4-udp'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP()/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP()/("X"*480)',
            'action': {'check_no_hash_or_different': 'gtpogre-ipv4-udp'},
        },
    ],
}
mac_ipv4_gtpu_eh_ul_ipv4_symmetric = eval(str(mac_ipv4_gtpu_eh_dl_ipv4_symmetric)
                                          .replace('(type=1', '(type=2')
                                          .replace('(type=0', '(type=1')
                                          .replace('(type=2', '(type=0')
                                          .replace('eh_dl', 'eh_ul')
                                          .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                                          )

mac_ipv4_gtpu_eh_ipv4_symmetric = [mac_ipv4_gtpu_eh_dl_ipv4_symmetric,  mac_ipv4_gtpu_eh_ul_ipv4_symmetric]

mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_no_hash_or_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_no_hash_or_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_no_hash_or_different',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_no_hash_or_different',
        },
    ],
}
mac_ipv4_gtpu_eh_ul_ipv4_udp_symmetric = eval(str(mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric)
                                              .replace('(type=1', '(type=2')
                                              .replace('(type=0', '(type=1')
                                              .replace('(type=2', '(type=0')
                                              .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                                              .replace('eh_dl', 'eh_ul'))
mac_ipv4_gtpu_eh_ipv4_udp_symmetric = [mac_ipv4_gtpu_eh_dl_ipv4_udp_symmetric, mac_ipv4_gtpu_eh_ul_ipv4_udp_symmetric]

mac_ipv4_gtpu_eh_ipv4_tcp_symmetric = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                                        .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                                        .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                       for element in mac_ipv4_gtpu_eh_ipv4_udp_symmetric]

mac_ipv4_gtpu_eh_ipv6_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_symmetric).replace('IPv6', 'IPv61')
                                       .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                       .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                       .replace(', frag=6)', ')/IPv6ExtHdrFragment()')
                                       .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                       .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                       .replace('ipv4 / end', 'ipv6 / end').replace('types ipv4', 'types ipv6')
                                       .replace('ipv4_symmetric', 'ipv6_symmetric')
                                       )

mac_ipv4_gtpu_eh_ipv6_udp_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_udp_symmetric).replace('IPv6', 'IPv61')
                                        .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                        .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                        .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                        .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                        .replace('ipv4 / udp / end', 'ipv6 / udp / end').replace('types ipv4-udp', 'types ipv6-udp')
                                        .replace('ipv4_udp_symmetric', 'ipv6_udp_symmetric')
                                        )


mac_ipv4_gtpu_eh_ipv6_tcp_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_tcp_symmetric).replace('IPv6', 'IPv61')
                                        .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                        .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                        .replace('IPv61(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(dst="192.168.0.1",src="192.168.0.2")')
                                        .replace('IPv61(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")', 'IP(src="192.168.0.1",dst="192.168.0.2")')
                                        .replace('ipv4 / tcp / end', 'ipv6 / tcp / end').replace('types ipv4-tcp', 'types ipv6-tcp')
                                        .replace('ipv4_tcp_symmetric', 'ipv6_tcp_symmetric')
                                        )

mac_ipv4_gtpu_ipv4_udp_basic = {
        'ipv4-udp': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
        'gtpogre-ipv4-udp': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
}

mac_ipv4_gtpu_ipv4_udp_l3dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv4_udp_l3src = eval(str(mac_ipv4_gtpu_ipv4_udp_l3dst)
                                    .replace('mac_ipv4_gtpu_ipv4_udp_l3dst', 'mac_ipv4_gtpu_ipv4_udp_l3src')
                                    .replace('l3-dst-only', 'l3-src-only')
                                    .replace('check_hash_same', 'hash_check_different')
                                    .replace('check_hash_different', 'check_hash_same')
                                    .replace('hash_check_different', 'check_hash_different'))

mac_ipv4_gtpu_ipv4_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33').replace('192.168.0.1',
                                                                                                '192.168.1.1'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv4_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=32').replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv4_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33').replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=32').replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}
mac_ipv4_gtpu_ipv4_udp_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=32')
                                                       .replace('192.168.0', '192.168.1'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}
mac_ipv4_gtpu_ipv4_udp_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=32')
                                                       .replace('192.168.0', '192.168.1'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv4_udp_all = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv4_udp_l3 = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_l3',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22,dport=23', 'sport=12,dport=13'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv4_udp_toeplitz = [mac_ipv4_gtpu_ipv4_udp_l3dst, mac_ipv4_gtpu_ipv4_udp_l3src,
                                   mac_ipv4_gtpu_ipv4_udp_l3dst_l4src, mac_ipv4_gtpu_ipv4_udp_l3dst_l4dst,
                                   mac_ipv4_gtpu_ipv4_udp_l3src_l4src, mac_ipv4_gtpu_ipv4_udp_l3src_l4dst,
                                   mac_ipv4_gtpu_ipv4_udp_l4src, mac_ipv4_gtpu_ipv4_udp_l4dst,
                                   mac_ipv4_gtpu_ipv4_udp_all, mac_ipv4_gtpu_ipv4_udp_l3]

mac_ipv4_gtpu_ipv4_tcp_toeplitz = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                        .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                        .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                   for element in mac_ipv4_gtpu_ipv4_udp_toeplitz]

mac_ipv4_gtpu_ipv6_basic = {
    'gtpogre-ipv6-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
}

mac_ipv4_gtpu_ipv6_l3src_changed_pkt = eval(str(mac_ipv4_gtpu_ipv6_basic).replace('ABAB', '1212'))
mac_ipv4_gtpu_ipv6_l3dst_changed_pkt = eval(str(mac_ipv4_gtpu_ipv6_basic).replace('CDCD', '3434'))

mac_ipv4_gtpu_ipv6_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['gtpogre-ipv6-nonfrag'],
            'action': {'save_hash', 'gtpogre-ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['gtpogre-ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['gtpogre-ipv6-nonfrag'],
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv6_l3src_only = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_l3src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['gtpogre-ipv6-nonfrag'],
            'action': {'save_hash', 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['gtpogre-ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['gtpogre-ipv6-nonfrag'],
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv6_l3src_only = eval(str(mac_ipv4_gtpu_ipv6_l3dst_only)
                                     .replace('mac_ipv4_gtpu_ipv6_l3dst', 'mac_ipv4_gtpu_ipv6_l3src')
                                     .replace('l3-dst-only', 'l3-src-only')
                                     .replace('check_hash_same', 'hash_check_different')
                                     .replace('check_hash_different', 'check_hash_same')
                                     .replace('hash_check_different', 'check_hash_different'))
mac_ipv4_gtpu_ipv6_all = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['gtpogre-ipv6-nonfrag'],
            'action': {'save_hash', 'ipv6-nonfrag'},
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3dst_changed_pkt['gtpogre-ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_l3src_changed_pkt['gtpogre-ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['gtpogre-ipv6-nonfrag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv6_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['gtpogre-ipv6-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['gtpogre-ipv6-nonfrag'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_basic['gtpogre-ipv6-nonfrag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv6_toeplitz = [mac_ipv4_gtpu_ipv6_l3dst_only, mac_ipv4_gtpu_ipv6_l3src_only,
                               mac_ipv4_gtpu_ipv6_all, mac_ipv4_gtpu_ipv6_gtpu]

mac_ipv4_gtpu_ipv6_udp_basic = {
        'ipv6-udp': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
        'gtpogre-ipv6-udp': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
}
mac_ipv4_gtpu_ipv6_udp_l3dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv6_udp_l3src = eval(str(mac_ipv4_gtpu_ipv6_udp_l3dst)
                                    .replace('mac_ipv4_gtpu_ipv6_udp_l3dst', 'mac_ipv4_gtpu_ipv6_udp_l3src')
                                    .replace('l3-dst-only', 'l3-src-only')
                                    .replace('check_hash_same', 'hash_check_different')
                                    .replace('check_hash_different', 'check_hash_same')
                                    .replace('hash_check_different', 'check_hash_different'))

mac_ipv4_gtpu_ipv6_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv6_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=32').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv6_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33').replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv6_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=32').replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}
mac_ipv4_gtpu_ipv6_udp_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=32')
                .replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}
mac_ipv4_gtpu_ipv6_udp_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=32')
                .replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv6_udp_all = {
    'sub_casename': 'mac_ipv4_gtpu_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('teid=0x123456', 'teid=0x12345'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_ipv6_udp_toeplitz = [mac_ipv4_gtpu_ipv6_udp_l3dst, mac_ipv4_gtpu_ipv6_udp_l3src,
                                   mac_ipv4_gtpu_ipv6_udp_l3dst_l4src, mac_ipv4_gtpu_ipv6_udp_l3dst_l4dst,
                                   mac_ipv4_gtpu_ipv6_udp_l3src_l4src, mac_ipv4_gtpu_ipv6_udp_l3src_l4dst,
                                   mac_ipv4_gtpu_ipv6_udp_l4src, mac_ipv4_gtpu_ipv6_udp_l4dst,
                                   mac_ipv4_gtpu_ipv6_udp_all]

mac_ipv4_gtpu_ipv6_tcp_toeplitz = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                        .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                        .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                   for element in mac_ipv4_gtpu_ipv6_udp_toeplitz]

mac_ipv4_gtpu_eh_dl_ipv4_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
}

mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv4_basic).replace('192.168.0.2', '192.168.1.2'))
mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt = eval(
    str(mac_ipv4_gtpu_eh_dl_ipv4_basic).replace('192.168.0.1', '192.168.1.1'))

mac_ipv4_gtpu_eh_dl_ipv4_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv4_l3src_only = eval(str(mac_ipv4_gtpu_eh_dl_ipv4_l3dst_only)
                                           .replace('eh_dl_ipv4_l3dst', 'eh_ul_ipv4_l3src')
                                           .replace('l3-dst-only', 'l3-src-only')
                                           .replace('check_hash_same', 'hash_check_different')
                                           .replace('check_hash_different', 'check_hash_same')
                                           .replace('hash_check_different', 'check_hash_different'))
mac_ipv4_gtpu_eh_dl_ipv4_all = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
    ],
    'post-test': []
}


mac_ipv4_gtpu_eh_dl_ipv4 = [mac_ipv4_gtpu_eh_dl_ipv4_l3dst_only, mac_ipv4_gtpu_eh_dl_ipv4_l3src_only,
                            mac_ipv4_gtpu_eh_dl_ipv4_all]

mac_ipv4_gtpu_eh_ul_ipv4 = [eval(str(element).replace('(type=1', '(type=2')
                            .replace('(type=0', '(type=1').replace('(type=2', '(type=0')
                            .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                            .replace('eh_dl', 'eh_ul'))
                            for element in mac_ipv4_gtpu_eh_dl_ipv4]

mac_ipv4_gtpu_eh_ipv4_toeplitz = mac_ipv4_gtpu_eh_dl_ipv4 + mac_ipv4_gtpu_eh_ul_ipv4

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic = {
    'gtpogre-ipv4-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
    'gtpogre-ipv4-nonfrag_ul': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic).replace('192.168.0.2', '192.168.1.2'))
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic).replace('192.168.0.1', '192.168.1.1'))

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_only = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_only)
                                           .replace('ul_dl_ipv4_l3dst', 'ul_dl_ipv4_l3src')
                                           .replace('l3-dst-only', 'l3-src-only')
                                           .replace('dst="192.168.0.1",src="192.168.1.2"', 'dst="192.168.0.1",src="192.168.1.3"')
                                           .replace('dst="192.168.1.1",src="192.168.0.2"', 'dst="192.168.0.1",src="192.168.1.2"')
                                           .replace('dst="192.168.0.1",src="192.168.1.3"', 'dst="192.168.1.1",src="192.168.0.2"')
                                                      )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_all = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_changed_pkt['gtpogre-ipv4-nonfrag'],
            'action': 'check_hash_different',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_gtpu = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_gtpu',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types gtpu end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['gtpogre-ipv4-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['gtpogre-ipv4-nonfrag'].replace('0x123456', '0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['gtpogre-ipv4-nonfrag'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['gtpogre-ipv4-nonfrag_ul'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['gtpogre-ipv4-nonfrag_ul'].replace('0x123456', '0x12345'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_basic['gtpogre-ipv4-nonfrag_ul'].replace('192.168.0.', '192.168.1.'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz = [mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3dst_only,
                                                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_l3src_only,
                                                mac_ipv4_gtpu_eh_without_ul_dl_ipv4_all]

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic = {
    'gtpogre-dl': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
    'gtpogre-ul': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('192.168.0.2', '192.168.1.2')
                                                                              .replace('sport=22, dport=23',
                                                                                       'sport=32, dport=33'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'].replace('192.168.0.2', '192.168.1.2')
                .replace('sport=22, dport=23',
                         'sport=32, dport=33'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_only = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_only)
                                                      .replace('ul_dl_ipv4_udp_l3dst', 'ul_dl_ipv4_udp_l3src')
                                                      .replace('l3-dst-only', 'l3-src-only')
                                                      .replace('dst="192.168.0.1",src="192.168.1.2"', 'dst="192.168.0.1",src="192.168.1.3"')
                                                      .replace('dst="192.168.1.1",src="192.168.0.2"', 'dst="192.168.0.1",src="192.168.1.2"')
                                                      .replace('dst="192.168.0.1",src="192.168.1.3"', 'dst="192.168.1.1",src="192.168.0.2"')
                                                      )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('192.168.0.1', '192.168.1.1')
                .replace('dport=23', 'dport=33')
                .replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'].replace('192.168.0.1', '192.168.1.1')
                .replace('dport=23', 'dport=33')
                .replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4dst = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src)
                                                           .replace('udp_l3src_l4src', 'udp_l3src_l4dst')
                                                           .replace('l4-src-only', 'l4-dst-only')
                                                           .replace('sport=32, dport=23', 'sport=22, dport=34')
                                                           .replace('sport=22, dport=33', 'sport=32, dport=23')
                                                           )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4src = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src)
                                                           .replace('udp_l3src_l4src', 'udp_l3dst_l4src')
                                                           .replace('l3-src-only', 'l3-dst-only')
                                                           .replace('dst="192.168.0.1",src="192.168.1.2"', 'dst="192.168.0.1",src="192.168.1.3"')
                                                           .replace('dst="192.168.1.1",src="192.168.0.2"', 'dst="192.168.0.1",src="192.168.1.2"')
                                                           .replace('dst="192.168.0.1",src="192.168.1.3"', 'dst="192.168.1.1",src="192.168.0.2"')
                                                           )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4dst = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4src)
                                                           .replace('udp_l3dst_l4src', 'udp_l3dst_l4dst')
                                                           .replace('l3-src-only', 'l3-dst-only')
                                                           .replace('l4-src-only', 'l4-dst-only')
                                                           .replace('sport=32, dport=23', 'sport=22, dport=34')
                                                           .replace('sport=22, dport=33', 'sport=32, dport=23')
                                                           )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('192.168.0', '192.168.1')
            .replace('dport=23', 'dport=33')
            .replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'].replace('192.168.0', '192.168.1')
            .replace('dport=23', 'dport=33')
            .replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4dst_only = eval(str(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only)
                                                          .replace('udp_l4src_only', 'udp_l4dst_only')
                                                          .replace('l4-src-only', 'l4-dst-only')
                                                          .replace('sport=32, dport=23', 'sport=22, dport=34')
                                                          .replace('sport=22, dport=33', 'sport=32, dport=23')
                                                          )
mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('0x123456', '0x12345'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3 = {
    'sub_casename': 'mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'],
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-dl'].replace('sport=22, dport=23', 'sport=12, dport=13'),
            'action': 'check_hash_same',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_basic['gtpogre-ul'].replace('sport=22, dport=23', 'sport=12, dport=13'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz = [
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4dst,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4src,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3src_l4src,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3dst_l4dst,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4src_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l4dst_only,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp,
    mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_l3,
]

mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                           .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                           .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                      for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz]

mac_ipv4_gtpu_eh_without_ul_dl_ipv6_toeplitz = [eval(str(element).replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                     .replace('types ipv4', 'types ipv6')
                                                     .replace('ul_dl_ipv4', 'ul_dl_ipv6')
                                                     .replace(', frag=6)', ')/IPv6ExtHdrFragment()')
                                                     .replace('IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(dst="192.168.0.3", src="192.168.0.3"',)
                                                     .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                     .replace('IP(dst="192.168.1.1",src="192.168.0.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                     .replace('IP(dst="192.168.0.1",src="192.168.1.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"')
                                                     .replace('IP(dst="192.168.1.1",src="192.168.1.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"')
                                                     .replace('IP(dst="192.168.0.3",src="192.168.0.3"', 'IP(dst="192.168.0.1",src="192.168.0.2"'))
                                                for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz]

mac_ipv4_gtpu_eh_without_ul_dl_ipv6_udp_toeplitz = [eval(str(element).replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                         .replace('ipv4-udp', 'ipv6-udp')
                                                         .replace('types ipv4', 'types ipv6')
                                                         .replace('ul_dl_ipv4_udp', 'ul_dl_ipv6_udp')
                                                         .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.1.1",src="192.168.0.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.0.1",src="192.168.1.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.1.1",src="192.168.1.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"'))
                                                    for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz]

mac_ipv4_gtpu_eh_without_ul_dl_ipv6_tcp_toeplitz = [eval(str(element).replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                         .replace('ipv4 / tcp', 'ipv6 / tcp')
                                                         .replace('types ipv4', 'types ipv6')
                                                         .replace('ipv4-tcp', 'ipv6-tcp')
                                                         .replace('ul_dl_ipv4_tcp', 'ul_dl_ipv6_tcp')
                                                         .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.1.1",src="192.168.0.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.0.1",src="192.168.1.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.1.1",src="192.168.1.2"', 'IPv6(dst="1212:910B:6666:3457:8295:3333:1800:2929",src="3434:910A:2222:5498:8475:1111:3900:2020"'))
                                                    for element in mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz]

mac_ipv4_gtpu_eh_dl_ipv4_udp_basic = {
        'gtpogre-ipv4-udp': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
}
mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src = eval(str(mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst)
                                          .replace('mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst',
                                                   'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src')
                                          .replace('l3-dst-only', 'l3-src-only')
                                          .replace('check_hash_same', 'hash_check_different')
                                          .replace('check_hash_different', 'check_hash_same')
                                          .replace('hash_check_different', 'check_hash_different'))

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33').replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=32').replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33').replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=32')
                                                             .replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}
mac_ipv4_gtpu_eh_dl_ipv4_udp_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=32')
                                                             .replace('192.168.0', '192.168.1'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}
mac_ipv4_gtpu_eh_dl_ipv4_udp_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=32')
                                                             .replace('192.168.0', '192.168.1'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_all = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_l3 = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv4_udp_l3',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.1', '192.168.1.1'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('192.168.0.2', '192.168.1.2'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv4_udp_basic['gtpogre-ipv4-udp'].replace('sport=22', 'sport=12').replace('dport=23', 'dport=13'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv4_udp_toeplitz = [mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst, mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src,
                                         mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4src,
                                         mac_ipv4_gtpu_eh_dl_ipv4_udp_l3dst_l4dst,
                                         mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4src,
                                         mac_ipv4_gtpu_eh_dl_ipv4_udp_l3src_l4dst,
                                         mac_ipv4_gtpu_eh_dl_ipv4_udp_l4src, mac_ipv4_gtpu_eh_dl_ipv4_udp_l4dst,
                                         mac_ipv4_gtpu_eh_dl_ipv4_udp_all, mac_ipv4_gtpu_eh_dl_ipv4_udp_l3]

mac_ipv4_gtpu_eh_ul_ipv4_udp_toeplitz = [eval(str(element).replace('(type=1', '(type=2')
                                                          .replace('(type=0', '(type=1').replace('(type=2', '(type=0')
                                                          .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                                                          .replace('eh_dl', 'eh_ul'))
                                         for element in mac_ipv4_gtpu_eh_dl_ipv4_udp_toeplitz]

mac_ipv4_gtpu_eh_ipv4_udp_toeplitz = mac_ipv4_gtpu_eh_dl_ipv4_udp_toeplitz + mac_ipv4_gtpu_eh_ul_ipv4_udp_toeplitz

mac_ipv4_gtpu_eh_ipv4_tcp_toeplitz = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                                       .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                                       .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                      for element in mac_ipv4_gtpu_eh_ipv4_udp_toeplitz]

mac_ipv4_gtpu_eh_dl_ipv6_basic = {
    'gtpogre-ipv6-nonfrag': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
}

mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt = eval(str(mac_ipv4_gtpu_eh_dl_ipv6_basic).replace('ABAB', '1212'))
mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt = eval(str(mac_ipv4_gtpu_eh_dl_ipv6_basic).replace('CDCD', '3434'))

mac_ipv4_gtpu_eh_dl_ipv6_l3dst_only = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['gtpogre-ipv6-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['gtpogre-ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['gtpogre-ipv6-nonfrag'],
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv6_l3src_only = eval(str(mac_ipv4_gtpu_eh_dl_ipv6_l3dst_only)
                                           .replace('mac_ipv4_gtpu_eh_dl_ipv6_l3dst', 'mac_ipv4_gtpu_eh_dl_ipv6_l3src')
                                           .replace('l3-dst-only', 'l3-src-only')
                                           .replace('check_hash_same', 'hash_check_different')
                                           .replace('check_hash_different', 'check_hash_same')
                                           .replace('hash_check_different', 'check_hash_different'))
mac_ipv4_gtpu_eh_dl_ipv6_all = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['gtpogre-ipv6-nonfrag'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3dst_changed_pkt['gtpogre-ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_l3src_changed_pkt['gtpogre-ipv6-nonfrag'],
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_basic['gtpogre-ipv6-nonfrag'].replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv6_toeplitz = [mac_ipv4_gtpu_eh_dl_ipv6_l3dst_only, mac_ipv4_gtpu_eh_dl_ipv6_l3src_only,
                                     mac_ipv4_gtpu_eh_dl_ipv6_all]

mac_ipv4_gtpu_eh_ul_ipv6_toeplitz = [eval(str(element).replace('(type=1', '(type=2')
                                                      .replace('(type=0', '(type=1').replace('(type=2', '(type=0')
                                                      .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                                                      .replace('eh_dl', 'eh_ul'))
                                     for element in mac_ipv4_gtpu_eh_dl_ipv6_toeplitz]

mac_ipv4_gtpu_eh_ipv6_toeplitz = mac_ipv4_gtpu_eh_dl_ipv6_toeplitz + mac_ipv4_gtpu_eh_ul_ipv6_toeplitz

mac_ipv4_gtpu_eh_dl_ipv6_udp_basic = {
        'gtpogre-ipv6-udp': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
}
mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src = eval(str(mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst)
                                          .replace('mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst', 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src')
                                          .replace('l3-dst-only', 'l3-src-only')
                                          .replace('check_hash_same', 'hash_check_different')
                                          .replace('check_hash_different', 'check_hash_same')
                                          .replace('hash_check_different', 'check_hash_different'))

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=32').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33').replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=32').replace('ABAB', '1212'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}
mac_ipv4_gtpu_eh_dl_ipv6_udp_l4dst = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l4dst',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=32')
                                                       .replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}
mac_ipv4_gtpu_eh_dl_ipv6_udp_l4src = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_l4src',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=32')
                                                       .replace('ABAB', '1212').replace('CDCD', '3434'),
            'action': 'check_hash_same',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_all = {
    'sub_casename': 'mac_ipv4_gtpu_eh_dl_ipv6_udp_all',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'],
            'action': 'save_hash',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('sport=22', 'sport=32'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('dport=23', 'dport=33'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('CDCD', '3434'),
            'action': 'check_hash_different',
        },
        {
            'send_packet': mac_ipv4_gtpu_eh_dl_ipv6_udp_basic['gtpogre-ipv6-udp'].replace('ABAB', '1212'),
            'action': 'check_hash_different',
        },
    ],
    'post-test': []
}

mac_ipv4_gtpu_eh_dl_ipv6_udp_toeplitz = [mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst, mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src,
                                         mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4src,
                                         mac_ipv4_gtpu_eh_dl_ipv6_udp_l3dst_l4dst,
                                         mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4src,
                                         mac_ipv4_gtpu_eh_dl_ipv6_udp_l3src_l4dst,
                                         mac_ipv4_gtpu_eh_dl_ipv6_udp_l4src, mac_ipv4_gtpu_eh_dl_ipv6_udp_l4dst,
                                         mac_ipv4_gtpu_eh_dl_ipv6_udp_all]
mac_ipv4_gtpu_eh_ul_ipv6_udp_toeplitz = [eval(str(element).replace('(type=1', '(type=2')
                                                          .replace('(type=0', '(type=1').replace('(type=2', '(type=0')
                                                          .replace('gtp_psc pdu_t is 0', 'gtp_psc pdu_t is 1')
                                                          .replace('eh_dl', 'eh_ul'))
                                         for element in mac_ipv4_gtpu_eh_dl_ipv6_udp_toeplitz]
mac_ipv4_gtpu_eh_ipv6_udp_toeplitz = mac_ipv4_gtpu_eh_dl_ipv6_udp_toeplitz + mac_ipv4_gtpu_eh_ul_ipv6_udp_toeplitz

mac_ipv4_gtpu_eh_ipv6_tcp_toeplitz = [eval(str(element).replace('TCP', 'TCP1').replace('udp', 'tcp')
                                                       .replace('UDP(sport', 'TCP(sport').replace('TCP1', 'UDP')
                                                       .replace('ipv4 / tcp / gtpu', 'ipv4 / udp / gtpu'))
                                      for element in mac_ipv4_gtpu_eh_ipv6_udp_toeplitz]

inner_l4_mac_ipv4_gtpu_ipv4_udp_tcp = {
    'sub_casename': 'mac_ipv4_gtpu_ipv4_udp_tcp',
    'port_id': 0,
    'rule': [
       'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end',
       'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end',
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'save_or_no_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same_or_no_hash',
        },
    ]
}
inner_l4_mac_ipv6_gtpu_ipv4_udp_tcp = eval(str(inner_l4_mac_ipv4_gtpu_ipv4_udp_tcp)
                                           .replace('eth / ipv4', 'eth / ipv6')
                                           .replace('gtpu / ipv4', 'gtpu / gtp_psc / ipv4')
                                           .replace('IP()', 'IPv6()')
                                           .replace('teid=0x123456)', 'teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)')
                                           .replace('mac_ipv4', 'mac_ipv6')
                                           .replace('IP(proto=0x2F)/GRE(proto=0x0800)', 'IPv6(nh=0x2F)/GRE(proto=0x86DD)'))
inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp = {
    'sub_casename': 'inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp',
    'port_id': 0,
    'rule': [
        'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end',
        'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end',
    ],
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'save_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_different',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)',
            'action': 'save_or_no_hash',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)',
            'action': 'check_hash_same_or_no_hash',
        },
    ]
}
inner_l4_mac_ipv6_gtpu_eh_ipv6_udp_tcp = eval(str(inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp)
                                              .replace('eth / ipv4', 'eth / ipv6')
                                              .replace('pdu_t is 0', 'pdu_t is 1')
                                              .replace('(type=0', '(type=1')
                                              .replace('IP()', 'IPv6()')
                                              .replace('mac_ipv4', 'mac_ipv6')
                                              .replace('IP(proto=0x2F)/GRE(proto=0x0800)', 'IPv6(nh=0x2F)/GRE(proto=0x86DD)'))
inner_l4_protocal_hash = [inner_l4_mac_ipv4_gtpu_ipv4_udp_tcp, inner_l4_mac_ipv6_gtpu_ipv4_udp_tcp,
                          inner_l4_mac_ipv4_gtpu_eh_ipv6_udp_tcp, inner_l4_mac_ipv6_gtpu_eh_ipv6_udp_tcp]

mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)',
            'action': {'save_hash': 'gtpogre-ipv4-nonfrag'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)',
            'action': {'check_no_hash_or_different': 'gtpogre-ipv4-nonfrag'},
        },
    ],
}

mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric)
                                                     .replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                     .replace('types ipv4', 'types ipv6')
                                                     .replace('gtpu_eh_ipv4', 'gtpu_eh_ipv6')
                                                     .replace(',frag=6)', ')/IPv6ExtHdrFragment()')
                                                     .replace('IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(dst="192.168.1.1", src="192.168.1.2"',)
                                                     .replace('IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(src="192.168.1.1", dst="192.168.1.2"',)
                                                     .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                     .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                                     )

mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': {'save_hash': 'gtpogre-udp-dl'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)',
            'action': {'save_hash': 'gtpogre-udp-ul'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-udp-dl'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-udp-dl'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-udp-dl'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-udp-ul'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-udp-ul'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-udp-ul'},
        },
    ],
}
mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric)
                                                         .replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                         .replace('types ipv4', 'types ipv6')
                                                         .replace('gtpu_eh_ipv4', 'gtpu_eh_ipv6')
                                                         .replace('IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(dst="192.168.1.1", src="192.168.1.2"',)
                                                         .replace('IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(src="192.168.1.1", dst="192.168.1.2"',)
                                                         .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                                         )

mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric = {
    'sub_casename': 'mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric',
    'port_id': 0,
    'rule': 'flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end',
    'test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': {'save_hash': 'gtpogre-tcp-dl'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)',
            'action': {'save_hash': 'gtpogre-tcp-ul'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': 'check_hash_same',
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            'action': 'check_hash_same',
        },
    ],
    'post-test': [
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-tcp-dl'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-tcp-dl'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-tcp-dl'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-tcp-ul'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-tcp-ul'},
        },
        {
            'send_packet': 'Ether(dst="00:11:22:33:44:55")/IP(proto=0x2F)/GRE(proto=0x0800)/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=23, dport=22)/("X"*480)',
            'action': {'check_no_hash_or_different', 'gtpogre-tcp-ul'},
        },
    ],
}

mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric = eval(str(mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric)
                                                         .replace('gtp_psc / ipv4', 'gtp_psc / ipv6')
                                                         .replace('types ipv4', 'types ipv6')
                                                         .replace('gtpu_eh_ipv4', 'gtpu_eh_ipv6')
                                                         .replace('IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(dst="192.168.1.1", src="192.168.1.2"',)
                                                         .replace('IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020"','IP(src="192.168.1.1", dst="192.168.1.2"',)
                                                         .replace('IP(dst="192.168.0.1",src="192.168.0.2"', 'IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020"')
                                                         .replace('IP(dst="192.168.0.2",src="192.168.0.1"', 'IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020",src="ABAB:910B:6666:3457:8295:3333:1800:2929"')
                                                         )


class TestCVLAdvancedIAVFRSSGTPoGRE(TestCase):

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
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.tester_iface1 = self.tester.get_interface(self.tester_port1)
        self.pci0 = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.pci1 = self.dut.ports_info[self.dut_ports[1]]['pci']
        self.pf0_intf = self.dut.ports_info[self.dut_ports[0]]['intf']

        self.vf_driver = self.get_suite_cfg()['vf_driver']
        if self.vf_driver is None:
            self.vf_driver = 'vfio-pci'
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=self.kdriver)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port_0]['vfs_port']
        self.dut.send_expect('ip link set %s vf 0 mac 00:11:22:33:44:55' % self.pf0_intf, '#')
        self.vf0_pci = self.sriov_vfs_port[0].pci
        for port in self.sriov_vfs_port:
            port.bind_driver(self.vf_driver)

        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)
        self.launch_testpmd()
        self.symmetric = False
        self.rxq = 16
        self.rssprocess = RssProcessing(self, self.pmd_output, [self.tester_iface0, self.tester_iface1], self.rxq)
        self.logger.info('rssprocess.tester_ifaces: {}'.format(self.rssprocess.tester_ifaces))
        self.logger.info('rssprocess.test_case: {}'.format(self.rssprocess.test_case))

    def set_up(self):
        """
        Run before each test case.
        """
        self.pmd_output.execute_cmd("start")

    def destroy_vf(self):
        self.dut.send_expect("quit", "# ", 60)
        time.sleep(2)
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])

    def launch_testpmd(self, symmetric=False):
        if symmetric:
            param = "--rxq=16 --txq=16"
        else:
            # if support add --disable-rss
            param = "--rxq=16 --txq=16"
        self.pmd_output.start_testpmd(cores="1S/4C/1T", param=param,
                                          eal_param=f"-w {self.vf0_pci}", socket=self.ports_socket)
        '''
        self.symmetric = symmetric
        if symmetric:
            # Need config rss in setup
            self.pmd_output.execute_cmd("port config all rss all")
        '''
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        res = self.pmd_output.wait_link_status_up('all', timeout=15)
        self.verify(res is True, 'there have port link is down')

    def switch_testpmd(self, symmetric=True):
        if symmetric != self.symmetric:
            self.pmd_output.quit()
            self.launch_testpmd(symmetric=symmetric)
            self.pmd_output.execute_cmd("start")

    def test_mac_ipv4_gtpogre_ipv4(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_toeplitz)

    def test_mac_ipv4_gtpogre_ipv4_udp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_udp_toeplitz)

    def test_mac_ipv4_gtpogre_ipv4_tcp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gtpogre_ipv6(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_toeplitz)

    def test_mac_ipv4_gtpogre_ipv6_udp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_udp_toeplitz)

    def test_mac_ipv4_gtpogre_ipv6_tcp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gtpogre_ipv4(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv4_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_ipv4_udp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv4_udp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_ipv4_tcp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv4_tcp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_ipv6(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv6_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_ipv6_udp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv6_udp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_ipv6_tcp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv6_tcp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpogre_eh_ipv4(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_toeplitz)

    def test_mac_ipv4_gtpogre_eh_ipv4_udp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_udp_toeplitz)

    def test_mac_ipv4_gtpogre_eh_ipv4_tcp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gtpogre_eh_ipv6(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_toeplitz)

    def test_mac_ipv4_gtpogre_eh_ipv6_udp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_udp_toeplitz)

    def test_mac_ipv4_gtpogre_eh_ipv6_tcp(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gtpogre_eh_ipv4(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv4_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv4_udp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv4_udp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv4_tcp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv4_tcp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv6_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_udp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv6_udp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_tcp(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv6_tcp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpogre_eh_ipv4_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz)

    def test_mac_ipv4_gtpogre_eh_ipv4_udp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz)

    def test_mac_ipv4_gtpogre_eh_ipv4_tcp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz)

    def test_mac_ipv4_gtpogre_eh_ipv6_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv6_toeplitz)

    def test_mac_ipv4_gtpogre_eh_ipv6_udp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv6_udp_toeplitz)

    def test_mac_ipv4_gtpogre_eh_ipv6_tcp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_without_ul_dl_ipv6_tcp_toeplitz)

    def test_mac_ipv6_gtpogre_eh_ipv4_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv4_udp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_udp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv4_tcp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_without_ul_dl_ipv4_tcp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_without_ul_dl_ipv6_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_udp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_without_ul_dl_ipv6_udp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_tcp_without_ul_dl(self):
        self.switch_testpmd(symmetric=False)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_without_ul_dl_ipv6_tcp_toeplitz)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpogre_ipv4_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_symmetric)

    def test_mac_ipv4_gtpogre_ipv4_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_udp_symmetric)

    def test_mac_ipv4_gtpogre_ipv4_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv4_tcp_symmetric)

    def test_mac_ipv4_gtpogre_ipv6_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_symmetric)

    def test_mac_ipv4_gtpogre_ipv6_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_udp_symmetric)

    def test_mac_ipv4_gtpogre_ipv6_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_ipv6_tcp_symmetric)

    def test_mac_ipv6_gtpogre_ipv4_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv4_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_ipv4_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv4_udp_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_ipv4_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv4_tcp_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_ipv6_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv6_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_ipv6_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv6_udp_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_ipv6_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_ipv6_tcp_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpogre_eh_ipv4_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_symmetric)

    def test_mac_ipv4_gtpogre_eh_ipv4_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_udp_symmetric)

    def test_mac_ipv4_gtpogre_eh_ipv4_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_tcp_symmetric)

    def test_mac_ipv4_gtpogre_eh_ipv6_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_symmetric)

    def test_mac_ipv4_gtpogre_eh_ipv6_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_udp_symmetric)

    def test_mac_ipv4_gtpogre_eh_ipv6_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_tcp_symmetric)

    def test_mac_ipv6_gtpogre_eh_ipv4_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv4_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv4_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv4_tcp_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv4_tcp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv4_tcp_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv6_symmetric)
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_udp_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv6_tcp_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_tcp_symmetric(self):
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv6_tcp_symmetric)
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv4_gtpogre_eh_ipv4_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric)

    def test_mac_ipv4_gtpogre_eh_ipv4_udp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric)

    def test_mac_ipv4_gtpogre_eh_ipv4_tcp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric)

    def test_mac_ipv4_gtpogre_eh_ipv6_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric)

    def test_mac_ipv4_gtpogre_eh_ipv6_udp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric)

    def test_mac_ipv4_gtpogre_eh_ipv6_tcp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric)

    def test_mac_ipv6_gtpogre_eh_ipv4_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv4_without_ul_dl_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv4_udp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv4_udp_without_ul_dl_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv4_tcp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv4_tcp_without_ul_dl_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv6_without_ul_dl_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_udp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv6_udp_without_ul_dl_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_mac_ipv6_gtpogre_eh_ipv6_tcp_without_ul_dl_symmetric(self):
        self.switch_testpmd(symmetric=True)
        ipv6_template = self.rssprocess.get_ipv6_template_by_ipv4_gtpogre(mac_ipv4_gtpu_eh_ipv6_tcp_without_ul_dl_symmetric)
        self.rssprocess.handle_rss_distribute_cases(cases_info=ipv6_template)

    def test_inner_l4_protocal_hash(self):
        self.switch_testpmd(symmetric=True)
        self.rssprocess.handle_rss_distribute_cases(cases_info=inner_l4_protocal_hash)

    def tear_down(self):
        # destroy all flow rule on port 0
        self.dut.send_command("flow flush 0", timeout=1)
        self.dut.send_command("clear port stats all", timeout=1)
        self.pmd_output.execute_cmd("stop")

    def tear_down_all(self):
        self.destroy_vf()
        self.dut.kill_all()
