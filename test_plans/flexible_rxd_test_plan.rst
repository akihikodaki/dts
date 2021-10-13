.. Copyright (c) <2019> Intel Corporation
   All rights reserved

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

========================
Flexible RXd Test Suites
========================


Description
===========

The test suite will cover the flexible RX descriptor on Intel E810
network interface card.


Prerequisites
=============

Copy correct ``ice.pkg`` into ``/lib/firmware/updates/intel/ice/ddp/``, \
For the test cases, comms package is expected.

Prepare test toplogoy, in the test case, it requires

- 1 Intel E810 interface
- 1 network interface for sending test packet,
  which could be connect to the E810 interface
- Directly connect the 2 interfaces

Patch testpmd for dumping flexible fields from RXD::

  diff --git a/app/test-pmd/util.c b/app/test-pmd/util.c
  index a1164b7..b90344d 100644
  --- a/app/test-pmd/util.c
  +++ b/app/test-pmd/util.c
  @@ -10,6 +10,7 @@
  #include <rte_ether.h>
  #include <rte_ethdev.h>
  #include <rte_flow.h>
  +#include <rte_pmd_ice.h>


  #include "testpmd.h"


  @@ -73,6 +74,9 @@ dump_pkt_burst(uint16_t port_id, uint16_t queue, struct rte_mbuf *pkts[],
                                  printf("hash=0x%x ID=0x%x ",
                                         mb->hash.fdir.hash, mb->hash.fdir.id);
                  }
  +               rte_net_ice_dump_proto_xtr_metadata(mb);
                  if (ol_flags & PKT_RX_TIMESTAMP)
                          printf(" - timestamp %"PRIu64" ", mb->timestamp);
                  if (ol_flags & PKT_RX_QINQ)


Compile DPDK and testpmd::

  make install -j T=x86_64-native-linuxapp-gcc

Bind Intel E810 interface to igb_uio driver, (e.g. 0000:18:00.0) ::

  ./usertools/dpdk-devbind.py -b igb_uio 18:00.0

Test Case 01: Check single VLAN fields in RXD (802.1Q)
======================================================

Launch testpmd by::

  ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -a 18:00.0,proto_xtr=vlan -- -i --rxq=32 --txq=32 --portmask=0x1 --nb-cores=2

  testpmd>set verbose 1
  testpmd>set fwd io
  testpmd>start

Please change the core setting (-l option) and port's PCI (-a option) \
by your DUT environment

Send a packet with VLAN tag from test network interface::

  scapy #launch scapy in shell

  #In scapy interactive UI
  p = Ether(src="3c:fd:fe:c0:e1:8c", dst="00:00:00:00:01:02", type=0x8100)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()
  sendp(p, iface='enp175s0f0', count=1)

Please notice

- Change ethernet source address with your test network interface's address
- Make sure the ethernet destination address is NOT your real E810 interface's address

Check the output in testpmd, **ctag=1:0:23** is expected, which is consistent with VLAN tag set in test packet::

  testpmd> port 0/queue 28: received 1 packets
  src=3C:FD:FE:C0:E1:8C - dst=00:00:00:00:01:02 - type=0x8100 - length=60 - nb_segs=1 - RSS hash=0xf31f649c - RSS queue=0x1c - Protocol Extraction:[0x0000:0x2017],vlan,stag=0:0:0,ctag=1:0:23  - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_UDP  - sw ptype: L2_ETHER_VLAN L3_IPV4 L4_UDP  - l2_len=18 - l3_len=20 - l4_len=8 - Receive queue=0x1c
  ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN


Test Case 02: Check double VLAN fields in RXD (802.1Q) only 1 VLAN tag
======================================================================

Test steps are same to ``Test Case 01``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -a 18:00.0,proto_xtr=vlan -- -i --rxq=32 --txq=32 --portmask=0x1 --nb-cores=2

Test packet::

  p = Ether(src='3c:fd:fe:bc:f6:78', dst='68:05:ca:a3:13:4c', type=0x9100)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()

Expected output in testpmd::

  stag=1:0:23


Test Case 03: Check double VLAN fields in RXD (802.1Q) 2 VLAN tags
==================================================================

