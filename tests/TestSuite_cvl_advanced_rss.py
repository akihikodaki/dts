import json
import time
import re
import packet
import os
from scapy.contrib.gtp import *
from test_case import TestCase
from pmd_output import PmdOutput
from utils import BLUE, RED
from collections import OrderedDict
from packet import IncreaseIP, IncreaseIPv6
import rte_flow_common as rfc

out = os.popen("pip list|grep scapy ")
version_result =out.read()
p=re.compile('scapy\s+2\.3\.\d+')
m=p.search(version_result)

if not m:
   GTP_TEID= "teid"
else:
   GTP_TEID= "TEID"

tv_mac_ipv4_l3_src_only = {
    "name":"tv_mac_ipv4_l3_src_only",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d")/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_src_only_frag = {
    "name":"tv_mac_ipv4_l3_src_only_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d", frag=5)/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_dst_only = {
    "name":"tv_mac_ipv4_l3_dst_only",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.%d", frag=5)/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_dst_only_frag = {
    "name":"tv_mac_ipv4_l3_dst_only_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.%d", frag=5)/SCTP(sport=%d)/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_src_only_frag_icmp = {
    "name":"tv_mac_ipv4_l3_src_only_frag_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d", frag=5)/ICMP()/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_dst_only_frag_icmp = {
    "name":"tv_mac_ipv4_l3_dst_only_frag_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.%d", frag=5)/ICMP()/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_all = {
    "name":"tv_mac_ipv4_l3_all",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d", dst="192.168.0.%d")/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_all_frag_icmp = {
    "name":"tv_mac_ipv4_l3_all_frag_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d", dst="192.168.0.%d")/ICMP()/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_all_nvgre_frag_icmp = {
    "name":"tv_mac_ipv4_l3_all_nvgre_frag_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src="192.168.0.%d", dst="192.168.0.%d")/ICMP()/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_src_nvgre_frag_icmp = {
    "name":"tv_mac_ipv4_l3_src_nvgre_frag_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src="192.168.0.%d", frag=5)/ICMP()/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_dst_nvgre_frag_icmp = {
    "name":"tv_mac_ipv4_l3_dst_nvgre_frag_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.%d", frag=5)/ICMP()/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_src_vxlan_frag_icmp = {
    "name":"tv_mac_ipv4_l3_src_vxlan_frag_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",    
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.%d",frag=5)/ICMP()/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_dst_vxlan_frag_icmp = {
    "name":"tv_mac_ipv4_l3_dst_vxlan_frag_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.%d",frag=5)/ICMP()/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_l3_all_vxlan_frag_icmp = {
    "name":"tv_mac_ipv4_l3_all_vxlan_frag_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.%d", dst="192.168.0.%d", frag=5)/ICMP()/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_l3_src = {
    "name":"tv_mac_ipv6_l3_src",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="2001::%d")/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_l3_src_frag = {
    "name":"tv_mac_ipv6_l3_src_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="2001::%d")/IPv6ExtHdrFragment()/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_l3_dst_frag = {
    "name":"tv_mac_ipv6_l3_dst_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(dst="2001::%d")/IPv6ExtHdrFragment()/("X"*480)' %i for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_l3_all_frag_icmp = {
    "name":"tv_mac_ipv6_l3_all_frag_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="2001::%d", dst="2001::%d")/IPv6ExtHdrFragment()/ICMP()/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_udp_l3src_l4dst = {
    "name":"tv_mac_ipv4_udp_l3src_l4dst",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d")/UDP(dport=%d)/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_udp_all_frag = {
    "name":"tv_mac_ipv4_udp_all_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=%d, dport=%d)/("X"*480)' %(i, i+10, i+50,i+55) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_udp_nvgre = {
    "name":"tv_mac_ipv4_udp_nvgre",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=%d, dport=%d)/("X"*480)' %(i, i+10, i+50,i+55) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_udp_vxlan= {
    "name":"tv_mac_ipv4_udp_vxlan",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end",    
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=%d, dport=%d)/("X"*480)' %(i, i+10, i+50,i+55) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_udp_all= {
    "name":"tv_mac_ipv6_udp_all",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="2001::%d")/UDP(sport=%d, dport=%d)/("X"*480)' %(i, i+10, i+50) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}


