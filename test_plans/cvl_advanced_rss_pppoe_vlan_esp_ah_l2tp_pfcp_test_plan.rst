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

=================================================
CVL: Advanced RSS FOR PPPOE/VLAN/ESP/AH/L2TP/PFCP
=================================================

Description
===========

* Enable RSS for PPPOE/VLAN/ESP/AH/L2TP/PFCP packets.
* Symmetric hash for PPPOE packets.
* Simple_xor hash for PPPOE packets.

Pattern and input set
---------------------
.. table::

    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | Hash function: toeplitz                                                                                                                      |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | Packet Type                   | Pattern                   | All the Input Set options in combination                                         |
    +===============================+===========================+==================================================================================+
    |                               | MAC_PPPOE_IPV4_PAY        | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only, ipv4                    |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOE_IPV4_UDP_PAY    | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only,                         |
    |                               |                           | l4-src-only, l4-dst-only, ipv4-udp                                               |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOE_IPV4_TCP_PAY    | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only,                         |
    |                               |                           | l4-src-only, l4-dst-only, ipv4-tcp                                               |
    |            PPPOE              +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOE_IPV6_PAY        | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only, ipv6                    |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOE_IPV6_UDP_PAY    | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only,                         |
    |                               |                           | l4-src-only, l4-dst-only, ipv6-udp                                               |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOE_IPV6_TCP_PAY    | eth, l2-src-only, l2-dst-only, l3-src-only, l3-dst-only,                         |
    |                               |                           | l4-src-only, l4-dst-only, ipv6-tcp                                               |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_PPPOE_PAY             | eth, l2-src-only, l2-dst-only, pppoe                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV4_PAY         | c-vlan                                                                           |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV4_UDP_PAY     | c-vlan                                                                           |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV4_TCP_PAY     | c-vlan                                                                           |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV4_SCTP_PAY    | c-vlan                                                                           |
    |             VLAN              +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV6_PAY         | c-vlan                                                                           |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV6_UDP_PAY     | c-vlan                                                                           |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV6_TCP_PAY     | c-vlan                                                                           |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV6_SCTP_PAY    | c-vlan                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_ESP              | esp                                                                              |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_UDP_ESP          | esp                                                                              |
    |             ESP               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_ESP              | esp                                                                              |
    |                               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_UDP_ESP          | esp                                                                              |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_AH               | ah                                                                               |
    |              AH               +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_AH               | ah                                                                               |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_L2TPv3           | l2tpv3                                                                           |
    |             L2TP              +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_L2TPv3           | l2tpv3                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_PFCP_SESSION     | pfcp                                                                             |
    |             PFCP              +---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_PFCP_SESSION     | pfcp                                                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+

.. note::

    The MAC_PPPOE_IPV4/IPV6_SCTP and MAC_VLAN_PPPOE patterns are not
    supported by 20.08.

.. table::

    +-------------------------------+---------------------------+-------------------+
    | Hash function: Symmetric_toeplitz                                             |
    +-------------------------------+---------------------------+-------------------+
    | Packet Type                   | Pattern                   | Input Set         |
    +===============================+===========================+===================+
    |                               | MAC_PPPOE_IPV4_PAY        | ipv4              |
    |                               +---------------------------+-------------------+
    |                               | MAC_PPPOE_IPV4_UDP_PAY    | ipv4-udp          |
    |                               +---------------------------+-------------------+
    |           PPPOE               | MAC_PPPOE_IPV4_TCP_PAY    | ipv4-tcp          |
    |                               +---------------------------+-------------------+
    |                               | MAC_PPPOE_IPV6_PAY        | ipv6              |
    |                               +---------------------------+-------------------+
    |                               | MAC_PPPOE_IPV6_UDP_PAY    | ipv6-udp          |
    |                               +---------------------------+-------------------+
    |                               | MAC_PPPOE_IPV6_TCP_PAY    | ipv6-tcp          |
    +-------------------------------+---------------------------+-------------------+

Prerequisites
=============

1. Hardware:

   - Intel E810 series ethernet cards: columbiaville_25g/columbiaville_100g

2. Software:

   - dpdk: http://dpdk.org/git/dpdk
   - scapy: http://www.secdev.org/projects/scapy/

3. Copy comm #1 package to /lib/firmware/intel/ice/ddp/ice.pkg,
   then load driver::

     rmmod ice
     insmod ice.ko

4. Bind pf to dpdk driver::

     ./usertools/dpdk-devbind.py -b vfio-pci 0000:18:00.0

5. Launch the testpmd in DUT for cases with toeplitz hash function::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -w 0000:18:00.0 -- -i --rxq=16 --txq=16 --disable-rss
     testpmd> port config 0 rss-hash-key ipv4 1b9d58a4b961d9cd1c56ad1621c3ad51632c16a5d16c21c3513d132c135d132c13ad1531c23a51d6ac49879c499d798a7d949c8a
     testpmd> set fwd rxonly
     testpmd> set verbose 1
     testpmd> start

   Launch testpmd for cases with symmetric_toeplitz and simple_xor hash function::

     ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 4 -w 0000:18:00.0 -- -i --rxq=16 --txq=16

