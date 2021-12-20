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

=================================
CVL DCF Switch Filter PPPOE Tests
=================================

Description
===========

This document provides the plan for testing DCF switch filter pppoe of CVL, including:

* Enable DCF switch filter for PPPOES (comm #1 package)


Pattern and input set
---------------------

  +---------------------+-------------------------------+-------------------------------------------+
  |    Packet Types     |           Pattern             |                Input Set                  |
  +=====================+===============================+===========================================+
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

     CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static x86_64-native-linuxapp-gcc
     ninja -C x86_64-native-linuxapp-gcc
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

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:01.0,cap=dcf -a 0000:18:01.1 -- -i
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
