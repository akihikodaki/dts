.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2020 Intel Corporation

================================================
ICE IAVF: Advanced RSS FOR VLAN/ESP/AH/L2TP/PFCP
================================================

Description
===========

* Enable IAVF RSS for VLAN/ESP/AH/L2TP/PFCP packets.

Pattern and input set
---------------------
.. table::

    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | Hash function: toeplitz                                                                                                                      |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | Packet Type                   | Pattern                   | All the Input Set options in combination                                         |
    +===============================+===========================+==================================================================================+
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

Prerequisites
=============

1. Hardware:

   - Intel® Ethernet 810 Series: E810-XXVDA4/E810-CQ

2. Software:

   - dpdk: http://dpdk.org/git/dpdk
   - scapy: http://www.secdev.org/projects/scapy/

3. Copy comms package to /lib/firmware/intel/ice/ddp/ice.pkg,
   then load driver::

     rmmod ice
     insmod ice.ko

4. create a VF from a PF in DUT, set mac address for thi VF::

    echo 1 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ip link set enp24s0f0 vf 0 mac 00:11:22:33:44:55

5. bind the VF to dpdk driver in DUT::

    modprobe vfio-pci
    usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:18:01.0

.. note::

   The kernel must be >= 3.6+ and VT-d must be enabled in bios.

6. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0xff -n 4 -a 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd>set fwd rxonly
    testpmd>set verbose 1

7. on tester side, copy the layer python file to /root::

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

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="enp134s0f0")

     change the field [SEID], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=8805)/PFCP(Sfield=1, SEID=2)/Raw("x"*80)],iface="enp134s0f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.25",dst="192.168.0.23")/UDP(sport=23,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="enp134s0f0")

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the first packet in matched packets, check the hash value of this packet is different with before.

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

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="enp134s0f0")

     change the field [SEID], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=22,dport=8805)/PFCP(Sfield=1, SEID=2)/Raw("x"*80)],iface="enp134s0f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=8805)/PFCP(Sfield=1, SEID=1)/Raw("x"*80)],iface="enp134s0f0")

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the first packet in matched packets, check the hash value of this packet is different with before.

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

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5", proto=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="enp134s0f0")

     change the field [session_id], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.4", proto=115)/L2TP('\x00\x00\x00\x12')/Raw("x"*480)], iface="enp134s0f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.5",dst="192.168.0.7", proto=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="enp134s0f0")

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the first packet in matched packets, check the hash value of this packet is different with before.

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

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="enp134s0f0")

     change the field [session_id], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=115)/L2TP('\x00\x00\x00\x12')/Raw("x"*480)], iface="enp134s0f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=115)/L2TP('\x00\x00\x00\x11')/Raw("x"*480)], iface="enp134s0f0")

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the first packet in matched packets, check the hash value of this packet is different with before.

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

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=50)/ESP(spi=12)/Raw("x"*480)], iface="enp134s0f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4",dst="192.168.0.7",proto=50)/ESP(spi=11)/Raw("x"*480)], iface="enp134s0f0")

   check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the first packet in matched packets, check the hash value of this packet is different with before.

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

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=4500)/ESP(spi=12)/Raw("x"*480)], iface="enp134s0f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4",dst="192.168.0.7")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the first packet in matched packets, check the hash value of this packet is different with before.

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

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=50)/ESP(spi=12)/Raw("x"*480)], iface="enp134s0f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=50)/ESP(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the first packet in matched packets, check the hash value of this packet is different with before.

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

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(dport=4500)/ESP(spi=12)/Raw("x"*480)], iface="enp134s0f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(dport=4500)/ESP(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the first packet in matched packets, check the hash value of this packet is different with before.

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

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5",proto=51)/AH(spi=12)/Raw("x"*480)], iface="enp134s0f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4",dst="192.168.0.8",proto=51)/AH(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the first packet in matched packets, check the hash value of this packet is different with before.

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

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     change the field [spi], send a packet::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022", nh=51)/AH(spi=12)/Raw("x"*480)], iface="enp134s0f0")

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(dst="00:11:22:33:44:55")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023", nh=51)/AH(spi=11)/Raw("x"*480)], iface="enp134s0f0")

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists in the list.
   send the first packet in matched packets, check the hash value of this packet is different with before.


Test case: MAC_VLAN_IPV4_PAY
============================
Subcase: MAC_VLAN_IPV4_VLAN
---------------------------

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

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="enp134s0f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the first packet in matched packets, check the hash value of this packet is different with before.

Subcase: MAC_VLAN_IPV4_L3DST
--------------------------------

1. validate a rule for RSS type of MAC_VLAN_IPV4_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV4_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV4_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [l3 dst address], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.3")/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash value is different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.2")/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV4_UDP_PAY
================================
Subcase: MAC_VLAN_IPV4_UDP_VLAN
-------------------------------

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

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/UDP(sport=19,dport=99)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are the same as as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the first packet in matched packets, check the hash value of this packet is different with before.

Subcase: MAC_VLAN_IPV4_UDP_L3SRC
--------------------------------

1. validate a rule for RSS type of MAC_VLAN_IPV4_UDP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv4 / udp / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV4_UDP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv4 / udp / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV4_UDP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [l3 src address], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.4")/UDP(sport=19,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Subcase: MAC_VLAN_IPV4_UDP_L4DST
--------------------------------