6. on tester side, copy the layer python file to /root::

      cp pfcp.py to /root

    then import layers when start scapy::

      >>> import sys
      >>> sys.path.append('/root')
      >>> from pfcp import PFCP

Test case: MAC_IPV4_PFCP_SESSION
================================

1. validate a rule for RSS type of MAC_IPV4_PFCP_SESSION::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_IPV4_PFCP_SESSION::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_IPV4_PFCP_SESSION packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="ens786f0")

     change the field [SEID], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(Sfield=1, SEID=2)/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:54")/IP(src="192.168.0.25",dst="192.168.0.23")/UDP(sport=23,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=25)/Raw("x"*80)],iface="ens786f0")

   check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_IPV6_PFCP_SESSION
================================

1. validate a rule for RSS type of MAC_IPV6_PFCP_SESSION::

     testpmd> flow validate 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_IPV6_PFCP_SESSION::

     testpmd> flow create 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_IPV6_PFCP_SESSION packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="ens786f0")

     change the field [SEID], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(Sfield=1, SEID=2)/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:53")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=25)/Raw("x"*80)],iface="ens786f0")

   check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_IPV4_L2TPv3
==========================

1. validate a rule for RSS type of MAC_IPV4_L2TPv3::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_IPV4_L2TPv3::

     testpmd> flow create 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_IPV4_L2TPv3 packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5", proto=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="ens786f0")

     change the field [session_id], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.4", proto=115)/L2TP('\x00\x00\x00\x12')/Raw("x"*480)], iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:53")/IP(src="192.168.0.5",dst="192.168.0.7", proto=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=25)/Raw("x"*80)],iface="ens786f0")

   check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_IPV6_L2TPv3
==========================

1. validate a rule for RSS type of MAC_IPV6_L2TPv3::

     testpmd> flow validate 0 ingress pattern eth / ipv6 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_IPV6_L2TPv3::

     testpmd> flow create 0 ingress pattern eth / ipv6 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_IPV6_L2TPv3 packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="ens786f0")

     change the field [session_id], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP('\x00\x00\x00\x12')/Raw("x"*480)], iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:53")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5", proto=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=25)/Raw("x"*80)],iface="ens786f0")

   check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_IPV4_ESP
=======================

1. validate a rule for RSS type of MAC_IPV4_ESP::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_IPV4_ESP::

     testpmd> flow create 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list

3. send matched packets

   * MAC_IPV4_ESP packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=12)/Raw("x"*480)], iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:53")/IP(src="192.168.0.4",dst="192.168.0.7",proto=50)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")

   check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5", proto=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=12)/Raw("x"*480)], iface="ens786f0")

   check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_IPV4_UDP_ESP
===========================

1. validate a rule for RSS type of MAC_IPV4_UDP_ESP::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / esp / end actions rss types esp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_IPV4_UDP_ESP::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / esp / end actions rss types esp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list

3. send matched packets

   * MAC_IPV4_UDP_ESP packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=12)/Raw("x"*480)], iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:53")/IP(src="192.168.0.4",dst="192.168.0.7")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")

   check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_IPV6_ESP
=======================

1. validate a rule for RSS type of MAC_IPV6_ESP::

     testpmd> flow validate 0 ingress pattern eth / ipv6 / esp / end actions rss types esp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_IPV6_ESP::

     testpmd> flow create 0 ingress pattern eth / ipv6 / esp / end actions rss types esp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list

3. send matched packets

   * MAC_IPV6_ESP packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=12)/Raw("x"*480)], iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:53")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=50)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_IPV6_UDP_ESP
===========================

1. validate a rule for RSS type of MAC_IPV6_UDP_ESP::

     testpmd> flow validate 0 ingress pattern eth / ipv6 / udp / esp / end actions rss types esp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_IPV6_UDP_ESP::

     testpmd> flow create 0 ingress pattern eth / ipv6 / udp / esp / end actions rss types esp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list

3. send matched packets

   * MAC_IPV6_UDP_ESP packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=12)/Raw("x"*480)], iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:53")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=11)/Raw("x"*480)], iface="ens786f0")

   check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_IPV4_AH
======================

1. validate a rule for RSS type of MAC_IPV4_AH::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / ah / end actions rss types ah end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_IPV4_AH::

     testpmd> flow create 0 ingress pattern eth / ipv4 / ah / end actions rss types ah end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_IPV4_AH packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=11)/Raw("x"*480)], iface="ens786f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=12)/Raw("x"*480)], iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:53")/IP(src="192.168.0.4",dst="192.168.0.8",proto=51)/AH(spi=11)/Raw("x"*480)], iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=11)/Raw("x"*480)], iface="ens786f0")

   check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_IPV6_AH
======================

1. validate a rule for RSS type of MAC_IPV6_AH::

     testpmd> flow validate 0 ingress pattern eth / ipv6 / ah / end actions rss types ah end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_IPV6_AH::

     testpmd> flow create 0 ingress pattern eth / ipv6 / ah / end actions rss types ah end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_IPV6_AH packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=11)/Raw("x"*480)], iface="ens786f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=12)/Raw("x"*480)], iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:53")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=51)/AH(spi=11)/Raw("x"*480)], iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=11)/Raw("x"*480)], iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_PPPOE_PAY
========================

