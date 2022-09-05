.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019-2020 Intel Corporation

=======================
ICE Switch Filter Tests
=======================

Description
===========

This document provides the plan for testing switch filter feature of Intel® Ethernet 800 Series, including:

* Enable switch filter for IPv4/IPv6 + TCP/UDP in non-pipeline/pipeline mode (comm #1 package)
* Enable switch filter for tunnel : VXLAN / NVGRE in non-pipeline/pipeline mode (comm #1 package)
* Enable "drop any" and "steering all to queue" action, any pattern packets will hit rule if these rules be created

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
   Intel® Ethernet 800 Series: E810-XXVDA4/E810-CQ
   design the cases with 2 ports card.

2. software:

   - dpdk: http://dpdk.org/git/dpdk
   - scapy: http://www.secdev.org/projects/scapy/

3. Copy comm #1 package to /lib/firmware/intel/ice/ddp/ice.pkg,
   then load driver::

     rmmod ice
     insmod ice.ko

4. Compile DPDK::

    CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

5. Bind pf to dpdk driver::

     ./usertools/dpdk-devbind.py -b vfio-pci 18:00.2

6. Launch dpdk with the following arguments in non-pipeline mode::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:00.0 --log-level="ice,7" -- -i --txq=16 --rxq=16
     testpmd> port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start

   If set VXLAN flow rule::

      testpmd> rx_vxlan_port add 4789 0

   Note: file ``testpmd_fdir_rules`` contains 15,360 fdir rules to make fdir table full.

   Launch dpdk in pipeline mode with the following testpmd command line::

      ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -a 0000:18:00.0,pipeline-mode-support=1 --log-level="ice,7" -- -i --txq=16 --rxq=16

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

   create rss rule to switch on ipfrag rss function::

     flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-frag end key_len 0 queues end / end

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

   create rss rule to switch on ipfrag rss function::

     flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-frag end key_len 0 queues end / end

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

   create rss rule to switch on ipfrag rss function::

     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext / end actions rss types ipv6-frag end key_len 0 queues end / end

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

   create rss rule to switch on ipfrag rss function::

     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext / end actions rss types ipv6-frag end key_len 0 queues end / end

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

   create rss rule to switch on ipfrag rss function::

     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext / end actions rss types ipv6-frag end key_len 0 queues end / end

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

Test steps for supported pattern
================================
1. validate rules.
2. create rules and list rules.
3. send matched packets, check the action is correct::
    queue index: to correct queue 
    rss queues: to correct queue group 
    drop: not receive pkt
4. send mismatched packets, check the action is not correct::
    queue index: not to correct queue 
    rss queues: not to correctt queue group 
    drop: receive pkt
5. destroy rule, list rules, check no rules.
6. send matched packets, check the action is not correct.

Test case: IPv4/IPv6 + TCP/UDP pipeline mode
============================================
MAC_IPV4_UDP + L4 MASK
----------------------
matched packets::
  
  sendp((Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2048,dport=1)/Raw("x"*80)),iface="ens260f0",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2303,dport=3841)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2047,dport=2)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2058,dport=3586)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 priority 0 ingress pattern eth / ipv4 / udp src is 2152 src mask 0xff00 dst is 1281 dst mask 0x00ff / end actions queue index 2 / end

MAC_IPV4_TCP + L4 MASK
----------------------
matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=2313,dport=23)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=2553,dport=23)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=2344,dport=23)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=2601,dport=23)/Raw("x"*80)],iface="ens260f0",count=1)

rss queues
.......... 
flow create 0 priority 0 ingress pattern eth / ipv4 / tcp src is 2345 src mask 0x0f0f / end actions rss queues 4 5 end / end

MAC_IPV6_UDP + L4 MASK 
----------------------
matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=10,dport=3328)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=20,dport=3343)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=3077)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=3349)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 priority 0 ingress pattern eth / ipv6 / udp dst is 3333 dst mask 0x0ff0 / end actions queue index 5 / end

