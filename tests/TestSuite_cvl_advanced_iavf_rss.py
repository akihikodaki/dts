import re
import time

from packet import Packet
from pmd_output import PmdOutput
from test_case import TestCase
import rte_flow_common as rfc

vf0_mac = "00:01:23:45:67:89"
vf1_mac = "00:11:22:33:44:55"

tv_iavf_mac_eth_src_only = {
    "name": "iavf_mac_eth_src_only",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4  / end actions rss types l2-src-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(src=RandMAC())/IP()/("X"*480)'],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_eth_dst_only = {
    "name": "iavf_mac_eth_dst_only",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4  / end actions rss types l2-dst-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP()/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_l3_src = {
    "name": "iavf_mac_ipv4_l3_src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_l3_src_frag = {
    "name": "iavf_mac_ipv4_l3_src_frag",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP(),frag=5)/SCTP(sport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP(src=RandIP(), dst="192.168.0.8", frag=5)/SCTP(sport=RandShort())/("X" * 80)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_l3_dst = {
    "name": "iavf_mac_ipv4_l3_dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(dst=RandIP())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP(src="192.168.0.8",dst=RandIP())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_l3_dst_frag = {
    "name": "iavf_mac_ipv4_l3_dst_frag",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(dst=RandIP(), frag=5)/SCTP(sport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_l3_src_frag_icmp = {
    "name": "iavf_mac_ipv4_l3_dst_frag_icmp",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP(), frag=5)/ICMP()/("X" *480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_l3_dst_frag_icmp = {
    "name": "iavf_mac_ipv4_l3_dst_frag_icmp",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(dst=RandIP(), frag=5)/ICMP()/("X" *480)' % vf0_mac,
                  'Ether(dst="%s")/IP(dst=RandIP(), src="192.168.0.5",frag=5)/ICMP()/("X" * 80)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_pay = {
    "name": "iavf_mac_ipv4_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/("X" *480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_pay_frag_icmp = {
    "name": "iavf_mac_ipv4_pay_frag_icmp",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/ICMP()/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_l3_src_nvgre = {
    "name": "iavf_mac_ipv4_l3_src_nvgre",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP()/NVGRE()/Ether()/IP(src=RandIP())/ICMP()/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_l3_dst_nvgre = {
    "name": "iavf_mac_ipv4_l3_dst_nvgre",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP()/NVGRE()/Ether()/IP(dst=RandIP())/ICMP()/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_nvgre_udp_frag = {
    "name": "iavf_mac_ipv4_nvgre_udp_frag",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP()/NVGRE()/Ether()/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_nvgre_sctp = {
    "name": "iavf_mac_ipv4_nvgre_sctp",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP()/NVGRE()/Ether()/IP(src=RandIP(),dst=RandIP())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_tcp_pay = {
    "name": "iavf_mac_ipv4_tcp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP()/TCP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/TCP()/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP(src=RandIP(),dst=RandIP(),frag=4)/TCP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac,
                  ],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_tcp_frag = {
    "name": "iavf_mac_ipv4_tcp_frag",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP()) / TCP(dport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP(src=RandIP(),dst="192.168.0.2")/TCP(sport=22,dport=RandShort())/("X"*480)' % vf0_mac,
                  ],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_udp = {
    "name": "iavf_mac_ipv4_udp",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types l3-src-only l4-dst-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP())/UDP(dport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP(src=RandIP(),dst="192.168.0.2")/UDP(sport=33,dport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_udp_frag = {
    "name": "iavf_mac_ipv4_udp_frag",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP()/UDP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/UDP()/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_sctp = {
    "name": "iavf_mac_ipv4_sctp",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types l3-src-only l4-dst-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP())/SCTP(dport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP(dst=RandIP())/SCTP(sport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_sctp_frag = {
    "name": "iavf_mac_ipv4_sctp_frag",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP()/UDP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/UDP()/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_l3_src = {
    "name": "iavf_mac_ipv6_l3_src",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / end actions rss types l3-src-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_l3_src_frag = {
    "name": "iavf_mac_ipv6_l3_src_frag",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / end actions rss types l3-src-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IPv6(src=RandIP6(),dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X" * 480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_l3_dst = {
    "name": "iavf_mac_ipv6_l3_dst",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / end actions rss types l3-dst-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6(dst=RandIP6())/IPv6ExtHdrFragment()/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst=RandIP6())/IPv6ExtHdrFragment()/("X" * 480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_pay = {
    "name": "iavf_mac_ipv6_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6(),dst=RandIP6())/IPv6ExtHdrFragment()/ICMP()/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_sctp_pay = {
    "name": "iavf_mac_ipv6_sctp_pay",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}
tv_iavf_mac_ipv6_udp = {
    "name": "iavf_mac_ipv6_udp",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6()) / UDP(sport=RandShort(), dport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_udp_frag = {
    "name": "iavf_mac_ipv6_udp_frag",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/UDP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_tcp = {
    "name": "iavf_mac_ipv6_tcp",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_tcp_frag = {
    "name": "iavf_mac_ipv6_tcp_frag",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6())/IPv6ExtHdrFragment()/TCP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_cvlan_rss = {
    "name": "iavf_mac_cvlan_rss",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss types c-vlan end key_len 0 queues end / end",
    "scapy_str": ['Ether()/Dot1Q(vlan=RandShort())/IP(src=RandIP())/UDP()/("X"*480)',
                  'Ether(type=0x8100)/Dot1Q(vlan=RandShort())/Dot1Q(vlan=56)/IP(src=RandIP())/UDP()/("X"*480)',
                  ],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_pfcp_session = {
    "name": "iavf_mac_ipv4_pfcp_session",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end",
    "scapy_str": [
        'Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=1, SEID=12)/Raw("X"*480)' % vf0_mac,
        'Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=0)/("X"*480)' % vf0_mac,
        'Ether(dst="%s")/IPv6()/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=1, SEID=12)/("X"*480)' % vf0_mac,
    ],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_pfcp_session = {
    "name": "iavf_mac_ipv6_pfcp_session",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6()/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=1, SEID=12)/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IPv6()/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=0)/("X"*480)' % vf0_mac,
                  'Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/PFCP(Sfield=1, SEID=12)/'
                  '("X"*480)' % vf0_mac,
                  ],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_up_match_dismatch = {
    "name": "iavf_gtpu_ipv4_up_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / "
                        "end actions rss types l3-src-only end key_len 0 queues end / end",

    "match_str": ['Ether(src="00:00:00:00:01:01",dst="%s")/IP() / UDP(dport=2152) / GTP_U_Header(gtp_type=255,teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader( pdu_type=1, qos_flow=0x34) / IP(src=RandIP()) /("X"*480)' % vf0_mac],

    "dismatch_str": ['Ether(src="00:00:00:00:01:01",dst="%s")/IP() / UDP(dport=2152) / GTP_U_Header(gtp_type=255,teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader( pdu_type=0, qos_flow=0x34) / IP(dst=RandIP()) /("X"*480)' % vf0_mac,
                     'Ether(src="00:00:00:00:01:01",dst="%s")/IP() / UDP(dport=2152) / GTP_U_Header(gtp_type=255,teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader( pdu_type=0, qos_flow=0x34) / IP(dst=RandIP()) / UDP() /("X"*480)' % vf0_mac,
                     ],

    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_down_match_dismatch = {
    "name": "iavf_gtpu_ipv4_down_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / "
                        "end actions rss types l3-dst-only end key_len 0 queues end / end",

    "match_str": ['Ether(src="00:00:00:00:01:01",dst="%s")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(dst=RandIP())/("X"*480)' % vf0_mac],

    "dismatch_str": ['Ether(src="00:00:00:00:01:01",dst="%s")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP())/("X"*480)' % vf0_mac,
                     ],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_frag_up_match_dismatch = {
    "name": "iavf_gtpu_ipv4_frag_up_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end "
                        "key_len 0 queues end / end ",

    "match_str": ['Ether(src="00:00:00:00:01:01", dst="%s")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP(),frag=6)/("X"*480)' % vf0_mac],

    "dismatch_str": ['Ether(src="00:00:00:00:01:01", dst="%s")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(src=RandIP(),frag=6)/("X"*480)' % vf0_mac],

    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_frag_down_match_dismatch = {

    "name": "iavf_gtpu_ipv4_frag_down_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end "
                        "key_len 0 queues end / end ",

    "match_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34) / IP(dst=RandIP(), frag=6) /("X"*480)' % vf0_mac],

    "dismatch_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34) / IP(src=RandIP(), frag=6) /("X"*480)' % vf0_mac],

    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_udp_up_match_dismatch = {
    "name": "iavf_gtpu_ipv4_udp_up_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types "
                        "l3-src-only end key_len 0 queues end / end",

    "match_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152) / GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP()) / UDP(dport=RandShort())/("X"*480)' % vf0_mac],

    "dismatch_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152) / GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP()) / UDP(dport=RandShort())/("X"*480)' % vf0_mac],

    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_udp_down_match_dismatch = {

    "name": "iavf_gtpu_ipv4_udp_down_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end "
                        "key_len 0 queues end / end ",

    "match_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34) / IP(dst=RandIP(), frag=6) /("X"*480)' % vf0_mac],

    "dismatch_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34) / IP(src=RandIP(), frag=6) /("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_tcp_up_match_dismatch = {
    "name": "iavf_gtpu_ipv4_tcp_up_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp /"
                        " end actions rss types l3-src-only end key_len 0 queues end / end",

    "match_str": ['Ether(dst="%s") / IP() / UDP(dport=2152) / GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP())/TCP(dport=RandShort())/("X"*480)' % vf0_mac],

    "dismatch_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / TCP(dport=2152) / GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP())/TCP(dport=RandShort())/("X"*480)' % vf0_mac],

    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_tcp_down_match_dismatch = {

    "name": "iavf_gtpu_ipv4_tcp_down_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp /"
                        " end actions rss types l3-dst-only end key_len 0 queues end / end",

    "match_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34) /IP(dst=RandIP())/TCP(dport=RandShort())/("X"*480)' % vf0_mac],

    "dismatch_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / TCP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34) /IP(src=RandIP())/TCP(dport=RandShort())/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_icmp_up_match_dismatch = {
    "name": "iavf_gtpu_ipv4_icmp_up_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end "
                        "key_len 0 queues end / end",

    "match_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152) / GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP())/ICMP()/("X"*480)' % vf0_mac],

    "dismatch_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152) / GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP())/ICMP()/("X"*480)' % vf0_mac],

    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_icmp_down_match_dismatch = {

    "name": "iavf_gtpu_ipv4_icmp_down_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end "
                        "key_len 0 queues end / end",

    "match_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34) /IP(dst=RandIP())/ICMP()/("X"*480)' % vf0_mac],

    "dismatch_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34) /IP(src=RandIP())/ICMP()/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_sctp_up_match_dismatch = {
    "name": "iavf_gtpu_ipv4_sctp_up_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end "
                        "key_len 0 queues end / end",
    "match_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152) / GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(src=RandIP())/SCTP()/("X"*480)' % vf0_mac],
    "dismatch_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152) / GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(dst=RandIP())/SCTP()/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_gtpu_ipv4_sctp_down_match_dismatch = {
    "name": "iavf_gtpu_ipv4_sctp_down_match_dismatch",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types l3-dst-only end "
                        "key_len 0 queues end / end",
    "match_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                  'GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34) /IP(dst=RandIP())/SCTP()/("X"*480)' % vf0_mac],
    "dismatch_str": ['Ether(src="00:00:00:00:01:01", dst="%s") / IP() / UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/'
                     'GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34) /IP(src=RandIP())/SCTP()/("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_mac_ipv4_tcp_inputset = {
    "name": "iavf_mac_ipv4_tcp_inputset",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end",
    "pf_rule": "rx-flow-hash tcp4 sdfn",
    "check_pf_rule_set": "rx-flow-hash tcp4",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "pf_scapy": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)'],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue,
    "check_pf_rss_func": rfc.check_pf_rss_queue
}

tv_mac_ipv4_udp_inputset = {
    "name": "iavf_mac_ipv4_udp_inputset",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
    "pf_rule": "rx-flow-hash udp4 sdfn",
    "check_pf_rule_set": "rx-flow-hash udp4",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "pf_scapy": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)'],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue,
    "check_pf_rss_func": rfc.check_pf_rss_queue
}

tv_mac_ipv4_sctp_inputset = {
    "name": "iavf_mac_ipv4_sctp_inputset",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-sctp4 end key_len 0 queues end / end",
    "pf_rule": "rx-flow-hash sctp4 sdfn",
    "check_pf_rule_set": "rx-flow-hash sctp4",
    "scapy_str": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "pf_scapy": ['Ether(dst="%s")/IP(src=RandIP(),dst=RandIP())/SCTP()/("X"*480)'],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue,
    "check_pf_rss_func": rfc.check_pf_rss_queue
}

tv_mac_ipv6_tcp_inputset = {
    "name": "iavf_mac_ipv6_tcp_inputset",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end",
    "pf_rule": "rx-flow-hash tcp6 sdfn",
    "check_pf_rule_set": "rx-flow-hash tcp6",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6(),dst=RandIP6())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "pf_scapy": ['Ether(dst="%s")/IPv6(src=RandIP6(),dst=RandIP6())/TCP(sport=RandShort(),dport=RandShort())/("X"*480)'],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue,
    "check_pf_rss_func": rfc.check_pf_rss_queue
}

tv_mac_ipv6_udp_inputset = {
    "name": "iavf_mac_ipv6_udp_inputset",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end",
    "pf_rule": "rrx-flow-hash udp6 sdfn",
    "check_pf_rule_set": "rx-flow-hash udp6",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6(),dst=RandIP6())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "pf_scapy": ['Ether(dst="%s")/IPv6(src=RandIP6(),dst=RandIP6())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)'],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue,
    "check_pf_rss_func": rfc.check_pf_rss_queue
}

tv_mac_ipv6_sctp_inputset = {
    "name": "iavf_mac_ipv6_sctp_inputset",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end key_len 0 queues end / end",
    "pf_rule": "rx-flow-hash sctp6 sdfn",
    "check_pf_rule_set": "rx-flow-hash sctp6",
    "scapy_str": ['Ether(dst="%s")/IPv6(src=RandIP6(),dst=RandIP6())/SCTP(sport=RandShort(),dport=RandShort())/("X"*480)' % vf0_mac],
    "pf_scapy": ['Ether(dst="%s")/IPv6(src=RandIP6(),dst=RandIP6())/SCTP()/("X"*480)'],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue,
    "check_pf_rss_func": rfc.check_pf_rss_queue
}

tv_iavf_mac_ipv4_l2tpv3 = {
    "name": "iavf_mac_ipv4_l2tpv3",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src="192.168.0.3", proto=115)/L2TP(hex(RandNum(16,255))[1:]+"\\x00\\x00\\x00")/Raw("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_l2tpv3 = {
    "name": "iavf_mac_ipv6_l2tpv3",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", nh=115)/L2TP(hex(RandNum(16,255))[1:]+"\\x00\\x00\\x00")/Raw("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_esp = {
    "name": "iavf_mac_ipv4_esp",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="%s")/IP(src="192.168.0.3", proto=50)/ESP(spi=RandShort())/Raw("X"*480)' % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_esp = {
    "name": "iavf_mac_ipv6_esp",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / esp / end actions rss types esp end key_len 0 queues end / end",
    "scapy_str": ["Ether(dst='%s')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888', nh=50)/ESP(spi=RandShort())/Raw('X'*480)" % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv4_ah = {
    "name": "iavf_mac_ipv4_ah",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / ah / end actions rss types ah end key_len 0 queues end / end",
    "scapy_str": ["Ether(dst='%s')/IP(src='192.168.0.3', proto=51)/AH(spi=RandShort())/Raw('X'*480)" % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tv_iavf_mac_ipv6_ah = {
    "name": "iavf_mac_ipv6_ah",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv6 / ah / end actions rss types ah end key_len 0 queues end / end",
    "scapy_str": ["Ether(dst='%s')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888', nh=51)/AH(spi=RandShort())/Raw('X'*480)" % vf0_mac],
    "send_count": 100,
    "check_func": rfc.check_iavf_packets_rss_queue
}

tvs_iavf_mac_eth_src = [
    tv_iavf_mac_eth_src_only,
]

tvs_iavf_mac_eth_dst = [
    tv_iavf_mac_eth_dst_only,
]
tvs_iavf_mac_rss_ipv4 = [
    tv_iavf_mac_ipv4_l3_src,
    tv_iavf_mac_ipv4_l3_src_frag,
    tv_iavf_mac_ipv4_l3_dst,
    tv_iavf_mac_ipv4_l3_dst_frag,
    tv_iavf_mac_ipv4_pay,
]

tvs_iavf_mac_rss_ipv4_icmp = [
    tv_iavf_mac_ipv4_l3_src_frag_icmp,
    tv_iavf_mac_ipv4_l3_dst_frag_icmp,
    tv_iavf_mac_ipv4_pay_frag_icmp
]

tvs_iavf_mac_rss_ipv4_nvgre = [
    tv_iavf_mac_ipv4_l3_src_nvgre,
    tv_iavf_mac_ipv4_l3_dst_nvgre,
    tv_iavf_mac_ipv4_nvgre_udp_frag,
    tv_iavf_mac_ipv4_nvgre_sctp,
]

tvs_iavf_mac_rss_ipv4_tcp = [
    tv_iavf_mac_ipv4_tcp_pay,
    tv_iavf_mac_ipv4_tcp_frag,
]

tvs_iavf_mac_rss_ipv4_udp = [
    tv_iavf_mac_ipv4_udp,
    tv_iavf_mac_ipv4_udp_frag,
]

tvs_iavf_mac_rss_ipv4_sctp = [
    tv_iavf_mac_ipv4_sctp,
    tv_iavf_mac_ipv4_sctp_frag,
]

tvs_iavf_mac_rss_ipv6 = [
    tv_iavf_mac_ipv6_l3_src,
    tv_iavf_mac_ipv6_l3_src_frag,
    tv_iavf_mac_ipv6_l3_dst,
    tv_iavf_mac_ipv6_pay,
    # tv_iavf_mac_ipv6_sctp_pay,
]

tvs_iavf_mac_rss_ipv6_udp = [
    tv_iavf_mac_ipv6_udp,
    tv_iavf_mac_ipv6_udp_frag,
]

tvs_iavf_mac_rss_ipv6_tcp = [
    tv_iavf_mac_ipv6_tcp,
    tv_iavf_mac_ipv6_tcp_frag,
]

tvs_iavf_mac_rss_cvlan = [
    tv_iavf_mac_cvlan_rss,
]

tvs_iavf_mac_rss_pfcp = [
    tv_iavf_mac_ipv4_pfcp_session,
    tv_iavf_mac_ipv6_pfcp_session,
]

tvs_iavf_gtpu_ipv4 = [
    tv_iavf_gtpu_ipv4_up_match_dismatch,
    tv_iavf_gtpu_ipv4_down_match_dismatch,
]

tvs_iavf_gtpu_ipv4_frag = [
    tv_iavf_gtpu_ipv4_frag_up_match_dismatch,
    tv_iavf_gtpu_ipv4_frag_down_match_dismatch,
]

tvs_iavf_gtpu_ipv4_udp = [
    tv_iavf_gtpu_ipv4_udp_up_match_dismatch,
    tv_iavf_gtpu_ipv4_udp_down_match_dismatch,
]

tvs_iavf_gtpu_ipv4_tcp = [
    tv_iavf_gtpu_ipv4_tcp_up_match_dismatch,
    tv_iavf_gtpu_ipv4_tcp_down_match_dismatch,
]

tvs_iavf_gtpu_ipv4_icmp = [
    tv_iavf_gtpu_ipv4_icmp_up_match_dismatch,
    tv_iavf_gtpu_ipv4_icmp_down_match_dismatch,
]

tvs_iavf_gtpu_ipv4_sctp = [
    tv_iavf_gtpu_ipv4_sctp_up_match_dismatch,
    tv_iavf_gtpu_ipv4_sctp_down_match_dismatch,
]

tvs_check_pf_vf_inputset = [
    tv_mac_ipv4_tcp_inputset,
    tv_mac_ipv4_udp_inputset,
    tv_mac_ipv4_sctp_inputset,
    tv_mac_ipv6_tcp_inputset,
    tv_mac_ipv6_udp_inputset,
    tv_mac_ipv6_sctp_inputset,
]

tvs_iavf_mac_rss_ipv4_l2tpv3 = [tv_iavf_mac_ipv4_l2tpv3]

tvs_iavf_mac_rss_ipv6_l2tpv3 = [tv_iavf_mac_ipv6_l2tpv3]

tvs_iavf_mac_rss_ipv4_esp = [tv_iavf_mac_ipv4_esp]

tvs_iavf_mac_rss_ipv6_esp = [tv_iavf_mac_ipv6_esp]

tvs_iavf_mac_rss_ipv4_ah = [tv_iavf_mac_ipv4_ah]

tvs_iavf_mac_rss_ipv6_ah = [tv_iavf_mac_ipv6_ah]


class AdvancedIavfRSSTest(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.dut_session = self.dut.create_session("pf_dut")
        self.pmd_session = self.dut.create_session("vf_pmd_dut")
        self.pmd_output = PmdOutput(self.dut)
        self.pmd_output_vf1 = PmdOutput(self.dut, self.pmd_session)
        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.used_dut_port = self.dut_ports[0]
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.tx_iface = self.tester.get_interface(localPort)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.verify(self.nic in ["columbiaville_25g", "columbiaville_100g"], "%s nic not support ethertype filter" % self.nic)
        self.ddp_fdir = "/lib/firmware/updates/intel/ice/ddp/"
        self.os_pkg_name = "ice-1.3.11.0.pkg"
        self.comms_pkg_name = "ice_comms-1.3.16.0.pkg"
        self.vf_flag = False
        self.create_iavf()

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
        if self.running_case == "test_vf_reset":
            self.dut.send_expect("ip link set %s vf 0 trust off" % self.pf_interface, "# ")
            self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf_interface, vf0_mac), "# ")
        elif self.running_case == "test_pf_reset":
            self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf_interface, vf0_mac), "# ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.destroy_iavf()

    def create_iavf(self):

        if self.vf_flag is False:
            self.dut.bind_interfaces_linux('ice')
            self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 2)
            self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]['vfs_port']
            self.vf_flag = True

            try:
                for port in self.sriov_vfs_port:
                    port.bind_driver(self.drivername)

                self.vf0_prop = {'opt_host': self.sriov_vfs_port[0].pci}
                self.vf1_prop = {'opt_host': self.sriov_vfs_port[1].pci}
                self.dut.send_expect("ifconfig %s up" % self.pf_interface, "# ")
                self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf_interface, vf0_mac), "# ")
                self.dut.send_expect("ip link set %s vf 1 mac %s" % (self.pf_interface, vf1_mac), "# ")
            except Exception as e:
                self.destroy_iavf()
                raise Exception(e)

    def destroy_iavf(self):
        if self.vf_flag is True:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.vf_flag = False

    def create_testpmd_command(self, port_info, pmd_param=None):
        """
        Create testpmd command for non-pipeline mode
        """
        port_pci = port_info['opt_host']
        param_str = " --rxq=16 --txq=16 --port-topology=loop "
        if pmd_param is not None:
            param_str = param_str + pmd_param
        self.pmd_output.start_testpmd(cores="1S/8C/1T", param=param_str, eal_param="-w %s" % port_pci)
        self.pmd_output.execute_cmd("set fwd rxonly", "testpmd> ", 15)
        self.pmd_output.execute_cmd("set verbose 1", "testpmd> ", 15)

    def create_testpmd2_command(self, port_info, pmd_param=None):
        """
        Create testpmd command for non-pipeline mode
        """
        self.pmd_session.send_expect("cd /root/dpdk/", "# ")
        port_pci = port_info['opt_host']
        param_str = " --rxq=16 --txq=16 --port-topology=loop "
        if pmd_param is not None:
            param_str = param_str + pmd_param
        self.pmd_output_vf1.start_testpmd(cores=list(range(9, 16)), param=param_str, eal_param="-w %s --file-prefix=multi_vfs_pmd" % port_pci)
        self.pmd_output_vf1.execute_cmd("set fwd rxonly", "testpmd> ", 15)
        self.pmd_output_vf1.execute_cmd("set verbose 1", "testpmd> ", 15)

    def _rte_flow_validate_pattern(self, test_vectors, rss_match=True):
        check_result = 0
        test_results = []
        log_msg = []
        for tv in test_vectors:
            self.pmd_output.execute_cmd(tv["rte_flow_pattern"])  # create a rule
            time.sleep(1)
            self.pkg_count = tv["send_count"]
            # send packet
            if "match" in tv["name"]:
                for match_pkg in tv["match_str"]:
                    out = self._pkg_send(match_pkg, self.pkg_count)
                    result, case_msg = tv["check_func"](out, self.pkg_count)
                    print(case_msg)
                    test_results.append(result)
                for dismatch_pkg in tv["dismatch_str"]:
                    out = self._pkg_send(dismatch_pkg, self.pkg_count)
                    result, case_msg = tv["check_func"](out, self.pkg_count, rss_match=False)
                    print(case_msg)
                    test_results.append(result)
            else:
                for scapy_str in tv["scapy_str"]:
                    out = self._pkg_send(scapy_str, self.pkg_count)
                    result, case_msg = tv["check_func"](out, self.pkg_count, rss_match)
                    print(case_msg)
                    test_results.append(result)
            self.pmd_output.execute_cmd("flow destroy 0 rule 0")

            # check test results
            if False in test_results:
                log_cmd = "%s test failed" % tv["name"]
                check_result = check_result + 1
            else:
                log_cmd = "%s test PASS" % tv["name"]
            log_msg.append(log_cmd)

        self.pmd_output.execute_cmd("flow flush 0")
        self.pmd_output.quit()
        print(log_msg)
        self.verify(check_result == 0, "Some test case failed.")

    def _check_inputset_pattern(self, test_vectors):
        for tv in test_vectors:
            self.pmd_output.execute_cmd(tv["rte_flow_pattern"])  # create a rule
            self.dut_session.send_expect("ethtool -N %s %s" % (self.pf_interface, tv["pf_rule"]), "# ")
            self.dut_session.send_expect("ethtool -n %s %s" % (self.pf_interface, tv["check_pf_rule_set"]), "# ")
            self._set_pf_queue_num()
            self.pkg_count = tv["send_count"]
            # send vf packet
            for scapy_str in tv["scapy_str"]:
                pf_rx_0 = self._get_pf_rx()
                out = self._pkg_send(scapy_str, self.pkg_count)
                result, case_msg = tv["check_func"](out, self.pkg_count)
                self.verify(result, case_msg)
                # check PF not recieve packets
                pf_rx_1 = self._get_pf_rx()
                pf_rx = (pf_rx_1 - pf_rx_0)
                self.verify(pf_rx == 0, "pf recieve vf packets!")

            # send pf packet
            for pf_scapy_str in tv["pf_scapy"]:
                pf_scapy_str = pf_scapy_str % self.pf_mac
                self._pkg_send(pf_scapy_str, self.pkg_count)
                out = self.dut_session.send_expect("ethtool -S %s |grep rx_queue" % self.pf_interface, "# ")
                result = tv["check_pf_rss_func"](out, self.pkg_count)
                self.verify(result, "PF not do hash")
            self.pmd_output.execute_cmd("flow destroy 0 rule 0")

        self.pmd_output.execute_cmd("flow flush 0")
        self.pmd_output.quit()

    def _pkg_send(self, test_packet, send_count):
        self.pmd_output.execute_cmd("start")
        pkt = Packet()
        for i in range(send_count):
            pkt.append_pkt(test_packet)
        pkt.send_pkt(self.tester, tx_port=self.tx_iface, count=1)
        out = self.pmd_output.execute_cmd("stop", timeout=30)
        return out

    def _set_pf_queue_num(self):
        self.dut_session.send_expect("ethtool -L %s rx 10 tx 10" % self.pf_interface, "# ")
        out = self.dut_session.send_expect("ethtool -l %s " % self.pf_interface, "# ")
        out = out.split("Current hardware settings")[1]
        pf_queue_num = re.findall(r'Combined:\s+(\d+)', out)[0]
        self.verify(int(pf_queue_num) == 10, "set rx tx queue fail!")

    def _get_pf_rx(self):
        out = self.dut_session.send_expect("ethtool -l %s " % self.pf_interface, "# ")
        out = out.split("Current hardware settings")[1]
        pf_rx = re.findall(r'RX:\s+(\d+)', out)[0]
        return int(pf_rx)

    def test_iavf_mac_eth_src_rss(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_eth_src)

    def test_iavf_mac_eth_dst_rss(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_eth_dst, rss_match=False)

    def test_iavf_rss_ipv4(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv4)

    def test_iavf_rss_ipv4_ICMP(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv4_icmp)

    def test_iavf_rss_ipv4_NVGRE(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv4_nvgre)

    def test_iavf_rss_ipv4_TCP(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv4_tcp)

    def test_iavf_rss_ipv4_UDP(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv4_udp)

    # def test_iavf_rss_ipv4_SCTP(self):
    #     self.create_testpmd_command(self.vf0_prop)
    #     self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv4_sctp)

    def test_iavf_rss_ipv6(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv6)

    def test_iavf_rss_ipv6_UDP(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv6_udp)

    def test_iavf_rss_ipv6_TCP(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv6_tcp)

    def test_iavf_rss_CVLAN(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_cvlan)

    def test_iavf_rss_PFCP(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_pfcp)

    def test_iavf_ipv4_gtpu_updown(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_gtpu_ipv4)

    def test_iavf_ipv4_frag_gtpu_updown(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_gtpu_ipv4_frag)

    def test_iavf_ipv4_udp_gtpu_updown(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_gtpu_ipv4_udp)

    def test_iavf_ipv4_tcp_gtpu_updown(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_gtpu_ipv4_tcp)

    def test_iavf_ipv4_icmp_gtpu_updown(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_gtpu_ipv4_icmp)

    def test_iavf_rss_ipv4_l2tpv3(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv4_l2tpv3)

    def test_iavf_rss_ipv6_l2tpv3(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv6_l2tpv3)

    def test_iavf_rss_ipv4_esp(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv4_esp)

    def test_iavf_rss_ipv6_esp(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv6_esp)

    def test_iavf_rss_ipv4_ah(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv4_ah)

    def test_iavf_rss_ipv6_ah(self):
        self.create_testpmd_command(self.vf0_prop)
        self._rte_flow_validate_pattern(tvs_iavf_mac_rss_ipv6_ah)

    # def test_iavf_ipv4_sctp_gtpu_updown(self):
    #     self.create_testpmd_command(self.vf0_prop)
    #     self._rte_flow_validate_pattern(tvs_iavf_gtpu_ipv4_sctp)

    def test_iavf_error_handle(self):
        self.create_testpmd_command(self.vf0_prop)
        error_rule = ['flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end',
                      'flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end']
        for rule in error_rule:
            out = self.pmd_output.execute_cmd(rule)
            self.verify("Failed to create flow" in out, "Rule can be created")

    def test_vf_reset(self):
        self.dut_session.send_expect("ip link set %s vf 0 trust on" % self.pf_interface, "# ")
        self.create_testpmd_command(self.vf0_prop, pmd_param="--nb-cores=2")
        flow_rule = "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end"
        self.pmd_output.execute_cmd(flow_rule)
        self.pmd_output.execute_cmd("show port 0 rss-hash")

        # send packets with vf0_mac, check hash work
        pkg = 'Ether(dst="%s")/IP(dst=RandIP(), frag=5)/SCTP(sport=RandShort())/("X"*480)' % vf0_mac
        pkg_count = 100
        out = self._pkg_send(pkg, pkg_count)
        result, log_str = rfc.check_iavf_packets_rss_queue(out, pkg_count)
        self.verify(result is True, log_str)

        # reset vf
        self.pmd_output.execute_cmd("port stop 0")
        self.pmd_output.execute_cmd("port reset 0")
        self.pmd_output.execute_cmd("port start 0")
        # send packets again with vf0_mac, check not do hash
        out = self._pkg_send(pkg, pkg_count)
        result, log_str = rfc.check_iavf_packets_rss_queue(out, pkg_count)
        self.verify(result is True, log_str)

        # reset PF and send packets check hash work
        reset_mac = "00:66:77:88:99:55"
        self.dut_session.send_expect("ip link set %s vf 0 mac %s" % (self.pf_interface, reset_mac), "# ")
        self.pmd_output.execute_cmd("port stop 0")
        self.pmd_output.execute_cmd("port reset 0")
        self.pmd_output.execute_cmd("port start 0")
        pkg = 'Ether(dst="%s")/IP(dst=RandIP(), frag=5)/SCTP(sport=RandShort())/("X"*480)' % reset_mac
        out = self._pkg_send(pkg, pkg_count)
        result, log_str = rfc.check_iavf_packets_rss_queue(out, pkg_count)
        self.verify(result is True, log_str)

    def test_pf_reset(self):
        param_str = " --rxq=16 --txq=16 --nb-cores=2"
        self.pmd_output.start_testpmd(cores="1S/8C/1T", param=param_str,
                                      eal_param="-w %s -w %s" % (self.vf0_prop['opt_host'], self.vf1_prop['opt_host']))
        self.pmd_output.execute_cmd("set fwd rxonly", "testpmd> ", 15)
        self.pmd_output.execute_cmd("set verbose 1", "testpmd> ", 15)
        vf0_rule = "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end"
        vf1_rule = "flow create 1 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end"
        self.pmd_output.execute_cmd(vf0_rule)
        self.pmd_output.execute_cmd(vf1_rule)
        pkg_count = 100

        # send packets with vf0_mac and vf1_mac, check hash work
        pkg_vf0 = 'Ether(dst="%s")/IP(src=RandIP())/UDP(dport=RandShort())/("X"*480)' % vf0_mac
        pkg_vf1 = 'Ether(dst="%s")/IP(dst=RandIP())/UDP(sport=RandShort())/("X"*480)' % vf1_mac

        out = self._pkg_send(pkg_vf0, pkg_count)
        result, msg = rfc.check_iavf_packets_rss_queue(out, pkg_count)
        self.verify(result is True, msg)
        out = self._pkg_send(pkg_vf1, pkg_count)
        result, msg = rfc.check_iavf_packets_rss_queue(out, pkg_count)
        self.verify(result is True, msg)

        # PF reset and check hash not do hash
        reset_mac = "00:66:77:88:99:55"
        self.dut_session.send_expect("ip link set %s vf 0 mac %s" % (self.pf_interface, reset_mac), "# ")
        reset_vf0 = 'Ether(dst="%s")/IP(src=RandIP())/UDP(dport=RandShort())/("X"*480)' % reset_mac
        out = self._pkg_send(reset_vf0, pkg_count)
        out = out.split("forward statistics for all ports")[1]
        rx_num = re.findall(r'RX-packets:\s?(\d+)', out)[0]
        self.verify(int(rx_num) == 0, "PF reset error")

        out = self._pkg_send(pkg_vf1, pkg_count)
        result, msg = rfc.check_iavf_packets_rss_queue(out, pkg_count)
        self.verify(result is True, msg)

    def test_mutil_vfs(self):
        self.create_testpmd_command(self.vf0_prop, pmd_param="--nb-cores=2")
        self.create_testpmd2_command(self.vf1_prop, pmd_param="--nb-cores=2")
        pkg_count = 100

        flow_rule = "flow create 0 ingress pattern eth / ipv4 / end actions rss types l3-dst-only end key_len 0 queues end / end"
        self.pmd_output.execute_cmd(flow_rule)
        self.pmd_output_vf1.execute_cmd(flow_rule)
        # send packets and check vf0 not recieved, vf1 hash do work
        pkg_vf1 = 'Ether(dst="%s")/IP(dst=RandIP(), frag=5)/SCTP(sport=RandShort())/("X"*480)' % vf1_mac
        self.pmd_output_vf1.execute_cmd("start")
        self._pkg_send(pkg_vf1, pkg_count)
        vf1_out = self.pmd_output_vf1.execute_cmd("stop")
        result, msg = rfc.check_iavf_packets_rss_queue(vf1_out, pkg_count)
        self.verify(result is True, msg)

    def test_check_inputset_with_pf_and_vf(self):
        self.create_testpmd_command(self.vf0_prop)
        self._check_inputset_pattern(tvs_check_pf_vf_inputset)

    def test_use_os_default_package(self):

        self.replace_pkg(self.os_pkg_name)
        self.create_testpmd_command(self.vf0_prop)
        error_rule = ["flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end ",
                      "flow create 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end ", ]
        try:
            for rule in error_rule:
                out = self.pmd_output.execute_cmd(rule)
                self.verify("Failed to create flow" in out, "Rule can be created")
        except Exception as e:
            raise Exception(e)
        finally:
            self.pmd_output.quit()
            self.replace_pkg(self.comms_pkg_name)

    def replace_pkg(self, pkg):
        self.dut_session.send_expect("cd %s" % self.ddp_fdir, "# ")
        self.dut_session.send_expect("rm -f ice.pkg", "# ")
        self.dut_session.send_expect("cp %s ice.pkg" % pkg, "# ")
        self.dut_session.send_expect("rmmod ice", "# ", 15)
        self.dut_session.send_expect("modprobe ice", "# ", 60)
        self.vf_flag = False
        self.create_iavf()
