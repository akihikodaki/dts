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

==================================
ICE IAVF IP FRAGMENT RTE FLOW TEST
==================================

Description
===========

This document provides the plan for testing ip fragment.

DPDK-21.05 enable ipv4/6 fragment in rte_flow by IPID on Intel E810 series ethernet cards, major feature are:

 - IP fragment packet can be filtered by IPID with RTE_FLOW in FDIR::

    queue index
    drop
    rss queues
    passthru
    mark
    mark/rss

 - IP fragment packet is based on 5-tuple(src-ip/dst-ip/src-port/dst-port/l3 protocol) + IPID as inputset to get hash
   value in RSS

 - It's enable on both PF and VF, this plan test on VF.

.. note::

   Currently, ipv4/6 fragment packet was treated as "IPv4/6 pay", so only validate ipv4/6 fragment pattern.

Prerequisites
=============

1. Hardware:
   Intel® Ethernet 800 Series: E810-XXVDA4/E810-CQ

2. Software:
   dpdk: http://dpdk.org/git/dpdk

   scapy: http://www.secdev.org/projects/scapy/

3. Get the pci device id of DUT, for example::

     ./usertools/dpdk-devbind.py -s

     0000:18:00.0 'Device 1593' if=enp24s0f0 drv=ice unused=vfio-pci
     0000:18:00.1 'Device 1593' if=enp24s0f1 drv=ice unused=vfio-pci

4. create vf and bind to dpdk::

     echo 1 > /sys/bus/pci/devices/0000:18:00.0/sriov_numvfs
     ip link set ens801f0 vf 0 mac 00:11:22:33:55:66

     ./usertools/dpdk-devbind.py -s
     0000:18:01.0 'Ethernet Adaptive Virtual Function 1889' if=enp24s1 drv=iavf unused=vfio-pci

     Bind VFs to dpdk driver:
     modprobe vfio-pci
     ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:01.0 0000:18:01.1

5. Launch testpmd::

     fdir testpmd command:
     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -- -i --rxq=16 --txq=16

     rss testpmd command:
     ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf -n 4 -- -i --rxq=16 --txq=16 --disable-rss --rxd=384 --txd=384

     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start


Basic Test Steps
================

The steps same as FDIR/RSS suites test steps

take 'MAC_IPV4_FRAG fdir queue index' for fdir example
------------------------------------------------------

.. note::

   The default rss not support ipfragment, need take a rss rule to enable ipfragment rss.

1. validate and create rule::

      take a ipfragment rss rule:
      flow create 0 ingress pattern eth / ipv4 / end actions rss types eth ipv4-frag end key_len 0 queues end / end

      take fdir rule:

      flow validate 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions queue index 1 / mark / end
      Flow rule validated
      flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions queue index 1 / mark / end
      Flow rule #0 created

2. send matched pkts and check two pkts distributed to queue 1, `RSS hash=0x261a7deb - RSS queue=0x1` in output::

      scapy:
      p = Ether()/IP(id=47750)/Raw('X'*666)
      pkts=fragment(p, fragsize=500)
      sendp(pkts, iface="enp1s0")

      Sent 2 packets.
            dut.10.240.183.133: port 0/queue 1: received 1 packets
      src=00:00:00:00:00:00 - dst=FF:FF:FF:FF:FF:FF - type=0x0800 - length=530 - nb_segs=1 - RSS hash=0x261a7deb - RSS queue=0x1 - FDIR matched ID=0x0 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV4 L4_FRAG  - l2_len=14 - l3_len=20 - l4_len=0 - Receive queue=0x1
      ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_GOOD
      port 0/queue 1: received 1 packets
      src=00:00:00:00:00:00 - dst=FF:FF:FF:FF:FF:FF - type=0x0800 - length=204 - nb_segs=1 - RSS hash=0x261a7deb - RSS queue=0x1 - FDIR matched ID=0x0 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV4 L4_FRAG  - l2_len=14 - l3_len=20 - l4_len=0 - Receive queue=0x1
      ol_flags: PKT_RX_RSS_HASH PKT_RX_FDIR PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_FDIR_ID PKT_RX_OUTER_L4_CKSUM_GOOD