Note: For PPPOE control packets, the hash input set should be
src mac address + PPP session id, so only add LCP/IPCP packets to the
L2_SRC_ONLY and SESSION_ID subcases in the case.

packets mismatched the pattern::

  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

Subcase 1: MAC_PPPOE_PAY_L2_SRC_ONLY
------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_PAY_L2_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / end actions rss types eth l2-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_PAY_L2_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / end actions rss types eth l2-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC], send a packet::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_LCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [Source MAC], send a packet::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=7)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [Source MAC], send a packet::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=7)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 2: MAC_PPPOE_PAY_L2_DST_ONLY
------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_PAY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / end actions rss types eth l2-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_PAY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / end actions rss types eth l2-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest MAC], send a packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/Raw("x"*80)],iface="ens786f0")

   check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 3: MAC_PPPOE_PAY_L2_SRC_ONLY_L2_DST_ONLY
------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / end actions rss types eth end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / end actions rss types eth end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source MAC][Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 4: MAC_PPPOE_PAY_SESSION_ID
===================================

1. validate a rule for RSS type of MAC_PPPOE_PAY_SESSION_ID::

     testpmd> flow validate 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_PAY_SESSION_ID::

     testpmd> flow create 0 ingress pattern eth / pppoes / end actions rss types pppoe end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_LCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [Session ID], send a packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [Session ID], send a packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 5: MAC_PPPOE_PAY_L2_SRC_ONLY_SESSION_ID
-----------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_PAY_L2_SRC_ONLY_SESSION_ID::

     testpmd> flow validate 0 ingress pattern eth / pppoes / end actions rss types eth l2-src-only pppoe end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_PAY_L2_SRC_ONLY_SESSION_ID::

     testpmd> flow create 0 ingress pattern eth / pppoes / end actions rss types eth l2-src-only pppoe end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_LCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     change the fields [Source MAC][Session ID], send a packet::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0xc021)/PPP_LCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     change the fields [Source MAC][Session ID], send a packet::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66",type=0x8864)/PPPoE(sessionid=7)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99",type=0x8864)/PPPoE(sessionid=3)/PPP(proto=0x8021)/PPP_IPCP()/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. send packets mismatched the rule, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_PPPOE_IPV4_PAY
=============================

packets mismatched the pattern::

  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=5)/Raw("x"*80)],iface="ens786f0")

Subcase 1: MAC_PPPOE_IPV4_PAY_L2_SRC_ONLY
-----------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_PAY_L2_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / end actions rss types eth l2-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_PAY_L2_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types eth l2-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=4)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV4_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=4)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5", frag=3)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 2: MAC_PPPOE_IPV4_PAY_L2_DST_ONLY
-----------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_PAY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / end actions rss types eth l2-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_PAY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types eth l2-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     change the field [Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=4)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV4_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=4)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5", frag=3)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 3: MAC_PPPOE_IPV4_PAY_L2_SRC_ONLY_L2_DST_ONLY
-----------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / end actions rss types eth end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types eth end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     change the fields [Source MAC][Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV4_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source MAC][Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5", frag=3)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 4: MAC_PPPOE_IPV4_PAY_L3_SRC_ONLY
-----------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_PAY_L3_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_PAY_L3_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     change the field [Source IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:54", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV4_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

     change the field [Source IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:54", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7", frag=3)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 5: MAC_PPPOE_IPV4_PAY_L3_DST_ONLY
-----------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_PAY_L3_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_PAY_L3_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     change the field [Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.3")/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.7", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV4_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.3", frag=5)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.7", dst="192.168.1.2", frag=3)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 6: MAC_PPPOE_IPV4_PAY_L3_SRC_ONLY_L3_DST_ONLY
-----------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_PAY_L3_SRC_ONLY_L3_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_PAY_L3_SRC_ONLY_L3_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55",dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.7")/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53",dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV4_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55",dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7", frag=5)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.7", frag=5)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53",dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=3)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_PPPOE_IPV4_UDP_PAY
=================================

packets mismatched the pattern::

  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

