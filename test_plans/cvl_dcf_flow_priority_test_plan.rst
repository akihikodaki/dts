.. Copyright (c) <2021>, Intel Corporation
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   - Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.

   - Neither the name of Intel Corporation nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.

================================
CVL Support Flow Priority in DCF
================================

Description
===========
* DCF is able to accept RTE_FLOW's priority attribute and create a switch rule with corresponding priority.
* Currently only support priority 0 and 1. 0 means low priority and 1 means high priority.
* When creating a new switch rule, the driver need to avoid reuse an existing recipe with a different priority even the input set is matched,
  it should either reject the request or create a new recipe with a different priority.
* When looking up rule table, matched pkt will hit the high priority rule firstly,
  it will hit the low priority rule only when there is no high priority rule exist.


Prerequisites
=============
1. Hardware:
   columbiaville_25g/columbiaville_100g

2. Software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/updates/intel/ice/ddp/ice.pkg,
   then load driver::

    rmmod ice
    insmod ice.ko

4. Compile DPDK::

    CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

5. Get the pci device id of DUT, for example::

    ./usertools/dpdk-devbind.py -s

    0000:18:00.0 'Device 159b' if=ens785f0 drv=ice unused=vfio-pci
    0000:18:00.1 'Device 159b' if=ens785f1 drv=ice unused=vfio-pci

6. Enable vlan prune flag::

    ethtool --set-priv-flags ens785f0 vf-vlan-prune-disable on

7. Generate 4 VFs on PF0(not all the VFs are used)::

    echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

    ./usertools/dpdk-devbind.py -s
    0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v0 drv=iavf unused=vfio-pci
    0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v1 drv=iavf unused=vfio-pci
    0000:18:01.2 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v2 drv=iavf unused=vfio-pci
    0000:18:01.3 'Ethernet Adaptive Virtual Function 1889' if=ens785f0v3 drv=iavf unused=vfio-pci

8. Set VF0 as trust::

    ip link set ens785f0 vf 0 trust on

9. Set mac addr for VF1, VF2 and VF3::

    ip link set ens785f0 vf 1 mac 00:11:22:33:44:11
    ip link set ens785f0 vf 2 mac 00:11:22:33:44:22
    ip link set ens785f0 vf 3 mac 00:11:22:33:44:33

10. Bind VFs to dpdk driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1 0000:18:01.2 0000:18:01.3

11. launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf -a 0000:18:01.1 -a 0000:18:01.2 -a 0000:18:01.3 -- -i

    testpmd> set fwd rxonly

    testpmd> set verbose 1

    testpmd> start

    testpmd> show port info all

   check the VF0 driver is net_ice_dcf.


test steps for supported pattern
================================
1. validate rules: two rules have same pattern, input set but different priority and action(priority 0 -> to vf 1, priority 1 -> to vf 2).
2. create rules and list rules.
3. send matched packets, check vf 1 receive the packets for hiting the priority 0.
4. send mismatched packets, check the packets are not received by vf 1 or 2.
5. destroy rule with priority 0, list rules.
6. send matched packets, check vf 2 receive the packets for hiting the priority 1.
7. send mismatched packets, check the packets are not received by vf 1 or 2.
8. recreate rules which priority is 0, list rule.
9. destroy rule with priority 1, list rules.
10. send matched packets, check vf 1 receive the packets for hiting the priority 0.
11. send mismatched packets, check the packets are not received by vf 1 or 2.
12. destroy rule with priority 0, list rules.
13. send matched packets, check the packets are not received by vf 1 or 2.