3. send mismatched pkts and check fdir id is none::

      scapy:
      p = Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666)
      pkts=fragment6(p, 500)
      sendp(pkts, iface="enp1s0")

      Sent 2 packets.
            dut.10.240.183.133: port 0/queue 3: received 1 packets
      src=00:00:00:00:00:00 - dst=FF:FF:FF:FF:FF:FF - type=0x86dd - length=494 - nb_segs=1 - RSS hash=0xe5ae2d03 - RSS queue=0x3 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV6_EXT L4_FRAG  - l2_len=14 - l3_len=48 - l4_len=0 - Receive queue=0x3
      ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_GOOD
      port 0/queue 3: received 1 packets
      src=00:00:00:00:00:00 - dst=FF:FF:FF:FF:FF:FF - type=0x86dd - length=296 - nb_segs=1 - RSS hash=0xe5ae2d03 - RSS queue=0x3 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV6_EXT L4_FRAG  - l2_len=14 - l3_len=48 - l4_len=0 - Receive queue=0x3
      ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_GOOD

4. destroy rule re-send step 2 pkts and check fdir id is none::

      flow destroy 0 rule 0
      Flow rule #0 destroyed

      p = Ether()/IP(id=47750)/Raw('X'*666)
      pkts=fragment(p, fragsize=500)
      sendp(pkts, iface="enp1s0")

      Sent 2 packets.
            dut.10.240.183.133: port 0/queue 7: received 1 packets
      src=00:00:00:00:00:00 - dst=FF:FF:FF:FF:FF:FF - type=0x0800 - length=530 - nb_segs=1 - RSS hash=0x4cf81c87 - RSS queue=0x7 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV4 L4_FRAG  - l2_len=14 - l3_len=20 - l4_len=0 - Receive queue=0x7
      ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_GOOD
      port 0/queue 7: received 1 packets
      src=00:00:00:00:00:00 - dst=FF:FF:FF:FF:FF:FF - type=0x0800 - length=204 - nb_segs=1 - RSS hash=0x4cf81c87 - RSS queue=0x7 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV4 L4_FRAG  - l2_len=14 - l3_len=20 - l4_len=0 - Receive queue=0x7
      ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_GOOD



take 'MAC_IPV4_FRAG_RSS for rss example
---------------------------------------
1. validate and create rule::

      flow validate 0 ingress pattern eth / ipv4 / end actions rss types eth ipv4-frag end key_len 0 queues end / end
      Flow rule validated
      flow create 0 ingress pattern eth / ipv4 / end actions rss types eth ipv4-frag end key_len 0 queues end / end
      Flow rule #0 created

2. send basic pkts and record hash values, `RSS hash=0xa1dd9f10 - RSS queue=0x0` in output::

      scapy:
      p = Ether(src='00:11:22:33:44:55', dst='00:11:22:33:55:66')/IP(src='192.168.6.11', dst='10.11.12.13', id=47750)/Raw('X'*666)
      pkts=fragment(p, fragsize=500)
      sendp(pkts, iface="enp1s0")

      Sent 2 packets.
            dut.10.240.183.133: port 0/queue 0: received 1 packets
      src=00:11:22:33:44:55 - dst=00:11:22:33:55:66 - type=0x0800 - length=530 - nb_segs=1 - RSS hash=0xa1dd9f10 - RSS queue=0x0 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV4 L4_FRAG  - l2_len=14 - l3_len=20 - l4_len=0 - Receive queue=0x0
      ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
      port 0/queue 0: received 1 packets
      src=00:11:22:33:44:55 - dst=00:11:22:33:55:66 - type=0x0800 - length=204 - nb_segs=1 - RSS hash=0xa1dd9f10 - RSS queue=0x0 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV4 L4_FRAG  - l2_len=14 - l3_len=20 - l4_len=0 - Receive queue=0x0
      ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

