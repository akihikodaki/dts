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
CVL Switch Filter Tests
=======================

Description
===========

This document provides the plan for testing switch filter feature of CVL, including:

* Enable switch filter for IPv4/IPv6 + TCP/UDP in non-pipeline/pipeline mode (comm #1 package)
* Enable switch filter for tunnel : VXLAN / NVGRE in non-pipeline/pipeline mode (comm #1 package)
* Enable switch filter for PPPOE in non-pipeline mode (comm #1 package)

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
table is 16K, so we create 16K fdir rules to make the fdir table full.

Pattern and input set
---------------------

  +---------------------+-------------------------------+---------------------------------------------------------------------------------------+
  |                     |                               |                                       Input Set                                       |
  |    Packet Types     |           Pattern             +-------------------------------------------+-------------------------------------------+
  |                     |                               |              non-pipeline mode            |              pipeline mode                |
  +=====================+===============================+===========================================+===========================================+
  |                     | MAC_IPV4_FRAG                 |  N/A         				                | [Source IP], [Dest IP],       |
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
  |                     |                               | [Source Port],[Dest Port]                 | [DSCP],                                   |
  |                     |                               |                                           | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_FRAG                 | [Source IP], [Dest IP]                    | [Source IP], [Dest IP],                   |
  |                     |                               |                                           | [TC]                                      |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_UDP_PAY              | [Source IP], [Dest IP],[TOS],[TTL],       | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port],[Dest Port]                 | [Source IP], [Dest IP],                   |
  |                     |                               |                                           | [TC],                                     |
  |                     |                               |                                           | [Source Port], [Dest Port]                |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV6_TCP                  | [Source IP], [Dest IP],[TOS],[TTL],       | [Source IP], [Dest IP],                   |
  |                     |                               | [Source Port],[Dest Port]                 | [Source IP], [Dest IP],                   |
  |                     |                               |                                           | [TC],                                     |
  |                     |                               |                                           | [Source Port], [Dest Port]                |
  +---------------------+-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_TUN_IPV4_FRAG        | [Out Dest IP], [VNI/GRE_KEY],             | [inner Source IP], [inner Dest IP],       |
  |                     |               	        | [Inner Source IP], [Inner Dest IP],       | [DSCP]                                    |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_IPV4_TUN_IPV4_PAY         | [Out Dest IP], [VNI/GRE_KEY],             | N/A                                       |
  |                     |                               | [Inner Source IP], [Inner Dest IP],       |                                           |
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
  |                     | MAC_PPPOD_PAY                 | all this kind of packets                  | N/A                                       |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |   PPPOD / PPPOE   	| MAC_PPPOE_PAY                 | all this kind of packets                  | N/A                                       |
  |                     +-------------------------------+-------------------------------------------+-------------------------------------------+
  |                     | MAC_PPPOE_IPV4_PAY            | [Dest MAC], [VLAN]                        | N/A                                       |
  +---------------------+-------------------------------+-------------------------------------------+-------------------------------------------+

Action type
-----------

* To queue
* To queue group
* Drop

Prerequisites
=============

1. Hardware:

   - columbiaville_25g/columbiaville_100g

2. software:

   - dpdk: http://dpdk.org/git/dpdk
   - scapy: http://www.secdev.org/projects/scapy/

3. Copy comm #1 package to /lib/firmware/intel/ice/ddp/ice.pkg,
   then reboot server, and compile DPDK.

4. Bind the pf to dpdk driver::

     ./usertools/dpdk-devbind.py -b igb_uio 18:00.2

5. Launch the app ``testpmd`` with the following arguments::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -w 0000:18:00.2 --log-level="ice,8" -- -i --txq=8 --rxq=8
     testpmd> port config 0 rss-hash-key ipv4 1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd
     testpmd> set fwd rxonly
     testpmd> set verbose 1

   If set VXLAN flow rule::

      testpmd> rx_vxlan_port add 4789 0
      testpmd> start

   If create rules in pipeline mode, please add the following parameters in testpmd command line::

      -w 0000:18:00.2,pipeline-mode-support=1


Test case: VXLAN non-pipeline mode
==================================

1. create fdir rules to make the fdir table full,
   which can be created as follows::

     flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 5 / end

2. create switch filter rules and verify

MAC_IPV4_VXLAN_IPV4_FRAG
------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV4_PAY
-----------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV4_UDP_PAY
---------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 4 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23) /Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23) /Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19) /Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23) /Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23) /Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19) /Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23) /Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23) /Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19) /Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV4_TCP
-----------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions queue index 5 / end