Subcase 1: MAC_PPPOE_IPV4_UDP_PAY_L2_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L2_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L2_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 2: MAC_PPPOE_IPV4_UDP_PAY_L2_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 3: MAC_PPPOE_IPV4_UDP_PAY_L2_SRC_ONLY_L2_DST_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types eth end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types eth end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source MAC][Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 4: MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 5: MAC_PPPOE_IPV4_UDP_PAY_L3_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 6: MAC_PPPOE_IPV4_UDP_PAY_L4_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=9,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.7")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 7: MAC_PPPOE_IPV4_UDP_PAY_L4_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.7")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 8: MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY_L4_SRC_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.9")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 9: MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY_L4_DST_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 10: MAC_PPPOE_IPV4_UDP_PAY_L3_DST_ONLY_L4_SRC_ONLY
----------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_DST_ONLY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_DST_ONLY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Dest IP][Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 11: MAC_PPPOE_IPV4_UDP_PAY_L3_DST_ONLY_L4_DST_ONLY
----------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_DST_ONLY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_L3_DST_ONLY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Dest IP][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.3")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 12: MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY_L3_DST_ONLY_L4_SRC_ONLY_L4_DST_ONLY
----------------------------------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest IP][Source Port][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.7")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_PPPOE_IPV4_TCP_PAY
=================================

packets mismatched the pattern::

  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

Subcase 1: MAC_PPPOE_IPV4_TCP_PAY_L2_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L2_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L2_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 2: MAC_PPPOE_IPV4_TCP_PAY_L2_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types eth l2-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types eth l2-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 3: MAC_PPPOE_IPV4_TCP_PAY_L2_SRC_ONLY_L2_DST_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types eth end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types eth end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source MAC][Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 4: MAC_PPPOE_IPV4_TCP_PAY_L3_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 5: MAC_PPPOE_IPV4_TCP_PAY_L3_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.3")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 6: MAC_PPPOE_IPV4_TCP_PAY_L4_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.7")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 7: MAC_PPPOE_IPV4_TCP_PAY_L4_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=19)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.7")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 8: MAC_PPPOE_IPV4_TCP_PAY_L3_SRC_ONLY_L4_SRC_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_SRC_ONLY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_SRC_ONLY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.9")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 9: MAC_PPPOE_IPV4_TCP_PAY_L3_SRC_ONLY_L4_DST_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_SRC_ONLY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_SRC_ONLY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 10: MAC_PPPOE_IPV4_TCP_PAY_L3_DST_ONLY_L4_SRC_ONLY
----------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_DST_ONLY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_DST_ONLY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Dest IP][Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=9,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=9,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 11: MAC_PPPOE_IPV4_TCP_PAY_L3_DST_ONLY_L4_DST_ONLY
----------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_DST_ONLY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_L3_DST_ONLY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Dest IP][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=90)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/TCP(sport=25,dport=90)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 12: MAC_PPPOE_IPV4_TCP_PAY_L3_SRC_ONLY_L3_DST_ONLY_L4_SRC_ONLY_L4_DST_ONLY
----------------------------------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest IP][Source Port][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.5")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_PPPOE_IPV6_PAY
=============================

packets mismatched the pattern::

  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

Subcase 1: MAC_PPPOE_IPV6_PAY_L2_SRC_ONLY
-----------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_PAY_L2_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / end actions rss types eth l2-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_PAY_L2_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types eth l2-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV6_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 2: MAC_PPPOE_IPV6_PAY_L2_DST_ONLY
-----------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_PAY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / end actions rss types eth l2-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_PAY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types eth l2-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     change the field [Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV6_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     change the field [Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 3: MAC_PPPOE_IPV6_PAY_L2_SRC_ONLY_L2_DST_ONLY
-----------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / end actions rss types eth end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types eth end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC][Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV6_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC][Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 4: MAC_PPPOE_IPV6_PAY_L3_SRC_ONLY
-----------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_PAY_L3_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_PAY_L3_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     change the field [Source IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:54", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV6_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     change the field [Source IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:54", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 5: MAC_PPPOE_IPV6_PAY_L3_DST_ONLY
-----------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_PAY_L3_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_PAY_L3_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     change the field [Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV6_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     change the field [Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 6: MAC_PPPOE_IPV6_PAY_L3_SRC_ONLY_L3_DST_ONLY
-----------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_PAY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_PAY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

   * MAC_PPPOE_IPV6_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_PPPOE_IPV6_UDP_PAY
=================================

packets mismatched the pattern::

  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

Subcase 1: MAC_PPPOE_IPV6_UDP_PAY_L2_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L2_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L2_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 2: MAC_PPPOE_IPV6_UDP_PAY_L2_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 3: MAC_PPPOE_IPV6_UDP_PAY_L2_SRC_ONLY_L2_DST_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types eth end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types eth end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source MAC][Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 4: MAC_PPPOE_IPV6_UDP_PAY_L3_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 5: MAC_PPPOE_IPV6_UDP_PAY_L3_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 6: MAC_PPPOE_IPV6_UDP_PAY_L4_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L4_SRC_ONLY

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 7: MAC_PPPOE_IPV6_UDP_PAY_L4_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 8: MAC_PPPOE_IPV6_UDP_PAY_L3_SRC_ONLY_L4_SRC_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_SRC_ONLY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_SRC_ONLY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 9: MAC_PPPOE_IPV6_UDP_PAY_L3_SRC_ONLY_L4_DST_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_SRC_ONLY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_SRC_ONLY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 10: MAC_PPPOE_IPV6_UDP_PAY_L3_DST_ONLY_L4_SRC_ONLY
----------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_DST_ONLY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_DST_ONLY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Dest IP][Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

   check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 11: MAC_PPPOE_IPV6_UDP_PAY_L3_DST_ONLY_L4_DST_ONLY
----------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_DST_ONLY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_L3_DST_ONLY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Dest IP][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 12: MAC_PPPOE_IPV6_UDP_PAY_L3_SRC_ONLY_L3_DST_ONLY_L4_SRC_ONLY_L4_DST_ONLY
----------------------------------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest IP][Source Port][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_PPPOE_IPV6_TCP_PAY
=================================

packets mismatched the pattern::

  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
  sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

Subcase 1: MAC_PPPOE_IPV6_TCP_PAY_L2_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L2_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L2_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types eth l2-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 2: MAC_PPPOE_IPV6_TCP_PAY_L2_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types eth l2-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types eth l2-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 3: MAC_PPPOE_IPV6_TCP_PAY_L2_SRC_ONLY_L2_DST_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types eth end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types eth end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source MAC][Dest MAC], send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 4: MAC_PPPOE_IPV6_TCP_PAY_L3_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 5: MAC_PPPOE_IPV6_TCP_PAY_L3_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest IP], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 6: MAC_PPPOE_IPV6_TCP_PAY_L4_SRC_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 7: MAC_PPPOE_IPV6_TCP_PAY_L4_DST_ONLY
---------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the field [Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 8: MAC_PPPOE_IPV6_TCP_PAY_L3_SRC_ONLY_L4_SRC_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_SRC_ONLY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_SRC_ONLY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 9: MAC_PPPOE_IPV6_TCP_PAY_L3_SRC_ONLY_L4_DST_ONLY
---------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_SRC_ONLY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_SRC_ONLY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 10: MAC_PPPOE_IPV6_TCP_PAY_L3_DST_ONLY_L4_SRC_ONLY
----------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_DST_ONLY_L4_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_DST_ONLY_L4_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Dest IP][Source Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 11: MAC_PPPOE_IPV6_TCP_PAY_L3_DST_ONLY_L4_DST_ONLY
----------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_DST_ONLY_L4_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_L3_DST_ONLY_L4_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Dest IP][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Subcase 12: MAC_PPPOE_IPV6_TCP_PAY_L3_SRC_ONLY_L3_DST_ONLY_L4_SRC_ONLY_L4_DST_ONLY
----------------------------------------------------------------------------------

1. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     change the fields [Source IP][Dest IP][Source Port][Dest Port], send packets::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/TCP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern, check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV4_PAY
============================

1. validate a rule for RSS type of MAC_VLAN_IPV4_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv4 / end actions rss types c-vlan end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV4_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv4 / end actions rss types c-vlan end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV4_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

  check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV4_UDP_PAY
================================

1. validate a rule for RSS type of MAC_VLAN_IPV4_UDP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv4 / udp / end actions rss types c-vlan end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV4_UDP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv4 / udp / end actions rss types c-vlan end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV4_UDP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/UDP(sport=19,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the hash values of the packets not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV4_TCP_PAY
================================

1. validate a rule for RSS type of MAC_VLAN_IPV4_TCP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv4 / tcp / end actions rss types c-vlan end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV4_TCP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv4 / tcp / end actions rss types c-vlan end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV4_TCP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/TCP(sport=19,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the hash values of the packets not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV4_SCTP_PAY
=================================

1. validate a rule for RSS type of MAC_VLAN_IPV4_SCTP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv4 / sctp / end actions rss types c-vlan end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV4_SCTP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv4 / sctp / end actions rss types c-vlan end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV4_SCTP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.5")/SCTP(sport=19,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the hash values of the packets not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV6_PAY
============================

1. validate a rule for RSS type of MAC_VLAN_IPV6_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv6 / end actions rss types c-vlan end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV6_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv6 / end actions rss types c-vlan end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV6_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("y" * 80)],iface="ens786f0",count=1)

   check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

  check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV6_UDP_PAY
================================

1. validate a rule for RSS type of MAC_VLAN_IPV6_UDP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv6 / udp / end actions rss types c-vlan end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV6_UDP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv6 / udp / end actions rss types c-vlan end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV6_UDP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

  check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV6_TCP_PAY
================================

1. validate a rule for RSS type of MAC_VLAN_IPV6_TCP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv6 / tcp / end actions rss types c-vlan end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV6_TCP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv6 / tcp / end actions rss types c-vlan end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV6_TCP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

  check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV6_SCTP_PAY
=================================

1. validate a rule for RSS type of MAC_VLAN_IPV6_SCTP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv6 / sctp / end actions rss types c-vlan end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV6_SCTP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv6 / sctp / end actions rss types c-vlan end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV6_SCTP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/SCTP(sport=25,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. send packets mismatched the pattern::

     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

  check the hash values not exist.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values the packets are not exist.

Test case: MAC_VLAN_PPPOE_PAY (not supported in 20.08)
======================================================

Subcase 1: MAC_VLAN_PPPOE_PAY_L2_SRC_ONLY
-----------------------------------------

1. validate a rule for RSS type of MAC_VLAN_PPPOE_PAY_L2_SRC_ONLY::

     testpmd> flow validate 0 ingress pattern eth / vlan / pppoes / end actions rss types eth l2-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_PPPOE_PAY_L2_SRC_ONLY::

     testpmd> flow create 0 ingress pattern eth / vlan / pppoes / end actions rss types eth l2-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send a MAC_VLAN_PPPOE_PAY_L2_SRC_ONLY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

   get the hash value
   change the field [Source MAC], send a packet::

     sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

   get the hash value
   check the hash value is different from the first packet.
   change other fields, send packets::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=7)/Raw("x"*80)],iface="ens786f0")

   check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the MAC_VLAN_PPPOE_PAY_L2_SRC_ONLY packet, and change the field [Source MAC],
   send the packet, check the hash values of the packets are not exist.

Subcase 2: MAC_VLAN_PPPOE_PAY_L2_DST_ONLY
-----------------------------------------

1. validate a rule for RSS type of MAC_VLAN_PPPOE_PAY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / vlan / pppoes / end actions rss types eth l2-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_PPPOE_PAY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / vlan / pppoes / end actions rss types eth l2-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send a MAC_VLAN_PPPOE_PAY_L2_DST_ONLY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

   get the hash value
   change the field [Dest MAC], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

   get the hash value
   check the hash value is different from the first packet.
   change other fields, send packets::

     sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=7)/Raw("x"*80)],iface="ens786f0")

   check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the MAC_VLAN_PPPOE_PAY_L2_DST_ONLY packet, and change the field [Dest MAC],
   send the packet, check the hash values of the packets are not exist.

