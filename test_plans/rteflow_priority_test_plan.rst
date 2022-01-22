.. Copyright (c) <2019>, Intel Corporation
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
Rte_flow Priority Tests
=======================


Description
===========

This document provides the plan for testing the Rte_flow Priority feature.
this feature uses devargs as a hint to active flow priority or not.

This test plan is based on Intel E810 series ethernet cards.
when priority is not active, flows are created on fdir then switch/ACL.
when priority is active, flows are identified into 2 category: 
High priority as permission stage that maps to switch/ACL,
Low priority as distribution stage that maps to fdir,
a no destination high priority rule is not acceptable, since it may be overwritten by a low priority rule due to cvl FXP behavior.

Note: Since these tests are focus on priority, the patterns in tests are examples.


Prerequisites
=============

Bind the pf to dpdk driver::

   ./usertools/dpdk-devbind.py -b vfio-pci af:00.0
   
Note: The kernel must be >= 3.6+ and VT-d must be enabled in bios.

Test Case: Setting Priority in Non-pipeline Mode
================================================

Priority is not active in non-pipeline mode. The default value of priority is 0 but it will be ignored.

Patterns in this case:
    MAC_IPV4

#. Start the ``testpmd`` application as follows::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:af:00.0 --log-level="ice,7" -- -i --txq=8 --rxq=8
    set fwd rxonly
    set verbose 1

#. Create a rule with priority 0, Check the flow can be created but it will map to fdir filter::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / mark / end
    ice_interrupt_handler(): OICR: MDD event
    ice_flow_create(): Succeeded to create (1) flow
    Flow rule #0 created

#. Create a rule with priority 1, check the flow can not be created for the vallue of priority is 0 in non-pipeline mode::

    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / mark / end
    ice_flow_create(): Failed to create flow
    Caught error type 4 (priority field): cause: 0x7ffe24e65738, Not support priority.: Invalid argument

#. Start the ``testpmd`` application as follows::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:af:00.0,pipeline-mode-support=0 --log-level="ice,7" -- -i --txq=8 --rxq=8
    set fwd rxonly
    set verbose 1

#. Create a rule with priority 0, Check the flow can be created but it will map to fdir filter::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / end
    ice_interrupt_handler(): OICR: MDD event
    ice_flow_create(): Succeeded to create (1) flow
    Flow rule #0 created

#. Create a rule with priority 1, check the flow can not be created for the vallue of priority is 0 in non-pipeline mode::

    testpmd> flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / end
    ice_flow_create(): Failed to create flow
    Caught error type 4 (priority field): cause: 0x7ffe24e65738, Not support priority.: Invalid argument

Test Case: Create Flow Rules with Priority in Pipeline Mode
============================================================

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

Test case: Create No Destination High Priority Flow Rule
========================================================

A no destination high priority rule is not acceptable. Destination here means exact actions.

Patterns in this case:
   MAC_IPV4_TCP

#. Start the ``testpmd`` application as follows::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:af:00.0,pipeline-mode-support=1 --log-level="ice,7" -- -i --txq=8 --rxq=8
    set fwd rxonly
    set verbose 1

#. Create a rule without exact actions, check the flows can not be created::

    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions / end
    Bad arguments
    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end
    Bad arguments

Test case: Create Flow Rules Only Supported by Fdir Filter with Priority 0
===========================================================================

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


Test case: Create flow rules only supported by switch filter with priority 1
=============================================================================

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

Test case: Create flow rules with same parameter but differenet actions 
==========================================================================

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