MAC_IPV6_TCP + L4 MASK 
----------------------
matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=10,dport=3328)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=20,dport=3343)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=50,dport=3077)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=50,dport=3349)/Raw("x"*80)],iface="ens260f0",count=1)
   
drop
....
flow create 0 priority 0 ingress pattern eth / ipv6 / tcp dst is 3333 dst mask 0x0ff0 / end actions drop / end

Test case: VXLAN pipeline mode
==============================
MAC_IPV4_UDP_VXLAN_ETH_IPV4_UDP + L4 MASK
-----------------------------------------
matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:CA:C1:B8:F6")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=32,dport=22)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:CA:C1:B8:F6")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=16,dport=22)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:CA:C1:B8:F6")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=33,dport=22)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:CA:C1:B8:F6 / ipv4 / udp src is 32 src mask 0x0f / end actions queue index 2 / end
 
MAC_IPV4_UDP_VXLAN_ETH_IPV4_TCP + L4 MASK
-----------------------------------------
matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:CA:C1:B8:F6")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=32,dport=22)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:CA:C1:B8:F6")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=16,dport=22)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:CA:C1:B8:F6")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=33,dport=22)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 priority 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:CA:C1:B8:F6 / ipv4 / tcp src is 32 src mask 0x0f / end actions queue index 3 / end

Test case: NVGRE non-pipeline mode
==================================  
MAC_IPV4_NVGRE_ETH_IPV4_UDP + L4 MASK
-------------------------------------
matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=1536)/Raw("x"*80)], iface="ens260f0", count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=1281)/Raw("x"*80)], iface="ens260f0", count=1)

queue index
...........
flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 1280 src mask 0x00ff / end actions queue index 7 / end

MAC_IPV4_NVGRE_ETH_IPV4_TCP + L4 MASK
-------------------------------------
matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=1536)/Raw("x"*80)], iface="ens260f0", count=1)

mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=1281)/Raw("x"*80)], iface="ens260f0", count=1)

queue index
...........
flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp dst is 1280 dst mask 0x00ff  / end actions queue index 4 / end

Test case: GTPU pipeline mode
=============================
MAC_IPV4_GTPU_IPV4_UDP + L4 MASK
--------------------------------
matched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP(sport=1280)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP(sport=1535)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP(sport=1536)/Raw("x"*80)],iface="ens260f0",count=1)

rss queues
..........
flow create 0 priority 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp src is 1280 src mask 0xf00 / end actions rss queues 4 5 end / end
         
MAC_IPV4_GTPU_IPV4_TCP + L4 MASK
--------------------------------
matched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=1280)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=1535)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=1536)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 priority 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 1280 src mask 0xf00 / end actions queue index 3 / end

MAC_IPV4_GTPU_EH_IPV4_UDP + L4 MASK
-----------------------------------
matched packets::

  sendp([Ether()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(dport=224)/("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(dport=239)/("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(dport=241)/("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 priority 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / udp dst is 230 dst mask 0x0f0 / end actions queue index 7 / end

MAC_IPV4_GTPU_EH_IPV4_TCP + L4 MASK
-----------------------------------
matched packets::

  sendp([Ether()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/TCP(dport=224)/("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/TCP(dport=239)/("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.1.1")/UDP(dport=241)/("x"*80)],iface="ens260f0",count=1)

drop
....
flow create 0 priority 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.1.1 / tcp dst is 230 dst mask 0x0f0 / end actions drop / end

MAC_IPV4_GTPU_IPV6_UDP + L4 MASK
--------------------------------
matched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=1280)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=1535)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=1536)/Raw("x"*80)],iface="ens260f0",count=1)

rss queues
..........
flow create 0 priority 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 1280 src mask 0xf00 / end actions rss queues 4 5 end / end  

MAC_IPV4_GTPU_IPV6_TCP + L4 MASK
--------------------------------
matched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=1280)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=1535)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=1536)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 priority 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 1280 src mask 0xf00 / end actions queue index 7 / end  
 