tv_mac_ipv6_udp_all_frag= {
    "name":"tv_mac_ipv6_udp_all_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="2001::%d")/IPv6ExtHdrFragment()/UDP(sport=%d, dport=%d)/("X"*480)' %(i, i+10, i+50) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_tcp_l3src_l4dst= {
    "name":"tv_mac_ipv4_tcp_l3src_l4dst",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d")/TCP(dport=%d)/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_tcp_l3dst_l4src= {
    "name":"tv_mac_ipv4_tcp_l3dst_l4src",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(dst="192.168.0.%d")/TCP(sport=%d)/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_tcp_all= {
    "name":"tv_mac_ipv4_tcp_all",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d",dst="192.168.0.%d")/TCP(sport=%d,dport=%d)/("X"*480)' %(i, i+10, i+50,i+55) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_tcp_all_nvgre_frag= {
    "name":"tv_mac_ipv4_tcp_all_nvgre_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(sport=%d, dport=%d)/("X"*480)' %(i, i+10, i+50,i+55) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_tcp_all_vxlan_frag= {
    "name":"tv_mac_ipv4_tcp_all_vxlan_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(sport=%d, dport=%d)/("X"*480)' %(i, i+10, i+50,i+55) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_tcp_all= {
    "name":"tv_mac_ipv6_tcp_all",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="2001::%d")/TCP(sport=%d, dport=%d)/("X"*480)' %(i, i+10, i+50) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_tcp_all_frag= {
    "name":"tv_mac_ipv6_tcp_all_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="2001::%d")/IPv6ExtHdrFragment()/TCP(sport=%d, dport=%d)/("X"*480)' %(i, i+10, i+50) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_sctp_l3src_l4dst= {
    "name":"tv_mac_ipv4_sctp_l3src_l4dst",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l4-dst-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d")/SCTP(dport=%d)/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_sctp_all_frag= {
    "name":"tv_mac_ipv4_sctp_all_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.%d",dst="192.168.0.%d", frag=4)/SCTP(sport=%d,dport=%d)/("X"*480)' %(i, i+10,i+50,i+55) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_sctp_nvgre= {
    "name":"tv_mac_ipv4_sctp_nvgre",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src="192.168.0.%d",dst="192.168.0.%d", frag=4)/SCTP(sport=%d,dport=%d)/("X"*480)' %(i, i+10,i+50,i+55) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_sctp_vxlan= {
    "name":"tv_mac_ipv4_sctp_vxlan",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.%d",dst="192.168.0.%d")/SCTP(sport=%d,dport=%d)/("X"*480)' %(i, i+10,i+50,i+55) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_sctp_all= {
    "name":"tv_mac_ipv6_sctp_all",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="2001::%d")/SCTP(sport=%d, dport=%d)/("X"*480)' %(i, i+10, i+50) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_pppod_pppoe= {
    "name":"tv_mac_ipv4_pppod_pppoe",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=%d)/PPP(proto=0x21)/IP(src="192.168.0.%d")/UDP(sport=%d)/("X"*480)' %(i, i+10,i+50) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_pppoe_all= {
    "name":"tv_mac_ipv4_pppoe_all",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=%d)/PPP(proto=0x21)/IP(src="192.168.0.%d",dst="192.168.0.%d")/("X"*480)' %(i, i+10,i+50) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_pppoe_udp= {
    "name":"tv_mac_ipv4_pppoe_udp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=%d)/PPP(proto=0x21)/IP(src="192.168.0.%d")/UDP(dport=%d)/("X"*480)' %(i, i+10,i+50) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_pppoe_tcp= {
    "name":"tv_mac_ipv4_pppoe_tcp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=%d)/PPP(proto=0x21)/IP(src="192.168.0.%d")/TCP(sport=%d)/("X"*480)' %(i, i+10,i+50) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_pppoe_sctp= {
    "name":"tv_mac_ipv4_pppoe_sctp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=%d)/PPP(proto=0x21)/IP(src="192.168.0.%d")/SCTP(dport=%d)/("X"*480)' %(i, i+10,i+50) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_pppoe_icmp= {
    "name":"tv_mac_ipv4_pppoe_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/PPPoE(sessionid=%d)/PPP(proto=0x21)/IP(src="192.168.0.%d")/ICMP()/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

