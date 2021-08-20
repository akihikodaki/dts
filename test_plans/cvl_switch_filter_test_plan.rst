.. Copyright (c) <2019-2020>, Intel Corporation
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

=======================
CVL Switch Filter Tests
=======================

Description
===========

This document provides the plan for testing switch filter feature of CVL, including:

* Enable switch filter for IPv4/IPv6 + TCP/UDP in non-pipeline/pipeline mode (comm #1 package)
* Enable switch filter for tunnel : VXLAN / NVGRE in non-pipeline/pipeline mode (comm #1 package)

In pipeline mode, a flow can be set at one specific stage by setting parameter ``priority``. Currently,
we support two stages: priority = 0 or !0. Flows with priority 0 located at the first pipeline stage
which typically be used as a firewall. At this stage, flow rules are created for the device's exact
match engine: switch. Flows with priority !0 located at the second stage, typically packets are
classified here and be steered to specific queue or queue group. At this stage, flow rules are created
for device's flow director engine.

In non-pipeline mode, ``priority`` is ignored, a flow rule can be created as a flow director rule or a
switch rule depends on its pattern/action. If a rule is supported by switch or fdir at the same time, it
will be created in the fdir table first. Therefore, to test switch filter in non-pipeline mode, we need to
fill the fdir table first, and then the rules are created in the switch filter table. The capacity of fdir
table is 16K, of which 14K is shared by all pfs and vfs, and the remaining 2K is gurantee for pfs. If 4*25G
NIC, the gurantee for each pf is 512. If 2*100G NIC, the gurantee of each pf is 1024. so 1 pf can create at
most 14848 rules on 4 ports card and 15360 rules on 2 ports card.

Pattern and input set
---------------------

  +---------------------+-------------------------------+---------------------------------------------------------------------------------------+
  |                     |                               |                                       Input Set                                       |
  |    Packet Types     |           Pattern             +-------------------------------------------+-------------------------------------------+
  |                     |                               |              non-pipeline mode            |              pipeline mode                |
  +=====================+===============================+===========================================+===========================================+
  |                     | MAC_IPV4_FRAG                 |  N/A         				    | [Source IP], [Dest IP],                   |
  |                     |                               |                                           | [DSCP]                                    |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_PAY                  | [Source IP], [Dest IP],[TOS],[TTL]        | [Source IP], [Dest IP],                   |
  |                     |                               |                                           | [IP protocol], [DSCP]                     |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_UDP_PAY              | [Source IP], [Dest IP],[TOS],[TTL],       | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port],[Dest Port]                 | [DSCP],                                   |
  |                     |                               |                                           | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  | IPv4/IPv6 + TCP/UDP	| MAC_IPV4_TCP                  | [Source IP], [Dest IP],[TOS],[TTL],       | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port], [Dest Port]                | [DSCP],                                   |
  |                     |                               |                                           | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV6                      | [Source IP], [Dest IP]                    | [Source IP], [Dest IP],                   |
  |                     |                               |                                           | [TC]                                      |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_UDP_PAY              | [Source IP], [Dest IP],[TOS],[TTL],       | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port],[Dest Port]                 | [TC],                                     |
  |                     |                               |                                           | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_TCP                  | [Source IP], [Dest IP],[TOS],[TTL],       | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port],[Dest Port]                 | [TC],                                     |
  |                     |                               |                                           | [Source Port], [Dest Port]                |
  +---------------------+-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_TUN_IPV4_FRAG        | [Out Dest IP], [VNI/GRE_KEY],             | [inner Source IP], [inner Dest IP],       |
  |                     |               	        | [Inner Source IP], [Inner Dest IP],       | [DSCP]                                    |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_TUN_IPV4_PAY         | [Out Dest IP], [VNI/GRE_KEY],             | [inner Source IP], [inner Dest IP],       |
  |                     |                               | [Inner Source IP], [Inner Dest IP],       | [IP protocol], [DSCP]                     |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_TUN_IPV4_UDP_PAY     | [Out Dest IP], [VNI/GRE_KEY],             | [inner Source IP], [inner Dest IP],       |
  |                     |                               | [Inner Source IP], [Inner Dest IP],       | [DSCP],                                   |
  |                     |                               | [Inner Source Port], [Inner Dest Port]    | [Inner Source Port], [Inner Dest Port]    |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_TUN_IPV4_TCP         | [Out Dest IP], [VNI/GRE_KEY],             | [Inner Source IP], [Inner Dest IP],       |
  |                     |                               | [Inner Source IP], [Inner Dest IP],       | [DSCP],                                   |
  |                     |                               | [Inner Source Port], [Inner Dest Port]    | [Inner Source Port], [Inner Dest Port]    |
  |        tunnel       +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_TUN_MAC_IPV4_FRAG    | [Out Dest IP], [VNI/GRE_KEY],             | N/A                                       |
  |                     |                               | [Inner Dest MAC],                         |                                           |
  |                     |                               | [Inner Source IP], [Inner Dest IP]        |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_TUN_MAC_IPV4_PAY     | [Out Dest IP], [VNI/GRE_KEY],             | N/A                                       |
  |                     |                               | [Inner Dest MAC],                         |                                           |
  |                     |                               | [Inner Source IP], [Inner Dest IP]        |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_TUN_MAC_IPV4_UDP_PAY	| [Out Dest IP], [VNI/GRE_KEY],             | N/A                                       |
  |                     |                               | [Inner Dest MAC],                         |                                           |
  |                     |                               | [Inner Source IP],[Inner Dest IP],        |                                           |
  |                     |                               | [Inner Source Port], [Inner Dest Port]    |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_TUN_MAC_IPV4_TCP     | [Out Dest IP], [VNI/GRE_KEY],             | N/A                                       |
  |                     |                               | [Inner Dest MAC],                         |                                           |
  |                     |                               | [Inner Source IP], [Inner Dest IP],       |                                           |
  |                     |                               | [Inner Source Port], [Inner Dest Port]    |                                           |
  +---------------------+-------------------------------+-------------------------------------------+-------------------------------------------+
  |  ethertype filter   | ethertype filter_PPPOED       | [Ether type]                              | [Ether type]                              |
  +---------------------+-------------------------------+-------------------------------------------+-------------------------------------------+