1. validate a rule for RSS type of MAC_VLAN_IPV4_UDP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV4_UDP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV4_UDP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [l4 dst address], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/UDP(sport=25,dport=24)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/UDP(sport=19,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV4_TCP_PAY
================================
Subcase: MAC_VLAN_IPV4_TCP_VLAN
-------------------------------

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

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.4")/TCP(sport=19,dport=99)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are the same as as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the first packet in matched packets, check the hash value of this packet is different with before.

Subcase: MAC_VLAN_IPV4_TCP_l3SRC_L4SRC
--------------------------------------

1. validate a rule for RSS type of MAC_VLAN_IPV4_TCP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV4_TCP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV4_TCP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [l3 src address and l4 sport], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.2")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=22,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.4")/TCP(sport=25,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV4_SCTP_PAY
=================================
Subcase: MAC_VLAN_IPV4_SCTP_VLAN
--------------------------------

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

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.5")/SCTP(sport=19,dport=99)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are the same as as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the first packet in matched packets, check the hash value of this packet is different with before.

Subcase: MAC_VLAN_IPV4_SCTP_ALL
-------------------------------

1. validate a rule for RSS type of MAC_VLAN_IPV4_SCTP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV4_SCTP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv4 / sctp / end actions rss types ipv4-sctp end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV4_SCTP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [ipv4-sctp], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.3", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.4")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=19,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=2,type=0x0800)/IP(src="192.168.1.1", dst="192.168.1.2")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV6_PAY
============================
Subcase: MAC_VLAN_IPV6_VLAN
-------------------------------

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

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="enp134s0f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("y" * 80)],iface="enp134s0f0",count=1)

   check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the first packet in matched packets, check the hash value of this packet is different with before.

Subcase: MAC_VLAN_IPV6_L3SRC
--------------------------------

1. validate a rule for RSS type of MAC_VLAN_IPV6_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV6_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV6_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [l3 src address], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/Raw("y" * 80)],iface="ens786f0",count=1)

   check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV6_UDP_PAY
================================
Subcase: MAC_VLAN_IPV6_UDP_VLAN
-------------------------------

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

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=23,dport=99)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the first packet in matched packets, check the hash value of this packet is different with before.

Subcase: MAC_VLAN_IPV6_UDP_L4SRC
--------------------------------

1. validate a rule for RSS type of MAC_VLAN_IPV6_UDP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV6_UDP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV6_UDP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [l4 src address], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/UDP(sport=19,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/UDP(sport=25,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV6_TCP_PAY
================================
Subcase: MAC_VLAN_IPV6_TCP_VLAN
-------------------------------

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

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=19,dport=99)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the first packet in matched packets, check the hash value of this packet is different with before.

Subcase: MAC_VLAN_IPV6_TCP_L3DST
--------------------------------

1. validate a rule for RSS type of MAC_VLAN_IPV6_TCP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV6_TCP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV6_TCP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [l3 dst address], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/TCP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/TCP(sport=19,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values of the packets are not exist.

Test case: MAC_VLAN_IPV6_SCTP_PAY
=================================
Subcase: MAC_VLAN_IPV6_SCTP_VLAN
--------------------------------

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

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     change the field [VLAN ID], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/SCTP(sport=25,dport=99)/Raw("x" * 80)],iface="enp134s0f0",count=1)

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the first packet in matched packets, check the hash value of this packet is different with before.

Subcase: MAC_VLAN_IPV6_SCTP_L3DST_L4DST
---------------------------------------

1. validate a rule for RSS type of MAC_VLAN_IPV6_SCTP_PAY::

     testpmd> flow validate 0 ingress pattern eth / vlan / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only l4-dst-only end key_len 0 queues end / end

   get the message::

     Flow rule validated

   check the flow list::

     testpmd> flow list 0

   check the rule not exists in the list.

2. create a rule for RSS type of MAC_VLAN_IPV6_SCTP_PAY::

     testpmd> flow create 0 ingress pattern eth / vlan / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only l4-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

3. send matched packets

   * MAC_VLAN_IPV6_SCTP_PAY packet::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     change the field [l3 dst address and l4 dport], send packets::

       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2023")/SCTP(sport=25,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)
       sendp([Ether(src="10:22:33:44:55:66", dst="00:11:22:33:44:55",type=0x8100)/Dot1Q(vlan=1,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1536", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=25,dport=99)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are different from the first packet.
     change other fields, send packets::

       sendp([Ether(src="10:22:33:44:55:99", dst="00:11:22:33:44:53",type=0x8100)/Dot1Q(vlan=2,type=0x86dd)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1537", dst="CDCD:910A:2222:5498:8475:1111:3900:2022")/SCTP(sport=19,dport=23)/Raw("x" * 80)],iface="ens786f0",count=1)

     check the hash values are the same as the first packet.

4. destroy the rule::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule not exists.
   send the matched packets, check the hash values the packets are not exist.

Test case: negative cases
=========================

Subcase 1: not support pattern and input set
--------------------------------------------

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

Subcase 2: void action
----------------------
1. create a rule with void action::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions end

   Failed to create flow, report message::

     NULL action.: Invalid argument

2. check the rule list::

     testpmd> flow list 0

   there is no rule listed.

Subcase 3: delete a non-existing rule
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

Subcase 4: unsupported pattern with OS default package
------------------------------------------------------

1. load OS default package and launch testpmd as step 3-5 in Prerequisites.

2. create unsupported patterns in OS default package::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end
     testpmd> flow create 0 ingress pattern eth / ipv4 / l2tpv3oip / end actions rss types l2tpv3 end key_len 0 queues end / end
     testpmd> flow create 0 ingress pattern eth / ipv4 / esp / end actions rss types esp end key_len 0 queues end / end
     testpmd> flow create 0 ingress pattern eth / ipv4 / ah / end actions rss types ah end key_len 0 queues end / end

3. check the rule list::

     testpmd> flow list 0

   there is no rule listed.

Subcase 5: invalid port
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