send mathced packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 5

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=29,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=100)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 5

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end

send mathced packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=29,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=100)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=29,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=50,dport=100)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV4_SCTP (not support in 19.11)
-----------------------------------------------

to queue action
---------------

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / sctp src is 25 dst is 23 / end actions queue index 4 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=19)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / sctp src is 25 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=19)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / sctp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=19)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV4_ICMP (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / icmp / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / icmp / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / icmp / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_MAC_IPV4_FRAG
----------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_MAC_IPV4_PAY
---------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these two packets to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3") /TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3") /TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5") /TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these two packets to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these two packets dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.4", dst="192.168.0.3")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.5")/TCP()/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_MAC_IPV4_UDP_PAY
--------------------------------

to queue action
---------------

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 1 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet to queue 1

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=29)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not to queue 1

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=29)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=29)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_MAC_IPV4_TCP
---------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions queue index 1 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet to queue 1

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=20,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=19)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not to queue 1

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions rss queues 1 2 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet to queue 1 or 2

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=20,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=19)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not to queue 1 and 2

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / tcp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=20,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP(sport=25,dport=19)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_MAC_IPV4_SCTP (not support in 19.11)
---------------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / sctp src is 25 dst is 23 / end actions queue index 4 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=29)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / sctp src is 25 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=29)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5


drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / sctp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/SCTP(sport=25,dport=29)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_MAC_IPV4_ICMP (not support in 19.11)
---------------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / icmp / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send a mismatched packet::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / icmp / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send a mismatched packet::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5


drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / vxlan vni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / icmp / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send a mismatched packet::

  sendp([Ether()/IP(dst="192.168.0.1")/UDP()/VXLAN(vni=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.2", dst="192.168.0.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

3. verify rules can be listed and destroyed::

     testpmd> flow list 0

   verify the rule exists in the list.
   destroy the rule, suppose the rule number is 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   verify the rule does not exist, and send matched packets, the packets are not to the corresponding queues.


Test case: VXLAN pipeline mode
==============================

1. create switch filter rules and verify

MAC_IPV4_VXLAN_IPV4_FRAG
------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3


drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV4_PAY (not support in 19.11)
----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule for tcp::

   testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue and 3

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_IPV4_VXLAN_IPV4_UDP_PAY
---------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=29)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=29)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5


drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=29)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV4_TCP
-----------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=19,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=30)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=19,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=30)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=19,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=30)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV4_SCTP (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / sctp src is 25 dst is 23 / end actions queue index 4 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=19,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=9)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / sctp src is 25 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=19,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=9)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / sctp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=19,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=9)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV4_ICMP (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / icmp type is 0x08 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x08)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x05)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / icmp type is 0x08 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x08)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x05)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / icmp type is 0x08 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x08)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x05)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_IPV4_VXLAN_IPV6_FRAG (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV6_PAY (not support in 19.11)
----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x06 tc is 3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 3

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x11 tc is 3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send a mismatched packet::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x06 tc is 3 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x11 tc is 3 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x06 tc is 3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x11 tc is 3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_IPV4_VXLAN_IPV6_UDP_PAY (not support in 19.11)
--------------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=29)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions rss queues 1 2 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 1 or 2

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=29)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 1 and 2

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=29)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV6_TCP (not support in 19.11)
----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 50 dst is 23 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=50,dport=30)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 50 dst is 23 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=50,dport=30)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=50,dport=30)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV6_SCTP (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / sctp src is 25 dst is 23 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=19)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / sctp src is 25 dst is 23 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=19)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / sctp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=19)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_VXLAN_IPV6_ICMPV6 (not support in 19.11)
-------------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / icmp type is 0x01 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x01)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x02)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / icmp type is 0x01 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x01)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x02)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / icmp type is 0x01 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x01)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/UDP()/VXLAN()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x02)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

2. verify rules can be listed and destroyed::

     testpmd> flow list 0

   verify the rule exists in the list.
   destroy the rule, suppose the rule number is 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   verify the rule does not exist, and send matched packets, the packets are not to the corresponding queues.


Test case: NVGRE non-pipeline mode
==================================

1. create fdir rules to make the fdir table full,
   which can be created as follows::

     flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 5 / end

2. create switch filter rules and verify