MAC_IPV4_GTPU_EH_IPV6_UDP + L4 MASK
-----------------------------------
matched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=224)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=239)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::
 
  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=245)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 priority 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 230 src mask 0x0f0 / end actions queue index 5 / end  

MAC_IPV4_GTPU_EH_IPV6_TCP + L4 MASK
-----------------------------------
matched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(dport=224)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(dport=239)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(dport=245)/Raw("x"*80)],iface="ens260f0",count=1)

drop
....
flow create 0 priority 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp dst is 230 dst mask 0x0f0 / end actions drop / end 

Test case: GTPU non-pipeline mode
=================================
MAC_IPV6_GTPU_IPV4_UDP + L4 MASK
--------------------------------
matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=1280)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=1535)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=1536)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp src is 1280 src mask 0xf00 / end actions queue index 8 / end  

MAC_IPV6_GTPU_IPV4_TCP + L4 MASK
--------------------------------
matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(dport=1280)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(dport=1535)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=1536)/Raw("x"*80)],iface="ens260f0",count=1)

drop
....
flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp dst is 1280 dst mask 0xf00 / end actions drop / end  

MAC_IPV6_GTPU_EH_IPV4_UDP + L4 MASK
-----------------------------------
matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=224)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=239)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=245)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv4 / udp src is 230 src mask 0x0f0 / end actions queue index 5 / end  

MAC_IPV6_GTPU_EH_IPV4_TCP + L4 MASK
-----------------------------------
matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(dport=224)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(dport=239)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(dport=245)/Raw("x"*80)],iface="ens260f0",count=1)

drop
....
flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 230 dst mask 0x0f0 / end actions drop / end  

MAC_IPV6_GTPU_IPV6_UDP + L4 MASK
--------------------------------
matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=1280)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=1535)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=1536)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp src is 1280 src mask 0xf00 / end actions queue index 3 / end 

MAC_IPV6_GTPU_IPV6_TCP + L4 MASK
--------------------------------
matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(dport=224)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(dport=239)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(dport=245)/Raw("x"*80)],iface="ens260f0",count=1)

rss queues
..........
flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp dst is 230 dst mask 0x0f0 / end actions rss queues 2 3 end / end  

MAC_IPV6_GTPU_EH_IPV6_UDP + L4 MASK
-----------------------------------
matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=32)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=16)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=33)/Raw("x"*80)],iface="ens260f0",count=1)

drop
....
flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / udp dst is 32 dst mask 0x0f / end actions drop / end  

MAC_IPV6_GTPU_EH_IPV6_TCP + L4 MASK
-----------------------------------
matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=32)/Raw("x"*80)],iface="ens260f0",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=16)/Raw("x"*80)],iface="ens260f0",count=1)

mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTPPDUSessionContainer()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=33)/Raw("x"*80)],iface="ens260f0",count=1)

queue index
...........
flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / tcp src is 32 src mask 0x0f / end actions queue index 7 / end 

#l4 qinq switch filter

Description
===========
Intel® Ethernet 800 Series support l4 for QinQ switch filter in PF driver is by
dst MAC + outer VLAN id + inner VLAN id + dst IP + dst port, and port can support
as eth / vlan / vlan / IP / tcp|udp.
* Enable QINQ switch filter for IPv4/IPv6, IPv4 + TCP/UDP in non-pipeline mode.
* Enable QINQ switch filter for IPv6 + TCP/UDP in pipeline mode.

Test Case
=========

Common Steps
------------
All the packets in the QINQ test case use below settings:
dst mac: 00:11:22:33:44:55
dst mac change inputset: 00:11:22:33:44:66
ipv4 src: 192.168.1.1
ipv4 dst: 192.168.1.2
ipv4 src change inputset: 192.168.1.3
ipv4 dst change inputset: 192.168.1.4
ipv6 dst: CDCD:910A:2222:5498:8475:1111:3900:2020
ipv6 dst change inputset: CDCD:910A:2222:5498:8475:1111:3900:2023
outer vlan tci: 2
outer vlan tci change inputset: 1
inner vlan tci: 1
inner vlan tci change inputset: 2
sport: 50
sport change inputset: 51
dport: 23
dport change inputset: 22