.. note::

   1. The maximum input set length of a switch rule is 32 bytes, and src ipv6,
      dst ipv6 account for 32 bytes. Therefore, for ipv6 cases, if need to test
      fields other than src, dst ip, we create rule by removing src or dst ip in
      the test plan.

   2. For MAC_IPV4_TUN_IPV4_FRAG/MAC_IPV4_TUN_IPV4_PAY cases and
      MAC_IPV4_TUN_MAC_IPV4_FRAG/MAC_IPV4_TUN_MAC_IPV4_PAY cases, the input set
      of each pair is the same, so use MAC_IPV4_TUN_IPV4 and MAC_IPV4_TUN_MAC_IPV4
      pattern to replace them in the test plan.

Supported function type
-----------------------

* validate
* create
* destroy
* flush
* list

Supported action type
---------------------

* to queue
* to queue group
* drop

Prerequisites
=============

1. Hardware:
   columbiaville_25g/columbiaville_100g
   design the cases with 2 ports card.

2. software:

   - dpdk: http://dpdk.org/git/dpdk
   - scapy: http://www.secdev.org/projects/scapy/

3. Copy comm #1 package to /lib/firmware/intel/ice/ddp/ice.pkg,
   then load driver::

     rmmod ice
     insmod ice.ko

4. Compile DPDK::

     make -j install T=x86_64-native-linuxapp-gcc

5. Bind pf to dpdk driver::

     ./usertools/dpdk-devbind.py -b vfio-pci 18:00.2