support pattern and input set
=============================

  +---------------------+-------------------------------+-------------------------------------------+
  |    Packet Types     |           Pattern             |                Input Set                  |
  +=====================+===============================+===========================================+
  |                     | MAC_PAY                       | [Source MAC], [Dest MAC], [Ether type]    |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_FRAG                 | [Dest MAC], [Source IP], [Dest IP],       |
  |                     |                               | [TTL], [DSCP]                             |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_PAY                  | [Dest MAC], [Source IP], [Dest IP],       |
  |                     |                               | [IP protocol], [TTL], [DSCP]              |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_UDP_PAY              | [Dest MAC], [Source IP], [Dest IP],       |
  |                     |                               | [TTL], [DSCP], [Source Port], [Dest Port] |
  |                     +-------------------------------+-------------------------------------------+
  |    IPv4/IPv6 +      | MAC_IPV4_TCP_PAY              | [Dest MAC], [Source IP], [Dest IP],       |
  |    TCP/UDP/IGMP     |                               | [TTL], [DSCP], [Source Port], [Dest Port] |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_IGMP                 | [IP protocol]                             |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_FRAG_srcip_dstip     | [Source IP], [Dest IP]                    |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_FRAG_dstip_tc        | [Dest MAC], [Dest IP], [TC]               |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_PAY_srcip_dstip      | [Source IP], [Dest IP]                    |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_PAY_dstip_tc         | [Dest MAC], [Dest IP], [TC]               |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_UDP_PAY              | [Dest MAC], [Dest IP], [TC],              |
  |                     |                               | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_TCP                  | [Dest MAC], [Dest IP], [TC],              |
  |                     |                               | [Source Port], [Dest Port]                |
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
  |       tunnel:       +-------------------------------+-------------------------------------------+
  |       NVGRE         | MAC_IPV4_TUN_MAC_IPV4_FRAG    | [Out Dest IP], [VNI/GRE_KEY],             |
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
  |                     | MAC_VLAN_PPPOE_IPV4_PAY       | [Dest MAC], [VLAN], [seid],               |
  |                     | _session_id_proto_id          | [pppoe_proto_id]                          |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV6_PAY       | [Dest MAC], [VLAN], [seid],               |
  |                     | _session_id_proto_id          | [pppoe_proto_id]                          |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV4_PAY            | [Dest MAC], [seid], [pppoe_proto_id]      |
  |                     | _session_id_proto_id          |                                           |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV6_PAY            | [Dest MAC], [seid], [pppoe_proto_id]      |
  |                     | _session_id_proto_id          |                                           |
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
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV6_UDP_PAY        | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV6_UDP_PAY        | [Source IP], [Dest IP]                    |
  |                     | _non_src_dst_port             |                                           |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV6_TCP_PAY        | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port], [Dest Port]                |
  |       PPPOES        +-------------------------------+-------------------------------------------+
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
  |                     | MAC_IPV4_PFCP_NODE            | [Dest Port], [S-field]                    |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_PFCP_SESSION         | [Dest Port], [S-field]                    |
  |        PFCP         +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_PFCP_NODE            | [Dest Port], [S-field]                    |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_PFCP_SESSION         | [Dest Port], [S-field]                    |
  +---------------------+-------------------------------+-------------------------------------------+
  |                     | IP multicast                  | [Dest IP]                                 |
  |      multicast      +-------------------------------+-------------------------------------------+
  |                     | L2 multicast                  | [Dest MAC]                                |
  +---------------------+-------------------------------+-------------------------------------------+
  |                     | ethertype filter_PPPOD        | [Ether type]                              |
  |                     +-------------------------------+-------------------------------------------+
  |   ethertype filter  | ethertype filter_PPPOE        | [Ether type]                              |
  |                     +-------------------------------+-------------------------------------------+
  |                     | ethertype filter_IPV6         | [Ether type]                              |
  +---------------------+-------------------------------+-------------------------------------------+
  |                     | UDP port filter_DHCP discovery| [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+
  |   UDP port filter   | UDP port filter_DHCP offer    | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+
  |                     | UDP port filter_VXLAN         | [Dest Port]                               |
  +---------------------+-------------------------------+-------------------------------------------+
  |   MAC VLAN filter   | MAC_VLAN filter               | [Dest MAC], [VLAN]                        |
  +---------------------+-------------------------------+-------------------------------------------+
  |    VLAN filter      | VLAN filter                   | [VLAN]                                    |
  +---------------------+-------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_L2TPv3               | [Source IP], [Dest IP], [Session_id]      |
  |        L2TPv3       +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_L2TPv3               | [Source IP], [Dest IP], [Session_id]      |
  +---------------------+-------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_ESP                  | [Source IP], [Dest IP], [SPI]             |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_ESP                  | [Source IP], [Dest IP], [SPI]             |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_AH                   | [Source IP], [Dest IP], [SPI]             |
  |         ESP         +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_AH                   | [Source IP], [Dest IP], [SPI]             |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_NAT-T-ESP            | [Source IP], [Dest IP], [SPI]             |
  |                     +-------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_NAT-T-ESP            | [Source IP], [Dest IP], [SPI]             |
  +---------------------+-------------------------------+-------------------------------------------+


test case 01: MAC_PAY (this case is not supported in dpdk-21.05)
================================================================
rules::

    flow validate 0 priority 0 ingress pattern eth src is 00:00:00:00:00:01 dst is 00:11:22:33:44:55 type is 0x0800 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth src is 00:00:00:00:00:01 dst is 00:11:22:33:44:55 type is 0x0800 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth src is 00:00:00:00:00:01 dst is 00:11:22:33:44:55 type is 0x0800 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth src is 00:00:00:00:00:01 dst is 00:11:22:33:44:55 type is 0x0800 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="00:00:00:00:00:01",dst="00:11:22:33:44:55")/IP()/Raw("x" *80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="00:00:00:00:00:02",dst="00:11:22:33:44:55")/IP()/Raw("x" *80)],iface="ens786f0",count=1)
    sendp([Ether(src="00:00:00:00:00:01",dst="00:11:22:33:44:54")/IP()/Raw("x" *80)],iface="ens786f0",count=1)
    sendp([Ether(src="00:00:00:00:00:01",dst="00:11:22:33:44:55")/IPv6()/Raw("x" *80)],iface="ens786f0",count=1)


