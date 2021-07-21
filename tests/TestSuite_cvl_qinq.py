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
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
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
import random
from packet import Packet
from pmd_output import PmdOutput
from test_case import TestCase, check_supported_nic, skip_unsupported_pkg
from utils import GREEN, RED
from rte_flow_common import RssProcessing

mac_qinq_ipv4_pay_src_ip = {
    'name': 'mac_qinq_ipv4_pay_src_ip',
    'rule': 'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv4 src is 196.222.232.221 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.222")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)']},
    'check_param': {'port_id':1}
}

mac_qinq_ipv4_pay_dst_ip = {
    'name': 'mac_qinq_ipv4_pay_dst_ip',
    'rule': 'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv4 dst is 196.222.232.221 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.222")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP(dst="196.222.232.221")/("X"*480)']},
    'check_param': {'port_id':1}
}

mac_qinq_ipv4_pay_dest_mac = {
    'name': 'mac_qinq_ipv4_pay_dest_mac',
    'rule': 'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv4 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x0800)/IP()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x0800)/IP()/("X"*480)',
                              ]},
    'check_param': {'port_id':1}
}

mac_qinq_ipv4_pay = [mac_qinq_ipv4_pay_src_ip, mac_qinq_ipv4_pay_dst_ip, mac_qinq_ipv4_pay_dest_mac]

mac_qinq_ipv6_pay_src_ip = {
    'name': 'mac_qinq_ipv6_pay_src_ip',
    'rule': 'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv6 src is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:9999")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)']},
    'check_param': {'port_id': 1}
}

mac_qinq_ipv6_pay_dst_ip = {
    'name': 'mac_qinq_ipv6_pay_dst_ip',
    'rule': 'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)']},
    'check_param': {'port_id': 1}
}

mac_qinq_ipv6_pay_dest_mac = {
    'name': 'mac_qinq_ipv6_pay_dest_mac',
    'rule': 'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / ipv6 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6()/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x86DD)/IPv6()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x86DD)/IPv6()/("X"*480)',
                              ]},
    'check_param': {'port_id': 1}
}

mac_qinq_ipv6_pay = [mac_qinq_ipv6_pay_src_ip, mac_qinq_ipv6_pay_dst_ip, mac_qinq_ipv6_pay_dest_mac]

mac_qinq_pppoe_pay = [{
    'name': 'mac_qinq_pppoe_pay',
    'rule': 'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)']},
    'check_param': {'port_id': 1}
}]

mac_qinq_pppoe_proto = [{
    'name': 'mac_qinq_pppoe_proto',
    'rule': 'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/("X"*480)']},
    'check_param': {'port_id': 1}
}]

mac_qinq_pppoe_ipv4_src_ip = {
    'name': 'mac_qinq_pppoe_ipv4_src_ip',
    'rule': 'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 src is 196.222.232.221 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.222")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)']},
    'check_param': {'port_id': 1}
}

mac_qinq_pppoe_ipv4_dst_ip = {
    'name': 'mac_qinq_pppoe_ipv4_dst_ip',
    'rule': 'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 dst is 196.222.232.221 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.222")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(src="196.222.232.221")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP(dst="196.222.232.221")/UDP(dport=23)/("X"*480)']},
    'check_param': {'port_id': 1}
}

mac_qinq_pppoe_ipv4_dest_mac = {
    'name': 'mac_qinq_pppoe_ipv4_dest_mac',
    'rule': 'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv4 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IPv6()/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x21\')/IP()/UDP(dport=23)/("X"*480)']},
    'check_param': {'port_id': 1}
}

mac_qinq_pppoe_ipv4 = [mac_qinq_pppoe_ipv4_src_ip, mac_qinq_pppoe_ipv4_dst_ip, mac_qinq_pppoe_ipv4_dest_mac]

mac_qinq_pppoe_ipv6_src_ip = {
    'name': 'mac_qinq_pppoe_ipv6_src_ip',
    'rule': 'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 src is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:9999")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)']},
    'check_param': {'port_id': 1}
}

mac_qinq_pppoe_ipv6_dst_ip = {
    'name': 'mac_qinq_pppoe_ipv6_dst_ip',
    'rule': 'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=23)/("X"*480)']},
    'check_param': {'port_id': 1}
}