Subcase 3: MAC_VLAN_PPPOE_PAY_L2_SRC_ONLY_L2_DST_ONLY
-----------------------------------------------------

1. validate a rule for RSS type of MAC_VLAN_PPPOE_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow validate 0 ingress pattern eth / vlan / pppoes / end actions rss types eth l2-src-only l2-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_PPPOE_PAY_L2_SRC_ONLY_L2_DST_ONLY::

     testpmd> flow create 0 ingress pattern eth / vlan / pppoes / end actions rss types eth l2-src-only l2-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send a MAC_VLAN_PPPOE_PAY_L2_SRC_ONLY_L2_DST_ONLY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

   get the hash value
   change the fields [Source MAC][Dest MAC], send a packet::

     sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:99")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")

   get the hash value
   check the hash value is different from the first packet.
   change other fields, send packets::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=7)/Raw("x"*80)],iface="ens786f0")

   check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the MAC_VLAN_PPPOE_PAY_L2_SRC_ONLY_L2_DST_ONLY packet,
   and change the field [Source MAC][Dest MAC], send the packet,
   check the hash values of the packets are not exist.

Subcase 4: MAC_VLAN_PPPOE_PAY_C_VLAN
------------------------------------

1. validate a rule for RSS type of MAC_VLAN_PPPOE_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / pppoes / end actions rss types c-vlan end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_PPPOE_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / pppoes / end actions rss types c-vlan end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send a MAC_VLAN_PPPOE_PAY packet::

     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x" * 80)],iface="ens786f0",count=1)

   get the hash value
   change the field [VLAN ID], send packets::

     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x8864)/PPPoE(sessionid=3)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the hash values are different from the first packet.
   change other fields, send packets::

     sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=3)/Raw("x" * 80)],iface="ens786f0",count=1)
     sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x8864)/PPPoE(sessionid=7)/Raw("x" * 80)],iface="ens786f0",count=1)

   check the hash values are the same as as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the MAC_VLAN_PPPOE_PAY packet, and change the field
   [VLAN ID], send the packet, check the hash values are not
   changed.