3. send change input set pkts and check received pkts have different hash value with basic pkts::

      p = Ether(src='00:11:22:33:44:66', dst='00:11:22:33:55:66')/IP(src='192.168.6.11', dst='10.11.12.13', id=47750)/Raw('X'*666)
      pkts=fragment(p, fragsize=500)
      sendp(pkts, iface="enp1s0")

      Sent 2 packets.
            dut.10.240.183.133: port 0/queue 12: received 1 packets
      src=00:11:22:33:44:66 - dst=00:11:22:33:55:66 - type=0x0800 - length=530 - nb_segs=1 - RSS hash=0xf4a26fbc - RSS queue=0xc - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV4 L4_FRAG  - l2_len=14 - l3_len=20 - l4_len=0 - Receive queue=0xc
      ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
      port 0/queue 12: received 1 packets
      src=00:11:22:33:44:66 - dst=00:11:22:33:55:66 - type=0x0800 - length=204 - nb_segs=1 - RSS hash=0xf4a26fbc - RSS queue=0xc - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV4 L4_FRAG  - l2_len=14 - l3_len=20 - l4_len=0 - Receive queue=0xc
      ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

4. send unhit rule pkts and check received pkts have no hash valuse::

      p = Ether()/IPv6()/IPv6ExtHdrFragment(id=47751)/Raw('X'*666)
      pkts=fragment6(p, 500)
      sendp(pkts, iface="enp1s0")

      Sent 2 packets.
            dut.10.240.183.133: port 0/queue 0: received 1 packets
      src=00:00:00:00:00:00 - dst=FF:FF:FF:FF:FF:FF - type=0x86dd - length=494 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV6_EXT L4_FRAG  - l2_len=14 - l3_len=48 - l4_len=0 - Receive queue=0x0
      ol_flags: PKT_RX_L4_CKSUM_UNKNOWN PKT_RX_IP_CKSUM_UNKNOWN PKT_RX_OUTER_L4_CKSUM_UNKNOWN
      port 0/queue 0: received 1 packets
      src=00:00:00:00:00:00 - dst=FF:FF:FF:FF:FF:FF - type=0x86dd - length=296 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV6_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV6_EXT L4_FRAG  - l2_len=14 - l3_len=48 - l4_len=0 - Receive queue=0x0
      ol_flags: PKT_RX_L4_CKSUM_UNKNOWN PKT_RX_IP_CKSUM_UNKNOWN PKT_RX_OUTER_L4_CKSUM_UNKNOWN

5. destroy rule re-send basic pkts and check received pkts have no hash valuse::

      flow destroy 0 rule 0
      Flow rule #0 destroyed

      scapy:
      p = Ether(src='00:11:22:33:44:55', dst='00:11:22:33:55:66')/IP(src='192.168.6.11', dst='10.11.12.13', id=47750)/Raw('X'*666)
      pkts=fragment(p, fragsize=500)
      sendp(pkts, iface="enp1s0")

      Sent 2 packets.
            dut.10.240.183.133: port 0/queue 0: received 1 packets
      src=00:11:22:33:44:55 - dst=00:11:22:33:55:66 - type=0x0800 - length=530 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV4 L4_FRAG  - l2_len=14 - l3_len=20 - l4_len=0 - Receive queue=0x0
      ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
      port 0/queue 0: received 1 packets
      src=00:11:22:33:44:55 - dst=00:11:22:33:55:66 - type=0x0800 - length=204 - nb_segs=1 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN L4_FRAG  - sw ptype: L2_ETHER L3_IPV4 L4_FRAG  - l2_len=14 - l3_len=20 - l4_len=0 - Receive queue=0x0
      ol_flags: PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN



Test case: MAC_IPV4_FRAG pattern fdir fragment
==============================================

Subcase 1: MAC_IPV4_FRAG fdir queue index
-----------------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions queue index 1 / mark / end

2. matched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

3. unmatched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

Subcase 2: MAC_IPV4_FRAG fdir rss queues
-----------------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions rss queues 2 3 end / mark / end

