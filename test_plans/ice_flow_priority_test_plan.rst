.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

===============================
ICE Support Flow Priority in PF
===============================

Description
===========
In Intel® Ethernet 800 Series PF rte_flow distribution mode(non-pipeline mode), a flow
with priority = 1 will be programmed into switch filter, a flow with priority = 0 will
be programmed into switch first then fdir. Currently only support priority 0 and 1. 1
means low priority and 0 means high priority. When looking up rule table, matched pkt
will hit the high priority rule firstly, it will hit the low priority rule only when
there is no high priority rule exist.


Prerequisites
=============

Topology
--------
1node/1nic/2port/fwd
2node/1nic/1port/loopback

Hardware
--------
Supportted NICs: Intel® Ethernet Network Adapter E810-XXVDA4/Intel® Ethernet Network Adapter E810-CQDA2

Software
--------
DPDK: http://dpdk.org/git/dpdk
Scapy: http://www.secdev.org/projects/scapy/

General Set Up
--------------
1. Compile DPDK::

    # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
    # ninja -C <dpdk build dir> -j 110

2. Get the pci device id and interface of DUT and tester. 
   For example, 0000:18:00.0 and 0000:18:00.1 is pci device id,
   ens785f0 and ens785f1 is interface::

    <dpdk dir># ./usertools/dpdk-devbind.py -s

    0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci
    0000:18:00.1 'Device 159b' if=ens785f1 drv=ice unused=vfio-pci

3. Bind the DUT port to dpdk::

    <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci <DUT port pci device id>

4. Launch the userland ``testpmd`` application on DUT as follows and ::

    <dpdk build dir>/app/dpdk-testpmd <EAL options> -- -i --rxq=<queue number> --txq=<queue number>
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> rx_vxlan_port add 4789 0
    testpmd> start

..note:: 

    For <EAL options>, you can use "-c 0xf -n 1", you can also refer to testpmd doc for other setings.


Test Case
=========

Common Steps
------------
1. validate rules: two rules have same pattern, input set but different priority and actions.
2. create rules and list rules.
3. send matched packets, check the action hiting the rule with priority 0.
4. send mismatched packets, check the packets will not hit any rules.
5. destroy rule with priority 0, list rules.
6. send matched packets, check the action hiting the rule with priority 1.
7. send mismatched packets, check the packets will not hit any rules.
8. recreate rules which priority is 0, list rule.
9. destroy rule with priority 1, list rules.
10. send matched packets, check the action hiting the rule with priority 0.
11. send mismatched packets, check the packets will not hit any rules.
12. destroy rule with priority 0, list rules.
13. send matched packets, check the packets will not hit any rules.

All the packets in this test plan use below settings:
dst mac: 68:05:ca:8d:ed:a8
dst mac change inputset: 68:05:ca:8d:ed:a3
ipv4 src: 192.168.0.1
ipv4 dst: 192.168.0.2
ipv4 src change inputset: 192.168.0.3
ipv4 dst change inputset: 192.168.0.4
inner ipv4 src: 192.168.1.1
inner ipv4 src change inputset: 192.168.1.2
inner ipv4 dst: 192.168.1.3
inner ipv4 dst change inputset: 192.168.1.4
ipv6 src: CDCD:910A:2222:5498:8475:1111:3900:1536
ipv6 dst: CDCD:910A:2222:5498:8475:1111:3900:2020
ipv6 src change inputset: CDCD:910A:2222:5498:8475:1111:3900:1538
ipv6 dst change inputset: CDCD:910A:2222:5498:8475:1111:3900:2028
tos: 4
tos change inputset: 5
ttl: 2
ttl change inputset: 9
sport: 23
sport change inputset: 33
dport: 24
dport change inputset: 34
tc: 3
tc change inputset: 7
tni: 0x8
tni change inputset: 0x1
ethertype: 0x8863
ethertype change inputset: 0x8864
tci: 1
tci change inputset: 2
seid: 3
seid change inputset: 4
ipv4 proto_id: 0x0021
ipv6 proto_id: 0x0057
LCP proto_id: 0xc021
IPCP proto_id: 0x8021