test case 02: MAC_IPV4_FRAG
===========================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2,frag=5)/("X"*480)], iface="ens786f0", count=1)

mismatched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2,frag=5)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4",dst="192.168.0.2",tos=4,ttl=2,frag=5)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.5",tos=4,ttl=2,frag=5)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=2,frag=5)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3,frag=5)/("X"*480)], iface="ens786f0", count=1)


test case 03: MAC_IPV4_PAY
===============================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 6 tos is 4 ttl is 2 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 6 tos is 4 ttl is 2 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 6 tos is 4 ttl is 2 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 6 tos is 4 ttl is 2 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)], iface="ens786f0", count=1)

mismatched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.5",tos=4,ttl=2)/TCP()/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=2)/TCP()/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP()/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/UDP()/("X"*480)], iface="ens786f0", count=1)


test case 04: MAC_IPV4_UDP_PAY
===============================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)

mismatched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.5",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.7",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=9)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=30,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=19)/("X"*480)], iface="ens786f0", count=1)


test case 05: MAC_IPV4_TCP_PAY
===============================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)

mismatched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.5",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.7",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=3)/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=9)/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=30,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=19)/("X"*480)], iface="ens786f0", count=1)


test case 06: MAC_IPV4_IGMP
===========================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 proto is 0x02 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 proto is 0x02 / end actions vf id 1 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 proto is 0x02 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 proto is 0x02 / end actions vf id 1 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/IGMP()/Raw("X"*480)], iface="ens786f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/Raw("X"*480)], iface="ens786f0", count=1)


test case 07: MAC_IPV6_srcip_dstip
==================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)], iface="ens786f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/("X"*480)], iface="ens786f0", count=1)


test case 08: MAC_IPV6_dstip_tc
===============================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/("X"*480)], iface="ens786f0", count=1)

mismatched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/("X"*480)], iface="ens786f0", count=1)


test case 09: MAC_IPV6_UDP_PAY
==============================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0",count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0",count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=7)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0",count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=30,dport=23)/("X"*480)], iface="ens786f0",count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=19)/("X"*480)], iface="ens786f0",count=1)


test case 10: MAC_IPV6_TCP
==========================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)

mismatched pkts::

    sendp([Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=7)/TCP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=30,dport=23)/("X"*480)], iface="ens786f0", count=1)
    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=19)/("X"*480)], iface="ens786f0", count=1)


test case 11: MAC_IPV4_NVGRE_IPV4_PAY
=====================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 2 / end

matched pkts::

    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)


test case 12: MAC_IPV4_NVGRE_IPV4_UDP_PAY
=========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)

mismatched pkts::

    sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.5", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.7")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)], iface="ens786f0", count=1)


test case 13: MAC_IPV4_NVGRE_IPV4_TCP
=====================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.5", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=20,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=39)/Raw("x"*80)],iface="ens786f0",count=1)


test case 14: MAC_IPV4_NVGRE_MAC_IPV4_PAY
=========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 2 / end

matched pkts::

    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)


test case 15: MAC_IPV4_NVGRE_MAC_IPV4_UDP_PAY
=============================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)

mismatched pkts::

    sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a2")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw("x"*80)], iface="ens786f0", count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw("x"*80)], iface="ens786f0", count=1)


test case 16: MAC_IPV4_NVGRE_MAC_IPV4_TCP
=========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a2")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.5", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw("x"*80)],iface="ens786f0",count=1)


test case 17: MAC_IPV4_PFCP_NODE
================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 2 / end

matched pkts::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")

mismatched pkts::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")


test case 18: MAC_IPV4_PFCP_SESSION
===================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 2 / end

matched pkts::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")

mismatched pkts::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")


test case 19: MAC_IPV6_PFCP_NODE
================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions vf id 2 / end

matched pkts::

    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")

mismatched pkts::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")


test case 20: MAC_IPV6_PFCP_SESSION
===================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions vf id 2 / end

matched pkts::

    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")

mismatched pkts::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")


test case 21: IP multicast
==========================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions vf id 2 / end

matched pkts::

    sendp([Ether()/IP(dst="239.0.0.0")/TCP()/Raw("x"*80)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether()/IP(dst="128.0.0.0")/TCP()/Raw("x"*80)], iface="enp27s0f0", count=1)


test case 22: L2 multicast
==========================
rules::

    flow validate 0 priority 0 ingress pattern eth dst spec 01:00:5e:00:00:00 dst mask ff:ff:ff:80:00:00 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst spec 01:00:5e:00:00:00 dst mask ff:ff:ff:80:00:00 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst spec 01:00:5e:00:00:00 dst mask ff:ff:ff:80:00:00 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst spec 01:00:5e:00:00:00 dst mask ff:ff:ff:80:00:00 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="01:00:5e:7f:00:00")/IP()/TCP()/Raw("x"*80)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst="01:00:5e:ff:00:00")/IP()/TCP()/Raw("x"*80)], iface="enp27s0f0", count=1)


test case 23: ethertype filter_PPPOD
====================================
rules::

    flow validate 0 priority 0 ingress pattern eth type is 0x8863 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth type is 0x8863 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth type is 0x8863 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth type is 0x8863 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x" *80)],iface="enp27s0f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x" *80)],iface="enp27s0f0",count=1)


test case 24: ethertype filter_PPPOE
====================================
rules::

    flow validate 0 priority 0 ingress pattern eth type is 0x8864 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth type is 0x8864 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth type is 0x8864 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth type is 0x8864 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x"*80)],iface="enp27s0f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x"*80)],iface="enp27s0f0",count=1)


test case 25: ethertype filter_IPV6
====================================
rules::

    flow validate 0 priority 0 ingress pattern eth type is 0x86dd / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth type is 0x86dd / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth type is 0x86dd / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth type is 0x86dd / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", tc=3)/TCP(dport=23)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", tc=3)/TCP(dport=23)/("X"*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/TCP(dport=23)/("X"*480)], iface="enp27s0f0", count=1)


test case 26: UDP port filter_DHCP discovery
============================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 / udp src is 68 dst is 67 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 / udp src is 68 dst is 67 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 / udp src is 68 dst is 67 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 / udp src is 68 dst is 67 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=68,dport=67)/BOOTP(chaddr="3c:fd:fe:b2:43:90")/DHCP(options=[("message-type","discover"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=63,dport=67)/BOOTP(chaddr="3c:fd:fe:b2:43:90")/DHCP(options=[("message-type","discover"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=68,dport=69)/BOOTP(chaddr="3c:fd:fe:b2:43:90")/DHCP(options=[("message-type","discover"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)


test case 27: UDP port filter_DHCP offer
========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 / udp src is 67 dst is 68 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 / udp src is 67 dst is 68 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 / udp src is 67 dst is 68 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 / udp src is 67 dst is 68 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=67,dport=68)/BOOTP(chaddr="3c:fd:fe:b2:43:90",yiaddr="192.168.1.0")/DHCP(options=[("message-type","offer"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=63,dport=68)/BOOTP(chaddr="3c:fd:fe:b2:43:90",yiaddr="192.168.1.0")/DHCP(options=[("message-type","offer"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=67,dport=63)/BOOTP(chaddr="3c:fd:fe:b2:43:90",yiaddr="192.168.1.0")/DHCP(options=[("message-type","offer"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)


test case 28: UDP port filter_VXLAN
===================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 / udp dst is 4789 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 / udp dst is 4789 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 / udp dst is 4789 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 / udp dst is 4789 / end actions vf id 2 / end

matched pkts::

    sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)

mismatched pkts::

    sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)


test case 29: MAC_VLAN filter
==============================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)],iface="enp27s0f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)],iface="enp27s0f0",count=1)


test case 30: VLAN filter
==========================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)],iface="enp27s0f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)],iface="enp27s0f0",count=1)


test case 31: MAC_IPV4_L2TPv3
=============================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst='00:11:22:33:44:12')/IP(src='192.168.0.2', proto=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst='00:11:22:33:44:12')/IP(src='192.168.0.2', proto=115)/L2TP('\x00\x00\x00\x02')/('X'*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst='00:11:22:33:44:12')/IP(src='192.168.1.2', proto=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst='00:11:22:33:44:12')/IP(dst='192.168.0.2', proto=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)


test case 32: MAC_IPV6_L2TPv3
=============================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / l2tpv3oip session_id is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / l2tpv3oip session_id is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / l2tpv3oip session_id is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / l2tpv3oip session_id is 1 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst='00:11:22:33:44:13')/IPv6(dst='1111:2222:3333:4444:5555:6666:7777:8888', nh=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst='00:11:22:33:44:13')/IPv6(dst='1111:2222:3333:4444:5555:6666:7777:8888', nh=115)/L2TP('\x00\x00\x00\x02')/('X'*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst='00:11:22:33:44:13')/IPv6(dst='1111:2222:3333:4444:5555:6666:7777:9999', nh=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst='00:11:22:33:44:13')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888', nh=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)


test case 33: MAC_IPV4_ESP
===========================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=50)/ESP(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.1.2", proto=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IP(dst="192.168.0.2", proto=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)


test case 34: MAC_IPV6_ESP
===========================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / esp spi is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / esp spi is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / esp spi is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / esp spi is 1 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=50)/ESP(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999", nh=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", nh=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)


test case 35: MAC_IPV4_AH
===========================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=51)/AH(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.1.2", proto=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IP(dst="192.168.0.2", proto=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)


test case 36: MAC_IPV6_AH
===========================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / ah spi is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / ah spi is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / ah spi is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / ah spi is 1 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=51)/AH(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999", nh=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", nh=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)


test case 37: MAC_IPV4_NAT-T-ESP
================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / udp / esp spi is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 / udp / esp spi is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / udp / esp spi is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 / udp / esp spi is 1 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2")/UDP(dport=4500)/ESP(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.1.2")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IP(dst="192.168.0.2")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)


test case 38: MAC_IPV6_NAT-T-ESP
================================
rules::

    flow validate 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / udp / esp spi is 1 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / udp / esp spi is 1 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / udp / esp spi is 1 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / udp / esp spi is 1 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
    sendp([Ether(dst="00:11:22:33:44:13")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)


test case 39: MAC_VLAN_PPPOE_IPV4_PAY_session_id_proto_id
=========================================================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)


test case 40: MAC_VLAN_PPPOE_IPV6_PAY_session_id_proto_id
=========================================================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)


test case 41: MAC_PPPOE_IPV4_PAY_session_id_proto_id
====================================================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)


test case 42: MAC_PPPOE_IPV6_PAY_session_id_proto_id
====================================================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)


test case 43: MAC_PPPOE_IPV4_PAY_IP_address
===========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)],iface="ens786f0",count=1)


test case 44: MAC_PPPOE_IPV4_UDP_PAY
===========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)


test case 45: MAC_PPPOE_IPV4_UDP_PAY_non_src_dst_port
=====================================================
rules::

    flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)


test case 46: MAC_PPPOE_IPV4_TCP_PAY
=====================================
rules::

    flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)


test case 47: MAC_PPPOE_IPV4_TCP_PAY_non_src_dst_port
======================================================
rules::

    flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)


test case 48: MAC_PPPOE_IPV6_PAY_IP_address
===========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)


test case 49: MAC_PPPOE_IPV6_UDP_PAY
====================================
rules::

    flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)


test case 50: MAC_PPPOE_IPV6_UDP_PAY_non_src_dst_port
=====================================================
rules::

    flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)


test case 51: MAC_PPPOE_IPV6_TCP_PAY
=====================================
rules::

    flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)


test case 52: MAC_PPPOE_IPV6_TCP_PAY_non_src_dst_port
=====================================================
rules::

    flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)


test case 53: MAC_VLAN_PPPOE_IPV4_PAY_IP_address
=================================================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)],iface="ens786f0",count=1)


test case 54: MAC_VLAN_PPPOE_IPV4_UDP_PAY
=========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)


test case 55: MAC_VLAN_PPPOE_IPV4_UDP_PAY_non_src_dst_port
==========================================================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)


test case 56: MAC_VLAN_PPPOE_IPV4_TCP_PAY
=========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)


test case 57: MAC_VLAN_PPPOE_IPV4_TCP_PAY_non_src_dst_port
==========================================================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)


test case 58: MAC_VLAN_PPPOE_IPV6_PAY_IP_address
================================================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)
    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)


test case 59: MAC_VLAN_PPPOE_IPV6_UDP_PAY
=========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)


test case 60: MAC_VLAN_PPPOE_IPV6_UDP_PAY_non_src_dst_port
==========================================================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)


test case 61: MAC_VLAN_PPPOE_IPV6_TCP_PAY
=========================================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)


test case 62: MAC_VLAN_PPPOE_IPV6_TCP_PAY_non_src_dst_port
==========================================================
rules::

    flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)


test case 63: MAC_PPPOE_LCP_PAY
===============================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)


test case 64: MAC_PPPOE_IPCP_PAY
================================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)


test case 65: MAC_VLAN_PPPOE_LCP_PAY
====================================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)


test case 66: MAC_VLAN_PPPOE_IPCP_PAY
=====================================
rules::

    flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 1 / end
    flow validate 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 2 / end

matched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched pkts::

    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
    sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)


test case: negative test cases
==============================

1. create rules, check all these rules can not be created::

    flow create 0 priority 2 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 1 / end
    flow create 0 priority a ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 1 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 4 / end


test case: exclusive test cases
===============================
subcase 1: same pattern/input set/action different priority
-----------------------------------------------------------
1. create same pattern, input set and action but different priority, check these two rules can be created::

    flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 2 / end

2. send matched pkts and check vf2 receive this pkt::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)], iface="ens786f0", count=1)

3. destroy rules::

    flow flush 0

subcase 2: same pattern/input set/priority different action
-----------------------------------------------------------
1. create same pattern, input set and priority but different action, check these two rules can be created::

    flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 2 / end

2. send matched pkts and check both vf1 and vf2 receive this pkt::

    sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)], iface="ens786f0", count=1)

3. destroy rules and repeat step 4, check the pkt cannot receive by any vf::

    flow flush 0

subcase 3: some rules overlap
-----------------------------
1. create rules::

    flow create 0 priority 1 ingress pattern eth / vlan / vlan / pppoes / pppoe_proto_id is 0x21 / end actions vf id 1 / end
    flow create 0 priority 1 ingress pattern eth / vlan / vlan tci is 2 / end actions vf id 1 / end
    flow create 0 priority 0 ingress pattern eth / vlan / vlan / pppoes seid is 1 / ipv4 / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:00:00:01:03:03 / vlan / vlan / end actions vf id 2 / end
    flow create 0 priority 0 ingress pattern eth dst is 00:00:00:01:03:03 / end actions vf id 3 / end
    flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / vlan tci is 2 / end actions vf id 3 / end

2. check all the rules exist in the list::

    flow list 0

3. send pkt which match rule 1, rule 3, rule 4 and rule 5, check the pkts can be received by vf 2 and 3 for high priority::

    sendp([Ether(dst="00:00:00:01:03:03")/Dot1Q(vlan=1)/Dot1Q(vlan=2)/Raw("x"*480)], iface="ens786f0", count=1)

4. destroy rule 5, repeat step 3 and check the pkts can be received by vf 2 and 3 for high priority::

    flow destroy 0 rule 5

5. destroy rule 4, repeat step 3 and check the pkts can be received by vf 2 for high priority::

    flow destroy 0 rule 4

6. destroy rule 3, repeat step 3 and check the pkts can be received by vf 1::

    flow destroy 0 rule 3

7. destroy rule 1, repeat step 3 and check the pkts can not be received::

    flow destroy 0 rule 1

8. send pkt which match rule 0 and rule 2, check the pkts can received by vf 2 for high priority::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8100)/Dot1Q(vlan=0x2,type=0x8864)/PPPoE(sessionid=0x1)/PPP(proto=0x21)/IP()/UDP(dport=23)/("X"*480)], iface="ens786f0")

9. destroy rule 2, repeat step 8 and check the pkts can be received by vf 1::

    flow destroy 0 rule 2

10. destroy rule 0, repeat step 8 and check the pkts can not be received::

     flow destroy 0 rule 0