pkt_str=[]
pkt = ['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(GTP_TEID=0x123456)/IP(src="192.168.0.%d")/ICMP()/("X"*480)' %i for i in range(0,100)]
for i in pkt:
    pkt_str.append(i.replace('GTP_TEID', GTP_TEID))

tv_mac_ipv4_gtpu_icmp= {
    "name":"tv_mac_ipv4_gtpu_icmp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
    "scapy_str":pkt_str,
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

pkt_str=[]
pkt = ['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(GTP_TEID=0x123456)/IP(src="192.168.0.%d", frag=6)/UDP(dport=%d)/("X"*480)' %(i, i+10) for i in range(0,100)]
for i in pkt:
    pkt_str.append(i.replace('GTP_TEID', GTP_TEID))

tv_mac_ipv4_gtpu_udp_frag= {
    "name":"tv_mac_ipv4_gtpu_udp_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end",
    "scapy_str":pkt_str,
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

pkt_str=[]
pkt = ['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(GTP_TEID=0x123456)/IP(src="192.168.0.%d", frag=6)/("X"*480)' %i for i in range(0,100)]
for i in pkt:
    pkt_str.append(i.replace('GTP_TEID', GTP_TEID))

tv_mac_ipv4_gtpu_ipv4_frag= {
    "name":"tv_mac_ipv4_gtpu_ipv4_frag",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
    "scapy_str":pkt_str,
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

pkt_str=[]
pkt =['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(GTP_TEID=0x123456)/IP(src="192.168.0.%d", frag=6)/TCP(dport=%d)/("X"*480)' %(i, i+10) for i in range(0,100)]
for i in pkt:
    pkt_str.append(i.replace('GTP_TEID', GTP_TEID))

tv_mac_ipv4_gtpu_tcp= {
    "name":"tv_mac_ipv4_gtpu_tcp",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end",
    "scapy_str":pkt_str,
    "check_func": rfc.check_packets_of_each_queue,
    "check_func_param": {"expect_port":0}
}

tvs_mac_rss_ipv4 = [
    tv_mac_ipv4_l3_src_only,
    tv_mac_ipv4_l3_src_only_frag,
    tv_mac_ipv4_l3_dst_only,
    tv_mac_ipv4_l3_all
    ]

tvs_mac_rss_ipv4_port = [
    tv_mac_ipv4_l3_src_only_frag_icmp,
    tv_mac_ipv4_l3_dst_only_frag_icmp,
    tv_mac_ipv4_l3_all_frag_icmp,
    tv_mac_ipv4_udp_l3src_l4dst,
    tv_mac_ipv4_udp_all_frag,
    tv_mac_ipv4_tcp_l3src_l4dst,
    tv_mac_ipv4_tcp_l3dst_l4src,
    tv_mac_ipv4_tcp_all,
    tv_mac_ipv4_sctp_l3src_l4dst,
    tv_mac_ipv4_sctp_all_frag
    ]

tvs_mac_rss_ipv4_nvgre = [
    tv_mac_ipv4_l3_all_nvgre_frag_icmp,
    tv_mac_ipv4_l3_src_nvgre_frag_icmp,
    tv_mac_ipv4_l3_dst_nvgre_frag_icmp,
    tv_mac_ipv4_tcp_all_nvgre_frag,
    tv_mac_ipv4_sctp_nvgre
    ]
tvs_mac_rss_ipv4_vxlan =[
    tv_mac_ipv4_l3_src_vxlan_frag_icmp,
    tv_mac_ipv4_l3_dst_vxlan_frag_icmp,
    tv_mac_ipv4_l3_all_vxlan_frag_icmp,
    tv_mac_ipv4_tcp_all_vxlan_frag,
    tv_mac_ipv4_sctp_vxlan,
    tv_mac_ipv4_udp_vxlan
    ]

tvs_mac_rss_ipv6 =[
    tv_mac_ipv6_l3_src,
    tv_mac_ipv6_l3_src_frag,
    tv_mac_ipv6_l3_dst_frag,
    tv_mac_ipv6_l3_all_frag_icmp,
    tv_mac_ipv6_udp_all,
    tv_mac_ipv6_udp_all_frag,
    tv_mac_ipv6_tcp_all,
    tv_mac_ipv6_tcp_all_frag,
    tv_mac_ipv6_sctp_all
]
    
tvs_mac_rss_ipv4_pppoe =[
    tv_mac_ipv4_pppod_pppoe,
    tv_mac_ipv4_pppoe_all,
    tv_mac_ipv4_pppoe_tcp,
    tv_mac_ipv4_pppoe_sctp,
    tv_mac_ipv4_pppoe_icmp
    ]
tvs_mac_rss_ipv4_gtp =[
    tv_mac_ipv4_gtpu_icmp,
    tv_mac_ipv4_gtpu_udp_frag,
    tv_mac_ipv4_gtpu_ipv4_frag,
    tv_mac_ipv4_gtpu_tcp
    ]

tv_mac_ipv4_symmetric_toeplitz = {
    "name": "tv_mac_ipv4_symmetric_toeplitz",
    "rte_flow_pattern": "flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port": 0}
}    

tv_mac_ipv4_frag_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_frag_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/("X"*480)',
                 'Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_udp_frag_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_udp_frag_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/UDP(sport=20,dport=22)/("X"*480)',
                 'Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/UDP(sport=22,dport=20)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_udp_frag_symmetric_toeplitz_all= {
    "name":"tv_mac_ipv4_udp_frag_symmetric_toeplitz_all",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp l3-src-only l3-dst-only l4-src-only l4-dst-only end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="1.1.4.1",dst="2.2.2.3")/UDP(sport=20,dport=22)/("X"*480)',
                 'Ether(dst="68:05:ca:a3:28:94")/IP(src="2.2.2.3",dst="1.1.4.1")/UDP(sport=22,dport=20)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_tcp_frag_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_tcp_frag_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/TCP(sport=20,dport=22)/("X"*480)',
                 'Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/TCP(sport=22,dport=20)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_sctp_frag_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_sctp_frag_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss func symmetric_toeplitz types ipv4-sctp end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/SCTP(sport=20,dport=22)/("X"*480)',
                 'Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/SCTP(sport=22,dport=20)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_icmp_frag_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_icmp_frag_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/ICMP()/("X"*480)',
                 'Ether(dst="68:05:ca:a3:28:94")/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/ICMP()/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end",
    "scapy_str":['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)',
                 'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_frag_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_frag_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/IPv6ExtHdrFragment()/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_udp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_udp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=30,dport=32)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=30)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_tcp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_tcp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=30,dport=32)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=30)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_sctp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_sctp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=30,dport=32)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=30)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_icmp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_icmp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/ICMP()/("X"*480)',
                'Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_nvgre_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_nvgre_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end ",
    "scapy_str": ['Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.8",dst="192.168.0.69",frag=6)/("X"*480)',
                  'Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.69",dst="192.168.0.8",frag=6)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_vxlan_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_vxlan_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.1",dst="192.168.0.2",frag=6)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.1",frag=6)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_nvgre_udp_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_nvgre_udp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="8.8.8.1",dst="5.6.8.2")/UDP(sport=20,dport=22)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="5.6.8.2",dst="8.8.8.1")/UDP(sport=22,dport=20)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_nvgre_sctp_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_nvgre_sctp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss func symmetric_toeplitz types ipv4-sctp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="8.8.8.1",dst="5.6.8.2")/SCTP(sport=20,dport=22)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="5.6.8.2",dst="8.8.8.1")/SCTP(sport=22,dport=20)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_nvgre_tcp_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_nvgre_tcp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="8.8.8.1",dst="5.6.8.2")/TCP(sport=20,dport=22)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether(dst="68:05:ca:a3:28:94")/IP(src="5.6.8.2",dst="8.8.8.1")/TCP(sport=22,dport=20)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_nvgre_icmp_symmetric_toeplitz= {
    "name":"tv_mac_ipv4_nvgre_icmp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src="8.8.8.1",dst="5.6.8.2")/ICMP()/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IP(src="5.6.8.2",dst="8.8.8.1")/ICMP()/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_nvgre_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_nvgre_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_nvgre_udp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_nvgre_udp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=30,dport=32)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=30)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_nvgre_tcp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_nvgre_tcp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=30,dport=32)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=30)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_nvgre_sctp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_nvgre_sctp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=30,dport=32)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=30)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_nvgre_icmp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_nvgre_icmp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/ICMP()/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_vxlan_udp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_vxlan_udp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=30,dport=32)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=30)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_vxlan_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_vxlan_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IP()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_vxlan_tcp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_vxlan_tcp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=30,dport=32)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=32,dport=30)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_vxlan_sctp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_vxlan_sctp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/SCTP(sport=30,dport=32)/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=32,dport=30)/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_vxlan_icmp_symmetric_toeplitz= {
    "name":"tv_mac_ipv6_vxlan_icmp_symmetric_toeplitz",
    "rte_flow_pattern":"flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end",
    "scapy_str": ['Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/ICMP()/("X"*480)',
                  'Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)'],
    "check_func": rfc.check_symmetric_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_simple_xor= {
    "name":"tv_mac_ipv4_simple_xor",
    "rte_flow_pattern":"flow create 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end",
    "scapy_str": ['Ether()/IP("src="1.1.4.1",dst="2.2.2.3")/("X"*480)',
                  'Ether()/IP("src="2.2.2.3",dst="1.1.4.1")/("X"*480)'],
    "check_func": rfc.check_simplexor_queue,
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_simple_xor= {
    "name":"tv_mac_ipv6_sctp_simple_xor",
    "rte_flow_pattern":"flow create 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end",
    "scapy_str": ['Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/ICMP()/("X"*480)',
                  'Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)'],
    "check_func": rfc.check_simplexor_queue,
    "check_func_param": {"expect_port":0}
}

tvs_mac_rss_ipv4_symmetric_toeplitz = [
    tv_mac_ipv4_symmetric_toeplitz,
    tv_mac_ipv4_frag_symmetric_toeplitz,
    tv_mac_ipv4_udp_frag_symmetric_toeplitz,
    tv_mac_ipv4_udp_frag_symmetric_toeplitz_all,
    tv_mac_ipv4_tcp_frag_symmetric_toeplitz,
    tv_mac_ipv4_sctp_frag_symmetric_toeplitz,
    tv_mac_ipv4_icmp_frag_symmetric_toeplitz
    ]

tvs_mac_rss_ipv6_symmetric_toeplitz = [
    tv_mac_ipv6_symmetric_toeplitz,
    tv_mac_ipv6_frag_symmetric_toeplitz,
    tv_mac_ipv6_udp_symmetric_toeplitz,
    tv_mac_ipv6_tcp_symmetric_toeplitz,
    tv_mac_ipv6_sctp_symmetric_toeplitz,
    tv_mac_ipv6_icmp_symmetric_toeplitz
    ]

tvs_mac_rss_ipv4_symmetric_toeplitz_nvgre = [
    tv_mac_ipv4_nvgre_symmetric_toeplitz,
    tv_mac_ipv4_nvgre_udp_symmetric_toeplitz,
    tv_mac_ipv4_nvgre_sctp_symmetric_toeplitz,
    tv_mac_ipv4_nvgre_tcp_symmetric_toeplitz,
    tv_mac_ipv4_nvgre_icmp_symmetric_toeplitz
    ]

tvs_mac_rss_ipv6_symmetric_toeplitz_nvgre = [
    tv_mac_ipv6_nvgre_symmetric_toeplitz,
    tv_mac_ipv6_nvgre_udp_symmetric_toeplitz,
    tv_mac_ipv6_nvgre_tcp_symmetric_toeplitz,
    tv_mac_ipv6_nvgre_sctp_symmetric_toeplitz,
    tv_mac_ipv6_nvgre_icmp_symmetric_toeplitz
    ]

tvs_mac_rss_symmetric_toeplitz_vxlan = [
    tv_mac_ipv4_vxlan_symmetric_toeplitz,
    tv_mac_ipv6_vxlan_udp_symmetric_toeplitz,
    tv_mac_ipv6_vxlan_symmetric_toeplitz,
    tv_mac_ipv6_vxlan_tcp_symmetric_toeplitz,
    tv_mac_ipv6_vxlan_icmp_symmetric_toeplitz
    ]

tvs_mac_rss_simple_xor = [
    tv_mac_ipv4_simple_xor,
    tv_mac_ipv6_simple_xor
    ]


test_results = OrderedDict()

class AdvancedRSSTest(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        #self.cores = "1S/8C/1T"
        self.pmdout = PmdOutput(self.dut)

        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.__tx_iface = self.tester.get_interface(localPort)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.verify(self.nic in ["columbiaville_25g","columbiaville_100g"], "%s nic not support ethertype filter" % self.nic)



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
        all_eal_param = self.dut.create_eal_parameters()
        print(all_eal_param)   #print eal parameters
        command = "./%s/app/testpmd %s  -- -i %s" % (self.dut.target, all_eal_param, "--rxq=64 --txq=64")
        return command

    def _rte_flow_validate_pattern(self, test_vectors, command, is_vxlan):

        global test_results
        out = self.dut.send_expect(command, "testpmd> ", 120)
        self.logger.debug(out)  #print the log
        self.dut.send_expect("port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd", "testpmd> ", 15)
        if is_vxlan:
            self.dut.send_expect("rx_vxlan_port add 4789 0", "testpmd> ", 15)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)

        test_results.clear()
        self.count = 1
        self.mac_count=100    
        for tv in test_vectors:
            out = self.dut.send_expect(tv["rte_flow_pattern"], "testpmd> ", 15)  #create a rule
            print(out)
            self.dut.send_expect("start", "testpmd> ", 15)
            time.sleep(2)
            tv["check_func_param"]["expect_port"] = self.dut_ports[0]
            print("expect_port is", self.dut_ports[0])

            #send a packet
            if isinstance(tv["scapy_str"], list):
                pkt = packet.Packet()
                pkt.update_pkt(tv["scapy_str"])
                pkt.send_pkt(self.tester, tx_port=self.__tx_iface, count=self.count)
            else:
                for index in range(10):
                    pkt = Packet(pkt_str=tv["scapy_str"])
                    pkt.send_pkt(self.tester, tx_port=self.__tx_iface, count=self.count)
                    print("packet:")
                    print(tv["scapy_str"])

            out = self.dut.send_expect("stop", "testpmd> ",60)
            print(out)
            log_msg =  tv["check_func"](out)
            print(log_msg)
            rfc.check_rx_tx_packets_match(out, self.mac_count)

        self.dut.send_expect("flow flush %d" % self.dut_ports[0], "testpmd> ")
        self.dut.send_expect("quit", "#")

    def test_advance_rss_ipv4(self):
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_rss_ipv4, command, is_vxlan = True)

    def test_advance_rss_ipv4_port(self):  
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_rss_ipv4_port, command, is_vxlan = True)

    def test_advance_rss_ipv4_nvgre(self):  
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_rss_ipv4_nvgre, command, is_vxlan = True)

    def test_advance_rss_ipv4_vxlan(self):  
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_rss_ipv4_vxlan, command, is_vxlan = True)

    def test_advance_rss_ipv6(self):  
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_rss_ipv6, command, is_vxlan = True)

    def test_advance_rss_ipv4_pppoe(self):  
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_rss_ipv4_pppoe, command, is_vxlan = True)

    def test_advance_rss_ipv4_gtp(self):  
        command = self.create_testpmd_command()
        self._rte_flow_validate_pattern(tvs_mac_rss_ipv4_gtp, command, is_vxlan = True)

    def test_rss_ipv4_symetric_toeplitz(self):  
         command = self.create_testpmd_command()
         self._rte_flow_validate_pattern(tvs_mac_rss_ipv4_symmetric_toeplitz, command, is_vxlan = True)
         
    def test_rss_ipv6_symetric_toeplitz(self):  
         command = self.create_testpmd_command()
         self._rte_flow_validate_pattern(tvs_mac_rss_ipv6_symmetric_toeplitz, command, is_vxlan = True)
    
    def test_rss_ipv4_symetric_toeplitz_nvgre(self):  
         command = self.create_testpmd_command()
         self._rte_flow_validate_pattern(tvs_mac_rss_ipv4_symmetric_toeplitz_nvgre, command, is_vxlan = True)
    
    def test_rss_ipv6_symetric_toeplitz_nvgre(self):  
         command = self.create_testpmd_command()
         self._rte_flow_validate_pattern(tvs_mac_rss_ipv6_symmetric_toeplitz_nvgre, command, is_vxlan = True)
         
    def test_rss_symetric_toeplitz_vxlan(self):  
         command = self.create_testpmd_command()
         self._rte_flow_validate_pattern(tvs_mac_rss_symmetric_toeplitz_vxlan, command, is_vxlan = True)
    
    def test_rss_simple_xor(self):  
         command = self.create_testpmd_command()
         self._rte_flow_validate_pattern(tvs_mac_rss_simple_xor, command, is_vxlan = True)   