Support Pattern and Input Set
-----------------------------
.. table::

    +---------------------+-------------------------------+-------------------------------------------+
    |    Packet Types     |           Pattern             | input set (non-pipeline mode)             |
    +=====================+===============================+===========================================+
    |                     | MAC_IPV4_FRAG                 |  N/A                                      |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV4_PAY                  | [Source IP], [Dest IP],[TOS],[TTL]        |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV4_UDP_PAY              | [Source IP], [Dest IP],[TOS],[TTL],       |
    |                     +-------------------------------+-------------------------------------------+
    | IPv4/IPv6 + TCP/UDP | MAC_IPV4_TCP                  | [Source IP], [Dest IP],[TOS],[TTL],       |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV6                      | [Source IP], [Dest IP]                    |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV6_UDP_PAY              | [Source IP], [Dest IP],[TOS],[TTL],       |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV6_TCP                  | [Source IP], [Dest IP],[TOS],[TTL],       |
    +---------------------+-------------------------------+-------------------------------------------+
    |                     | MAC_IPV4_TUN_IPV4_FRAG        | [Out Dest IP], [VNI/GRE_KEY],             |
    |                     |                               | [Inner Source IP], [Inner Dest IP]        |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV4_TUN_IPV4_PAY         | [Out Dest IP], [VNI/GRE_KEY],             |
    |                     |                               | [Inner Source IP], [Inner Dest IP]        |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV4_TUN_IPV4_UDP_PAY     | [Out Dest IP], [VNI/GRE_KEY],             |
    |                     |                               | [Inner Source IP], [Inner Dest IP],       |
    |                     |                               | [Inner Source Port], [Inner Dest Port]    |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV4_TUN_IPV4_TCP         | [Out Dest IP], [VNI/GRE_KEY],             |
    |                     |                               | [Inner Source IP], [Inner Dest IP],       |
    |                     |                               | [Inner Source Port], [Inner Dest Port]    |
    |        tunnel       +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV4_TUN_MAC_IPV4_FRAG    | [Out Dest IP], [VNI/GRE_KEY],             |
    |                     |                               | [Inner Dest MAC],                         |
    |                     |                               | [Inner Source IP], [Inner Dest IP]        |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV4_TUN_MAC_IPV4_PAY     | [Out Dest IP], [VNI/GRE_KEY],             |
    |                     |                               | [Inner Dest MAC],                         |
    |                     |                               | [Inner Source IP], [Inner Dest IP]        |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV4_TUN_MAC_IPV4_UDP_PAY | [Out Dest IP], [VNI/GRE_KEY],             |
    |                     |                               | [Inner Dest MAC],                         |
    |                     |                               | [Inner Source IP],[Inner Dest IP],        |
    |                     |                               | [Inner Source Port], [Inner Dest Port]    |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_IPV4_TUN_MAC_IPV4_TCP     | [Out Dest IP], [VNI/GRE_KEY],             |
    |                     |                               | [Inner Dest MAC],                         |
    |                     |                               | [Inner Source IP], [Inner Dest IP],       |
    |                     |                               | [Inner Source Port], [Inner Dest Port]    |
    +---------------------+-------------------------------+-------------------------------------------+
    |  ethertype filter   | ethertype filter_PPPOED       | [Ether type]                              |
    +---------------------+-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV4_PAY       | [Dest MAC], [VLAN], [seid],               |
    |                     | _session_id_proto_id          | [pppoe_proto_id]                          |
    |                     +-------------------------------+-------------------------------------------+
    |                	  | MAC_VLAN_PPPOE_IPV6_PAY       | [Dest MAC], [VLAN], [seid],               |
    |                     | _session_id_proto_id          | [pppoe_proto_id]                          |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV4_PAY_session_id | [Dest MAC], [seid], [pppoe_proto_id]      |
    |                     | _proto_id                     |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV6_PAY_session_id | [Dest MAC], [seid], [pppoe_proto_id]      |
    |                     | _proto_id                     |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV4_PAY_IP_address | [Source IP], [Dest IP]                    |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV4_UDP_PAY        | [Source IP], [Dest IP],                   |
    |                     |                               | [Source Port], [Dest Port]                |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV4_UDP_PAY        | [Source IP], [Dest IP]                    |
    |                     | _non_src_dst_port             |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV4_TCP_PAY        | [Source IP], [Dest IP],                   |
    |                     |                               | [Source Port], [Dest Port]                |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV4_TCP_PAY        | [Source IP], [Dest IP]                    |
    |                     | _non_src_dst_port             |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV6_PAY_IP_address | [Source IP], [Dest IP]                    |
    |      PPPOES         +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV6_UDP_PAY        | [Source IP], [Dest IP],                   |
    |                     |                               | [Source Port], [Dest Port]                |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV6_UDP_PAY        | [Source IP], [Dest IP]                    |
    |                     | _non_src_dst_port             |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV6_TCP_PAY        | [Source IP], [Dest IP],                   |
    |                     |                               | [Source Port], [Dest Port]                |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPV6_TCP_PAY        | [Source IP], [Dest IP],                   |
    |                     | _non_src_dst_port             |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV4_PAY       | [VLAN], [Source IP], [Dest IP]            |
    |                     | _IP_address                   |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV4_UDP_PAY   | [VLAN], [Source IP], [Dest IP]            |
    |                     |                               | [Source Port], [Dest Port]                |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV4_UDP_PAY   | [VLAN], [Source IP], [Dest IP]            |
    |                     | _non_src_dst_port             |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV4_TCP_PAY   | [VLAN], [Source IP], [Dest IP]            |
    |                     |                               | [Source Port], [Dest Port]                |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV4_TCP_PAY   | [VLAN], [Source IP], [Dest IP]            |
    |                     | _non_src_dst_port             |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV6_PAY       | [VLAN], [Source IP], [Dest IP]            |
    |                     | _IP_address                   |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV6_UDP_PAY   | [VLAN], [Source IP], [Dest IP]            |
    |                     |                               | [Source Port], [Dest Port]                |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV6_UDP_PAY   | [VLAN], [Source IP], [Dest IP]            |
    |                     | _non_src_dst_port             |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV6_TCP_PAY   | [VLAN], [Source IP], [Dest IP]            |
    |                     |                               | [Source Port], [Dest Port]                |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPV6_TCP_PAY   | [VLAN], [Source IP], [Dest IP]            |
    |                     | _non_src_dst_port             |                                           |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_LCP_PAY             | [Dest MAC], [seid], [pppoe_proto_id]      |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_PPPOE_IPCP_PAY            | [Dest MAC], [seid], [pppoe_proto_id]      |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_LCP_PAY        | [Dest MAC], [VLAN], [seid],               |
    |                     |                               | [pppoe_proto_id]                          |
    |                     +-------------------------------+-------------------------------------------+
    |                     | MAC_VLAN_PPPOE_IPCP_PAY       | [Dest MAC], [VLAN], [seid],               |
    |                     |                               | [pppoe_proto_id]                          |
    +---------------------+-------------------------------+-------------------------------------------+