2. matched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

3. unmatched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

Subcase 3: MAC_IPV4_FRAG fdir passthru
--------------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions passthru / mark / end

2. matched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

3. unmatched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

Subcase 4: MAC_IPV4_FRAG fdir drop
----------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions drop / mark / end

2. matched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

3. unmatched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

Subcase 5: MAC_IPV4_FRAG fdir mark+rss
--------------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions mark / rss / end

2. matched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

3. unmatched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

Subcase 6: MAC_IPV4_FRAG fdir mark
----------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions mark id 1 / end

2. matched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

3. unmatched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

Test case: MAC_IPV6_FRAG pattern fdir fragment
==============================================

Subcase 1: MAC_IPV6_FRAG fdir queue index
-----------------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions queue index 1 / mark / end

2. matched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

3. unmatched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

Subcase 2: MAC_IPV6_FRAG fdir rss queues
----------------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions rss queues 2 3 end / mark / end

2. matched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

3. unmatched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

Subcase 3: MAC_IPV6_FRAG fdir passthru
--------------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions passthru / mark / end

2. matched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

3. unmatched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

Subcase 4: MAC_IPV6_FRAG fdir drop
----------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions drop / mark / end

2. matched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

3. unmatched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

Subcase 5: MAC_IPV6_FRAG fdir mark+rss
--------------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions mark / rss / end

2. matched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

3. unmatched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

Subcase 6: MAC_IPV6_FRAG fdir mark
----------------------------------

1. rules::

     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions mark id 1 / end

2. matched packets::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

3. unmatched packets::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment(p, 500)

Test case: MAC_IPV4_FRAG_fdir_with_l2
=====================================
.. note::

   VF not support take l2 as inputset

Test case: MAC_IPV6_FRAG_fdir_with_l2
=====================================
.. note::

   VF not support take l2 as inputset

Test case: MAC_IPV4_FRAG_fdir_with_l3
=====================================

1. The test step is the same as MAC_IPV4_FRAG pattern fdir fragment

2. rule and pkt need contain IP(src='XX') addr

take 'mac_ipv4_frag_l3src_fdir_queue_index' example::

   1.rules:

   flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions queue index 1 / mark / end

   2.matched packets:

   p=Ether()/IP(id=47750, src='192.168.1.1')/Raw('X'*666); pkts=fragment(p, fragsize=500)

   3.unmatched packets:

   p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkts=fragment6(p, 500)

subcase 1: MAC_IPV4_FRAG_fdir_with_l3dst
----------------------------------------

subcase 2: MAC_IPV4_FRAG_fdir_with_l3src
----------------------------------------

Test case: MAC_IPV6_FRAG_fdir_with_l3
=====================================

1. The test step is the same as MAC_IPV6_FRAG pattern fdir fragment

2. rule and pkt need contain IPv6(src='XX') addr

take 'mac_ipv6_frag_l3src_fdir_queue_index' example::

   1.rules:

   flow create 0 ingress pattern eth / ipv6 src is 2001::1 / ipv6_frag_ext frag_data spec 0x0001 frag_data mask 0x0001 / end actions queue index 1 / mark / end

   2.matched packets:

   p=Ether()/IPv6(src='2001::1')/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkts=fragment6(p, 500)

   3.unmatched packets:

   p=Ether()/IP(id=47750, src='192.168.1.1')/Raw('X'*666); pkts=fragment(p, fragsize=500)

subcase 1: MAC_IPV6_FRAG_fdir_with_l3dst
----------------------------------------

subcase 2: MAC_IPV6_FRAG_fdir_with_l3src
----------------------------------------

Test case: MAC_IPV4_FRAG RSS
============================

1. rule::

     flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-frag end key_len 0 queues end / end

2. basic packet::

     p=Ether(src='00:11:22:33:44:55', dst='66:77:88:99:AA:BB')/IP(src='192.168.6.11', dst='10.11.12.13', id=47750)/Raw('X'*666); pkts=fragment(p, 500)