MAC_IPV4_NVGRE_IPV4_FRAG
------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these two packets dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV4_PAY
-----------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.4", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.5")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV4_UDP_PAY
---------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions queue index 4 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify this packet to queue 4

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify these packets not to queue 4

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / udp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=20,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether()/IP(src="192.168.0.2", dst="192.168.0.3")/UDP(sport=50,dport=19)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV4_TCP
-----------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions queue index 1 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 1

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=39)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 1

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions rss queues 1 2 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" )/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 1 or 2

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=39)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 1 and 2

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3" )/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=39)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV4_SCTP (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / sctp src is 25 dst is 23 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / sctp src is 25 dst is 23 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / sctp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV4_ICMP (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / icmp / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / icmp / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / icmp / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether()/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_IPV4_NVGRE_MAC_IPV4_FRAG
----------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5" ,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_MAC_IPV4_PAY
---------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.2")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=3)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a9")/IP(src="192.168.1.2", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.4", dst="192.168.1.3")/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.5")/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_MAC_IPV4_UDP_PAY
-------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 0x8 /  eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / udp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=2,dport=23)/Raw('x'*80)], iface="enp27s0f2", count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=0x8)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP(sport=25,dport=20)/Raw('x'*80)], iface="enp27s0f2", count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_MAC_IPV4_TCP
---------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / tcp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/TCP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_MAC_IPV4_SCTP (not support in 19.11)
---------------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / sctp src is 25 dst is 23 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=19)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / sctp src is 25 dst is 23 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=19)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / sctp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/SCTP(sport=25,dport=19)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_MAC_IPV4_ICMP (not support in 19.11)
---------------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / icmp / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / icmp / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / nvgre tni is 2 / eth dst is 68:05:ca:8d:ed:a8  / ipv4 src is 192.168.1.2 dst is 192.168.1.3 / icmp / end actions drop / end

send matched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/ICMP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(dst="192.168.0.1")/NVGRE(TNI=2)/Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.1.2", dst="192.168.1.3")/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

3. verify rules can be listed and destroyed::

     testpmd> flow list 0

   verify the rule exists in the list.
   destroy the rule, suppose the rule number is 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   verify the rule does not exist, and send matched packets, the packets are not to the corresponding queues.


Test case: NVGRE pipeline mode
==============================

1. create switch filter rules and verify

MAC_IPV4_NVGRE_IPV4_FRAG
------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 3

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=5,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV4_PAY (not support in 19.11)
----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2 and 3

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x11,tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",proto=0x06,tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_IPV4_NVGRE_IPV4_UDP_PAY
---------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=100)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=100)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=100)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV4_TCP
-----------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=3,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=100)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=3,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=100)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=3,dport=23)/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=100)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV4_SCTP (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / sctp src is 25 dst is 23 / end actions queue index 4 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=4,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=10)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / sctp src is 25 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=4,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=10)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / sctp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=4,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=10)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV4_ICMP (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / icmp type is 0x08 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x08)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x04)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / icmp type is 0x08 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x08)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x04)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / icmp type is 0x08 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x08)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x04)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_IPV4_NVGRE_IPV6_FRAG (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV6_PAY (not support in 19.11)
----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x06 tc is 3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 3

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x11 tc is 3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x06 tc is 3 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x11 tc is 3 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x06 tc is 3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x11 tc is 3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_IPV4_NVGRE_IPV6_UDP_PAY (not support in 19.11)
--------------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=5,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=30)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=5,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=30)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=5,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=25,dport=30)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV6_TCP (not support in 19.11)
----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions queue index 1 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 1

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=7,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 1

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=7,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=7,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV6_SCTP (not support in 19.11)
-----------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / sctp src is 25 dst is 23 / end actions queue index 5 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 5

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=39)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 5

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / sctp src is 25 dst is 23 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=39)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / sctp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=20,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=39)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_NVGRE_IPV6_ICMPV6 (not support in 19.11)
-------------------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / icmp type is 0x01 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x01)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x04)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / icmp type is 0x01 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x01)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x04)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 / nvgre / eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / icmp type is 0x01 / end actions drop / end

send matched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x01)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP()/NVGRE()/Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x04)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

2. verify rules can be listed and destroyed::

     testpmd> flow list 0

   verify the rule exists in the list.
   destroy the rule, suppose the rule number is 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   verify the rule does not exist, and send matched packets, the packets are not to the corresponding queues.


Test case: PPPOD non-pipeline mode
==================================

1. create fdir rules to make the fdir table full,
   which can be created as follows::

     flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 5 / end