..note::

    the basic switch function of supported pattern is covered by ice_switch_filter_test_plan.rst and ice_switch_filter_pppoe_test_plan.rst.
    this test plan is designed to check the flow priority in switch, so we only select some patterns not all matrix in test plan.


Test Case 1: MAC_IPV4_PAY
-------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / ipv4 src is <ipv4 src> dst is <ipv4 dst> tos is <tos> ttl is <ttl> / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth dst is <dst mac> / ipv4 src is <ipv4 src> dst is <ipv4 dst> tos is <tos> ttl is <ttl> / end actions queue index 4 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>",tos=<tos>,ttl=<ttl>)/("X"*480)], iface="<tester interface>")

mismatched packets::

  >>> sendp([Ether(dst="<dst mac change inputset>")/IP(src="<ipv4 src>",dst="<ipv4 dst>",tos=<tos>,ttl=<ttl>)/("X"*480)], iface="<tester interface>")
  >>> sendp([Ether(dst="<dst mac>")/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>",tos=<tos>,ttl=<ttl>)/("X"*480)], iface="<tester interface>")
  >>> sendp([Ether(dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>",tos=<tos>,ttl=<ttl>)/("X"*480)], iface="<tester interface>")
  >>> sendp([Ether(dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>",tos=<tos change inputset>,ttl=<ttl>)/("X"*480)], iface="<tester interface>")
  >>> sendp([Ether(dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>",tos=<tos>,ttl=<ttl change inputset>)/("X"*480)], iface="<tester interface>")


Test Case 2: MAC_IPV4_UDP_PAY
-----------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> tos is <tos> / udp src is <sport> dst is <dport> / end actions rss queues 4 5 end / end
    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> tos is <tos> / udp src is <sport> dst is <dport> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether()/IP(src="<ipv4 src>",dst="<ipv4 dst>",tos=<tos>)/UDP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether()/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>",tos=<tos>)/UDP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>")
  >>> sendp([Ether()/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>",tos=<tos>)/UDP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>")
  >>> sendp([Ether()/IP(src="<ipv4 src>",dst="<ipv4 dst>",tos=<tos change inputset>)/UDP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>")
  >>> sendp([Ether()/IP(src="<ipv4 src>",dst="<ipv4 dst>",tos=<tos>)/UDP(sport=<sport change inputset>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>")
  >>> sendp([Ether()/IP(src="<ipv4 src>",dst="<ipv4 dst>",tos=<tos>)/UDP(sport=<sport>,dport=<dport change inputset>)/Raw("x"*80)],iface="<tester interface>")


Test Case 3: MAC_IPV6_PAY
-------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 src is <ipv6 src> dst is <ipv6 dst> / end actions rss queues 4 5 end / end
    testpmd> flow create 0 priority 1 ingress pattern eth / ipv6 src is <ipv6 src> dst is <ipv6 dst> / end actions queue index 8 / end

matched packets::

  >>> sendp([Ether()/IPv6(src="<ipv6 src>", dst="<ipv6 dst>")/("X"*480)], iface="<tester interface>")

mismatched packets::

  >>> sendp([Ether()/IPv6(src="<ipv6 src change inputset>", dst="<ipv6 dst>")/("X"*480)], iface="<tester interface>")
  >>> sendp([Ether()/IPv6(src="<ipv6 src>", dst="<ipv6 dst change inputset>")/("X"*480)], iface="<tester interface>")

Test Case 4: MAC_IPV6_TCP
-------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is <ipv6 dst> tc is <tc> / tcp src is <sport> dst is <dport> / end actions rss queues 4 5 end / end
    testpmd> flow create 0 priority 1 ingress pattern eth / ipv6 dst is <ipv6 dst> tc is <tc> / tcp src is <sport> dst is <dport> / end actions queue index 3 / end

matched packets::

  >>> sendp([Ether()/IPv6(src="<ipv6 src>",dst="<ipv6 dst>",tc=<tc>)/TCP(sport=<sport>,dport=23)/Raw("x"*80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether()/IPv6(src="<ipv6 src>",dst="<ipv6 dst change inputset>",tc=<tc>)/TCP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IPv6(src="<ipv6 src>",dst="<ipv6 dst>",tc=<tc change inputset>)/TCP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IPv6(src="<ipv6 src>",dst="<ipv6 dst>",tc=<tc>)/TCP(sport=<sport change inputset>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IPv6(src="<ipv6 src>",dst="<ipv6 dst>",tc=<tc>)/TCP(sport=<sport>,dport=<dport change inputset>)/Raw("x"*80)],iface="<tester interface>",count=1)


Test Case 5: MAC_IPV4_VXLAN_IPV4_FRAG
-------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions rss queues 2 3 end / end
    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 5 / end

matched packets::

  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src>", dst="<ipv4 dst>",frag=5)/Raw("x"*80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src change inputset>", dst="<ipv4 dst>",frag=5)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src>", dst="<ipv4 dst change inputset>",frag=5)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src>", dst="<ipv4 dst>",frag=5)/Raw("x"*80)],iface="<tester interface>",count=1)


Test Case 6: MAC_IPV4_VXLAN_IPV4_PAY
------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 5 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions rss queues 2 3 end / end

matched packets::

  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src>", dst="<ipv4 dst>")/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src>", dst="<ipv4 dst>")/TCP()/Raw("x"*80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src change inputset>", dst="<ipv4 dst>")/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src>", dst="<ipv4 dst change inputset>")/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src>", dst="<ipv4 dst>")/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src>", dst="<ipv4 dst>")/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src change inputset>", dst="<ipv4 dst>")/TCP()/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src>", dst="<ipv4 dst change inputset>")/TCP()/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="<ipv4 src>", dst="<ipv4 dst>")/TCP()/Raw("x"*80)],iface="<tester interface>",count=1)


Test Case 7: MAC_IPV4_NVGRE_MAC_IPV4_UDP_PAY
--------------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 dst is <ipv4 dst> / nvgre tni is <tni> / eth dst is <dst mac> / ipv4 src is <inner ipv4 src> dst is <inner ipv4 dst> / udp src is <sport> dst is <dport> / end actions rss queues 2 3 end / end
    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 dst is <ipv4 dst> / nvgre tni is <tni> / eth dst is <dst mac> / ipv4 src is <inner ipv4 src> dst is <inner ipv4 dst> / udp src is <sport> dst is <dport> / end actions queue index 4 / end

matched packets::

  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/UDP(sport=<sport>,dport=<dport>)/Raw("x"*80)], iface="<tester interface>", count=1)

mismatched packets::

  >>> sendp([Ether()/IP(dst="<ipv4 dst change inputset>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/UDP(sport=<sport>,dport=<dport>)/Raw("x"*80)], iface="<tester interface>", count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni change inputset>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/UDP(sport=<sport>,dport=<dport>)/Raw("x"*80)], iface="<tester interface>", count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac change inputset>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/UDP(sport=<sport>,dport=<dport>)/Raw("x"*80)], iface="<tester interface>", count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src change inputset>", dst="<inner ipv4 dst>")/UDP(sport=<sport>,dport=<dport>)/Raw("x"*80)], iface="<tester interface>", count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst change inputset>")/UDP(sport=<sport>,dport=<dport>)/Raw("x"*80)], iface="<tester interface>", count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/UDP(sport=<sport change inputset>,dport=<dport>)/Raw("x"*80)], iface="<tester interface>", count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/UDP(sport=<sport>,dport=<dport change inputset>)/Raw("x"*80)], iface="<tester interface>", count=1)


Test Case 8: MAC_IPV4_NVGRE_MAC_IPV4_TCP
----------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 dst is <ipv4 dst> / nvgre tni is <tni> / eth dst is <dst mac>  / ipv4 src is <inner ipv4 src> dst is <inner ipv4 dst> / tcp src is <sport> dst is <dport> / end actions queue index 5 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 dst is <ipv4 dst> / nvgre tni is <tni> / eth dst is <dst mac>  / ipv4 src is <inner ipv4 src> dst is <inner ipv4 dst> / tcp src is <sport> dst is <dport> / end actions rss queues 2 3 end / end

matched packets::

  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/TCP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether()/IP(dst="<ipv4 dst change inputset>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/TCP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni change inputset>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/TCP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac change inputset>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/TCP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src change inputset>", dst="<inner ipv4 dst>")/TCP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst change inputset>")/TCP(sport=<sport>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>", dst="<inner ipv4 dst>")/TCP(sport=<sport change inputset>,dport=<dport>)/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether()/IP(dst="<ipv4 dst>")/NVGRE(TNI=<tni>)/Ether(dst="<dst mac>")/IP(src="<inner ipv4 src>2", dst="<inner ipv4 dst>")/TCP(sport=<sport>,dport=<dport change inputset>)/Raw("x"*80)],iface="<tester interface>",count=1)


Test Case 9: ethertype filter_PPPOED
------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth type is <ethertype> / end actions queue index 4 / end
    testpmd> flow create 0 priority 1 ingress pattern eth type is <ethertype> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>", type=<ethertype>)/Raw("x" *80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>")/PPPoED()/Raw("x" *80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac>", type=<ethertype change inputset>)/Raw("x" *80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>")/PPPoE()/Raw("x" *80)],iface="<tester interface>",count=1)


Test Case 10: MAC_VLAN_PPPOE_IPV4_PAY_session_id_proto_id
---------------------------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <ipv4 proto_id> / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <ipv4 proto_id> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<proto_id>)/IP()/Raw("x"*80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci change inputset>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid change inputset>)/PPP(proto=<ipv4 proto_id>)/IP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6()/Raw("x" * 80)],iface="<tester interface>",count=1)