3. hit pattern packet with changed input set in the rule::

     p=Ether(src='00:11:22:33:44:66', dst='66:77:88:99:AA:BB')/IP(src='192.168.6.11', dst='10.11.12.13', id=47750)/Raw('X'*666); pkts=fragment6(p, 500)
     p=Ether(src='00:11:22:33:44:55', dst='66:77:88:99:AA:CC')/IP(src='192.168.6.11', dst='10.11.12.13', id=47750)/Raw('X'*666); pkts=fragment6(p, 500)
     p=Ether(src='00:11:22:33:44:55', dst='66:77:88:99:AA:BB')/IP(src='192.168.6.12', dst='10.11.12.13', id=47750)/Raw('X'*666); pkts=fragment6(p, 500)
     p=Ether(src='00:11:22:33:44:55', dst='66:77:88:99:AA:BB')/IP(src='192.168.6.11', dst='10.11.12.14', id=47750)/Raw('X'*666); pkts=fragment6(p, 500)
     p=Ether(src='00:11:22:33:44:55', dst='66:77:88:99:AA:BB')/IP(src='192.168.6.11', dst='10.11.12.13', id=47751)/Raw('X'*666); pkts=fragment6(p, 500)

4. not hit pattern packets with input set in the rule::

     p=Ether()/IPv6()/IPv6ExtHdrFragment(id=47751)/Raw('X'*666); pkt=fragment6(p, 500)

Test case: MAC_IPV6_FRAG RSS
============================

1. rules::

     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext / end actions rss types ipv6-frag end key_len 0 queues end / end

2. basic packet::

     p=Ether(src='00:11:22:33:44:55', dst='66:77:88:99:AA:BB')/IPv6(src='CDCD:910A:2222:5498:8475:1111:3900:1537', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)