Test case: MAC_PPPOE_IPV4_PAY_symmetric
=======================================

1. validate a rule for RSS type of MAC_PPPOE_IPV4_PAY_symmetric::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV4_PAY_symmetric::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV4_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55",dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     swap the values of [Source IP] and [Dest IP], send the packet::

       sendp([Ether(src="00:11:22:33:44:55",dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.

  * MAC_PPPOE_IPV4_FRAG packet::

      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")

    swap the values of [Source IP] and [Dest IP], send the packet::

      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1", frag=5)/Raw("x"*80)],iface="ens786f0")

    check the hash value is not changed.

4. send packets mismatched the rule, and swap the [Source IP] and [Dest IP]

   * MAC_PPPOE_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_PPPOE_IPV6_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_IPV4_PAY packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21",dst="192.168.0.20")/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_IPV4_FRAG packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=5)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21",dst="192.168.0.20", frag=5)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   repeat step 3, check the hash values not exist.

Test case: MAC_PPPOE_IPV4_UDP_PAY_symmetric
===========================================

1. turn on default RSS configure to make mismatched packets have hash values::

     testpmd> port config all rss all

2. validate a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_symmetric::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

3. create a rule for RSS type of MAC_PPPOE_IPV4_UDP_PAY_symmetric::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send matched packets

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     swap the values of [Source IP] and [Dest IP], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.
     swap the values of [Source Port] and [Dest Port], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.
     swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.

5. send packets mismatched the rule, and swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port]

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/TCP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=23,dport=19)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

    * MAC_PPPOE_IPV4_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_IPV4_UDP_PAY packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21",dst="192.168.0.20")/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

6. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   repeat step 4, swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port],
   check the hash value is changed.

Test case: MAC_PPPOE_IPV4_TCP_PAY_symmetric
===========================================

1. turn on default RSS configure to make mismatched packets have hash values::

     testpmd> port config all rss all

2. validate a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_symmetric::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

3. create a rule for RSS type of MAC_PPPOE_IPV4_TCP_PAY_symmetric::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send matched packets

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     swap the values of [Source IP] and [Dest IP], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.
     swap the values of [Source Port] and [Dest Port], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.
     swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/TCP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.

5. send packets mismatched the rule, and swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port]

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

    * MAC_PPPOE_IPV4_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_IPV4_TCP_PAY packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.21",dst="192.168.0.20")/TCP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

6. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   repeat step 3, swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port],
   check the hash value is changed.

Test case: MAC_PPPOE_IPV6_PAY_symmetric
=======================================