Test Case 11: MAC_VLAN_PPPOE_IPV6_PAY_session_id_proto_id
---------------------------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <ipv6 proto_id> / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <ipv6 proto_id> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6()/Raw("x" * 80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci change inputset>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid change inputset>)/PPP(proto=<ipv6 proto_id>)/IPv6()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP()/Raw("x" * 80)],iface="<tester interface>",count=1)


Test Case 12: MAC_PPPOE_IPV4_PAY_IP_address
-------------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / pppoes / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="<ipv4 src>", dst="<ipv4 dst>")/Raw("x"*80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="<ipv4 src change inputset>", dst="<ipv4 dst>")/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="<ipv4 src>", dst="<ipv4 dst change inputset>")/Raw("x"*80)],iface="<tester interface>",count=1)


Test Case 13: MAC_PPPOE_IPV6_UDP_PAY
------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is <ipv6 dst> / udp src is <sport> dst is <dport> / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / pppoes / ipv6 dst is <ipv6 dst> / udp src is <sport> dst is <dport> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6(src="<ipv6 src>", dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport>)/Raw("x" * 80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6(src="<ipv6 src>", dst="<ipv6 dst change inputset>")/UDP(sport=<sport>,dport=<dport>)/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6(src="<ipv6 src>", dst="<ipv6 dst>")/UDP(sport=<sport change inputset>,dport=<dport>)/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6(src="<ipv6 src>", dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport change inputset>)/Raw("x" * 80)],iface="<tester interface>",count=1)


