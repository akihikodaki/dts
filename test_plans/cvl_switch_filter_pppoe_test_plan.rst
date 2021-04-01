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

* Enable switch filter for PPPOE in non-pipeline/pipeline mode (comm #1 package)

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
  |  ethertype filter   | ethertype filter_PPPOES       | [Ether type]                              | [Ether type]                              |
  +---------------------+-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV4_PAY       | [Dest MAC], [VLAN], [seid],               | [Dest MAC], [VLAN], [seid],               |
  |                     | _session_id_proto_id          | [pppoe_proto_id]                          | [pppoe_proto_id]                          |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                	| MAC_VLAN_PPPOE_IPV6_PAY       | [Dest MAC], [VLAN], [seid],               | [Dest MAC], [VLAN], [seid],               |
  |                     | _session_id_proto_id          | [pppoe_proto_id]                          | [pppoe_proto_id]                          |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV4_PAY_session_id | [Dest MAC], [seid], [pppoe_proto_id]      | [Dest MAC], [seid], [pppoe_proto_id]      |
  |                     | _proto_id                     |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV6_PAY_session_id | [Dest MAC], [seid], [pppoe_proto_id]      | [Dest MAC], [seid], [pppoe_proto_id]      |
  |                     | _proto_id                     |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV4_PAY_IP_address | [Source IP], [Dest IP]                    | [Source IP], [Dest IP]                    |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV4_UDP_PAY        | [Source IP], [Dest IP],                   | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port], [Dest Port]                | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV4_UDP_PAY        | [Source IP], [Dest IP]                    | [Source IP], [Dest IP]                    |
  |                     | _non_src_dst_port             |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV4_TCP_PAY        | [Source IP], [Dest IP],                   | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port], [Dest Port]                | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV4_TCP_PAY        | [Source IP], [Dest IP]                    | [Source IP], [Dest IP]                    |
  |                     | _non_src_dst_port             |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV6_PAY_IP_address | [Source IP], [Dest IP]                    | [Source IP], [Dest IP]                    |
  |      PPPOES         +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV6_UDP_PAY        | [Source IP], [Dest IP],                   | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port], [Dest Port]                | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV6_UDP_PAY        | [Source IP], [Dest IP]                    | [Source IP], [Dest IP]                    |
  |                     | _non_src_dst_port             |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV6_TCP_PAY        | [Source IP], [Dest IP],                   | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port], [Dest Port]                | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV6_TCP_PAY        | [Source IP], [Dest IP],                   | [Source IP], [Dest IP],                   |
  |                     | _non_src_dst_port             |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV4_PAY       | [VLAN], [Source IP], [Dest IP]            | [VLAN], [Source IP], [Dest IP]            |
  |                     | _IP_address                   |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV4_UDP_PAY   | [VLAN], [Source IP], [Dest IP]            | [VLAN], [Source IP], [Dest IP]            |
  |                     |                               | [Source Port], [Dest Port]                | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV4_UDP_PAY   | [VLAN], [Source IP], [Dest IP]            | [VLAN], [Source IP], [Dest IP]            |
  |                     | _non_src_dst_port             |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV4_TCP_PAY   | [VLAN], [Source IP], [Dest IP]            | [VLAN], [Source IP], [Dest IP]            |
  |                     |                               | [Source Port], [Dest Port]                | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV4_TCP_PAY   | [VLAN], [Source IP], [Dest IP]            | [VLAN], [Source IP], [Dest IP]            |
  |                     | _non_src_dst_port             |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV6_PAY       | [VLAN], [Source IP], [Dest IP]            | [VLAN], [Source IP], [Dest IP]            |
  |                     | _IP_address                   |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV6_UDP_PAY   | [VLAN], [Source IP], [Dest IP]            | [VLAN], [Source IP], [Dest IP]            |
  |                     |                               | [Source Port], [Dest Port]                | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV6_UDP_PAY   | [VLAN], [Source IP], [Dest IP]            | [VLAN], [Source IP], [Dest IP]            |
  |                     | _non_src_dst_port             |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV6_TCP_PAY   | [VLAN], [Source IP], [Dest IP]            | [VLAN], [Source IP], [Dest IP]            |
  |                     |                               | [Source Port], [Dest Port]                | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPV6_TCP_PAY   | [VLAN], [Source IP], [Dest IP]            | [VLAN], [Source IP], [Dest IP]            |
  |                     | _non_src_dst_port             |                                           |                                           |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_LCP_PAY             | [Dest MAC], [seid], [pppoe_proto_id]      | [Dest MAC], [seid], [pppoe_proto_id]      |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPCP_PAY            | [Dest MAC], [seid], [pppoe_proto_id]      | [Dest MAC], [seid], [pppoe_proto_id]      |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_LCP_PAY        | [Dest MAC], [VLAN], [seid],               | [Dest MAC], [VLAN], [seid],               |
  |                     |                               | [pppoe_proto_id]                          | [pppoe_proto_id]                          |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_VLAN_PPPOE_IPCP_PAY       | [Dest MAC], [VLAN], [seid],               | [Dest MAC], [VLAN], [seid],               |
  |                     |                               | [pppoe_proto_id]                          | [pppoe_proto_id]                          |
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

Test case: Ethertype filter
===========================

Ethertype filter_PPPOES
-----------------------

create PPPOE rule to enable RSS for PPPOE packets::

  testpmd> flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55", type=0x8864)/PPPoE(sessionid=3)/Raw("x" *80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55", type=0x8863)/PPPoED()/Raw("x" *80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth type is 0x8864 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth type is 0x8864 / end actions queue index 2 / end

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

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth type is 0x8864 / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth type is 0x8864 / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth type is 0x8864 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth type is 0x8864 / end actions rss queues 4 5 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth type is 0x8864 / end actions rss queues 4 5 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth type is 0x8864 / end actions rss queues 4 5 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth type is 0x8864 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth type is 0x8864 / end actions drop / end

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

     testpmd> flow validate 0 priority 0 ingress pattern eth type is 0x8864 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth type is 0x8864 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Test case: MAC_VLAN_PPPOE_IPV4_PAY_session_id_proto_id
======================================================

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x"*80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
---------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end

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

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
---------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
-----------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Test case: MAC_VLAN_PPPOE_IPV6_PAY_session_id_proto_id
======================================================

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
---------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end

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

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
----------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
-----------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Test case: MAC_PPPOE_IPV4_PAY_session_id_proto_id
=================================================

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
---------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end

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

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
---------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions rss queues 4 5 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0021 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Test case: MAC_PPPOE_IPV6_PAY_session_id_proto_id
=================================================

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:54",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
---------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packet are distributed to queue 2.
   send mismatched packets, check the packets are not to queue 2.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
---------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packet to queue 4 or 5.
   send mismatched packets, check the packet not to queue 4 and 5.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 4 and 5.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions rss queues 4 5 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
-----------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packet is dropped.
   send mismatched packets, check the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not dropped.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x0057 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Test case: PPPoE data
=====================

Subcase 1: MAC_PPPOE_IPV4_PAY_IP_address
----------------------------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end

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

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 2: MAC_PPPOE_IPV4_UDP_PAY
---------------------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 7 or 8.
   send mismatched packets, check the packets are not to queue 7 and 8.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 7 and 8.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 3: MAC_PPPOE_IPV4_UDP_PAY_non_src_dst_port
--------------------------------------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end

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

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 2 3 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 4: MAC_PPPOE_IPV4_TCP_PAY
---------------------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 7 or 8.
   send mismatched packets, check the packets are not to queue 7 and 8.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 7 and 8.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 5: MAC_PPPOE_IPV4_TCP_PAY_non_src_dst_port
--------------------------------------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end

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

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 7 or 8.
   send mismatched packets, check the packets are not to queue 7 and 8.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 7 and 8.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 6: MAC_PPPOE_IPV6_PAY_IP_address
----------------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions rss queues 2 3 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 7: MAC_PPPOE_IPV6_UDP_PAY
---------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 8: MAC_PPPOE_IPV6_UDP_PAY_non_src_dst_port
--------------------------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions rss queues 2 3 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 9: MAC_PPPOE_IPV6_TCP_PAY
---------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 10: MAC_PPPOE_IPV6_TCP_PAY_non_src_dst_port
---------------------------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions rss queues 2 3 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 11: MAC_VLAN_PPPOE_IPV4_PAY_IP_address
----------------------------------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/Raw("x"*80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end

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

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 12: MAC_VLAN_PPPOE_IPV4_UDP_PAY
---------------------------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end

   create a rule::

     flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 7 or 8.
   send mismatched packets, check the packets are not to queue 7 and 8.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 7 and 8.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp src is 25 dst is 23 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 13: MAC_VLAN_PPPOE_IPV4_UDP_PAY_non_src_dst_port
--------------------------------------------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end

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

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 7 8 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 7 8 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 7 or 8.
   send mismatched packets, check the packets are not to queue 7 and 8.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 7 and 8.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 7 8 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions rss queues 7 8 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / udp / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 14: MAC_VLAN_PPPOE_IPV4_TCP_PAY
---------------------------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 7 or 8.
   send mismatched packets, check the packets are not to queue 7 and 8.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 7 and 8.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions rss queues 7 8 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp src is 25 dst is 23 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 15: MAC_VLAN_PPPOE_IPV4_TCP_PAY_non_src_dst_port
--------------------------------------------------------

matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end

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

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions queue index 2 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 7 or 8.
   send mismatched packets, check the packets are not to queue 7 and 8.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 7 and 8.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions rss queues 7 8 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / tcp / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 16: MAC_VLAN_PPPOE_IPV6_PAY_IP_address
----------------------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions rss queues 2 3 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 17: MAC_VLAN_PPPOE_IPV6_UDP_PAY
---------------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 18: MAC_VLAN_PPPOE_IPV6_UDP_PAY_non_src_dst_port
--------------------------------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions rss queues 2 3 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / udp / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 19: MAC_VLAN_PPPOE_IPV6_TCP_PAY
---------------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 25 dst is 23 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 20: MAC_VLAN_PPPOE_IPV6_TCP_PAY_non_src_dst_port
--------------------------------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions rss queues 2 3 end / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / vlan tci is 1 / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 / tcp / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Test case: PPPoE Control
========================

create a PPPOE rule to enable RSS for PPPOE_control packets::

  testpmd> flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end

Subcase 1: MAC_PPPOE_LCP_PAY
----------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow destroy 0 rule 15361
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2 and 3.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 2: MAC_PPPOE_IPCP_PAY
-----------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow destroy 0 rule 15361
     testpmd> flow list 0

   check the rules not exists in the list.
   send matched packets, check the packets are not to queue 2 and 3.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 3: MAC_VLAN_PPPOE_LCP_PAY
---------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow destroy 0 rule 15361
     testpmd> flow list 0

   check the rules not exist in the list.
   send matched packets, check the packets are not to queue 2 and 3.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0xc021 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Subcase 4: MAC_VLAN_PPPOE_IPCP_PAY
----------------------------------

matched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

mismatched packets::

  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=4)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
  sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x" * 80)],iface="ens786f0",count=1)

to queue action
................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions queue index 1 / end

   repeat step 1-4 to check the pattern in pipeline mode.

to queue group action
......................

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end

   get the message::

     Succeeded to create (2) flow

   check the flow list::

     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets, check the packets are to queue 2 or 3.
   send mismatched packets, check the packets are not to queue 2 and 3.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow destroy 0 rule 15361
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 2 and 3.

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions rss queues 2 3 end / end

   repeat step 1-4 to check the pattern in pipeline mode.

drop action
............

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end

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

5. check the pattern in pipeline mode

   validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end

   create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes seid is 3 / pppoe_proto_id is 0x8021 / end actions drop / end

   repeat step 1-4 to check the pattern in pipeline mode.

Test case: negative cases
=========================
Note: some of the error messages may be differernt.

Subcase 1: invalid parameters of queue index
--------------------------------------------

1. create a rule with invalid queue index::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 16 / end

   Failed to create flow, report message::

     Invalid action type or queue number: Invalid argument

2. check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 2: invalid parameters of rss queues
-------------------------------------------

1. Invalid number of queues::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end
     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 end / end
     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues end / end

   Failed to create flow, report messag::

     Invalid action type or queue number: Invalid argument

2. Discontinuous queues::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end

   Failed to create flow, report message::

     Discontinuous queue region: Invalid argument

3. Invalid queue index::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 15 16 end / end

   Failed to create flow, report message::

     Invalid queue region indexes: Invalid argument

4. set queue group 17 queues::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 end / end

   Failed to create flow, report message::

     Invalid action type or queue number: Invalid argument

5. check the flow list::

     testpmd> flow list 0

   check the rules not exist in the list.

Subcase 4: unsupported input set
--------------------------------

1. create an nvgre rule with unsupported input set field [inner tos]::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 tos is 4 / end actions queue index 1 / end

2. Failed to create flow, report message::

     Invalid input set: Invalid argument

3. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 5: duplicated rules
---------------------------

1. create a rule::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

2. create the same rule again, Failed to create flow, report message::

     switch filter create flow fail: Invalid argument

3. check the flow list::

     testpmd> flow list 0

   check only the first rule exists in the list.

Subcase 6: conflicted rules
---------------------------

1. create a rule::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end
    testpmd> flow list 0

   check the rule exists in the list.

2. create a rule with same input set but different actions::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 2 / end
    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions drop / end

   Failed to create the two rules, report message::

    switch filter create flow fail: Invalid argument

3. check the flow list::

     testpmd> flow list 0

   check only the first rule exists in the list.

Subcase 7: multiple actions
---------------------------

1. create a rule with two conflicted actions::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / rss queues 2 3 end / end

   Failed to create flow, report message::

     Invalid input action number: Invalid argument

2. check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 8: void action
----------------------

1. create a rule with void action::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp src is 25 dst is 23 / end actions end

   Failed to create flow, report message::

     NULL action.: Invalid argument

2. check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 9: unsupported action
-----------------------------

1. create a rule with void action::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions mark id 1 / end

   Failed to create flow, report message::

     Invalid action type: Invalid argument

2. check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 10: delete a non-existing rule
--------------------------------------

1. check the rule list::

     testpmd> flow list 0

   check no switch filter rule exists in the list.

2. destroy the rule 20000::

     testpmd> flow destroy 0 rule 20000

   check no error reports.

Subcase 11: add long switch rule
--------------------------------

Description: A recipe has 5 words, one of which is reserved for switch ID,
so a recipe can use 4 words, and a maximum of 5 recipes can be chained,
one of which is reserved. Therefore, a rule can use up to 4*4*2 = 32 bytes.
This case is used to test that a rule whose input set is longer than 32
bytes can not be created successfully, and will not affect the creation of
other rules.

1. create a rule with input set length longer than 32 bytes::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end

   Failed to create flow, report message::

     Invalid input set: Invalid argument

2. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

3. create a MAC_PPPOE_IPV6_UDP_PAY rule with to queue action::

     testpmd> flow create 0 priority 0 ingress pattern eth / pppoes / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send matched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check queue 1 receive the packet.
   send mismatched packets::

     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=27,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="11:22:33:44:55:99",dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=19)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the packets are not to queue 1.

5. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 15360
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check the packets are not to queue 1.

Subcase 12: void input set value
--------------------------------

1. create a IPV4_PAY rule with void input set value::

     testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / end actions queue index 1 / end

   Failed to create flow, report message::

     Invalid input set: Invalid argument

2. check the rule list::

     testpmd> flow list 0

   check the rule not exists in the list.

Subcase 13: invalid port
------------------------

1. create a rule with invalid port::

     testpmd> flow create 1 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end

   Failed to create flow, report message::

     No such device: No such device

2. check the rule list on port 0::

     testpmd> flow list 0

   check the rule not exists in the list.
   check on port 1::

     testpmd> flow list 1

   get the message::

     Invalid port 1

Test case: negative validation
==============================
Note: some of the error messages may be different.

1. invalid parameters of queue index

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 16 / end

   get the error message::

     Invalid action type or queue number: Invalid argument

2. invalid parameters of rss queues

   Invalid number of queues::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end
     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 end / end
     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues end / end

   get the error message::

     Invalid action type or queue number: Invalid argument

   Discontinuous queues::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end

   get the error message::

     Discontinuous queue region: Invalid argument

   Invalid rss queues index::

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 15 16 end / end

   get the error message::

     Invalid queue region indexes: Invalid argument

4. unsupported input set

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 tos is 4 / end actions queue index 1 / end

   get the error message::

     Invalid input set: Invalid argument

5. multiple actions

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / rss queues 2 3 end / end

   get the error message::

     Invalid input action number: Invalid argument

6. void action

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / udp src is 25 dst is 23 / end actions end

   get the error message::

     NULL action.: Invalid argument

7. unsupported action

     testpmd> flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions mark id 1 / end

   get the error message::

     Invalid action type: Invalid argument

8. long switch rule

     testpmd> flow validate 0 priority 0 ingress pattern eth / pppoes / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 25 dst is 23 / end actions queue index 1 / end

   get the error message::

     Invalid input set: Invalid argument

9. void input set value

     testpmd> flow validate 0 priority 0 ingress pattern eth / ipv4 / end actions queue index 1 / end

   get the error message::

     Invalid input set: Invalid argument

10. invalid port

      testpmd> flow validate 1 priority 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end

    get the error message::

      No such device: No such device

11. check the rule list::

      testpmd> flow list 0

    no rule exists in the list.