#non-pipeline mode

Test Case 1: MAC_QINQ_IPV4
--------------------------
The test case enable QINQ switch filter for IPv4 in non-pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv4.

Test Steps
..........
1. Validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 2 / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 src is <ipv4 src> dst is <ipv4 dst> / end actions queue index 2 / end

   Get the message::

     Flow rule #0 created

3. Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV4 => QUEUE

4. Send matched packet in scapy on tester, check the DUT received this packet and the action is right.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*80)],iface="<tester interface>")

DUT::

    testpmd> port 0/queue 2: received 1 packets
  src=A4:BF:01:4D:6F:32 - dst=00:11:22:33:44:55 - type=0x8100 - length=122 - nb_segs=1 - RSS hash=0x26878aad - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - Receive queue=0x2
  ol_flags: RTE_MBUF_F_RX_RSS_HASH RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_GOOD

5. Send mismatched packet in scapy on tester, check the DUT received this packet and the action is not right.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci change inputset>,type=0x0800)/IP(src="<ipv4 src>",dst="<ipv4 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP(src="<ipv4 src change inputset>",dst="<ipv4 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP(src="<ipv4 src>",dst="<ipv4 dst change inputset>")/("X"*80)],iface="<tester interface>")

6. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

7. Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 4, check the action is not right.

Test Case 2: MAC_QINQ_IPV6
--------------------------
The test case enable QINQ switch filter for IPv6 in non-pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv6.

Test Steps
..........
1. Validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / end actions rss queues 2 3 end / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / end actions rss queues 2 3 end / end

   Get the message::

     Flow rule #0 created

3. Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV6 => RSS

4. Send matched packet in scapy on tester, check the DUT received this packet and the action is right.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/("X"*80)],iface="<tester interface>")

DUT::

    testpmd> port 0/queue 2: received 1 packets
  src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x8100 - length=142 - nb_segs=1 - RSS hash=0xb0c13d2c - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_NONFRAG  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV6  - l2_len=18 - inner_l2_len=4 - inner_l3_len=40 - Receive queue=0x2
  ol_flags: RTE_MBUF_F_RX_RSS_HASH RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_GOOD

5. Send mismatched packet in scapy on tester, check the DUT received this packet and the action is not right.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci change inputset>,type=0x0800)/IPv6(dst="<ipv6 dst>")/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst change inputset>")/("X"*80)],iface="<tester interface>")

6. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

7. Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 4, check the action is not right.

Test Case 3: MAC_QINQ_IPV4_UDP
------------------------------
The test case enable QINQ switch filter for IPv4 + UDP in non-pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv4 + UDP.

Test Steps
..........
1. Validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 / udp src is <sport> dst is <dport> / end actions queue index 2 / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 / udp src is <sport> dst is <dport> / end actions queue index 2 / end

   Get the message::

     Flow rule #0 created

3. Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV4 UDP => QUEUE

4. Send matched packet in scapy on tester, check the DUT received this packet and the action is right.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP()/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

DUT::

    testpmd> port 0/queue 2: received 1 packets
  src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x8100 - length=130 - nb_segs=1 - RSS hash=0xddc4fdb3 - RSS queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_UDP  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4 INNER_L4_UDP  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - inner_l4_len=8 - Receive queue=0x2
  ol_flags: RTE_MBUF_F_RX_RSS_HASH RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_GOOD

5. Send mismatched packet in scapy on tester, check the DUT received this packet and the action is not right.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP()/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP()/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci change inputset>,type=0x0800)/IP()/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP()/UDP(sport=<sport change inputset>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP()/UDP(sport=<sport>,dport=<dport change inputset>)/("X"*80)],iface="<tester interface>")

6. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

7. Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 4, check the action is not right.

Test Case 4: MAC_QINQ_IPV4_TCP
------------------------------
The test case enable QINQ switch filter for IPv4 + TCP in non-pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv4 + TCP.

Test Steps
..........
1. Validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 / tcp src is <sport> dst is <dport> / end actions rss queues 4 5 end / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv4 / tcp src is <sport> dst is <dport> / end actions rss queues 4 5 end / end

   Get the message::

     Flow rule #0 created

3. Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV4 TCP => RSS

4. Send matched packet in scapy on tester, check the DUT received this packet and the action is right.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP()/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

DUT::

    testpmd> port 0/queue 5: received 1 packets
  src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x8100 - length=142 - nb_segs=1 - RSS hash=0xddc4fdb3 - RSS queue=0x5 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_TCP  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV4 INNER_L4_TCP  - l2_len=18 - inner_l2_len=4 - inner_l3_len=20 - inner_l4_len=20 - Receive queue=0x5
  ol_flags: RTE_MBUF_F_RX_RSS_HASH RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_GOOD

5. Send mismatched packet in scapy on tester, check the DUT received this packet and the action is not right.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP()/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP()/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci change inputset>,type=0x0800)/IP()/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP()/TCP(sport=<sport change inputset>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IP()/TCP(sport=<sport>,dport=<dport change inputset>)/("X"*80)],iface="<tester interface>")

6. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

7. Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 4, check the action is not right.

#pipeline mode

Test Case 5: MAC_QINQ_IPV6_UDP
------------------------------
The test case enable QINQ switch filter for IPv6 + UDP in pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv6 + UDP.

Test Steps
..........
1. Validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / udp src is <sport> dst is <dport> / end actions drop / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / udp src is <sport> dst is <dport> / end actions drop / end

   Get the message::

     Flow rule #0 created

3. Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV6 UDP => DROP

4. Send matched packet in scapy on tester, check the DUT received this packet and the action is right.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