Test Case 14: MAC_VLAN_PPPOE_IPV4_TCP_PAY_non_src_dst_port
----------------------------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is <tci> / pppoes / ipv4 src is <ipv4 src> dst is <ipv4 dst> / tcp / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / vlan tci is <tci> / pppoes / ipv4 src is <ipv4 src> dst is <ipv4 dst> / tcp / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP(src="<ipv4 src>", dst="<ipv4 dst>")/TCP()/Raw("x" * 80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci change inputset>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP(src="<ipv4 src>", dst="<ipv4 dst>")/TCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP(src="<ipv4 src change inputset>", dst="<ipv4 dst>")/TCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP(src="<ipv4 src>", dst="<ipv4 dst change inputset>")/TCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP(src="<ipv4 src>", dst="<ipv4 dst>")/UDP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP(src="<ipv4 src>", dst="<ipv4 dst>")/Raw("x" * 80)],iface="<tester interface>",count=1)


Test Case 15: MAC_VLAN_PPPOE_IPV6_PAY_IP_address
------------------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is <tci> / pppoes / ipv6 src is <ipv6 src> / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / vlan tci is <tci> / pppoes / ipv6 src is <ipv6 src> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6(src="<ipv6 src>", dst="<ipv6 dst>")/Raw("x"*80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci change inputset>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6(src="<ipv6 src>", dst="<ipv6 dst>")/Raw("x"*80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv6 proto_id>)/IPv6(src="<ipv6 src change inputset>", dst="<ipv6 dst>")/Raw("x"*80)],iface="<tester interface>",count=1)


Test Case 16: MAC_PPPOE_LCP_PAY
-------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / pppoes seid is <seid> / pppoe_proto_id is <LCP proto_id> / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth dst is <dst mac> / pppoes seid is <seid> / pppoe_proto_id is <LCP proto_id> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<LCP proto_id>)/PPP_LCP()/Raw("x" * 80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<LCP proto_id>)/PPP_LCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=<seid change inputset>)/PPP(proto=<LCP proto_id>)/PPP_LCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP()/Raw("x" * 80)],iface="<tester interface>",count=1)


Test Case 17: MAC_PPPOE_IPCP_PAY
--------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / pppoes seid is <seid> / pppoe_proto_id is <IPCP proto_id> / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth dst is <dst mac> / pppoes seid is <seid> / pppoe_proto_id is <IPCP proto_id> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<IPCP proto_id>)/PPP_IPCP()/Raw("x" * 80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<IPCP proto_id>)/PPP_IPCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=<seid change inputset>)/PPP(proto=<IPCP proto_id>)/PPP_IPCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP()/Raw("x" * 80)],iface="<tester interface>",count=1)


Test Case 18: MAC_VLAN_PPPOE_LCP_PAY
------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <LCP proto_id> / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <LCP proto_id> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<LCP proto_id>)/PPP_LCP()/Raw("x" * 80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<LCP proto_id>)/PPP_LCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci change inputset>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<LCP proto_id>)/PPP_LCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid change inputset>)/PPP(proto=<LCP proto_id>)/PPP_LCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP()/Raw("x" * 80)],iface="<tester interface>",count=1)