2. create switch filter rules and verify

MAC_PPPOD_PAY
-------------

to queue action
^^^^^^^^^^^^^^^

create rules::

  testpmd> flow create 0 ingress pattern eth type is 0x8863 / end actions queue index 2 / end

send matched packets::

  sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw('x' *80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw('x' *80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth type is 0x8863 / end actions drop / end

send matched packets::

  sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw('x' *80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw('x' *80)],iface="enp27s0f2",count=1)

verify this packet not dropped

3. verify rules can be listed and destroyed::

     testpmd> flow list 0

   verify the rule exists in the list.
   destroy the rule, suppose the rule number is 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   verify the rule does not exist, and send matched packets, the packets are not to the corresponding queues.


Test case: PPPOE non-pipeline mode
==================================

1. create fdir rules to make the fdir table full,
   which can be created as follows::

     flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 5 / end

2. create switch filter rules and verify

MAC_PPPOE_PAY
-------------

to queue action
^^^^^^^^^^^^^^^

create rules::

  testpmd> flow create 0 ingress pattern eth type is 0x8864 / end actions queue index 2 / end

send matched packets::

  sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth type is 0x8864 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth type is 0x8864 / end actions drop / end

send matched packets::

  sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP()/IP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_PPPOE_IPV4_PAY
------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions queue index 1 / end

send matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet to queue 1

send mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet not to queue 1

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / vlan tci is 1 / pppoes / end actions drop / end

send matched packets::

  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether(dst="00:11:22:33:44:54",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw('x' * 80)],iface="enp27s0f2",count=1)
  sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE()/PPP(proto=0x0021)/IP()/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet not dropped

3. verify rules can be listed and destroyed::

     testpmd> flow list 0

   verify the rule exists in the list.
   destroy the rule, suppose the rule number is 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   verify the rule does not exist, and send matched packets, the packets are not to the corresponding queues.


Test case: IPv4/IPv6 + TCP/UDP pipeline mode
============================================

1. create switch filter rules and verify

MAC_IPV4_FRAG
-------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 3

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=7,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

create a rule with partial fields::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 3

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=7,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

create a rule with partial fields::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

  verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets dropped

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=7,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

create a rule with partial fields::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.3",tos=4,frag=5)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets dropped

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.4", dst="192.168.0.3",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2", dst="192.168.0.5",tos=4,frag=5)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_PAY
------------

to queue action
^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2 and 3

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x06 tos is 4 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 proto is 0x11 tos is 4 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_IPV4_UDP_PAY
----------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=3)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=3)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=2,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=50,dport=3)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_TCP
------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=5,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=7)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=5,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=7)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=5,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=50,dport=7)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_SCTP (not support in 19.11)
------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / sctp src is 25 dst is 23 / end actions queue index 4 / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=3)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / sctp src is 25 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=3)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / sctp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/SCTP(sport=25,dport=3)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV4_ICMP (not support in 19.11)
------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / icmp type is 0x08 / end actions queue index 2 / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x08)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x04)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 2

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / icmp type is 0x08 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x08)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x04)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / icmp type is 0x08 / end actions drop / end

send matched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x08)/Raw('x' * 80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/ICMP(type=0x04)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_IPV6_FRAG

to queue action
^^^^^^^^^^^^^^^

create a rule with src ipv6 + dst ipv6::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 5 / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 5

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1514",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 5

create a rule with dst ipv6 + tc::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2027",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule with src ipv6 + dst ipv6::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1514",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

create a rule with dst ipv6 + tc::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2027",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule with src ipv6 + dst ipv6::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1515 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1514",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2023",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

create a rule with dst ipv6 + tc::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / end actions drop / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2027",tc=3)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=4)/IPv6ExtHdrFragment()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV6_PAY (not support in 19.11)
-----------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x06 tc is 3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 3

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x11 tc is 3 / end actions queue index 3 / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 3

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 3

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x06 tc is 3 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x11 tc is 3 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule for tcp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x06 tc is 3 / end actions drop / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

create a rule for udp::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 0x11 tc is 3 / end actions drop / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x11,tc=3)/UDP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",nh=0x06,tc=3)/TCP()/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

MAC_IPV6_UDP_PAY
----------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions queue index 5 / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 5

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=3,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=4)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 5

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions rss queues 2 3 end / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 2 or 3

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=3,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=4)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not to queue 2 and 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / udp src is 50 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=3,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/UDP(sport=50,dport=4)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these packets not dropped