3. hit pattern packet with changed input set in the rule::

     p=Ether(src='00:11:22:33:44:66', dst='66:77:88:99:AA:BB')/IPv6(src='CDCD:910A:2222:5498:8475:1111:3900:1537', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)
     p=Ether(src='00:11:22:33:44:55', dst='66:77:88:99:AA:CC')/IPv6(src='CDCD:910A:2222:5498:8475:1111:3900:1537', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)
     p=Ether(src='00:11:22:33:44:55', dst='66:77:88:99:AA:BB')/IPv6(src='CDCD:910A:2222:5498:8475:1111:3900:1538', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)
     p=Ether(src='00:11:22:33:44:55', dst='66:77:88:99:AA:BB')/IPv6(src='CDCD:910A:2222:5498:8475:1111:3900:1537', dst='CDCD:910A:2222:5498:8475:1111:3900:2021')/IPv6ExtHdrFragment(id=47750)/Raw('X'*666); pkt=fragment6(p, 500)
     p=Ether(src='00:11:22:33:44:55', dst='66:77:88:99:AA:BB')/IPv6(src='CDCD:910A:2222:5498:8475:1111:3900:1537', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/IPv6ExtHdrFragment(id=47751)/Raw('X'*666); pkt=fragment6(p, 500)

4. not hit pattern packets with input set in the rule::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment6(p, 500)


Test case: VF exclusive validation
==================================

Subcase 1: exclusive validation fdir rule
-----------------------------------------
1. create fdir filter rules::

     flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark / end
     flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions queue index 2 / mark / end

2. hit pattern/defined input set id, the pkt received for queue 2::

     p=Ether()/IP(src="192.168.0.20", id=47750)/Raw('X'*666)

Subcase 2: exclusive validation fdir rule
-----------------------------------------
1. create fdir filter rules::

     flow create 0 ingress pattern eth / ipv4 fragment_offset spec 0x2000 fragment_offset mask 0x2000 / end actions queue index 1 / end actions queue index 2 / mark / end
     flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark / end

2. hit pattern/defined input set id, the pkt received for queue 2::

     p=Ether()/IP(src="192.168.0.20", id=47750)/Raw('X'*666)

Subcase 3: exclusive validation rss rule
----------------------------------------
1. create rss rules::

     flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
     flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-frag end key_len 0 queues end / end

2. hit pattern/defined input set id, the pkt received for rss different queue::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment6(p, 500)
     p=Ether()/IP(id=47751)/Raw('X'*666); pkts=fragment6(p, 500)

Subcase 4: exclusive validation rss rule
----------------------------------------
1. create rss rules::

     flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-frag end key_len 0 queues end / end
     flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

2. hit pattern/defined input set id, the pkt received for rss different queue::

     p=Ether()/IP(id=47750)/Raw('X'*666); pkts=fragment6(p, 500)
     p=Ether()/IP(id=47751)/Raw('X'*666); pkts=fragment6(p, 500)

Test case: negative validation
==============================
Note: there may be error message change.

1. Invalid action::

     flow create 0 ingress pattern eth / ipv6 packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff fragment_offset spec 0x2000 fragment_offset last 0x1fff fragment_offset mask 0xffff / end actions queue index 2 / end
     flow create 0 ingress pattern eth / ipv6 packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff fragment_offset spec 0x2000 fragment_offset last 0x1fff fragment_offset mask 0xffff / end actions queue index 300 / end
     flow create 0 ingress pattern eth / ipv6 packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff fragment_offset spec 0x2 fragment_offset last 0x1fff fragment_offset mask 0xffff / end actions queue index 2 / end
     flow create 0 ingress pattern eth / ipv6 packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff fragment_offset spec 0x2000 fragment_offset last 0x1 fragment_offset mask 0xffff / end actions queue index 2 / end
     flow create 0 ingress pattern eth / ipv6 packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff fragment_offset spec 0x2000 fragment_offset last 0x1fff fragment_offset mask 0xf / end actions queue index 2 / end
     flow create 0 ingress pattern eth / ipv4 packet_id is 47750 fragment_offset last 0x1fff fragment_offset mask 0xffff / end actions queue index 2 / end
     flow create 0 ingress pattern eth / ipv4 packet_id is 47750 fragment_offset spec 0x2000 fragment_offset / end actions queue index 2 / end
     flow create 0 ingress pattern eth / ipv4 packet_id is 47750 fragment_offset spec 0x2000 fragment_offset last 0x1fff / end actions queue index 2 / end
     flow create 0 ingress pattern eth / ipv4 packet_id is 47750 / end actions queue index 300 / end
     flow create 0 ingress pattern eth / ipv4 packet_id last 0xffff packet_id mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv4 packet_id spec 0 packet_id mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv4 packet_id spec 0 packet_id last 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv4 / ipv6_frag_ext packet_id is 47750 frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 47750 frag_data spec 0xfff8 frag_data last 0x0001 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 47750 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 47750 frag_data spec 0x0001 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 47750 frag_data spec 0x0001 frag_data last 0xfff8 / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 47750 frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 300 / end
     flow create 0 ingress pattern eth / ipv4 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0xffff packet_id last 0x0 packet_id mask 0xffff frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff frag_data spec 0xfff8 frag_data last 0x0001 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / packet_id last 0xffff packet_id mask 0xffff frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id mask 0xffff frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff frag_data spec 0x0001 frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff frag_data last 0xfff8 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff frag_data spec 0x0001 frag_data last 0xfff8 / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id spec 0 packet_id last 0xffff packet_id mask 0xffff frag_data spec 0x0001 frag_data mask 0xffff / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv4 / ipv6_frag_ext packet_id is 47750 / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext packet_id is 0x10000 / end actions queue index 1 / end
     flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv4-frag end key_len 0 queues end / end
     flow create 0 ingress pattern eth / ipv4 / ipv6_frag_ext / end actions rss types ipv6-frag end key_len 0 queues end / end
     flow create 0 ingress pattern eth / ipv6 / ipv6_frag_ext / end actions rss types ipv4-frag end key_len 0 queues end / end