Test Case 19: MAC_VLAN_PPPOE_IPCP_PAY
-------------------------------------
rules::

    testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <IPCP proto_id> / end actions queue index 1 / end
    testpmd> flow create 0 priority 1 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <IPCP proto_id> / end actions queue index 2 / end

matched packets::

  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<IPCP proto_id>)/PPP_IPCP()/Raw("x" * 80)],iface="<tester interface>",count=1)

mismatched packets::

  >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<IPCP proto_id>)/PPP_IPCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci change inputset>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<IPCP proto_id>)/PPP_IPCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid change inputset>)/PPP(proto=<IPCP proto_id>)/PPP_IPCP()/Raw("x" * 80)],iface="<tester interface>",count=1)
  >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<tci>,type=0x8864)/PPPoE(sessionid=<seid>)/PPP(proto=<ipv4 proto_id>)/IP()/Raw("x" * 80)],iface="<tester interface>",count=1)


Test Case 20: check flow priority filter
----------------------------------------
1. launch testpmd with --log-level="ice,7"

2. create rules with priority 0, check the rule is created to switch with a log "Succeeded to create (2) flow"::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 dst is <ipv4 src> / nvgre tni is <tni> / eth / ipv4 src is <inner ipv4 src> dst is <inner ipv4 dst> / end actions queue index 3 / end
    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / tcp src is <sport> dst is <dport> / end actions rss queues 4 5 end / end
    testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <ipv6 proto_id> / end actions drop / end

3. create rules with priority 0, and the action is mark, check the rule is created to fdir with a log "Succeeded to create (1) flow"::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / tcp src is <sport> dst is <dport> / end actions rss queues 4 5 end / mark id 3 / end

4. create rules with priority 1, check the rule is created to switch with a log "Succeeded to create (2) flow"::

    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / tcp src is <sport> dst is <dport> / end actions rss queues 4 5 end / end
    testpmd> flow create 0 priority 1 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <ipv6 proto_id> / end actions drop / end

5. create rules with priority 1, and the action is mark, check the rule create fail::

    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 dst is <ipv4 src> / nvgre tni is <tni> / eth / ipv4 src is <inner ipv4 src> dst is <inner ipv4 dst> / end actions queue index 3 / mark id 3 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / tcp src is <sport> dst is <dport> / end actions rss queues 4 5 end / mark id 3 / end
    testpmd> flow create 0 priority 1 ingress pattern eth dst is <dst mac> / vlan tci is <tci> / pppoes seid is <seid> / pppoe_proto_id is <ipv6 proto_id> / end actions drop / mark id 3 / end


Test Case 21: negative test cases
---------------------------------
1. create rules, check all these rules can not be created::

    testpmd> flow create 0 priority 2 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 3 / end
    testpmd> flow create 0 priority a ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 3 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions mark / rss / end


Test Case 22: exclusive test cases
----------------------------------
Subcase 1: same pattern/input set/action different priority
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. create same pattern, input set and action but different priority, check these two rules can be created::

    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 3 / end
    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 3 / end

2. send matched pkts and check queue 3 receive this pkt::

    >>> sendp([Ether(dst="<dst mac>")/IP(src="<ipv4 src>",dst="<ipv4 dst>")/TCP()/("X"*480)], iface="<tester interface>", count=1)

3. destroy rules::

    flow flush 0

Subcase 2: same pattern/input set/priority different action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. create same pattern, input set and priority but different action, check the second rule can not be created::

    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 3 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions rss queues 4 5 end / end

Subcase 3: some rules overlap
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. create rules::

    testpmd> flow create 0 priority 0 ingress pattern eth / vlan / vlan / pppoes / pppoe_proto_id is 0x21 / end actions queue index 3 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / vlan / vlan / pppoes seid is 1 / ipv4 / end actions queue index 2 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / vlan / vlan tci is 12 / end actions queue index 4 / end
    testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:00:00:01:03:13 / vlan / vlan / end actions rss queues 1 2 end / end
    testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:00:00:01:03:03 / end actions queue index 8 / end
    testpmd> flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / vlan tci is 2 / end actions queue index 4 / end

2. check all the rules exist in the list::

    flow list 0

