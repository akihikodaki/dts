.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2021 Intel Corporation

============================
ICE IAVF Flexible Descriptor
============================


Description
===========

To carry more metadata to descriptor and fill them to mbuf to save CPU cost on packet parsing.
Intel® Ethernet 800 Series flexible descriptor capability can be used. iavf driver could
negotiate descriptor format with PF driver by virtchnl. It is implemented in DPDK20.11, and
requires ice base driver >= 1.3.0.

Prerequisites
=============

1. NIC requires

   - Intel® Ethernet 800 Series ethernet cards: E810-XXVDA4/E810-CQ, etc.

2. Toplogy

   - 1 Intel E810 interface
   - 1 network interface for sending test packet, which could be connect to the E810 interface
   - Directly connect the 2 interfaces

3. DDP Package Preparation

   - copy correct ``ice.pkg`` into ``/lib/firmware/updates/intel/ice/ddp/``.
   - unbind, then bind device back to ice.ko to update ddp package in the NIC.

.. warning::

    Need unbind all ports in NIC, then bind device back to ice.ko

.. note::

    To test all test cases, comms/wireless package is expected, as os package only support MPLS cases.

4. DPDK Application Preparation

The default DPDK don't support dump flexible descriptor fields, so need to patch dpdk and re-compile it.

 1. Patch testpmd for dumping flexible fields from RXD::

      diff --git a/app/test-pmd/meson.build b/app/test-pmd/meson.build
      index 7e9c7bdd6..b75b90a9c 100644
      --- a/app/test-pmd/meson.build
      +++ b/app/test-pmd/meson.build
      @@ -49,6 +49,9 @@ endif
      if dpdk_conf.has('RTE_NET_I40E')
      deps += 'net_i40e'
      endif
      +if dpdk_conf.has('RTE_NET_ICE')
      +       deps += ['net_ice', 'net_iavf']
      +endif
      if dpdk_conf.has('RTE_NET_IXGBE')
      deps += 'net_ixgbe'
      endif

      diff --git a/app/test-pmd/util.c b/app/test-pmd/util.c
      index a9e431a8b..3447a9b43 100644
      --- a/app/test-pmd/util.c
      +++ b/app/test-pmd/util.c
      @@ -12,6 +12,7 @@
      #include <rte_vxlan.h>
      #include <rte_ethdev.h>
      #include <rte_flow.h>
      +#include <rte_pmd_iavf.h>

      #include "testpmd.h"

      @@ -151,6 +152,7 @@ dump_pkt_burst(uint16_t port_id, uint16_t queue, struct rte_mbuf *pkts[],
      eth_type, (unsigned int) mb->pkt_len,
      (int)mb->nb_segs);
      ol_flags = mb->ol_flags;
      +                rte_pmd_ifd_dump_proto_xtr_metadata(mb);
      if (ol_flags & PKT_RX_RSS_HASH) {
      MKDUMPSTR(print_buf, buf_size, cur_len,
      " - RSS hash=0x%x",

 2. Compile DPDK and testpmd::

      CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib x86_64-native-linuxapp-gcc
      ninja -C x86_64-native-linuxapp-gcc -j 70

5. Generate 1 VF on each PF and set mac address for each VF::

      echo 1 > /sys/bus/pci/devices/0000:af:00.0/sriov_numvfs
      ip link set ens802f0 vf 0 mac 00:11:22:33:44:55

6. Bind the vf interface to vfio-pci driver::

   ./usertools/dpdk-devbind.py -b vfio-pci af:01.0

VLAN cases
==========

1. Launch testpmd by::

     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-9 -n 4 -a af:01.0,proto_xtr=vlan -- -i --rxq=4 --txq=4 --portmask=0x1 --nb-cores=2
     testpmd>set verbose 1
     testpmd>set fwd io
     testpmd>start

2. check RXDID value correct::

      expected: RXDID[17]

.. note::
    Please change the core setting (-l option) and port's PCI (-a option) by your DUT environment

Test Case: Check single VLAN fields in RXD (802.1Q)
---------------------------------------------------

Send a packet with VLAN tag from test network interface::

  p = Ether(src="68:05:ca:a3:1b:28", dst="00:11:22:33:44:55", type=0x9100)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()
  sendp(p, iface='ens192f0', count=1)

.. note::

    - Change ethernet source address with your test network interface's address
    - Make sure the ethernet destination address is NOT your real E810 interface's address

Check the output in testpmd, **ctag=1:0:23** is expected, which is consistent with VLAN tag set in test packet::

  testpmd> port 0/queue 28: received 1 packets
  src=68:05:CA:A3:1B:28 - dst=00:11:22:33:44:55 - type=0x8100 - length=60 - nb_segs=1 - RSS hash=0xf31f649c - RSS queue=0x1c -
  Protocol Extraction:[0x0000:0x2017],vlan,stag=0:0:0,ctag=1:0:23  - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_UDP  -
  sw ptype: L2_ETHER_VLAN L3_IPV4 L4_UDP  - l2_len=18 - l3_len=20 - l4_len=8 - Receive queue=0x1c
  ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

Test Case: Check single VLAN fields in RXD (802.1ad)
----------------------------------------------------

Test packet::

  p = Ether(src='68:05:ca:a3:1b:28', dst='00:11:22:33:44:55', type=0x88A8)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()

Expected output in testpmd::

  stag=1:0:23


Test Case: Check double VLAN fields in RXD (802.1Q) only 1 VLAN tag
-------------------------------------------------------------------

Test packet::

  p = Ether(src='68:05:ca:a3:1b:28', dst='00:11:22:33:44:55', type=0x9100)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()

Expected output in testpmd::

  stag=1:0:23

Test Case: Check double VLAN fields in RXD (802.1Q) 2 VLAN tags
---------------------------------------------------------------

Test packet::

  p = Ether(src='68:05:ca:a3:1b:28', dst='00:11:22:33:44:55', type=0x9100)/Dot1Q(prio=1,vlan=23)/Dot1Q(prio=4,vlan=56)/IP()/UDP()/DNS()

Expected output in testpmd::

  stag=1:0:23
  ctag=4:0:56


Test Case: Check double VLAN fields in RXD (802.1ad)
----------------------------------------------------

Test packet::

  p = Ether(src='68:05:ca:a3:1b:28', dst='00:11:22:33:44:55', type=0x88A8)/Dot1Q(prio=1,vlan=23)/Dot1Q(prio=4,vlan=56)/IP()/UDP()/DNS()

Expected output in testpmd::

  stag=1:0:23
  ctag=4:0:56


Check IPv4 fields in RXD
========================

Test steps are same to ``VLAN cases``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-9 -n 4 -a af:01.0,proto_xtr=ipv4 -- -i --rxq=4 --txq=4 --portmask=0x1 --nb-cores=2

check RXDID value correct::

   expected: RXDID[18]

Test packet::

  p = Ether(src='68:05:ca:a3:1b:28', dst='00:11:22:33:44:55')/IP(tos=23,ttl=98)/UDP()/Raw(load='XXXXXXXXXX')

Expected output in testpmd::

  ver=4
  hdrlen=5
  tos=23
  ttl=98
  proto=17


Check IPv6 fields in RXD
========================

Test steps are same to ``VLAN cases``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-9 -n 4 -a af:01.0,proto_xtr=ipv6 -- -i --rxq=4 --txq=4 --portmask=0x1 --nb-cores=2

check RXDID value correct::

   expected: RXDID[19]

Test packet::

  p = Ether(src='68:05:ca:a3:1b:28', dst='00:11:22:33:44:55')/IPv6(tc=12,hlim=34,fl=0x98765)/UDP()/Raw(load='XXXXXXXXXX')

Expected output in testpmd::

  ver=6
  tc=12
  flow_hi4=0x9
  nexthdr=17
  hoplimit=34


Check IPv6 flow field in RXD
============================

Test steps are same to ``VLAN cases``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-9 -n 4 -a af:01.0,proto_xtr=ipv6_flow -- -i --rxq=4 --txq=4 --portmask=0x1 --nb-cores=2

check RXDID value correct::

   expected: RXDID[20]

Test packet::

  p = Ether(src='68:05:ca:a3:1b:28', dst='00:11:22:33:44:55')/IPv6(tc=12,hlim=34,fl=0x98765)/UDP()/Raw(load='XXXXXXXXXX')

Expected output in testpmd::

  ver=6
  tc=12
  flow=0x98765


Check TCP fields in IPv4 in RXD
===============================

Test steps are same to ``VLAN cases``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-9 -n 4 -a af:01.0,proto_xtr=tcp -- -i --rxq=4 --txq=4 --portmask=0x1 --nb-cores=2

check RXDID value correct::

   expected: RXDID[21]

Test packet::

  p = Ether(src='68:05:ca:a3:1b:28', dst='00:11:22:33:44:55')/IP()/TCP(flags='AS')/Raw(load='XXXXXXXXXX')

Expected output in testpmd::

  doff=5
  flags=AS


Check TCP fields in IPv6 in RXD
===============================

Test steps are same to ``VLAN cases``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-9 -n 4 -a af:01.0,proto_xtr=tcp -- -i --rxq=4 --txq=4 --portmask=0x1 --nb-cores=2

check RXDID value correct::

   expected: RXDID[21]

Test packet::

  p = Ether(src='68:05:ca:a3:1b:28', dst='00:11:22:33:44:55')/IPv6()/TCP(flags='S')/Raw(load='XXXXXXXXXX')

Expected output in testpmd::

  doff=5
  flags=S


Check IPv4, IPv6, TCP fields in RXD on specific queues
======================================================

Test steps are same to ``VLAN cases``, just change the launch command of testpmd, test packet and expected output

Launch testpmd command::

  ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-9 -n 4 -a af:01.0,proto_xtr='[(2):ipv4,(3):ipv6,(4):tcp]' -- -i --rxq=16 --txq=16 --portmask=0x1

check RXDID value correct::

   expected: RXDID[16], RXDID[18], RXDID[19], RXDID[21]

Create generic flow on NIC::

  flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 23 ttl is 98 / end actions queue index 2 / end
  flow create 0 ingress pattern eth / ipv6 src is 2001::3 dst is 2001::4 tc is 12 / end actions queue index 3 / end
  flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / tcp src is 25 dst is 23 / end actions queue index 4 / end

Test packet::

  p = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.2",tos=23,ttl=98)/UDP()/Raw(load='XXXXXXXXXX')
  p = Ether(src='68:05:ca:a3:1b:28', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4', tc=12,hlim=34,fl=0x98765)/UDP()/Raw(load='XXXXXXXXXX')
  p = Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.1',dst='192.168.0.2')/TCP(flags='AS', dport=23, sport=25)/Raw(load='XXXXXXXXXX')

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

  Receive queue=0x4
  doff=5
  flags=AS


Check testpmd use different parameters start
============================================
Test steps are same to ``VLAN cases``, use different "proto_xtr" parameters the launch command of testpmd, check RXDID value.

use error parameter Launch testpmd::

  ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-9 -n 4 -a af:01.0,proto_xtr=vxlan -- -i --rxq=4 --txq=4 --portmask=0x1 --nb-cores=2

testpmd can't started, check "iavf_lookup_flex_desc_type(): wrong flex_desc type, it should be: vlan|ipv4|ipv6|ipv6_flow|tcp|ovs|ip_offset" in testpmd output.

don't use parameter launch testpmd::

   ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -l 6-9 -n 4 -a af:01.0 -- -i --rxq=4 --txq=4 --portmask=0x1 --nb-cores=2

testpmd started, check "iavf_configure_queues(): request RXDID[16] in Queue[0]" in testpmd output


MPLS cases
==========

Test steps are same to ``VLAN cases``, just change the launch command of testpmd, test packet and expected output

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