5. Send mismatched packet in scapy on tester, check the DUT received this packet and the action is not right.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci change inputset>,type=0x0800)/IPv6(dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst change inputset>")/UDP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/UDP(sport=<sport>,dport=<dport change inputset>)/("X"*80)],iface="<tester interface>")

6. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

7. Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 4, check the action is not right.

Test Case 6: MAC_QINQ_IPV6_TCP
------------------------------
The test case enable QINQ switch filter for IPv6 + TCP in pipeline mode, and port can support as dst MAC + outer VLAN id + inner VLAN id + IPv6 + TCP.

Test Steps
..........
1. Validate a rule::

     testpmd> flow validate 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / tcp src is <sport> dst is <dport> / end actions queue index 7 / end

   Get the message::

     Flow rule validated

2. Create a rule and list rules::

     testpmd> flow create 0 priority 0 ingress pattern eth dst is <dst mac> / vlan tci is <outer vlan tci> / vlan tci is <inner vlan tci> / ipv6 dst is <ipv6 dst> / tcp src is <sport> dst is <dport> / end actions queue index 7 / end

   Get the message::

     Flow rule #0 created

3. Check the flow list::

     testpmd> flow list 0

   ID      Group   Prio    Attr    Rule
   0       0       0       i--     ETH VLAN VLAN IPV6 TCP => QUEUE

4. Send matched packet in scapy on tester, check the DUT received this packet and the action is right.

Tester::

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

DUT::

    testpmd> port 0/queue 7: received 1 packets
  src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x8100 - length=162 - nb_segs=1 - RSS hash=0xc5dfbe3f - RSS queue=0x7 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_TCP  - sw ptype: L2_ETHER_VLAN INNER_L2_ETHER_VLAN INNER_L3_IPV6 INNER_L4_TCP  - l2_len=18 - inner_l2_len=4 - inner_l3_len=40 - inner_l4_len=20 - Receive queue=0x7
  ol_flags: RTE_MBUF_F_RX_RSS_HASH RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_GOOD

5. Send mismatched packet in scapy on tester, check the DUT received this packet and the action is not right.

Tester::

    >>> sendp([Ether(dst="<dst mac change inputset>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci change inputset>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci change inputset>,type=0x0800)/IPv6(dst="<ipv6 dst>")/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst change inputset>")/TCP(sport=<sport>,dport=<dport>)/("X"*80)],iface="<tester interface>")

    >>> sendp([Ether(dst="<dst mac>",type=0x8100)/Dot1Q(vlan=<outer vlan tci>,type=0x8100)/Dot1Q(vlan=0x<inner vlan tci>,type=0x0800)/IPv6(dst="<ipv6 dst>")/TCP(sport=<sport>,dport=<dport change inputset>)/("X"*80)],iface="<tester interface>")

6. Destroy a rule and list rules::

     testpmd> flow destroy 0 rule 0

   Get the message::

     Flow rule #0 destroyed

7. Check the flow list::

     testpmd> flow list 0

   Check the rule not exists in the list.
   Send matched packets in step 4, check the action is not right.

Pattern Any Test Case
=====================

Test case 1: check rule is programmed to switch
-----------------------------------------------

1. launch testpmd with --log-level="ice,7" create a rule::

    testpmd> flow create 0 ingress pattern any / end actions drop / end
    ice_flow_create(): Succeeded to create (2) flow
    Flow rule #0 created

2. destroy drop any rule::

    testpmd> flow destroy 0 rule 0

3. create to queue rule::

    testpmd> flow create 0 ingress pattern any / end actions queue index 4 / end
    ice_flow_create(): Succeeded to create (2) flow
    Flow rule #0 created

Test case 2: drop any rule
--------------------------
1. create a rule::

    testpmd> flow create 0 ingress pattern any / end actions drop / end
    testpmd> flow list 0

    check the rule exists in the list.

2. send matched packets::

    >>> sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw("x"*80)],iface="ens786f0",count=1)
    >>> sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0",count=1)
    >>> sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw("x"*80)],iface="ens786f0",count=1)
    >>> sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4,proto=0x06)/Raw("x"*80)],iface="ens786f0",count=1)
    >>> sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0",count=1)
    >>> sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/Raw("x"*80)],iface="ens786f0",count=1)
    >>> sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/Raw("x" *80)],iface="ens786f0",count=1)
    >>> sendp([Ether(dst="00:11:22:33:44:55", type=0x8863)/Raw("x" *80)],iface="ens786f0",count=1)
    >>> sendp([Ether(dst="00:11:22:33:44:55", type=0x8864)/PPPoE(sessionid=3)/Raw("x" *80)],iface="ens786f0",count=1)
    >>> sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP()/Raw("x"*80)],iface="ens786f0",count=1)
    >>> sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)
    >>> sendp([Ether(dst="00:11:22:33:44:55",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6()/Raw("x" * 80)],iface="ens786f0",count=1)
    >>> sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
    >>> sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=11)/Raw("x"*480)], iface="ens786f0")
    >>> sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")
    >>> sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")
    >>> sendp([Ether(dst="00:11:22:33:44:54")/IP(src="192.168.0.25",dst="192.168.0.23")/UDP(sport=23,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="ens786f0")
    >>> sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="ens786f0")
    >>> sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="ens786f0")
    >>> sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="ens786f0")

    check port 0 can't receive these packets.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets in step 2, check the packets are received by port 0.

Test case 3: any to queue rule
------------------------------
1. create a rule::

    testpmd> flow create 0 ingress pattern any / end actions queue index 4 / end
    testpmd> flow list 0

    check the rule exists in the list.

2. send matched packets, same with test case 2 step 2, check port 0 receive these packets by queue 4.

3. verify rules can be destroyed::

    testpmd> flow destroy 0 rule 0
    testpmd> flow list 0

    check the rule not exists in the list.
    send matched packets in step 2, check the packets are received by queue 0.

Test case 4: pattern any priority check
---------------------------------------