3. send pkt which match rule 0 and rule 1, check the pkt can be received by queue 3::

    >>> sendp([Ether(type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/UDP(dport=23)/("X"*480)], iface="<tester interface>")

4. destroy rule 0, repeat step 3 and check the pkt can be received by queue 2::

    flow destroy 0 rule 0

5. send pkt which match rule 2 and rule 3, check the pkt can be received by queue 1 or 2::

    >>> sendp([Ether(dst="00:00:00:01:03:13")/Dot1Q(vlan=1)/Dot1Q(vlan=12)/Raw("x"*480)], iface="<tester interface>", count=1)

6. destroy rule 3, repeat step 5 and check the pkt can be received by queue 4::

    flow destroy 0 rule 3

7. send pkt which match rule 4 and rule 5, check the pkt will be received by queue 8::

    >>> sendp([Ether(dst="00:00:00:01:03:03")/Dot1Q(vlan=1)/Dot1Q(vlan=2)/Raw("x"*480)], iface="<tester interface>", count=1)

8. destroy rule 4, repeat step 7 and check the pkts can be received by queue 4::

    flow destroy 0 rule 3

Test case 23: Create Flow Rules Only Supported by Fdir Filter with Priority 0
-----------------------------------------------------------------------------

Creating a rule only supported by fdir filter with priority 0, it is not acceptable.

Patterns in this case:
   MAC_IPV6_SCTP
   MAC_IPV4_SCTP

#. Start the ``testpmd`` application as follows::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:af:00.0,pipeline-mode-support=1 --log-level="ice,7" -- -i --txq=8 --rxq=8
    set fwd rxonly
    set verbose 1

#. Create rules, check the flows can not be created::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 src is 1111:2222:3333:4444:5555:6666:7777:8888 dst is 1111:2222:3333:4444:5555:6666:7777:9999 / sctp src is 25 dst is 23 / end actions queue index 1 / end
    ice_flow_create(): Failed to create flow
    Caught error type 2 (flow rule (handle)): Invalid input pattern: Invalid argument

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 ttl is 20 / sctp src is 25 dst is 23 / end actions queue index 1 / end
    ice_flow_create(): Failed to create flow
    Caught error type 2 (flow rule (handle)): Invalid input pattern: Invalid argument


Test case 24: Create flow rules only supported by switch filter with priority 1
-------------------------------------------------------------------------------

Create a rule only supported by fdir switch with priority 1, it is not acceptable.

Patterns in this case:
   MAC_IPV4_NVGRE_MAC_IPV4
   MAC_IPV4_NVGRE_MAC_IPV4_UDP

#. Start the ``testpmd`` application as follows::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:af:00.0,pipeline-mode-support=1 --log-level="ice,7" -- -i --txq=8 --rxq=8
    set fwd rxonly
    set verbose 1

#. Create rules, check the flows can not be created::

    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 3 / end
    ice_flow_create(): Failed to create flow
    Caught error type 13 (specific pattern item): cause: 0x7fffe65b8128, Unsupported pattern: Invalid argument

    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 25 dst is 23 / end actions queue index 3 / end
    ice_flow_create(): Failed to create flow
    Caught error type 13 (specific pattern item): cause: 0x7fffe65b8128, Unsupported pattern: Invalid argument

Test case 25: Create Flow Rules with Priority in Pipeline Mode
--------------------------------------------------------------

Priority is active in pipeline mode.
Creating flow rules and setting priority 0/1 will map switch/fdir filter separately.

Patterns in this case:
   MAC_IPV4_TCP
   MAC_IPV4_VXLAN_IPV4_UDP_PAY

#. Start the ``testpmd`` application as follows::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:af:00.0,pipeline-mode-support=1 --log-level="ice,7" -- -i --txq=8 --rxq=8
    set fwd rxonly
    set verbose 1
    rx_vxlan_port add 4789 0

#. Create switch filter rules::

    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 1 / end

    flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 25 dst is 23 / end actions queue index 2 / end

#. Create fdir filter rules::

    flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.4 dst is 192.168.0.7 tos is 4 ttl is 20 / tcp src is 25 dst is 23 / end actions queue index 3 / end

    flow create 0 priority 1 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.4 dst is 192.168.0.7 / udp src is 25 dst is 23 / end actions queue index 4 / end

#. Check flow list with commands "flow list 0", all flows are created correctly::

    +-----+--------+--------+--------+-----------------------+
    |ID	 | Group  | Prio   | Attr   | Rul                   |
    +=====+========+========+========+=======================+
    | 0   | 0      | 0	   | i-     | ETH IPV4 TCP => QUEUE |
    +-----+--------+--------+--------+-----------------------+
    | 1       ...			                    |
    +-----+--------+--------+--------+-----------------------+
    | 2       ...			                    |
    +-----+--------+--------+--------+-----------------------+
    | 3       ...			                    |
    +-----+--------+--------+--------+-----------------------+

#. Send packets according to the created rules in tester::

    sendp([Ether(dst="00:00:00:00:11:00",src="11:22:33:44:55:66")/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp134s0f0")
    sendp([Ether(dst="00:00:00:00:11:00",src="11:22:33:44:55:66")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=25,dport=23)/Raw('x'*80)],iface="enp134s0f0")
    sendp([Ether(dst="00:00:00:00:11:00",src="11:22:33:44:55:66")/IP(src="192.168.0.4",dst="192.168.0.7",tos=4,ttl=20)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp134s0f0")
    sendp([Ether(dst="00:00:00:00:11:00",src="11:22:33:44:55:66")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.4 ",dst="192.168.0.7")/UDP(sport=25,dport=23)/Raw('x'*80)],iface="enp134s0f0")

#. Check the packets are recieved in right queues by dut::

    testpmd> port 0/queue 1: received 1 packets
     src=11:22:33:44:55:66 - dst=00:00:00:00:11:00 - type=0x0800 - length=134 - nb_segs=1 - RSS hash=0x96803f93 - RSS queue=0x1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_TCP  - sw ptype: L2_ETHER L3_IPV4 L4_TCP  - l2_len=14 - l3_len=20 - l4_len=20 - Receive queue=0x1
     ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    ......

#. Create rules without priority, Check only patterns supported by switch can be created for the default priorty is 0.
So the first flow can be created and the second flow can not be created::

   testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.1 tos is 5 / tcp src is 25 dst is 23 / end actions queue index 1 / end
   ice_flow_create(): Succeeded to create (2) flow
   Flow rule #1 created
   testpmd>  flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 ttl is 20 / sctp src is 25 dst is 23 / end actions queue index 1 / end
   ice_flow_create(): Failed to create flow
   Caught error type 2 (flow rule (handle)): Invalid input pattern: Invalid argument

Test case 26: Create flow rules with same parameter but different actions
-------------------------------------------------------------------------

It is acceptable to create same rules with differenet filter in pipeline mode.
When fdir filter and switch filter has the same parameter rules, the flow will map to switch then fdir.

Patterns in this case:
    MAC_IPV4_TCP

#. Start the ``testpmd`` application as follows::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:af:00.0,pipeline-mode-support=1 --log-level="ice,7" -- -i --txq=8 --rxq=8
    set fwd rxonly
    set verbose 1

#. Create switch rule then fdir rule with the same parameter, check two flows can be created::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 1 / end
    ice_flow_create(): Succeeded to create (2) flow
    Flow rule #0 created

    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 3 / end
    ice_interrupt_handler(): OICR: MDD event
    ice_flow_create(): Succeeded to create (1) flow
    Flow rule #1 created

#. Tester send a pkt to dut::

    sendp([Ether(dst="00:00:00:00:11:00",src="11:22:33:44:55:66")/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp134s0f0")

#. Check the packets are recieved by dut in queue 1::

    testpmd> port 0/queue 1: received 1 packets
    src=11:22:33:44:55:66 - dst=00:00:00:00:11:00 - type=0x0800 - length=134 - nb_segs=1 - RSS hash=0xf12811f1 - RSS queue=0x1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_TCP  - sw ptype: L2_ETHER L3_IPV4 L4_TCP  - l2_len=14 - l3_len=20 - l4_len=20 - Receive queue=0x1
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

#. Remove the switch rule::

    testpmd>flow destroy 0 rule 0

#. Tester send a pkt to dut::

    sendp([Ether(dst="00:00:00:00:11:00",src="11:22:33:44:55:66")/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp134s0f0")

#. Check the packets are recieved in queue 3::

    testpmd> port 0/queue 3: received 1 packets
    src=11:22:33:44:55:66 - dst=00:00:00:00:11:00 - type=0x0800 - length=134 - nb_segs=1 - RSS hash=0xf12811f1 - RSS queue=0x3 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_TCP  - sw ptype: L2_ETHER L3_IPV4 L4_TCP  - l2_len=14 - l3_len=20 - l4_len=20 - Receive queue=0x3
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

#. Restart the ``testpmd`` application as follows::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:af:00.0, pipeline-mode-support=1 --log-level="ice,7" -- -i --txq=8 --rxq=8
    set fwd rxonly
    set verbose 1

#. Create fdir rule then switch rule with the same parameter, check two flows can be created::

    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 3 / end
    ice_interrupt_handler(): OICR: MDD event
    ice_flow_create(): Succeeded to create (1) flow
    Flow rule #0 created

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 1 / end
    ice_flow_create(): Succeeded to create (2) flow
    Flow rule #1 created

#. Tester send a pkt to dut::

    sendp([Ether(dst="00:00:00:00:11:00",src="11:22:33:44:55:66")/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp134s0f0")

#. Check the packets are recieved by dut in queue 1::

    testpmd> port 0/queue 1: received 1 packets
     src=11:22:33:44:55:66 - dst=00:00:00:00:11:00 - type=0x0800 - length=134 - nb_segs=1 - RSS hash=0xf12811f1 - RSS queue=0x1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_TCP  - sw ptype: L2_ETHER L3_IPV4 L4_TCP  - l2_len=14 - l3_len=20 - l4_len=20 - Receive queue=0x1
     ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

#. Remove the switch rule::

    testpmd>flow destroy 0 rule 1

#. Tester send a pkt to dut::

    sendp([Ether(dst="00:00:00:00:11:00",src="11:22:33:44:55:66")/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp134s0f0")

#. Check the packets are recieved in queue 3::

    testpmd> port 0/queue 3: received 1 packets
     src=11:22:33:44:55:66 - dst=00:00:00:00:11:00 - type=0x0800 - length=134 - nb_segs=1 - RSS hash=0xf12811f1 - RSS queue=0x3 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_TCP  - sw ptype: L2_ETHER L3_IPV4 L4_TCP  - l2_len=14 - l3_len=20 - l4_len=20 - Receive queue=0x3
     ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN