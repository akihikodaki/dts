.. Copyright (c) <2020>, Intel Corporation
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

===========================
CVL DCF Switch Filter Tests
===========================

Description
===========

This document provides the plan for testing DCF switch filter of CVL, including:

* Enable DCF switch filter for IPv4/IPv6 + TCP/UDP/IGMP (comm #1 package)
* Enable DCF switch filter for tunnel: NVGRE (comm #1 package)
* Enable DCF switch filter for PPPOES (comm #1 package)
* Enable DCF switch filter for PFCP/L2TPv3/AH/ESP/NAT-T-ESP (comm #1 package)
* Enable DCF switch filter for IP/L2 multicast (comm #1 package)
* Enable DCF switch filter for ethertype/UDP port/MAC VLAN/VLAN filter (comm #1 package)


Pattern and input set
---------------------

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
  |    IPv4/IPv6 + 	| MAC_IPV4_TCP_PAY              | [Dest MAC], [Source IP], [Dest IP],       |
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
  |                     |               	        | [Inner Source IP], [Inner Dest IP]        |
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
  |                     | MAC_IPV4_TUN_MAC_IPV4_UDP_PAY	| [Out Dest IP], [VNI/GRE_KEY],             |
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

.. note::

   1. The maximum input set length of a switch rule is 32 bytes, and src ipv6,
      dst ipv6 account for 32 bytes. Therefore, for ipv6 cases, if need to test
      fields other than src, dst ip, we create rule by removing src or dst ip in
      the test plan.

Supported function type
-----------------------

* create
* validate
* destroy
* flush
* list


Supported action type
---------------------

* To vf/vsi


Prerequisites
=============

1. Hardware:
   columbiaville_25g/columbiaville_100g
   design the cases with 2 ports card.

2. Software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/updates/intel/ice/ddp/ice.pkg,
   then load driver::

     rmmod ice
     insmod ice.ko

4. Compile DPDK::

     make -j install T=x86_64-native-linuxapp-gcc

5. Get the pci device id of DUT, for example::

     ./usertools/dpdk-devbind.py -s

     0000:18:00.0 'Device 1593' if=enp24s0f0 drv=ice unused=vfio-pci
     0000:18:00.1 'Device 1593' if=enp24s0f1 drv=ice unused=vfio-pci

6. Generate 4 VFs on PF0::

     echo 4 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

     ./usertools/dpdk-devbind.py -s
     0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' if=enp24s1 drv=iavf unused=vfio-pci
     0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f1 drv=iavf unused=vfio-pci
     0000:18:01.2 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f2 drv=iavf unused=vfio-pci
     0000:18:01.3 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f3 drv=iavf unused=vfio-pci

7. Set VF0 as trust::

     ip link set enp24s0f0 vf 0 trust on

8. Bind VFs to dpdk driver::

     modprobe vfio-pci
     ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1 0000:18:01.2 0000:18:01.3

9. Launch dpdk on VF0 and VF1, and VF0 request DCF mode::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -w 0000:18:01.0,cap=dcf -w 0000:18:01.1 -- -i
     testpmd> set portlist 1
     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start
     testpmd> show port info all

   check the VF0 driver is net_ice_dcf.

10. on tester side, copy the layer python file to /root::

      cp pfcp.py to /root

    then import layers when start scapy::

      >>> import sys
      >>> sys.path.append('/root')
      >>> from pfcp import PFCP
      >>> from scapy.contrib.igmp import *


Test case: MAC_PAY
==================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth src is 00:00:00:00:00:01 dst is 00:11:22:33:44:55 type is 0x0800 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth src is 00:00:00:00:00:01 dst is 00:11:22:33:44:55 type is 0x0800 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="00:00:00:00:00:01",dst="00:11:22:33:44:55")/IP()/Raw("x" *80)],iface="enp27s0f0",count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(src="00:00:00:00:00:02",dst="00:11:22:33:44:55")/IP()/Raw("x" *80)],iface="enp27s0f0",count=1)
     sendp([Ether(src="00:00:00:00:00:01",dst="00:11:22:33:44:54")/IP()/Raw("x" *80)],iface="enp27s0f0",count=1)
     sendp([Ether(src="00:00:00:00:00:01",dst="00:11:22:33:44:55")/IPv6()/Raw("x" *80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_FRAG
========================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2,frag=5)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2,frag=5)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4",dst="192.168.0.2",tos=4,ttl=2,frag=5)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.5",tos=4,ttl=2,frag=5)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=2,frag=5)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3,frag=5)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_PAY
=======================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 6 tos is 4 ttl is 2 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 proto is 6 tos is 4 ttl is 2 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4",dst="192.168.0.2",tos=4,ttl=2)/TCP()/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.5",tos=4,ttl=2)/TCP()/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=2)/TCP()/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP()/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/UDP()/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_UDP_PAY
===========================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.5",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.7",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=9)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=30,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=19)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_TCP_PAY
===========================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.5",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.7",tos=4,ttl=3)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=3)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=9)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=30,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/TCP(sport=25,dport=19)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_IGMP
========================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 proto is 0x02 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 proto is 0x02 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IP()/IGMP()/Raw("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IP()/TCP()/Raw("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/Raw("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV6_srcip_dstip
===============================

Description: The maximum input set length of a switch rule is 32 bytes.
Therefore, if a rule carries src ipv6, dst ipv6, it can not take any other fields.

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV6_dstip_tc
============================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV6_UDP_PAY
===========================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0",count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0",count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0",count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=7)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0",count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=30,dport=23)/("X"*480)], iface="enp27s0f0",count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=19)/("X"*480)], iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV6_TCP
=======================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a3")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=7)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=30,dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=19)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_VXLAN_IPV4_FRAG (not support in 20.05)
==========================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_VXLAN_IPV4_PAY (not support in 20.05)
=========================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_VXLAN_IPV4_UDP_PAY (not support in 20.05)
=============================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23) /Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23) /Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19) /Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_VXLAN_IPV4_TCP (not support in 20.05)
=========================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=29,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=100)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_VXLAN_MAC_IPV4_FRAG (not support in 20.05)
==============================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3" ,frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5" ,frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_VXLAN_MAC_IPV4_PAY (not support in 20.05)
=============================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3") /TCP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5") /TCP()/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_VXLAN_MAC_IPV4_UDP_PAY (not support in 20.05)
=================================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=29)/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_VXLAN_MAC_IPV4_TCP (not support in 20.05)
=============================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=20,dport=23)/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_NVGRE_IPV4_PAY
===================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_NVGRE_IPV4_UDP_PAY
======================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.5", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.7")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_NVGRE_IPV4_TCP
==================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.5", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=20,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=39)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_NVGRE_MAC_IPV4_PAY
======================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_NVGRE_MAC_IPV4_UDP_PAY
==========================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a2")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw("x"*80)], iface="enp27s0f0", count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw("x"*80)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_NVGRE_MAC_IPV4_TCP
======================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a2")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.5", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw("x"*80)],iface="enp27s0f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_VLAN_PPPOE_IPV4_PAY_session_id_proto_id
======================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_VLAN_PPPOE_IPV6_PAY_session_id_proto_id
======================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_PPPOE_IPV4_PAY_session_id_proto_id
=================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_PPPOE_IPV6_PAY_session_id_proto_id
=================================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: PPPoE data
=====================

Subcase 1: MAC_PPPOE_IPV4_PAY_IP_address
----------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 2: MAC_PPPOE_IPV4_UDP_PAY
---------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 3: MAC_PPPOE_IPV4_UDP_PAY_non_src_dst_port
--------------------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 4: MAC_PPPOE_IPV4_TCP_PAY
---------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 5: MAC_PPPOE_IPV4_TCP_PAY_non_src_dst_port
--------------------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 6: MAC_PPPOE_IPV6_PAY_IP_address
----------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 7: MAC_PPPOE_IPV6_UDP_PAY
---------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 8: MAC_PPPOE_IPV6_UDP_PAY_non_src_dst_port
--------------------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 9: MAC_PPPOE_IPV6_TCP_PAY
---------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 10: MAC_PPPOE_IPV6_TCP_PAY_non_src_dst_port
---------------------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 11: MAC_VLAN_PPPOE_IPV4_PAY_IP_address
----------------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 12: MAC_VLAN_PPPOE_IPV4_UDP_PAY
---------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 13: MAC_VLAN_PPPOE_IPV4_UDP_PAY_non_src_dst_port
--------------------------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 14: MAC_VLAN_PPPOE_IPV4_TCP_PAY
---------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 15: MAC_VLAN_PPPOE_IPV4_TCP_PAY_non_src_dst_port
--------------------------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 16: MAC_VLAN_PPPOE_IPV6_PAY_IP_address
----------------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 17: MAC_VLAN_PPPOE_IPV6_UDP_PAY
---------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 18: MAC_VLAN_PPPOE_IPV6_UDP_PAY_non_src_dst_port
--------------------------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 19: MAC_VLAN_PPPOE_IPV6_TCP_PAY
---------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 20: MAC_VLAN_PPPOE_IPV6_TCP_PAY_non_src_dst_port
--------------------------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: PPPoE control
========================

Subcase 1: MAC_PPPOE_LCP_PAY
----------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 2: MAC_PPPOE_IPCP_PAY
-----------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 3: MAC_VLAN_PPPOE_LCP_PAY
---------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 4: MAC_VLAN_PPPOE_IPCP_PAY
----------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_PFCP_NODE
=============================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. DUT create switch filter rules for MAC_IPV4_PFCP_NODE to VF1::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end

   check the rule exists in the list.

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP PFCP => VF

3. send matched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")

   check port 1 receive the packet.
   send mismatched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_PFCP_SESSION
================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. DUT create switch filter rules for MAC_IPV4_PFCP_SESSION to VF2::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 2 / end

   check the rule exists in the list.

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP PFCP => VF

3. send matched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")

   check port 2 receive the packet.
   send mismatched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")

   check the packets are not to port 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 2.

Test case: MAC_IPV6_PFCP_NODE
=============================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions vf id 3 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. DUT create switch filter rules for MAC_IPV6_PFCP_NODE to VF3::

    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions vf id 3 / end

   check the rule exists in the list.

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV6 UDP PFCP => VF

3. send matched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")

   check port 3 receive the packet.
   send mismatched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")

   check the packets are not to port 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 3.

Test case: MAC_IPV6_PFCP_SESSION
================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. DUT create switch filter rules for MAC_IPV6_PFCP_SESSION to VF1::

    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions vf id 1 / end

   check the rule exists in the list.

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV6 UDP PFCP => VF

3. send matched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")

   check port 1 receive the packet.
   send mismatched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: IP multicast
=======================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="239.0.0.0")/TCP()/Raw("x"*80)], iface="enp27s0f0", count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="128.0.0.0")/TCP()/Raw("x"*80)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: L2 multicast
=======================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst spec 01:00:5e:00:00:00 dst mask ff:ff:ff:80:00:00 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst spec 01:00:5e:00:00:00 dst mask ff:ff:ff:80:00:00 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="01:00:5e:7f:00:00")/IP()/TCP()/Raw("x"*80)], iface="enp27s0f0", count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="01:00:5e:ff:00:00")/IP()/TCP()/Raw("x"*80)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: ethertype filter_PPPOD
=================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth type is 0x8863 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth type is 0x8863 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x" *80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x" *80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: ethertype filter_PPPOE
=================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth type is 0x8864 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth type is 0x8864 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: ethertype filter_IPV6
=================================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth type is 0x86dd / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth type is 0x86dd / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", tc=3)/TCP(dport=23)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", tc=3)/TCP(dport=23)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IP()/TCP(dport=23)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: UDP port filter_DHCP discovery
=========================================

Description: The udp port used by DHCP server is 67, and 68 by DHCP client.
Therefore, for DHCP discovery packets, the udp srcport is 68 and the dstport is 67.

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp src is 68 dst is 67 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 68 dst is 67 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=68,dport=67)/BOOTP(chaddr="3c:fd:fe:b2:43:90")/DHCP(options=[("message-type","discover"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=63,dport=67)/BOOTP(chaddr="3c:fd:fe:b2:43:90")/DHCP(options=[("message-type","discover"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=68,dport=69)/BOOTP(chaddr="3c:fd:fe:b2:43:90")/DHCP(options=[("message-type","discover"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: UDP port filter_DHCP offer
=====================================

Description: For DHCP offer packets, the udp srcport is 67 and the dstport is 68.

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp src is 67 dst is 68 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 67 dst is 68 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=67,dport=68)/BOOTP(chaddr="3c:fd:fe:b2:43:90",yiaddr="192.168.1.0")/DHCP(options=[("message-type","offer"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=63,dport=68)/BOOTP(chaddr="3c:fd:fe:b2:43:90",yiaddr="192.168.1.0")/DHCP(options=[("message-type","offer"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=67,dport=63)/BOOTP(chaddr="3c:fd:fe:b2:43:90",yiaddr="192.168.1.0")/DHCP(options=[("message-type","offer"),"end"])/Raw("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: UDP port filter_VXLAN
================================

Description: The UDP dst port number used by VXLAN is 4789.

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp dst is 4789 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp dst is 4789 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw("x"*80)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_VLAN filter
==========================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)],iface="enp27s0f0",count=1)
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: VLAN filter
======================

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)],iface="enp27s0f0",count=1)

   check port 1 receive the packets.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*480)],iface="enp27s0f0",count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_L2TPv3
==========================

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst='00:11:22:33:44:12')/IP(src='192.168.0.2', proto=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst='00:11:22:33:44:12')/IP(src='192.168.0.2', proto=115)/L2TP('\x00\x00\x00\x02')/('X'*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst='00:11:22:33:44:12')/IP(src='192.168.1.2', proto=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst='00:11:22:33:44:12')/IP(dst='192.168.0.2', proto=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV6_L2TPv3
==========================

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / l2tpv3oip session_id is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / l2tpv3oip session_id is 1 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst='00:11:22:33:44:13')/IPv6(dst='1111:2222:3333:4444:5555:6666:7777:8888', nh=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst='00:11:22:33:44:13')/IPv6(dst='1111:2222:3333:4444:5555:6666:7777:8888', nh=115)/L2TP('\x00\x00\x00\x02')/('X'*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst='00:11:22:33:44:13')/IPv6(dst='1111:2222:3333:4444:5555:6666:7777:9999', nh=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst='00:11:22:33:44:13')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888', nh=115)/L2TP('\x00\x00\x00\x01')/('X'*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_ESP
=======================

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=50)/ESP(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.1.2", proto=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IP(dst="192.168.0.2", proto=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV6_ESP
=======================

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / esp spi is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / esp spi is 1 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=50)/ESP(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999", nh=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", nh=50)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_AH
======================

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=51)/AH(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.1.2", proto=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IP(dst="192.168.0.2", proto=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV6_AH
======================

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / ah spi is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / ah spi is 1 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888", nh=51)/AH(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999", nh=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888", nh=51)/AH(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV4_NAT-T-ESP
=============================

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / udp / esp spi is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / udp / esp spi is 1 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2")/UDP(dport=4500)/ESP(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.1.2")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IP(dst="192.168.0.2")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: MAC_IPV6_NAT-T-ESP
=============================

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / udp / esp spi is 1 / end actions vf id 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is 1111:2222:3333:4444:5555:6666:7777:8888 / udp / esp spi is 1 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=2)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(dst="1111:2222:3333:4444:5555:6666:7777:9999")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=1)/("X"*480)], iface="enp27s0f0", count=1)

   check the packets are not to port 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test Case: multirules test
==========================

Subcase 1: add existing rules but with different vfs
----------------------------------------------------

1. Launch dpdk on VF0, VF1 and VF2, and VF0 request DCF mode::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -w 0000:18:01.0,cap=dcf -w 0000:18:01.1 -w 0000:18:01.2 -- -i
     testpmd> set portlist 1,2
     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start

2. create rules with same pattern items but to different vfs::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 2 / end
     testpmd> flow list 0

   check both rules exist in the list.

3. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)

   check both port 1 and 2 receive the packet.

4. destroy the rule 0, and send the matched packets::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check only rule 1 exists in the list.
   send the same matched packets, check only port 2 receives the packets.

5. destroy rule 1, send the matched packets::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check no rule exists in the list
   send the same matched packets, check the packets are not to port 1 and 2.

Subcase 2: add existing rules with the same vfs
-----------------------------------------------

1. create two indentical rules::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end

2. check the first rule is created successfully, and
   the second one can not be created successfully,
   and testpmd provide a friendly output, showing::

     ice_flow_create(): Failed to create flow
     port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): switch filter create flow fail: Invalid argument

3. check the rule list::

     testpmd> flow list 0

   check only the first rule exists in the list.

Subcase 3: add two rules with one rule's input set included in the other
-------------------------------------------------------------------------

1. Launch dpdk on VF0, VF1 and VF2, and VF0 request DCF mode::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -w 0000:18:01.0,cap=dcf -w 0000:18:01.1 -w 0000:18:01.2 -- -i
     testpmd> set portlist 1,2
     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start

2. create rules with one rule's input set included in the other::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 2 / end
     testpmd> flow list 0

   check both rules exist in the list.

3. send a packet p0 that matches both rules::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="ens786f0", count=1)

   check both port 1 and 2 receive the packet.
   send a packet that only matches the rule 0 but not rule 1::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.3")/("X"*480)], iface="ens786f0", count=1)

   check only port 1 receives the packet.

4. destroy the rule 0, and send the packet p0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check only rule 1 exists in the list.
   send the matched packet p0, check only port 2 receives the packet.

5. destroy rule 1, send the packet p0::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check no rule exists in the list.
   send the matched packet p0, check the packet are not to port 1 and 2.

Subcase 4: different input set, same vf id
------------------------------------------

1. DUT create switch filter rules for MAC_IPV4_PFCP_SESSION and MAC_IPV4_PFCP_NODE to VF1::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end
    Flow rule #0 created
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 1 / end
    Flow rule #1 created

   check the rule exists in the list.

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP PFCP => VF
    1       0       0       i--     ETH IPV4 UDP PFCP => VF

2. send matched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")

   check port 1 receive the two packets.
   send mismatched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")

   check the packets are not to port 1.

3. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Subcase 5: different input set, different vf id
-----------------------------------------------

1. DUT create switch filter rules for MAC_IPV4_PFCP_SESSION and MAC_IPV4_PFCP_NODE to VF1::

    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end
    Flow rule #0 created
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions vf id 2 / end
    Flow rule #1 created

   check the rule exists in the list.

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP PFCP => VF
    1       0       0       i--     ETH IPV4 UDP PFCP => VF

2. send matched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")

   check port 1 receive the first packet, port 2 receive the second packet.
   send mismatched packets::

    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:11")/IPv6()/UDP(dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")

   check the packets are not to port 1 or port 2.

3. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1 or port 2.

Test case: test forwarding with single vf
=========================================

Description: This case is used to test the packets that match switch filter rules can be
received and forwarded when there is one vf for forwarding, and no packets are dropped.

1. set the forwarding mode to mac::

     testpmd> set fwd mac

2. create a rule with input set [Source IP], [Dest IP]::

     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list

3. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="ens786f0", count=1)

4. check port 1 receives the packet and forward it, and no packets are dropped::

     testpmd> stop
     ---------------------- Forward statistics for port 1  ----------------------
     RX-packets: 1              RX-dropped: 0             RX-total: 1
     TX-packets: 1              TX-dropped: 0             TX-total: 1
     ----------------------------------------------------------------------------

     +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
     RX-packets: 1              RX-dropped: 0             RX-total: 1
     TX-packets: 1              TX-dropped: 0             TX-total: 1
     ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

   check the RX-packets and TX-packets of port 1 are both 1, and the TX-dropped in
   "Accumulated forward statistics for all ports" is 0.

Test case: test forwarding with multi vfs
=========================================

Description: This case is used to test the packets that match switch filter rules
can be received and forwarded when there are multi vfs for forwarding, and no packets
are dropped.

1. Launch dpdk on VF0, VF1 and VF2, and VF0 request DCF mode::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -w 0000:18:01.0,cap=dcf -w 0000:18:01.1 -w 0000:18:01.2 -- -i
     testpmd> set portlist 1,2
     testpmd> set fwd mac
     testpmd> set verbose 1
     testpmd> start

2. create a rule with input set [Source IP], [Dest IP]::

     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list

3. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="ens786f0", count=1)

4. check port 1 receives the packet, and forward it to port 2, and no packets are dropped::

     testpmd> stop
     ---------------------- Forward statistics for port 1  ----------------------
     RX-packets: 1         RX-dropped: 0             RX-total: 1
     TX-packets: 0         TX-dropped: 0             TX-total: 0
     ----------------------------------------------------------------------------

     ---------------------- Forward statistics for port 2  ----------------------
     RX-packets: 0              RX-dropped: 0             RX-total: 0
     TX-packets: 1              TX-dropped: 0             TX-total: 1
     ----------------------------------------------------------------------------

     +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
     RX-packets: 1              RX-dropped: 0             RX-total: 1
     TX-packets: 1              TX-dropped: 0             TX-total: 1
     ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


   check the RX-packets of port 1 is 1, the TX-packets of port 2 is 1, and the TX-dropped in
   "Accumulated forward statistics for all ports" is 0.

Test case: Max vfs
==================

Description: 256 VFs can be created on a CVL NIC, if 2*100G NIC, each PF
can create 128 VFs, else if 4*25G NIC, each PF can create 64 VFs. This
case is used to test when all VFs on a PF are used, switch filter rules can work.
This case is designed based on 4*25G NIC.

1. generate 64 VFs on PF::

     echo 64 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs

2. Get the interface name of the VFs, for example::

     ./usertools/dpdk-devbind.py -s

     0000:18:01.1 'Ethernet Adaptive Virtual Function 1889' if=enp24s1f1 drv=iavf unused=igb_uio

3. Start the 64 VFs in the kernel, for example::

     ifconfig enp24s1f1 up

4. Set VF0 as trust::

     ip link set enp24s0f0 vf 0 trust on

5. bind VF0 to dpdk driver::

     ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0

6. launch dpdk on VF0, and request DCF mode::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -w 0000:18:01.0,cap=dcf -- -i

7. set a switch rule to each VF from DCF, totally 63 rules::

     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / tcp / end actions vf id 2 / end
     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 / tcp / end actions vf id 3 / end
     ......
     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.63 / tcp / end actions vf id 63 / end
     testpmd> flow list 0

   check the rules exist in the list.

8. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1")/TCP()/Raw("X"*480)], iface="ens786f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2")/TCP()/Raw("X"*480)], iface="ens786f0", count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.3")/TCP()/Raw("X"*480)], iface="ens786f0", count=1)
     ......
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.63")/TCP()/Raw("X"*480)], iface="ens786f0", count=1)

   check the VF 1-63 each receives a packet in kernel, for example::

     ifconfig
     enp24s1f1: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
             inet6 fe80::fc5e:4aff:fe55:824b  prefixlen 64  scopeid 0x20<link>
             ether fe:5e:4a:55:82:4b  txqueuelen 1000  (Ethernet)
             RX packets 1  bytes 538 (538.0 B)
             RX errors 0  dropped 0  overruns 0  frame 0
             TX packets 7  bytes 490 (490.0 B)
             TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

     the "RX packets" number is 1.

   send mismatched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.64")/TCP()/Raw("X"*480)], iface="ens786f0", count=1)

   check the packets are not to any VF.

9. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check the packets are not to any VF.

Test case: max field vectors
============================

Description: 48 field vectors can be used on a CVL nic. This case is used
to test when field vectors are run out of, then creating a rule, testpmd
will not hang and provide a friendly output.

1. create the following nvgre rules::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.2 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.3 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rules exist in the list.

2. the three rules have run out of field vectors, and
   continue to create the following rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.10 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a1  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions vf id 1 / end

   check the rule can not be created successfully, and testpmd
   provide a friendly output, showing::

     ice_flow_create(): Failed to create flow
     port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): switch filter create flow fail: Invalid argument

3. check the rule list::

     testpmd> flow list 0

   check the rule in step 2 not exists in the list.

4. send 3 matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)
     sendp([Ether()/IP(dst="192.168.0.3")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)

   check port 1 receives the packets
   send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.5")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)],iface="ens786f0",count=1)

   check the packets are not to port 1.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check the packets are not to port 1.

Test case: negative cases
=========================

Subcase 1: can not create rule on vf 1
--------------------------------------

1. create rule on vf 1::

     testpmd> flow create 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end

   Failed to create flow, report message::

     Failed to create parser engine.: Invalid argument

2. check the flow list::

     testpmd> flow list 1

   there is no rule listed.

Subcase 2: unsupported pattern in os default package
----------------------------------------------------

1. load os default package and launch testpmd as step 3-8 in Prerequisites.

2. create unsupported pattern in os default package::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions vf id 1 / end
     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / udp / esp spi is 1 / end actions vf id 1 / end

   Failed to create flow, report message::

     Invalid input pattern: Invalid argument

3. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 3: unsupported input set
--------------------------------

1. create an nvgre rule with unsupported input set field [inner tos]::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 tos is 4 / end actions vf id 1 / end

   Failed to create flow, report message::

     Invalid input set: Invalid argument

2. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 4: duplicated rules
---------------------------

1. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

2. create the same rule again, Failed to create flow, report message::

     switch filter create flow fail: Invalid argument

3. check the flow list::

     testpmd> flow list 0

   check only the first rule exists in the list.

Subcase 5: void action
----------------------

1. create a rule with void action::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp src is 25 dst is 23 / end actions end

   Failed to create flow, report message::

     NULL action.: Invalid argument

2. check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 6: unsupported action
-----------------------------

1. create a rule with void action::

     testpmd> flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions mark id 1 / end

   Failed to create flow, report message::

     Invalid action type: Invalid argument

2. check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 7: void input set value
-------------------------------

1. create a rule with void input set value::

     testpmd> flow create 0 ingress pattern eth / ipv4 / end actions vf id 1 / end

   Failed to create flow, report message::

     Invalid input set: Invalid argument

2. check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 8: invalid vf id
------------------------

1. create a rule with invalid vf id 5::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 5 / end

   Failed to create flow, report message::

     Invalid vf id: Invalid argument

2. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 9: delete a non-existing rule
-------------------------------------

1. check the rule list::

     testpmd> flow list 0

   check no rule exists in the list.

2. destroy the rule 0::

     testpmd> flow destroy 0 rule 0

   check no error reports.

3. flush rules::

     testpmd> flow flush 0

   check no error reports.

Subcase 10: add long switch rule
--------------------------------

Description: A recipe has 5 words, one of which is reserved for switch ID,
so a recipe can use 4 words, and a maximum of 5 recipes can be chained,
one of which is reserved. Therefore, a rule can use up to 4*4*2 = 32 bytes.
This case is used to test that a rule whose input set is longer than 32
bytes can not be created successfully, and will not affect the creation of
other rules.

1. create a rule with input set length longer than 32 bytes::

     testpmd> flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 tc is 3 / end actions vf id 1 / end

   Failed to create flow, report message::

     Invalid input set: Invalid argument

2. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

3. create a MAC_IPV6_UDP_PAY rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0",count=1)

   check port 1 receive the packet.
   send mismatched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=30,dport=23)/("X"*480)], iface="ens786f0",count=1)
     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=19)/("X"*480)], iface="ens786f0",count=1)

   check the packets are not to port 1.

5. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to port 1.

Test case: negative validation
==============================
Note: some of the error messages may be different.

Subcase 1: can not create rule on vf 1
--------------------------------------

1. validate rule on vf 1::

     testpmd> flow validate 1 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end

   get the error message::

     Failed to create parser engine.: Invalid argument

2. list the rule::

     testpmd> flow list 1

   there is no rule listed.

Subcase 2: unsupported patterns in os default
---------------------------------------------

1. load os default package and launch testpmd as step 3-8 in Prerequisites.

2. validate unsupported patterns in os default::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions vf id 1 / end
     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions vf id 1 / end
     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions vf id 1 / end
     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions vf id 1 / end
     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions vf id 1 / end
     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / udp / esp spi is 1 / end actions vf id 1 / end

   get the error message::

     Invalid input pattern: Invalid argument

4. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 3: unsupported input set
--------------------------------

1. validate an nvgre rule with unsupported input set field [inner tos]::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 tos is 4 / end actions vf id 1 / end

   get the error message::

     Invalid input set: Invalid argument

2. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 4: void action
----------------------

1. validate a rule with void action::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp src is 25 dst is 23 / end actions end

   Failed to create flow, report message::

     NULL action.: Invalid argument

2. check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 5: unsupported action
-----------------------------

1. validate a rule with void action::

     testpmd> flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions mark id 1 / end

   Failed to create flow, report message::

     Invalid action type: Invalid argument

2. check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 6: void input set value
-------------------------------

1. validate a rule with void input set value::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / end actions vf id 1 / end

   get the error message::

     Invalid input set: Invalid argument

2. check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 7: invalid vf id
------------------------

1. validate a rule with invalid vf id 5::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / tcp src is 25 dst is 23 / end actions vf id 5 / end

   get the error message::

     Invalid vf id: Invalid argument

3. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 8: long switch rule
---------------------------

1. validate a rule with input set length longer than 32 bytes::

     testpmd> flow validate 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 tc is 3 / end actions vf id 1 / end

   get the error message::

     Invalid input set: Invalid argument

2. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

Test case: Stress test
======================

Subcase 1: DCF stop/DCF start
-----------------------------

1. create MAC_IPV4_UDP_PAY rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions vf id 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send matched packets::

     sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="ens786f0", count=1)

   check port 1 receive the packet.

3. stop the DCF, then start the DCF::

     tetspmd> port stop 0
     testpmd> port start 0

4. check the rule list::

     testpmd> flow list 0

   check the rule is still there.

5. send matched packets, port 1 can still receive the packets.

Test case: Drop action test
======================

Subcase 1: DCF DROP IPV4 SRC PACKAGES
-----------------------------

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create MAC_IPV4_SRC_ADDR rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions drop / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(src="192.168.0.1")/Raw("x"*80)],iface="enp27s0f0")

   check port can't receive the packet.

4. send mismatched packets::

     sendp([Ether()/IP(src="192.168.0.2")/Raw("x"*80)],iface="enp27s0f0")

   check port can receive the packet.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check port can receive the packet.

Subcase 2: DCF DROP IPV4 SRC SPEC MASK PACKAGES
-----------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create MAC_IPV4_SRC_SPEC_PAY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions drop / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(dst="239.0.0.0")/TCP()/Raw("x"*80)],iface="enp27s0f0")

   check port can't receive the packet.

4. send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(dst="128.0.0.0")/TCP()/Raw("x"*80)],iface="enp27s0f0")

   check port can receive the packet.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check port can receive the packet.
 
Subcase 3: DCF DROP NVGRE PACKAGES
-----------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create MAC_IPV4_NVGRE_PAY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0")

   check port can't receive the packet.

4. send mismatched packets::

     sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=1)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0")

   check port can receive the packet.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check port can receive the packet.

Subcase 4: DCF DROP PPOES PACKAGES
-----------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create MAC_IPV4_PPOES_PAY rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b'\\x00\\x21')/IP()/Raw("x" * 80)],iface="enp27s0f0")

   check port can't receive the packet.

4. send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=2)/PPP(b'\\x00\\x21')/IP()/Raw("x" * 80)],iface="enp27s0f0")

   check port can receive the packet.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check port can receive the packet.
 
Subcase 5:  DCF DROP PFCP PACKAGES
-----------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create MAC_IPV4_PFCP rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions drop / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=0),iface="enp27s0f0")

   check port can't receive the packet.

4. send mismatched packets::

     sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=1),iface="enp27s0f0")

   check port can receive the packet.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check port can receive the packet.

Subcase 6:  DCF DROP VLAN PACKAGES
-----------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create MAC_VLAN rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions drop / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*80)],iface="enp27s0f0")

   check port can't receive the packet.

4. send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*80)],iface="enp27s0f0")

   check port can receive the packet.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check port can receive the packet.

Subcase 7:  DCF DROP L2TP PACKAGES
-----------------------------

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create MAC_IPV4_L2TP_PAY rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / l2tpv3oip session_id is 1 / end actions drop / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst='00:11:22:33:44:12')/IP(src='192.168.0.2', proto=115)/L2TP(b'\\x00\\x00\\x00\\x01')/('X'*480)], iface="enp27s0f0", count=1)

   check port can't receive the packet.

4. send mismatched packets::

     sendp([Ether(dst='00:11:22:33:44:12')/IP(src='192.168.0.2', proto=115)/L2TP(b'\\x00\\x00\\x00\\x02')/('X'*480)], iface="enp27s0f0", count=1)

   check port can receive the packet.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check port can receive the packet.

Subcase 8:  DCF DROP ESP PACKAGES
-----------------------------

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create MAC_IPV4_ESP_PAY rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / esp spi is 1 / end actions drop / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=50)/ESP(spi=1)/("X"*80)], iface="enp27s0f0")

   check port can't receive the packet.

4. send mismatched packets::

     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.2", proto=50)/ESP(spi=2)/("X"*80)], iface="enp27s0f0")

   check port can receive the packet.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check port can receive the packet.

Subcase 8:  DCF DROP blend PACKAGES
-----------------------------

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions drop / end
     testpmd> flow validate 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions drop / end
     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end
     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end
     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions drop / end
     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions drop / end
     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.4 / l2tpv3oip session_id is 1 / end actions drop / end
     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.5 / esp spi is 1 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions drop / end
     testpmd> flow create 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions drop / end
     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end
     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end
     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions drop / end
     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / end actions drop / end
     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.4 / l2tpv3oip session_id is 1 / end actions drop / end
     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.5 / esp spi is 1 / end actions drop / end

   check the rule exists in the list.

3. send matched packets::

     sendp([Ether()/IP(src="192.168.0.1")/Raw("x"*80)],iface="enp27s0f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(dst="239.0.0.0")/TCP()/Raw("x"*80)],iface="enp27s0f0")
     sendp([Ether()/IP(dst="192.168.0.3")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0")
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(b'\\x00\\x21')/IP()/Raw("x" * 80)],iface="enp27s0f0")
     sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=0),iface="enp27s0f0")
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*80)],iface="enp27s0f0")
     sendp([Ether(dst='00:11:22:33:44:12')/IP(src='192.168.0.4', proto=115)/L2TP(b'\\x00\\x00\\x00\\x01')/('X'*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.5", proto=50)/ESP(spi=1)/("X"*80)], iface="enp27s0f0")

   check port can't receive the packet.

4. send mismatched packets::

     sendp([Ether()/IP(src="192.168.0.6")/Raw("x"*80)],iface="enp27s0f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(dst="128.0.0.0")/TCP()/Raw("x"*80)],iface="enp27s0f0")
     sendp([Ether()/IP(dst="192.168.0.8")/NVGRE(TNI=1)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f0")
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=2)/PPP(b'\\x00\\x21')/IP()/Raw("x" * 80)],iface="enp27s0f0")
     sendp(Ether(dst="00:11:22:33:44:11")/IP()/UDP(dport=8805)/PFCP(S=1),iface="enp27s0f0")
     sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2)/IP(src="192.168.0.9",dst="192.168.0.2",tos=4,ttl=2)/TCP()/Raw("X"*80)],iface="enp27s0f0")
     sendp([Ether(dst='00:11:22:33:44:12')/IP(src='192.168.0.10', proto=115)/L2TP(b'\\x00\\x00\\x00\\x02')/('X'*480)], iface="enp27s0f0", count=1)
     sendp([Ether(dst="00:11:22:33:44:13")/IP(src="192.168.0.11", proto=50)/ESP(spi=2)/("X"*80)], iface="enp27s0f0")

   check port can receive the packet.

5. verify rules can be destroyed::

     testpmd> flow flush 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check port can receive the packet.