Test steps are same to ``Test Case 01``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -a 18:00.0,proto_xtr=vlan -- -i --rxq=32 --txq=32 --portmask=0x1 --nb-cores=2

Test packet::

  p = Ether(src='3c:fd:fe:bc:f6:78', dst='68:05:ca:a3:13:4c', type=0x9100)/Dot1Q(prio=1,vlan=23)/Dot1Q(prio=4,vlan=56)/IP()/UDP()/DNS()

Expected output in testpmd::

  stag=1:0:23
  ctag=4:0:56


Test Case 04: Check double VLAN fields in RXD (802.1ad)
=======================================================

Test steps are same to ``Test Case 01``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -a 18:00.0,proto_xtr=vlan -- -i --rxq=32 --txq=32 --portmask=0x1 --nb-cores=2

Test packet::

  p = Ether(src='3c:fd:fe:bc:f6:78', dst='68:05:ca:a3:13:4c', type=0x88A8)/Dot1Q(prio=1,vlan=23)/Dot1Q(prio=4,vlan=56)/IP()/UDP()/DNS()

Expected output in testpmd::

  stag=1:0:23
  ctag=4:0:56


Test Case 05: Check IPv4 fields in RXD
======================================

Test steps are same to ``Test Case 01``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -a 18:00.0,proto_xtr=ipv4 -- -i --rxq=32 --txq=32 --portmask=0x1 --nb-cores=2

Test packet::

  p = Ether(src='3c:fd:fe:bc:f6:78', dst='68:05:ca:a3:13:4c')/IP(tos=23,ttl=98)/UDP()/Raw(load='XXXXXXXXXX')

Expected output in testpmd::
  
  ver=4
  hdrlen=5
  tos=23
  ttl=98
  proto=17


Test Case 06: Check IPv6 fields in RXD
=======================================================

Test steps are same to ``Test Case 01``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -a 18:00.0,proto_xtr=ipv6 -- -i --rxq=32 --txq=32 --portmask=0x1 --nb-cores=2

Test packet::

  p = Ether(src='3c:fd:fe:bc:f6:78', dst='68:05:ca:a3:13:4c')/IPv6(tc=12,hlim=34,fl=0x98765)/UDP()/Raw(load='XXXXXXXXXX')

Expected output in testpmd::

  ver=6
  tc=12
  flow_hi4=0x9
  nexthdr=17
  hoplimit=34


Test Case 07: Check IPv6 flow field in RXD
=======================================================

Test steps are same to ``Test Case 01``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -a 18:00.0,proto_xtr=ipv6_flow -- -i --rxq=32 --txq=32 --portmask=0x1 --nb-cores=2

Test packet::

  p = Ether(src='3c:fd:fe:bc:f6:78', dst='68:05:ca:a3:13:4c')/IPv6(tc=12,hlim=34,fl=0x98765)/UDP()/Raw(load='XXXXXXXXXX')

Expected output in testpmd::

  ver=6
  tc=12
  flow=0x98765


Test Case 08: Check TCP fields in IPv4 in RXD
=======================================================

Test steps are same to ``Test Case 01``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -a 18:00.0,proto_xtr=tcp -- -i --rxq=32 --txq=32 --portmask=0x1 --nb-cores=2

Test packet::

  p = Ether(src='3c:fd:fe:bc:f6:78', dst='68:05:ca:a3:13:4c')/IP()/TCP(flags='AS')/Raw(load='XXXXXXXXXX')

Expected output in testpmd::

  doff=5
  flags=AS


Test Case 09: Check TCP fields in IPv6 in RXD
=======================================================

Test steps are same to ``Test Case 01``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -a 18:00.0,proto_xtr=tcp -- -i --rxq=32 --txq=32 --portmask=0x1 --nb-cores=2

Test packet::

  p = Ether(src='3c:fd:fe:bc:f6:78', dst='68:05:ca:a3:13:4c')/IPv6()/TCP(flags='S')/Raw(load='XXXXXXXXXX')

Expected output in testpmd::

  doff=5
  flags=S


Test Case 10: Check IPv4, IPv6, TCP fields in RXD on specific queues
====================================================================

Test steps are same to ``Test Case 01``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linux-gcc/app/testpmd -l 6-9 -n 4 -a 18:00.0,proto_xtr='[(2):ipv4,(3):ipv6,(4):tcp]' -- -i --rxq=64 --txq=64 --portmask=0x1

Create generic flow on NIC::

  flow create 0 ingress pattern eth dst is 68:05:ca:a3:13:4c / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 23 ttl is 98 / end actions queue index 2 / end
  flow create 0 ingress pattern eth / ipv6 src is 2001::3 dst is 2001::4 tc is 8 / end actions queue index 3 / end
  flow create 0 ingress pattern eth dst is 68:05:ca:8d:ed:a9 / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / tcp src is 25 dst is 23 / end actions queue index 63 / end

Test packet::

  p = Ether(dst="68:05:ca:a3:13:4c")/IP(src="192.168.0.1",dst="192.168.0.2",tos=23,ttl=98)/UDP()/Raw(load='XXXXXXXXXX')
  p = Ether(src='3c:fd:fe:bc:f6:78', dst='68:05:ca:a3:13:4c')/IPv6(src='2001::3', dst='2001::4', tc=8,hlim=34,fl=0x98765)/UDP()/Raw(load='XXXXXXXXXX')
  p = Ether(dst='68:05:ca:8d:ed:a9')/IP(src='192.168.0.1', dst='192.168.0.2')/TCP(flags='AS', dport=23, sport=25)/Raw(load='XXXXXXXXXX')

Expected output in testpmd::

  Receive queue=0x2
  ver=4
  hdrlen=5
  tos=23
  ttl=98
  proto=17

  Receive queue=0x3
  ver=6
  tc=12
  flow_hi4=0x9
  nexthdr=17
  hoplimit=34

  Receive queue=0x3f
  doff=5
  flags=AS


Test Case 11: Check effect of replacing pkg from RXID #22 to RXID #16
=====================================================================

Put the ice.pkg with RXID #16(ice-1.3.7.0.pkg and more) to /lib/firmware/updates/intel/ice/ddp/ice.pkg, then reload ice driver::

  rmmod ice
  modprobe ice

Make sure the new ice.pkg is different with the original one. Take 'dmesg' command to get ice.pkg version::

  dmesg | grep package

Start the testpmd::

  ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64

Check the testpmd started failed. Failed info output::

  Port (0) - Rx queue (0) is set with RXDID : 16
  ice_rx_queue_start(): fail to program RX queue 0
  ice_dev_start(): fail to start Rx queue 0
  Fail to start port 0
  Please stop the ports first
  Port (0) - Rx queue (0) is set with RXDID : 16

Replace correct ice.pkg to /lib/firmware/updates/intel/ice/ddp/ice.pkg,then reload ice driver::

  rmmod ice
  modprobe ice.ko

MPLS cases
==========

Test steps are same to ``Test Case 01``, just change the launch command of testpmd, test packet and expected output

MPLS cases use same parameter Launch testpmd::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-9 -n 4 -a af:01.0,proto_xtr=ip_offset -- -i  --portmask=0x1 --nb-cores=2

check RXDID value correct::

    expected: RXDID[25]

scapy prepare::

    about scapy:
    from scapy.contrib.mpls import MPLS

Test Case: Check ip offset of ip
--------------------------------

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=18

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=18

Test Case: check ip offset with vlan
------------------------------------

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=22

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=22

Test Case: check offset with 2 vlan tag
---------------------------------------

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=26

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=26

Test Case: check ip offset with multi MPLS
------------------------------------------

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=18

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=22

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=26

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=30

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=34

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=18

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=22

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=26

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=30

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=34

Test Case: check ip offset with multi MPLS with vlan tag
--------------------------------------------------------

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=22

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=26

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=30

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=34

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=38

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=22

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=26

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=30

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=34

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=38

Test Case: check ip offset with multi MPLS with 2 vlan tag
----------------------------------------------------------

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=26

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=30

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=34

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=38

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()

Expected output in testpmd::

    Protocol Offset:ip_offset=42

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=26

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=30

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=34

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=38

Test packet::

    p = Ether(dst="00:11:22:33:44:55",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()

Expected output in testpmd::

    Protocol Offset:ip_offset=42