6. Launch dpdk with the following arguments in non-pipeline mode::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -w 0000:18:00.0 --log-level="ice,8" -- -i --txq=16 --rxq=16 --cmdline-file=testpmd_fdir_rules
     testpmd> port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start

   If set VXLAN flow rule::

      testpmd> rx_vxlan_port add 4789 0

   Note: file ``testpmd_fdir_rules`` contains 15,360 fdir rules to make fdir table full.

   Launch dpdk in pipeline mode with the following testpmd command line::

      ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -w 0000:18:00.0,pipeline-mode-support=1 --log-level="ice,8" -- -i --txq=16 --rxq=16

Test case: VXLAN non-pipeline mode
==================================

MAC_IPV4_VXLAN_IPV4
-------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
...............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 3 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 3 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 3.
   send mismatched packets, check the packets are not to queue 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 3.

drop action
...........

1. validate a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_VXLAN_IPV4_UDP_PAY
---------------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.5", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.7")/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
...............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 4 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 4 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4.
   send mismatched packets, check the packets are not to queue 4.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4.

to queue group action
.....................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4 or 5.
   send mismatched packets, check the packets are not to queue 4 and 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4 and 5.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_VXLAN_IPV4_TCP
-----------------------

mathced packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.5", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.7")/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=29,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=100)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions queue index 5 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions queue index 5 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 5.
   send mismatched packets, check the packets are not to queue 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 5.

drop action
...........

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_VXLAN_MAC_IPV4
-----------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

drop action
...........

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_VXLAN_MAC_IPV4_UDP_PAY
-------------------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a1")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.5", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.7")/UDP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=29)/Raw("x" * 80)],iface="enp27s0f2",count=1)

to queue action
---------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 1 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 1.
   send mismatched packets, check the packets are not to queue 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 1.

to queue group action
.....................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4 or 5.
   send mismatched packets, check the packets are not to queue 4 and 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4 and 5.

drop action
...........

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_VXLAN_MAC_IPV4_TCP
---------------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a2")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.5", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.7")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=20,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 1.
   send mismatched packets, check the packets are not to queue 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 1.

drop action
...........

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

Test case: VXLAN pipeline mode
==============================

MAC_IPV4_VXLAN_IPV4_FRAG
------------------------

matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

drop action
...........

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_VXLAN_IPV4_PAY
-----------------------

MAC_IPV4_VXLAN_IPV4_PAY proto tcp
.................................

matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=4, proto=0x06)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=4)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.5", dst="192.168.0.3", tos=4, proto=0x06)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.7", tos=4, proto=0x06)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=5, proto=0x06)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=4, proto=0x01)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.5", dst="192.168.0.3", tos=4)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.7", tos=4)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=5)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=4)/ICMP()/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 proto is 0x06 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 proto is 0x06 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rules exist in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check the packets are not to queue 2.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 proto is 0x06 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 proto is 0x06 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exist in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_VXLAN_IPV4_PAY proto udp
.................................

matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=4, proto=0x11)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=4)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.5", dst="192.168.0.3", tos=4, proto=0x11)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.7", tos=4, proto=0x11)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=5, proto=0x11)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=4, proto=0x01)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.5", dst="192.168.0.3", tos=4)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.7", tos=4)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=5)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3", tos=4)/ICMP()/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 proto is 0x11 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 proto is 0x11 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rules exist in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check the packets are not to queue 2.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 proto is 0x11 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 proto is 0x11 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rules exist in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check the packets are not to queue 2 and 3.

drop action
...........

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 proto is 0x11 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 proto is 0x11 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exist in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_VXLAN_IPV4_UDP_PAY
---------------------------

matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=20,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=99)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4 or 5.
   send mismatched packets, check the packets are not to queue 4 and 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue queue 4 and 5.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_VXLAN_IPV4_TCP
-----------------------

matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5)/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=19,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=30)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 3 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 3 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 3.
   send mismatched packets, check the packets are not to queue 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 3.

drop action
...........

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

Test case: NVGRE non-pipeline mode
==================================

MAC_IPV4_NVGRE_IPV4
-------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 3.
   send mismatched packets, check the packets are not to queue 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 3.

drop action
...........

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_NVGRE_IPV4_UDP_PAY
---------------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x1)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.5", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.7")/UDP(sport=50,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw("x"*80)], iface="enp27s0f2", count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 4 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 4 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4.
   send mismatched packets, check the packets are not to queue 4.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4 or 5.
   send mismatched packets, check the packets are not to queue 4 and 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4 and 5.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_NVGRE_IPV4_TCP
-----------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.5", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=20,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=39)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 1.
   send mismatched packets, check the packets are not to queue 1.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 1.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_NVGRE_MAC_IPV4
-----------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5")/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 3.
   send mismatched packets, check the packets are not to queue 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 3.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_NVGRE_MAC_IPV4_UDP_PAY
-------------------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x1)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.5", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw("x"*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw("x"*80)], iface="enp27s0f2", count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2 and 3.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_NVGRE_MAC_IPV4_TCP
---------------------------

matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a3")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.5", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions queue index 3 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions queue index 3 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 3.
   send mismatched packets, check the packets are not to queue 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 3.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

Test case: NVGRE pipeline mode
==============================

MAC_IPV4_NVGRE_IPV4_FRAG
------------------------

matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.5", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.7",tos=4,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 3 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 3 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 3.
   send mismatched packets, check the packets are not to queue 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 3.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_NVGRE_IPV4_PAY
-----------------------

MAC_IPV4_NVGRE_IPV4_PAY proto tcp
.................................

matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.5",dst="192.168.0.3",proto=0x06,tos=4)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.7",proto=0x06,tos=4)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x01,tos=4)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP()/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_NVGRE_IPV4_PAY proto udp
.................................

matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.5",dst="192.168.0.3",proto=0x11,tos=4)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.7",proto=0x11,tos=4)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x01,tos=4)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP()/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2 and 3.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_NVGRE_IPV4_UDP_PAY
---------------------------

matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=100)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_NVGRE_IPV4_TCP
-----------------------

matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4)/TCP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5)/TCP(sport=50,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=3,dport=23)/Raw("x" * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=100)/Raw("x" * 80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

Test case: IPv4/IPv6 + TCP/UDP pipeline mode
============================================

MAC_IPV4_FRAG
-------------

matched packets::

  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=7,frag=5)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 3 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 3 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 3.
   send mismatched packets, check the packets are not to queue 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 3.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2 and 3.

drop action
............

1. validate a rule::

    testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_PAY
------------

MAC_IPV4_PAY proto tcp
......................

matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4,proto=0x06)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.4",dst="192.168.0.3",tos=4,proto=0x06)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.5",tos=4,proto=0x06)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=7,proto=0x06)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4,proto=0x01)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.4",dst="192.168.0.3",tos=4)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.5",tos=4)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=7)/TCP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP()/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions queue index 5 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions queue index 5 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 5.
   send mismatched packets, check the packets are not to queue 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 5.

to queue group action
......................

1. validate a rule::

     testpmd> flow validateg 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions rss queues 4 5 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4 or 5.
   send mismatched packets, check the packets are not to queue 4 and 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4 and 5.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_PAY proto udp
......................

matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4,proto=0x11)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4,proto=0x11)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4,proto=0x11)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5,proto=0x11)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4,proto=0x01)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5)/UDP()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP()/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2 and 3.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_UDP_PAY
----------------

matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=3)/Raw("x"*80)],iface="enp27s0f2",count=1)


to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4 or 5.
   send mismatched packets, check the packets are not to queue 4 and 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4 and 5.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_TCP
------------

matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.5",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.7",tos=4)/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=5)/TCP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=5,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=7)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 3 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 3 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 3.
   send mismatched packets, check the packets are not to queue 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 3.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4 or 5.
   send mismatched packets, check the packets are not to queue 4 and 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4 and 5.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV6
--------

MAC_IPV6 src ipv6 + dst ipv6
.................................

matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1514",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1514",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 5 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 5 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 5.
   send mismatched packets, check the packets are not to queue 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 5.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2 and 3.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV6 dst ipv6 + tc
...........................

matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2027",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions queue index 3 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions queue index 3 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 3.
   send mismatched packets, check the packets are not to queue 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 3.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2 and 3.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV6_UDP_PAY
----------------

matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=5)/UDP(sport=50,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=3,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=4)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions queue index 5 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions queue index 5 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 5.
   send mismatched packets, check the packets are not to queue 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 5.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2 and 3.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV6_TCP
------------

matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=7)/TCP(sport=25,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=1,dport=23)/Raw("x"*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw("x"*80)],iface="enp27s0f2",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions queue index 4 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions queue index 4 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4.
   send mismatched packets, check the packets are not to queue 4.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4 or 5.
   send mismatched packets, check the packets are not to queue 4 and 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4 and 5.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

Test case: IPv4/IPv6 + TCP/UDP non-pipeline mode
================================================

MAC_IPV4_PAY
------------

matched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/("X"*480)], iface="enp27s0f2", count=100)

mismatched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a1")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.3",dst="192.168.0.2",tos=4,ttl=2)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.7",tos=4,ttl=2)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=2)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=9)/("X"*480)], iface="enp27s0f2", count=100)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions queue index 4 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions queue index 4 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 4.
   send mismatched packets, check the packets are not to queue 4.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_UDP_PAY
----------------

matched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)

mismatched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a1")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.3",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.5",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=5,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=9)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=19,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=99)/("X"*480)], iface="enp27s0f2", count=100)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV4_TCP_PAY
----------------

matched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.32",tos=4)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)

mismatched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a1")/IP(src="192.168.0.1",dst="192.168.0.32",tos=4)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.3",dst="192.168.0.32",tos=4)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.39",tos=4)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.32",tos=5)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.32",tos=4)/TCP(sport=19,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.32",tos=4)/TCP(sport=25,dport=99)/("X"*480)], iface="enp27s0f2", count=100)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.32 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.32 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.32 tos is 4 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.32 tos is 4 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV6_PAY
------------

matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f2", count=100)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f2", count=100)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 8 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 8 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 8.
   send mismatched packets, check the packets are not to queue 8.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 8.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV6_UDP
------------

matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=19,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=25,dport=99)/("X"*480)], iface="enp27s0f2", count=100)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 25 dst is 23 / end actions queue index 6 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 25 dst is 23 / end actions queue index 6 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 6.
   send mismatched packets, check the packets are not to queue 6.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 6.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 25 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

MAC_IPV6_TCP
------------

matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=19,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=25,dport=99)/("X"*480)], iface="enp27s0f2", count=100)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 25 dst is 23 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 25 dst is 23 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

Test case: Ethertype filter
===========================

Ethertype filter_PPPOED
-----------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55", type=0x8863)/Raw("x" *80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/Raw("x" *80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55", type=0x8864)/Raw("x" *80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/Raw("x" *80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth type is 0x8863 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth type is 0x8863 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

5. check the pattern in pipeline mode

   The rules in pipeline mode are similar to rules in non-pipeline mode,
   just need to add priority 0 to show it is created as a switch filter rule.

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth type is 0x8863 / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth type is 0x8863 / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth type is 0x8863 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth type is 0x8863 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to dropped.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth type is 0x8863 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth type is 0x8863 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Test case: unsupported patterns in os default package
=====================================================

1. load os default package and launch testpmd in pipeline mode as step 3-6 in Prerequisites.

2. create unsupported patterns in os default package::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 1 / end
     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end
     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / end
     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions rss queues 2 3 end / end
     testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 / udp / esp spi is 8 / end actions rss queues 2 3 end / end
     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 / ah spi is 1 / end actions queue index 1 / end

   Failed to create flow, report message::

     Invalid input pattern: Invalid argument

3. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.