1. validate a rule for RSS type of MAC_PPPOE_IPV6_PAY_symmetric::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_PPPOE_IPV6_PAY_symmetric::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_PPPOE_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")

     swap the values of [Source IP] and [Dest IP], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.

   * MAC_PPPOE_IPV6_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     swap the values of [Source IP] and [Dest IP], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.

4. send packets mismatched the rule, and swap the values of [Source IP] and [Dest IP]

   * MAC_PPPOE_IPV4_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_PPPOE_IPV4_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2", frag=5)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1", frag=5)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_IPV6_FRAG packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/IPv6ExtHdrFragment()/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

5. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   repeat step 3, check the hash values not exist.

Test case: MAC_PPPOE_IPV6_UDP_PAY_symmetric
===========================================

1. turn on default RSS configure to make mismatched packets have hash values::

     testpmd> port config all rss all

2. validate a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_symmetric::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

3. create a rule for RSS type of MAC_PPPOE_IPV6_UDP_PAY_symmetric::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send matched packets

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     swap the values of [Source IP] and [Dest IP], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.
     swap the values of [Source Port] and [Dest Port], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.
     swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.

5. send packets mismatched the rule, and swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port]

   * MAC_PPPOE_IPV4_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_PPPOE_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

6. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   repeat step 3, swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port],
   check the hash values are changed.

Test case: MAC_PPPOE_IPV6_TCP_PAY_symmetric
===========================================

1. turn on default RSS configure to make mismatched packets have hash values::

     testpmd> port config all rss all

2. validate a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_symmetric::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

3. create a rule for RSS type of MAC_PPPOE_IPV6_TCP_PAY_symmetric::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send matched packets

   * MAC_PPPOE_IPV6_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     swap the values of [Source IP] and [Dest IP], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.
     swap the values of [Source Port] and [Dest Port], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.
     swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port], send the packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash value is not changed.

5. send packets mismatched the rule, and swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port]

   * MAC_PPPOE_IPV4_TCP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_PPPOE_IPV6_UDP_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_PPPOE_IPV6_PAY packet::

       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")
       sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are different.

   * MAC_IPV6_TCP_PAY packet::

      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=23,dport=25)/Raw("x"*80)],iface="ens786f0")

    check the hash values of the two packets are different.

6. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   repeat step 3, swap the values of [Source IP] and [Dest IP], [Source Port] and [Dest Port],
   check the hash values are changed.

Test case: simple_xor
=====================

1. validate a simple_xor rule::

     testpmd> flow validate 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a simple_xor rule::

     testpmd> flow create 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send packets, and swap the values of [Source IP] and [Dest IP]

   * MAC_PPPOE_IPV4_PAY packet::

      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/Raw("x"*80)],iface="ens786f0")
      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

   check the hash values of the two packets are the same.

   * MAC_PPPOE_IPV4_UDP_PAY packet::

      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash values of the two packets are the same.

   * MAC_PPPOE_IPV4_TCP_PAY packet::

      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.2", dst="192.168.1.1")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash values of the two packets are the same.

   * MAC_PPPOE_IPV6_PAY packet::

      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x"*80)],iface="ens786f0")
      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are the same.

   * MAC_PPPOE_IPV6_UDP_PAY packet::

      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

     check the hash values of the two packets are the same.

   * MAC_PPPOE_IPV6_TCP_PAY packet::

      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
      sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0057)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2022", dst="CDCD:910A:2222:5498:8475:1111:3900:1536")/TCP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash values of the two packets are the same.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   repeat step 3, check the hash values are changed.

Test Case: multirules test
==========================

Subcase 1: two rules with same pattern but different hash input set, not hit default profile
--------------------------------------------------------------------------------------------

1. create a MAC_PPPOE_IPV4_UDP_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_PPPOE_IPV4_UDP_PAY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash value is different from the first packet.