mac_qinq_pppoe_ipv6_dest_mac = {
    'name': 'mac_qinq_pppoe_ipv6_dest_mac',
    'rule': 'flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 2 / vlan tci is 1 / pppoes seid is 1 / ipv6 / end actions vf id 1 / end',
    'scapy_str': {'matched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)'],
               'mismatched': ['Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x2)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IP()/UDP(dport=23)/("X"*480)',
                              'Ether(dst="00:11:22:33:44:33",type=0x8100)/Dot1Q(vlan=2,type=0x8100)/Dot1Q(vlan=0x1,type=0x8864)/PPPoE(sessionid=0x1)/PPP(b\'\\x00\\x57\')/IPv6()/UDP(dport=23)/("X"*480)']},
    'check_param': {'port_id': 1}
}

mac_qinq_pppoe_ipv6 = [mac_qinq_pppoe_ipv6_src_ip, mac_qinq_pppoe_ipv6_dst_ip, mac_qinq_pppoe_ipv6_dest_mac]


class TestCvlQinq(TestCase):

    @check_supported_nic(["columbiaville_25g", "columbiaville_100g", "columbiaville_25gx2"])
    def set_up_all(self):
        '''
        Run at the start of each test suite.
        prerequisites.
        '''
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, 'Insufficient ports for testing')
        # Verify that enough threads are available
        cores = self.dut.get_core_list('1S/4C/1T')
        self.verify(cores is not None, 'Insufficient cores for speed testing')
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.tester_port0 = self.tester.get_local_port(self.dut_ports[0])
        self.tester_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_iface0 = self.tester.get_interface(self.tester_port0)
        self.tester_iface1 = self.tester.get_interface(self.tester_port1)

        self.used_dut_port = self.dut_ports[0]
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        port = self.dut.ports_info[0]['port']
        port.bind_driver()

        self.vf_flag = False
        self.vf0_mac = ''
        self.vf1_mac = '00:11:22:33:44:11'
        self.vf2_mac = '00:11:22:33:44:22'
        self.vf3_mac = '00:11:22:33:44:33'
        self.path = self.dut.apps_name['test-pmd']
        self.pkt = Packet()
        self.pmd_output = PmdOutput(self.dut)

    def set_up(self):
        '''
        Run before each test case.
        '''
        self.pci_list = []
        self.dut.send_expect('ethtool --set-priv-flags %s vf-vlan-prune-disable on' % self.pf_interface, "#")

    def setup_pf_vfs_env(self, vfs_num=4):

        if self.vf_flag is False:
            self.dut.generate_sriov_vfs_by_port(self.used_dut_port, vfs_num, driver=self.kdriver)
            self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]['vfs_port']
            self.vf_flag = True
            if vfs_num > 1:
                self.dut.send_expect('ip link set %s vf 0 trust on' % (self.pf_interface), '# ')
                self.dut.send_expect('ip link set %s vf 1 mac %s' % (self.pf_interface, self.vf1_mac), '# ')
                self.dut.send_expect('ip link set %s vf 2 mac %s' % (self.pf_interface, self.vf2_mac), '# ')
                self.dut.send_expect('ip link set %s vf 3 mac %s' % (self.pf_interface, self.vf3_mac), '# ')
            else:
                self.dut.send_expect('ip link set %s vf 0 mac %s' % (self.pf_interface, self.vf1_mac), '# ')

            try:
                for port in self.sriov_vfs_port:
                    port.bind_driver(self.drivername)
                    self.pci_list.append(port.pci)

                self.vf0_prop = {'opt_host': self.sriov_vfs_port[0].pci}
                self.dut.send_expect('ifconfig %s up' % self.pf_interface, '# ')
                self.dut.send_expect('ip link set dev %s vf 0 spoofchk off' % self.pf_interface, '# ')
                if vfs_num == 4:
                    self.dut.send_expect('ip link set dev %s vf 1 spoofchk off' % self.pf_interface, '# ')
                    self.dut.send_expect('ip link set dev %s vf 2 spoofchk off' % self.pf_interface, '# ')
                    self.dut.send_expect('ip link set dev %s vf 3 spoofchk off' % self.pf_interface, '# ')
            except Exception as e:
                self.destroy_iavf()
                raise Exception(e)

    def destroy_iavf(self):
        if self.vf_flag is True:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.vf_flag = False

    def launch_testpmd(self, vfs_num=4, dcf_param=False):
        if dcf_param:
            port_options = {self.pci_list[0]: 'cap=dcf,representor=[1]'}
        else:
            port_options = {self.pci_list[0]: 'cap=dcf'}
        if vfs_num > 1:
            param = ' '
            self.pmd_output.start_testpmd(cores='1S/4C/1T', param=param,
                                          ports=self.pci_list, socket=self.ports_socket, port_options=port_options)
        else:
            param = '--rxq=16 --txq=16'
            self.pmd_output.start_testpmd(cores='1S/4C/1T', param=param,
                                                ports=self.pci_list, socket=self.ports_socket)
        self.confing_testpmd(vfs_num, dcf_param)

    def confing_testpmd(self, vfs_num, dcf_param):
        driver_type = 'Device name.*?%s.*?\n(.*)' % self.sriov_vfs_port[0].pci
        if dcf_param or vfs_num == 1:
            flow_type = 'mac'
            if vfs_num > 1:
                output = self.pmd_output.execute_cmd('show port info all')
                out = re.findall(driver_type, output)
                self.verify(len(out) == 2, "port0 and port1 driver not is net_ice_dcf")
        else:
            flow_type = 'rxonly'
            output = self.pmd_output.execute_cmd('show port info 0')
            out = re.findall(driver_type, output)
            self.verify(len(out) == 1, "vf0 driver not is net_ice_dcf")
        self.pmd_output.execute_cmd('set fwd %s' % flow_type)
        self.pmd_output.execute_cmd('set verbose 1')
        self.pmd_output.execute_cmd('start')

    def create_switch_rule(self, rule, session_name="", check_stats=True):
        if session_name == "":
            session_name = self.pmd_output
        p = re.compile(r"Flow rule #(\d+) created")
        rule_list = []
        if isinstance(rule, list):
            for rule in rule:
                out = session_name.execute_cmd(rule)  #create a rule
                m = p.search(out)
                if m:
                    rule_list.append(m.group(1))
                else:
                    rule_list.append(False)
        else:
            out = session_name.execute_cmd(rule)  #create a rule
            m = p.search(out)
            if m:
                rule_list.append(m.group(1))
            else:
                rule_list.append(False)
        if check_stats:
            self.verify(all(rule_list), "some rules not created successfully, result %s, rule %s" % (rule_list, rule))
        else:
            self.verify(not any(rule_list), "all rules should create failed, result %s" % rule_list)
        return rule_list

    def check_switch_rule(self, port_id=0, stats=True, rule_list=None):
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

    def destroy_switch_rule(self, port_id=0, rule_id=None):
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
        self.check_switch_rule(stats=False)

    def send_packets(self, pkts, tx_port=None, count=1):
        self.pkt.update_pkt(pkts)
        tx_port = self.tester_iface0 if not tx_port else tx_port
        self.pkt.send_pkt(crb=self.tester, tx_port=tx_port, count=count)

    def send_pkts_getouput(self, pkts, port_id=0, count=1):
        tx_port = self.tester_iface0 if port_id == 0 else self.tester_iface1
        self.send_packets(pkts, tx_port=tx_port, count=count)
        time.sleep(0.5)
        out = self.pmd_output.get_output()
        port_stats = self.pmd_output.execute_cmd("show port stats all")
        self.pmd_output.execute_cmd("clear port stats all")
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("start")
        return out + port_stats

    def check_packets(self, out, port_id, pkt_num=1, check_stats=True):
        p = 'port (\d+)/queue.*'
        result_list = re.findall(p, out)
        if check_stats:
            self.verify(len(result_list) == pkt_num, "received packets mismatch".format(port_id))
        for res in result_list:
            if check_stats:
                self.verify(int(res) == port_id, "port {} did not received the packets".format(port_id))
            else:
                self.verify(int(res) != port_id, "port {} should not received a packets".format(port_id))

    def _rte_flow_validate_pattern(self, test_vector):
        test_results = {}
        for test in test_vector:
            self.logger.info((GREEN("========test subcase: %s========" % test["name"])))
            try:
                port_id = test['check_param']['port_id']
                rule_list = self.create_switch_rule(test['rule'])
                self.check_switch_rule()
                # send matched packets and check
                matched_packets = test['scapy_str']['matched']
                out = self.send_pkts_getouput(matched_packets)
                self.check_packets(out, port_id, len(matched_packets))
                # send mismatched packets and check
                mismatched_packets = test['scapy_str']['mismatched']
                out = self.send_pkts_getouput(mismatched_packets)
                self.check_packets(out, port_id, len(mismatched_packets), check_stats=False)
                self.destroy_switch_rule()
                out = self.send_pkts_getouput(matched_packets)
                self.check_packets(out, port_id, len(matched_packets), check_stats=False)
                test_results[test["name"]] = True
                self.logger.info((GREEN("subcase passed: %s" % test["name"])))
            except Exception as e:
                self.logger.warning((RED(e)))
                self.dut.send_command("flow flush 0", timeout=1)
                self.dut.send_command("flow flush 1", timeout=1)
                test_results[test["name"]] = False
                self.logger.info((RED("subcase failed: %s" % test["name"])))
                continue
        failed_cases = []
        for k, v in list(test_results.items()):
            if not v:
                failed_cases.append(k)
        self.verify(all(test_results.values()), "{} failed.".format(failed_cases))

    def start_tcpdump(self, rxItf):
        self.tester.send_expect("rm -rf getPackageByTcpdump.cap", "#")
        self.tester.send_expect("tcpdump -A -nn -e -vv -w getPackageByTcpdump.cap -i %s 2> /dev/null& " % rxItf, "#")
        time.sleep(2)

    def get_tcpdump_package(self):
        time.sleep(1)
        self.tester.send_expect("killall tcpdump", "#")
        return self.tester.send_expect("tcpdump -A -nn -e -vv -r getPackageByTcpdump.cap", "#")

    def test_mac_qinq_ipv4_pay(self):
        """
        DCF switch for MAC_QINQ_IPV4_PAY
        """
        self.setup_pf_vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_ipv4_pay)

    def test_mac_qinq_ipv6_pay(self):
        """
        DCF switch for MAC_QINQ_IPV6_PAY
        """
        self.setup_pf_vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_ipv6_pay)

    @skip_unsupported_pkg('os default')
    def test_mac_qinq_pppoe_pay(self):
        """
        DCF switch for MAC_QINQ_PPPOE_PAY
        """
        self.setup_pf_vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_pppoe_pay)

    @skip_unsupported_pkg('os default')
    def test_mac_qinq_pppoe_pay_proto(self):
        """
        DCF switch for MAC_QINQ_PPPOE_PAY_Proto
        """
        self.setup_pf_vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_pppoe_proto)

    @skip_unsupported_pkg('os default')
    def test_mac_qinq_pppoe_ipv4(self):
        """
        DCF switch for MAC_QINQ_PPPOE_IPV4
        """
        self.setup_pf_vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_pppoe_ipv4)

    @skip_unsupported_pkg('os default')
    def test_mac_qinq_pppoe_ipv6(self):
        """
        DCF switch for MAC_QINQ_PPPOE_IPV6
        """
        self.setup_pf_vfs_env()
        self.launch_testpmd()
        self._rte_flow_validate_pattern(mac_qinq_pppoe_ipv6)

    def reset_vf(self):
        self.pmd_output.execute_cmd("port stop 2")
        self.pmd_output.execute_cmd("port reset 2")
        self.pmd_output.execute_cmd("port start 2")
        self.pmd_output.execute_cmd("start")

    def send_packet_check_vlan_strip(self, pkts, outer=False, inner=False):
        for pkt in pkts:
            pkt_index = pkts.index(pkt)
            self.start_tcpdump(self.tester_iface0)
            out = self.send_pkts_getouput(pkt)
            self.check_packets(out, 2, pkt_num=1)
            tcpdump_out = self.get_tcpdump_package()
            vlan_list = re.findall("vlan \d+", tcpdump_out)
            if pkt_index == 1:
                vlan_num = 2
                if outer or inner:
                    vlan_num -= 1
                self.verify(len(vlan_list) == vlan_num, "received outer vlan packet!!!")
            else:
                vlan_num = 4
                if inner and outer:
                    vlan_num -= 2
                elif outer:
                    vlan_num -= 1
                self.verify(len(vlan_list) == vlan_num, "received outer vlan packet error!!!")

    def test_vlan_strip_in_pvid_enable(self):
        """
        vlan strip when pvid enable
        """
        pkts = ['Ether(dst="%s",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac,
                'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=21,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac]
        self.setup_pf_vfs_env()
        self.launch_testpmd(dcf_param=True)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set strip on 1")
        self.reset_vf()
        self.send_packet_check_vlan_strip(pkts, outer=True)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set strip off 1")
        self.reset_vf()
        self.send_packet_check_vlan_strip(pkts)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set strip on 1")
        self.reset_vf()
        self.pmd_output.execute_cmd("vlan set strip on 2")
        self.send_packet_check_vlan_strip(pkts, outer=True, inner=True)
        self.pmd_output.execute_cmd("quit", "#")
        self.launch_testpmd(dcf_param=True)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set strip on 2")
        self.pmd_output.execute_cmd("vlan set strip on 1")
        self.reset_vf()
        self.send_packet_check_vlan_strip(pkts, outer=True, inner=True)

    def _send_packet_check_vlan_inter(self, pkts, out_vlan, port_id=3,  vlan_header=None, iner_vlan=None):
        for pkt in pkts:
            pkt_index = pkts.index(pkt)
            self.start_tcpdump(self.tester_iface0)
            out = self.send_pkts_getouput(pkt)
            self.check_packets(out, port_id)
            p = "vlan (\d+)"
            tcpdump_out = self.get_tcpdump_package()
            vlan_list = re.findall(p, tcpdump_out)
            if vlan_header:
                header = re.findall(vlan_header, tcpdump_out)
            if pkt_index == 0:
                if out_vlan == 1:
                    self.verify(len(vlan_list) == 1, "received packet outer vlan not is %s" % out_vlan)
                elif out_vlan == 0:
                    self.verify(len(vlan_list) == 0, "received packet outer vlan not is %s" % out_vlan)
                else:
                    self.verify(int(vlan_list[0]) == out_vlan, "received packet outer vlan not is %s" % out_vlan)
                if iner_vlan:
                    self.verify(int(vlan_list[1]) == iner_vlan, "received packet outer vlan not is %s" % iner_vlan)
            else:
                if out_vlan == 1:
                    self.verify(len(vlan_list) == 3 and int(vlan_list[1]) == out_vlan, "received packet outer vlan not is %s" % out_vlan)
                elif out_vlan == 0:
                    self.verify(len(vlan_list) == 2, "received packet outer vlan not is %s" % out_vlan)
                else:
                    self.verify(int(vlan_list[1]) == out_vlan, "received packet outer vlan not is %s" % out_vlan)
                if iner_vlan:
                    self.verify(int(vlan_list[2]) == iner_vlan, "received packet outer vlan not is %s" % iner_vlan)
            if vlan_header == "0x8100":
                self.verify(vlan_header in tcpdump_out, "vlan header not matched, expect: %s." % vlan_header)
            elif vlan_header is None:
                pass
            else:
                self.verify(len(header) == 1, "vlan header not matched, expect: %s." % vlan_header)

    def test_vlan_insert_in_pvid_enable(self):
        """
        vlan insertion when pvid enable
        """
        out_vlan = 24
        iner_vlan = 11
        header = "0x8100"
        pkt_list = ['Ether(dst="%s",type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf2_mac,
                    'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf2_mac]
        self.setup_pf_vfs_env()
        self.launch_testpmd(dcf_param=True)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("tx_vlan set pvid 1 %d on" % out_vlan)
        self.reset_vf()
        self._send_packet_check_vlan_inter(pkt_list, out_vlan, vlan_header=header)
        header = "0x88a8"
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set outer tpid %s 1" % header)
        self.reset_vf()
        self._send_packet_check_vlan_inter(pkt_list, out_vlan, vlan_header=header)
        header = "0x9100"
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set outer tpid %s 1" % header)
        self.reset_vf()
        self._send_packet_check_vlan_inter(pkt_list, out_vlan, vlan_header=header)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop 2")
        self.pmd_output.execute_cmd("tx_vlan set 2 %d" % iner_vlan)
        self.pmd_output.execute_cmd("port start 2")
        self.pmd_output.execute_cmd("start")
        self._send_packet_check_vlan_inter(pkt_list, out_vlan, vlan_header=header, iner_vlan=iner_vlan)
        self.pmd_output.execute_cmd("quit", "# ")
        self.launch_testpmd(dcf_param=True)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop 2")
        self.pmd_output.execute_cmd("tx_vlan set 2 %d" % iner_vlan)
        self.pmd_output.execute_cmd("port start 2")
        self.pmd_output.execute_cmd("tx_vlan set pvid 1 %d on" % out_vlan)
        self.reset_vf()
        self._send_packet_check_vlan_inter(pkt_list, out_vlan, port_id=3, vlan_header=header, iner_vlan=iner_vlan)

    def test_vlan_filter_in_pvid_enable(self):
        """
        vlan filter when pvid enable
        """
        pkt_list1 = ['Ether(dst="%s",type=0x8100)/Dot1Q(vlan=11,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac,
                     'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=11,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac]
        pkt_list2 = ['Ether(dst="%s",type=0x8100)/Dot1Q(vlan=21,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac,
                     'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=21,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac]
        self.dut.send_expect('ethtool --set-priv-flags %s vf-vlan-prune-disable off' % self.pf_interface, '#')
        self.setup_pf_vfs_env()
        self.launch_testpmd(dcf_param=True)
        self.pmd_output.execute_cmd("vlan set filter on 1")
        out = self.pmd_output.execute_cmd("rx_vlan add 11 1")
        self.verify("failed" in out, "add rx_vlan successfully for VF1 by representor")
        self.pmd_output.execute_cmd("vlan set filter on 2")
        self.pmd_output.execute_cmd("rx_vlan add 11 2")
        for pkt in pkt_list1:
            out = self.send_pkts_getouput(pkt)
            self.check_packets(out, 2)
        for pkt in pkt_list2:
            out = self.send_pkts_getouput(pkt)
            self.check_packets(out, 2, pkt_num=0, check_stats=False)
        self.pmd_output.execute_cmd("rx_vlan rm 11 2")
        for pkt in pkt_list1:
            out = self.send_pkts_getouput(pkt)
            self.check_packets(out, 2, pkt_num=0, check_stats=False)

    def check_vlan_offload(self, vlan_type, stats):
        p = "VLAN offload.*\n.*?%s (\w+)" % vlan_type
        out = self.pmd_output.execute_cmd("show port info 0")
        vlan_stats = re.search(p, out).group(1)
        self.verify(vlan_stats == stats, "VLAN stats mismatch")

    def test_enable_disable_iavf_vlan_filter(self):
        """
        Enable/Disable IAVF VLAN filtering
        """
        pkt_list1 = ['Ether(dst="%s",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac,
                     'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac]
        pkt_list2 = ['Ether(dst="%s",type=0x8100)/Dot1Q(vlan=11,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac,
                     'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=11,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac]
        self.dut.send_expect('ethtool --set-priv-flags %s vf-vlan-prune-disable off' % self.pf_interface, '#')
        self.setup_pf_vfs_env(vfs_num=1)
        self.launch_testpmd(vfs_num=1)
        self.pmd_output.execute_cmd("vlan set filter on 0")
        self.check_vlan_offload(vlan_type="filter", stats="on")
        out = self.send_pkts_getouput(pkt_list1)
        receive_pkt = re.findall('dst=%s' % self.vf1_mac, out)
        self.verify(len(receive_pkt) == 0, 'Failed error received vlan packet!')

        self.pmd_output.execute_cmd("rx_vlan add 1 0")
        self.start_tcpdump(self.tester_iface0)
        out = self.send_pkts_getouput(pkt_list1)
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall("dst=%s" % self.vf1_mac, out)
        self.verify(len(receive_pkt) == 2, "Failed error received vlan packet!")
        tester_pkt = re.findall("vlan \d+", tcpdump_out)
        self.verify(len(tester_pkt) == 6, "Failed pass received vlan packet!")

        out = self.send_pkts_getouput(pkt_list2)
        receive_pkt = re.findall('dst=%s' % self.vf1_mac, out)
        self.verify(len(receive_pkt) == 0, 'Failed error received vlan packet!')

        self.pmd_output.execute_cmd("rx_vlan rm 1 0")
        out = self.send_pkts_getouput(pkt_list1)
        receive_pkt = re.findall('dst=%s' % self.vf1_mac, out)
        self.verify(len(receive_pkt) == 0, 'Failed error received vlan packet!')

    def test_enable_disable_iavf_vlan_strip(self):
        """
        Enable/Disable IAVF VLAN header stripping
        """
        pkt_list = ['Ether(dst="%s",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac,
                    'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac]
        self.dut.send_expect('ethtool --set-priv-flags %s vf-vlan-prune-disable off' % self.pf_interface, '#')
        self.setup_pf_vfs_env(vfs_num=1)
        self.launch_testpmd(vfs_num=1)
        self.pmd_output.execute_cmd("vlan set filter on 0")
        self.pmd_output.execute_cmd("rx_vlan add 1 0")
        self.check_vlan_offload(vlan_type="filter", stats="on")
        self.pmd_output.execute_cmd("vlan set strip on 0")
        self.check_vlan_offload(vlan_type="strip", stats="on")

        self.start_tcpdump(self.tester_iface0)
        out = self.send_pkts_getouput(pkt_list)
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall("dst=%s" % self.vf1_mac, out)
        self.verify(len(receive_pkt) == 2, "Failed error received vlan packet!")
        tester_pkt = re.findall("vlan \d+", tcpdump_out)
        self.verify(len(tester_pkt) == 4, "Failed pass received vlan packet!")

        self.pmd_output.execute_cmd("vlan set strip off 0")
        self.check_vlan_offload(vlan_type="strip", stats="off")
        self.start_tcpdump(self.tester_iface0)
        out = self.send_pkts_getouput(pkt_list)
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall("dst=%s" % self.vf1_mac, out)
        self.verify(len(receive_pkt) == 2, "Failed error received vlan packet!")
        tester_pkt = re.findall("vlan \d+", tcpdump_out)
        self.verify(len(tester_pkt) == 6, "Failed pass received vlan packet!")

    def test_enable_disable_iavf_vlan_insert(self):
        """
        Enable/Disable IAVF VLAN header insertion
        """
        out_vlan = 1
        pkt_list = ['Ether(dst="%s",type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac,
                    'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=11,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac]
        self.dut.send_expect('ethtool --set-priv-flags %s vf-vlan-prune-disable on' % self.pf_interface, '#')
        self.setup_pf_vfs_env(vfs_num=1)
        self.launch_testpmd(vfs_num=1)
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop 0")
        self.pmd_output.execute_cmd("tx_vlan set 0 1")
        self.pmd_output.execute_cmd("port start 0")
        self.pmd_output.execute_cmd("start")
        self._send_packet_check_vlan_inter(pkt_list, out_vlan, port_id=0)

        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop 0")
        self.pmd_output.execute_cmd("tx_vlan reset 0")
        self.pmd_output.execute_cmd("port start 0")
        self.pmd_output.execute_cmd("start")
        self._send_packet_check_vlan_inter(pkt_list, out_vlan=0, port_id=0)

    def _send_pkt_check_vlan_and_crc(self, pkt, pkt_len=None, vlan_strip=False, crc_strip=False):
        if pkt_len:
            self.start_tcpdump(self.tester_iface0)
        out = self.send_pkts_getouput(pkt)
        pkt_length = re.search("length=(\d+)", out).group(1)
        rx_bytes = re.search("RX-bytes:\s+(\d+)", out).group(1)
        if crc_strip:
            self.verify(rx_bytes == pkt_length, "CRC strip on failed")
        else:
            self.verify(int(rx_bytes) == int(pkt_length)+4, "CRC strip off failed")
        if pkt_len:
            tcpdump_out = self.get_tcpdump_package()
            vlan_list = re.findall("vlan\s+\d+", tcpdump_out)
            if not vlan_strip:
                self.verify(pkt_length == pkt_len, "vlan strip off failed")
                self.verify(len(vlan_list) == 4, "Failed pass received vlan packet")
            elif vlan_strip:
                self.verify(int(pkt_length)+4 == int(pkt_len), "vlan strip off failed")
                self.verify(len(vlan_list) == 3 and vlan_list[0] != vlan_list[-1], "Failed error received vlan packet")

    def test_enable_disable_iavf_CRC_strip(self):
        """
        Enable/disable AVF CRC stripping
        """
        param = '--rxq=16 --txq=16 --disable-crc-strip'
        pkt = 'Ether(dst="%s",type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac
        self.dut.send_expect('ethtool --set-priv-flags %s vf-vlan-prune-disable off' % self.pf_interface, '#')
        self.setup_pf_vfs_env(vfs_num=1)
        self.pmd_output.start_testpmd(cores='1S/4C/1T', param=param, ports=self.pci_list, socket=self.ports_socket)
        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")
        self._send_pkt_check_vlan_and_crc(pkt)

        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop 0")
        self.pmd_output.execute_cmd("port config 0 rx_offload keep_crc off")
        self.pmd_output.execute_cmd("port start 0")
        self.pmd_output.execute_cmd("start")
        self._send_pkt_check_vlan_and_crc(pkt, crc_strip=True)

        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop 0")
        self.pmd_output.execute_cmd("port config 0 rx_offload keep_crc on")
        self.pmd_output.execute_cmd("port start 0")
        self.pmd_output.execute_cmd("start")
        self._send_pkt_check_vlan_and_crc(pkt)

        self.pmd_output.execute_cmd("quit", "#")
        self.launch_testpmd(vfs_num=1)
        self.start_tcpdump(self.tester_iface0)
        self._send_pkt_check_vlan_and_crc(pkt, crc_strip=True)

    def test_CRC_strip_iavf_vlan_strip_coexists(self):
        """
        AVF CRC strip and Vlan strip co-exists
        """
        pkt = 'Ether(dst="%s",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="196.222.232.221")/("X"*480)' % self.vf1_mac
        self.dut.send_expect('ethtool --set-priv-flags %s vf-vlan-prune-disable off' % self.pf_interface, "#")
        self.setup_pf_vfs_env(vfs_num=1)
        self.launch_testpmd(vfs_num=1)
        self.check_vlan_offload(vlan_type="strip", stats="off")
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("vlan set strip off 0")
        self.check_vlan_offload(vlan_type="strip", stats="off")
        self.pmd_output.execute_cmd("vlan set filter on 0")
        self.pmd_output.execute_cmd("rx_vlan add 1 0")
        self.pmd_output.execute_cmd("start")

        self.start_tcpdump(self.tester_iface0)
        out = self.send_pkts_getouput(pkt)
        tcpdump_out = self.get_tcpdump_package()
        pkt_len = re.search("length=(\d+)", out).group(1)
        vlan_list = re.findall("vlan\s+\d+", tcpdump_out)
        self.verify(len(vlan_list) == 4, "vlan strip off failed")
        rx_bytes = re.search("RX-bytes:\s+(\d+)", out).group(1)
        tx_bytes = re.search("TX-bytes:\s+(\d+)", out).group(1)
        self.verify(rx_bytes == tx_bytes == pkt_len, "CRC strip on failed")

        self.pmd_output.execute_cmd("vlan set strip on 0")
        self.check_vlan_offload(vlan_type="strip", stats="on")
        self._send_pkt_check_vlan_and_crc(pkt=pkt, pkt_len=pkt_len, vlan_strip=True)

        self.pmd_output.execute_cmd("vlan set strip off 0")
        self.check_vlan_offload(vlan_type="strip", stats="off")
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop 0")
        self.pmd_output.execute_cmd("port config 0 rx_offload keep_crc on")
        self.pmd_output.execute_cmd("port start 0")
        self.pmd_output.execute_cmd("start")
        self._send_pkt_check_vlan_and_crc(pkt=pkt, pkt_len=pkt_len)

        out = self.pmd_output.execute_cmd("vlan set strip on 0")
        p = "iavf_config_vlan_strip_v2(): fail to execute command VIRTCHNL_OP_ENABLE_VLAN_STRIPPING_V2"
        self.verify(p in out, "set vlan strip on successfully")
        self._send_pkt_check_vlan_and_crc(pkt=pkt, pkt_len=pkt_len)

        self.pmd_output.execute_cmd("vlan set strip off 0")
        self.check_vlan_offload(vlan_type="strip", stats="off")
        self.pmd_output.execute_cmd("stop")
        self.pmd_output.execute_cmd("port stop 0")
        self.pmd_output.execute_cmd("port config 0 rx_offload keep_crc off")
        self.pmd_output.execute_cmd("port start 0")
        self.pmd_output.execute_cmd("start")
        self._send_pkt_check_vlan_and_crc(pkt=pkt, pkt_len=pkt_len, crc_strip=True)

    def tear_down(self):
        self.pmd_output.execute_cmd('quit', '#')
        self.dut.kill_all()
        self.destroy_iavf()

    def tear_down_all(self):
        self.dut.send_expect('ethtool --set-priv-flags %s vf-vlan-prune-disable off' % self.pf_interface, '#')