subcase 1: non-pipeline mode
............................

1. create drop any rule with priority 0, to queue rule with priority 1::

    testpmd> flow create 0 priority 0 ingress pattern any / end actions drop / end
    ice_flow_create(): Succeeded to create (2) flow
    Flow rule #0 created

    testpmd> flow create 0 priority 1 ingress pattern any / end actions queue index 4 / end
    ice_flow_create(): Succeeded to create (2) flow
    Flow rule #1 created

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ANY => DROP
    1       0       1       i--     ANY => QUEUE

2. send matched packets, same with test case 2 step 2, check all the packets are dropped.

3. destroy rule 0, send matched packets, check all the packets received by queue 4.

4. destroy rule 1, send matched packets, check all the packets received by rss.

5. change the rule priority, repeat step 2-4, check the result is same.

subcase 2: non-pipeline mode with other rule
............................................

1. create 2 rules::

    testpmd> flow create 0 priority 1 ingress pattern any / end actions drop / end
    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 1.1.1.2 dst is 1.1.1.3 tos is 4 / udp src is 23 dst is 25 / end actions queue index 2 / end

2. send packet which match 2 rules, check the packet is dropped::

    >>> sendp([Ether()/IP(src="1.1.1.2",dst="1.1.1.3",tos=4)/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0",count=1)

3. destroy rule 0, repeat step 2, check the packet is received by queue 2::

    testpmd> flow destroy 0 rule 0

4. create 2 rules::

    testpmd> flow create 0 priority 1 ingress pattern any / end actions queue index 4 / end
    testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 1.1.1.2 dst is 1.1.1.3 tos is 4 / udp src is 23 dst is 25 / end actions queue index 2 / end

5. send packet which match 2 rules, check the packet is received by queue 2::

    >>> sendp([Ether()/IP(src="1.1.1.2",dst="1.1.1.3",tos=4)/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0",count=1)

6. destroy rule 1, repeat step 5, check the packet is received by queue 4::

    testpmd> flow destroy 0 rule 1

subcase 3: pipeline mode
........................

1. launch testpmd with pipeline mode, create rule, check the rule can be created::

    testpmd> flow create 0 priority 0 ingress pattern any / end actions drop / end

2. destroy the rule::

    testpmd> flow flush 0

3. create rule, check the rule can be created::

    testpmd> flow create 0 priority 0 ingress pattern any / end actions queue index 4 / end

4. destroy the rule::

    testpmd> flow flush 0

5. create rule, check the rule can not be created::

    testpmd> flow create 0 priority 1 ingress pattern any / end actions drop / end

6. destroy the rule::

    testpmd> flow flush 0

7. create rule, check the rule can not be created::

    testpmd> flow create 0 priority 1 ingress pattern any / end actions queue index 4 / end

Test case: L3 mask
=======================

subcase 1: ipv4 dst + mask + queue action
-----------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions queue index 12 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 dst spec 224.0.0.0 dst mask 240.0.0.0 / end actions queue index 12 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp(Ether()/IP(src="192.168.0.1", dst="239.255.255.255")/UDP()/Raw("x"*80), iface="enp27s0f0", count=1),

   check all the packets received by queue 12.
   send mismatched packets::

     sendp(Ether()/IP(src="192.168.0.1", dst="223.0.0.0")/TCP()/Raw("x"*80), iface="enp27s0f0", count=1)
     sendp(Ether()/IP(src="192.168.0.1", dst="240.0.0.0")/UDP()/Raw("x"*80), iface="enp27s0f0", count=1)
     sendp(Ether()/IP(src="192.168.0.1", dst="128.0.0.0")/Raw("x"*80)], iface="enp27s0f0", count=1)

   check all the packets can't received by queue 12.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check all the packets can't received by queue 12.

subcase 2: ipv6 src + mask + drop action
----------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth / ipv6 src spec CDCD:910A:2222:5498:8475:1111:3900:2023 src mask ffff:ffff:ffff:ffff:0:0:0:0 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth / ipv6 src spec CDCD:910A:2222:5498:8475:1111:3900:2023 src mask ffff:ffff:ffff:ffff:0:0:0:0 / end actions drop / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp(Ether(dst="00:00:5e:00:00:01")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:1515", src="CDCD:910A:2222:5498:ffff:ffff:ffff:ffff")/TCP()/("X"*480), iface="enp27s0f0", count=1),

   check all the packets are dropped.
   send mismatched packets::

     sendp(Ether(dst="00:00:5e:00:00:01")/IPv6(src="CDCD:910A:2222:ffff:8475:1111:3900:2023")/("X"*480), iface="enp27s0f0", count=1)
     sendp(Ether(dst="00:00:5e:00:00:01")/IPv6(src="CFCD:910A:ffff:5498:8475:1111:3900:2023")/UDP()/("X"*480), iface="enp27s0f0", count=1)
     sendp(Ether(dst="00:00:5e:00:00:01")/IPv6(src="CDCD:ffff:2222:5498:8475:1111:3900:1515")/TCP()/("X"*480), iface="enp27s0f0", count=1)
	 sendp(Ether(dst="00:00:5e:00:00:01")/IPv6(src="ffff:910A:2222:5498:8475:1111:3900:1515")/TCP()/("X"*480), iface="enp27s0f0", count=1)

   check all the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check all the packets are not dropped.

Test case: L2 mask
=======================

subcase 1: mac dst + mask + queue action
----------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth dst spec 00:00:5e:00:00:00 dst mask ff:ff:ff:80:00:00 / end actions queue index 12 / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth dst spec 00:00:5e:00:00:00 dst mask ff:ff:ff:80:00:00 / end actions queue index 12 / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp(Ether(src="00:00:5e:00:00:01", dst="00:00:5e:7f:ff:ff")/IP()/UDP()/Raw("x"*80)), iface="enp27s0f0", count=1)

   check all the packets received by queue 12.
   send mismatched packets::

     sendp(Ether(dst="00:00:5e:80:00:00")/Raw("x"*80), iface="enp27s0f0", count=1)
     sendp(Ether(dst="00:00:ff:00:00:00")/IP()/Raw("x"*80), iface="enp27s0f0", count=1)
     sendp(Ether(dst="00:ff:5e:00:00:00")/IP()/TCP()/Raw("x"*80), iface="enp27s0f0", count=1)
     sendp(Ether(dst="ff:00:5e:00:00:00")/IP()/UDP()/Raw("x"*80), iface="enp27s0f0", count=1)

   check all the packets can't receive by queue 12.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check all the packets can't receive by queue 12.

subcase 2: mac src + mask + drop action
---------------------------------------

1. validate a rule::

     testpmd> flow validate 0 ingress pattern eth src spec 00:00:5e:00:00:00 src mask ff:ff:ff:80:00:00 / end actions drop / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule::

     testpmd> flow create 0 ingress pattern eth src spec 00:00:5e:00:00:00 src mask ff:ff:ff:80:00:00 / end actions drop / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets::

     sendp(Ether(dst="00:00:5e:00:00:01", src="00:00:5e:7f:ff:ff")/IP()/UDP()/Raw("x"*80), iface="enp27s0f0", count=1)

   check all the packets are dropped.
   send mismatched packets::

     sendp(Ether(src="00:00:5e:80:00:00")/Raw("x"*80), iface="enp27s0f0", count=1)
     sendp(Ether(src="00:00:ff:00:00:00")/IP()/Raw("x"*80), iface="enp27s0f0", count=1)
     sendp(Ether(src="00:ff:5e:00:00:00")/IP()/TCP()/Raw("x"*80), iface="enp27s0f0", count=1)
     sendp(Ether(src="ff:00:5e:00:00:00")/IP()/UDP()/Raw("x"*80), iface="enp27s0f0", count=1)

   check all the packets are not dropped.

4. verify rules can be destroyed::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send matched packets, check all the packets are not dropped.