3. create a rule with same pattern but different hash input set::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_PPPOE_IPV4_UDP_PAY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash value is the same as the first packet.
   change the field [Dest IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash value is different from the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   send a MAC_PPPOE_IPV4_UDP_PAY packet, hit default pppoe_ipv4 profile::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   change the fields [Source IP][Dest IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash values are different from the first packet.
   destroy the rule 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule 0 not exists in the list.
   send a MAC_PPPOE_IPV4_UDP_PAY packet, hit default pppoe_ipv4 profile::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   change the fields [Source IP][Dest IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")
     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.7")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash values are different from the first packet.

Subcase 2: two rules with same pattern but different hash input set, hit default profile
----------------------------------------------------------------------------------------

1. create a MAC_PPPOE_IPV4_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_PPPOE_IPV4_PAY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

   check the hash value is different from the first packet.
   change the field [Dest IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.5")/Raw("x"*80)],iface="ens786f0")

   check the hash value is the same as the first packet.

3. create a rule with same pattern but different hash input set::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_PPPOE_IPV4_PAY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

   check the hash value is the same as the first packet.
   change the field [Dest IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.7")/Raw("x"*80)],iface="ens786f0")

   check the hash value is different from the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   send the MAC_PPPOE_IPV4_PAY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x"*80)],iface="ens786f0")

   check the hash value not exists.
   destroy the rule 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule 0 not exists in the list.
   send the MAC_PPPOE_IPV4_PAY packet, check the hash value not exists.

Subcase 3: two rules, scope smaller created first, and the larger one created later
-----------------------------------------------------------------------------------

1. create a MAC_PPPOE_IPV4_UDP_PAY_L4_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_PPPOE_IPV4_UDP_PAY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   change the field [Source Port], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

   check the hash value is the same as the first packet.

3. create a MAC_PPPOE_IPV4_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_PPPOE_IPV4_UDP_PAY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.5")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

   check the hash value is the same as the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   repeat step 2, get the same result.
   destroy the rule 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   send a MAC_PPPOE_IPV4_UDP_PAY packet, check the hash values not exists.

Subcase 4: two rules, scope larger created first, and the smaller one created later
-----------------------------------------------------------------------------------

1. create a MAC_PPPOE_IPV4_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_PPPOE_IPV4_UDP_PAY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   change the field [Source IP], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.5")/UDP(sport=19,dport=99)/Raw("x"*80)],iface="ens786f0")

   check the hash value is the same as the first packet.

3. create a MAC_PPPOE_IPV4_UDP_PAY_L4_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_PPPOE_IPV4_UDP_PAY packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="ens786f0")

   change the field [Source Port], send a packet::

     sendp([Ether(src="00:11:22:33:44:55", dst="10:22:33:44:55:66")/PPPoE(sessionid=3)/PPP(proto=0x0021)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=19,dport=23)/Raw("x"*80)],iface="ens786f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(src="00:11:22:33:44:53", dst="10:22:33:44:55:99")/PPPoE(sessionid=7)/PPP(proto=0x0021)/IP(src="192.168.1.3", dst="192.168.1.5")/UDP(sport=25,dport=99)/Raw("x"*80)],iface="ens786f0")

   check the hash value is the same as the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   repeat step 2, hit pppoe_ipv4 profile, get the same result.
   destroy the rule 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   send a MAC_PPPOE_IPV4_UDP_PAY packet, check the hash values not exists.

Test case: negative cases
=========================

Subcase 1: wrong hash input set
-------------------------------

1. validate a rule with wrong input set::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / end actions rss types l2-src-only l2-dst-only end key_len 0 queues end / end

   get the error message::

     Invalid input set: Invalid argument

   create a rule with wrong hash input set::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / end actions rss types l2-src-only l2-dst-only end key_len 0 queues end / end

   Failed to create flow, report error message::

     Invalid input set: Invalid argument

2. validate a rule with wrong hash type::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end

   get the error message::

     Invalid input set: Invalid argument

   create a rule with wrong hash type::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end

   Failed to create flow, report error message::

     Invalid input set: Invalid argument

3. validate a rule with wrong symmetric hash input set::

     testpmd> flow validate 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp l3-src-only end key_len 0 queues end / end

   get the error message::

     Invalid input set: Invalid argument

   create a rule with wrong symmetric hash input set::

     testpmd> flow create 0 ingress pattern eth / pppoes / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp l3-src-only end key_len 0 queues end / end

   Failed to create flow, report error message::

     Invalid input set: Invalid argument

4. check the rule list::

     testpmd> flow list 0

  there is no listed.

Subcase 2: duplicated rules (not supported in 20.08)
----------------------------------------------------

1. create a  PFCP rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end

   the rule is created successfully.

2. create the same rule again, Failed to create flow, report message::

  Add rule failed.: Operation not permitted

3. check only the first rule exists in the list.

Subcase 3: void action
----------------------

1. validate a rule with void action::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / pfcp / end actions end

   get the error message::

     NULL action.: Invalid argument

   create a rule with void action::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions end

   Failed to create flow, report message::

     NULL action.: Invalid argument

2. check the rule list::

     testpmd> flow list 0

   there is no rule listed.

Subcase 4: delete a non-existing rule
-------------------------------------

1. show the rule list of port 0::

     testpmd> flow list 0

   There is no rule listed.

2. destroy rule 0 of port 0::

     testpmd> flow destroy 0 rule 0

   There is no error message reported.

3. flush rules of port 0::

     testpmd> flow flush 0

   There is no error message reported.

Subcase 5: unsupported pattern with OS default package
------------------------------------------------------

1. load os default package and launch testpmd as step 3-5 in Prerequisites.

2. validate unsupported patterns in OS default package::

     testpmd> flow validate 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end
     testpmd> flow validate 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end
     testpmd> flow validate 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end
     testpmd> flow validate 0 ingress pattern eth / ipv4 / ah / end actions rss types ah end key_len 0 queues end / end

   get the error message::

     Invalid input pattern: Invalid argument

3. create unsupported patterns in OS default package::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end
     testpmd> flow create 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end
     testpmd> flow create 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end
     testpmd> flow create 0 ingress pattern eth / ipv4 / ah / end actions rss types ah end key_len 0 queues end / end

4. check the rule list::

     testpmd> flow list 0

   there is no rule listed.

Subcase 6: invalid port
-----------------------

1. create a rule with invalid port::

     testpmd> flow create 1 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end

   Failed to create flow, report message::

    No such device: No such device

2. check the rule list on port 0::

     testpmd> flow list 0

   there is no rule listed.
   check on port 1::

     testpmd> flow list 1

   get the error message::

     Invalid port 1