MAC_IPV6_TCP
------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions queue index 4 / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets not to queue 4

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=20)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets not dropped

MAC_IPV6_SCTP (not support in 19.11)
------------------------------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / sctp src is 25 dst is 23 / end actions queue index 4 / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=1,dport=23)/Raw('x'*80)],iface="enp27s0f2",count=1)
  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/SCTP(sport=25,dport=9)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify these two packets not to queue 4

to queue group action
^^^^^^^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / icmp type is 0x01 / end actions rss queues 4 5 end / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x01)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet to queue 4 or 5

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x03)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not to queue 4 and 5

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 priority 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / icmp type is 0x01 / end actions drop / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x01)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet dropped

send mismatched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515",dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/ICMP(type=0x03)/Raw('x'*80)],iface="enp27s0f2",count=1)

verify this packet not dropped

2. verify rules can be listed and destroyed::

     testpmd> flow list 0

   verify the rule exists in the list.
   destroy the rule, suppose the rule number is 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   verify the rule does not exist, and send matched packets, the packets are not to the corresponding queues.

Test case: IPv4/IPv6 + TCP/UDP non-pipeline mode
================================================

1. create fdir rules to make the fdir table full,
   which can be created as follows::

     flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 5 / end

2. create switch filter rules and verify

MAC_IPV4_PAY
------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 2 / end actions queue index 4 / end

send matched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=2)/("X"*480)], iface="enp27s0f2", count=100)
  
verify these 100 packets to queue 4

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.3 tos is 4 ttl is 2 / end actions drop / end

send matched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.3",tos=4,ttl=2)/("X"*480)], iface="enp27s0f2", count=100)  
  
verify theses 100 packets dropped

MAC_IPV4_UDP_PAY
----------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 4 ttl is 3 / udp src is 25 dst is 23 / end actions queue index 2 / end
  
send matched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.2",tos=4,ttl=3)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)

verify these 100 packets to queue 2

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.3 tos is 4 / udp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.3",tos=4)/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
 
verify theses 100 packets dropped

MAC_IPV4_TCP_PAY
----------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.32 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 3 / end

send matched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.32",tos=4)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)

verify these 100 packets to queue 3

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a8 / ipv4 src is 192.168.0.1 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions drop / end

send matched packets::

  sendp([Ether(dst="68:05:ca:8d:ed:a8")/IP(src="192.168.0.1",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)
 
verify theses 100 packets dropped
 

MAC_IPV6_PAY
------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 8 / end
 
send matched packets::

 sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)], iface="enp27s0f2", count=100)

verify these 100 packets to queue 8

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1537 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions drop / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)], iface="enp27s0f2", count=100)

verify theses 100 packets dropped

MAC_IPV6_FRAG
-------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2022 / end actions queue index 10 / end
 
send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f2", count=100)	

verify these 100 packets to queue 10

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv6 src is CDCD:910A:2222:5498:8475:1111:3900:1536 dst is CDCD:910A:2222:5498:8475:1111:3900:2023 / end actions drop / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/("X"*480)], iface="enp27s0f2", count=100)

verify theses 100 packets dropped
 
MAC_IPV6_UDP
------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is CDCD:910A:2222:5498:8475:1111:3900:1518 / udp src is 25 dst is 23 / end actions queue index 6 / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)

verify these 100 packets to queue 6

drop action
^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is CDCD:910A:2222:5498:8475:1111:3900:1528 / udp src is 25 dst is 23 / end actions drop / end
 
send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1528", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=25,dport=23)/("X"*480)], iface="enp27s0f2", count=100)

verify theses 100 packets dropped
 
MAC_IPV6_TCP
------------

to queue action
^^^^^^^^^^^^^^^

create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is CDCD:910A:2222:5498:8475:1111:3900:1515 / tcp / end actions queue index 12 / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1515", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP()/("X"*480)], iface="enp27s0f2", count=100)

verify these 100 packets to queue 12


create a rule::

  testpmd> flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is CDCD:910A:2222:5498:8475:1111:3900:1516 / tcp / end actions drop / end

send matched packets::

  sendp([Ether()/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1516", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP()/("X"*480)], iface="enp27s0f2", count=100)

verify theses 100 packets dropped

3. verify rules can be listed and destroyed::

     testpmd> flow list 0

   verify the rule exists in the list.
   destroy the rule, suppose the rule number is 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   verify the rule does not exist, and send matched packets, the packets are not to the corresponding queues.

