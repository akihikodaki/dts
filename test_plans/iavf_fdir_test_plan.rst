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

======================================
CVL:advanced iavf with FDIR capability
======================================

Support flow director to steering packets to queue/queue group in iavf
Enable fdir filter for IPv4/IPv6 + TCP/UDP/SCTP  (OS default package)
Enable fdir filter for GTP (comm #1 package)
Enable fdir filter for L2 Ethertype (comm #1 package)
Enable fdir filter for PFCP (comm #1 package)
Enable fdir filter for IPv4/IPv6 + GRE + IPV4/IPV6 + TCP/UDP

Description
===========

Pattern and input set
---------------------

    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |    Packet Type               |        Pattern               |            Input Set                                              |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | IPv4/IPv6 + TCP/UDP/SCTP     |MAC_IPV4_PAY                  | [Source IP], [Dest IP], [IP protocol], [TTL], [DSCP]              |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_UDP                  | [Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port] |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_TCP                  | [Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port] |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_SCTP                 | [Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port] |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_PAY                  | [Source IP], [Dest IP], [IP protocol], [TTL], [TC]                |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_UDP                  | [Source IP], [Dest IP], [TTL], [TC], [Source Port], [Dest Port]   |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_TCP                  | [Source IP], [Dest IP], [TTL], [TC], [Source Port], [Dest Port]   |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_SCTP                 | [Source IP], [Dest IP], [TTL], [TC], [Source Port], [Dest Port]   |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | L2 Ethertype                 |L2 Ethertype                  | [Ethertype]                                                       |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | PFCP                         |MAC_IPV4_PFCP_NODE            | [Dest Port], [S-field]                                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_PFCP_SESSION         | [Dest Port], [S-field]                                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_PFCP_NODE            | [Dest Port], [S-field]                                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_PFCP_SESSION         | [Dest Port], [S-field]                                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | L2TPv3                       |MAC_IPV4_L2TPv3               | [Session ID]                                                      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_L2TPv3               | [Session ID]                                                      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | ESP                          |MAC_IPV4_ESP                  | [Source IP], [Dest IP], [SPI]                                     |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_ESP                  | [Source IP], [Dest IP], [SPI]                                     |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_AH                   | [SPI]                                                             |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_AH                   | [SPI]                                                             |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_NAT-T-ESP            | [Source IP], [Dest IP], [SPI]                                     |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_NAT-T-ESP            | [Source IP], [Dest IP], [SPI]                                     |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | IPv4 + GTP-U  outer          |MAC_IPV4_GTPU                 | outer:[Source IP], [Dest IP], [TEID]                              |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH              | outer:[Source IP], [Dest IP], [TEID], [QFI]                       |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | IPv6 + GTP-U  outer          |MAC_IPV6_GTPU                 | outer:[Source IPV6], [Dest IPV6], [TEID]                          |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_GTPU_EH              | outer:[Source IPV6], [Dest IPV6], [TEID], [QFI]                   |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | IPv4 + GTP-U + inner IPv4    |MAC_IPV4_GTPU_IPV4            | inner:[Source IP], [Dest IP]                                      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_IPV4_UDP        | inner:[Source IP], [Dest IP], [Source Port], [Dest Port]          |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_IPV4_TCP        | inner:[Source IP], [Dest IP], [Source Port], [Dest Port]          |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_IPV4         | inner:[Source IP], [Dest IP]                                      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_IPV4_UDP     | inner:[Source IP], [Dest IP], [Source Port], [Dest Port]          |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_IPV4_TCP     | inner:[Source IP], [Dest IP], [Source Port], [Dest Port]          |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_DL_IPV4      | inner:[Source IP], [Dest IP]                                      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_DL_IPV4_UDP  | inner:[Source IP], [Dest IP], [Source Port], [Dest Port]          |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_DL_IPV4_TCP  | inner:[Source IP], [Dest IP], [Source Port], [Dest Port]          |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_UL_IPV4      | inner:[Source IP], [Dest IP]                                      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_UL_IPV4_UDP  | inner:[Source IP], [Dest IP], [Source Port], [Dest Port]          |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_UL_IPV4_TCP  | inner:[Source IP], [Dest IP], [Source Port], [Dest Port]          |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | IPv4 + GTP-U + inner IPv6    |MAC_IPV4_GTPU_IPV6            | inner:[Source IPv6], [Dest IPv6]                                  |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_IPV6_UDP        | inner:[Source IPv6], [Dest IPv6], [Source Port], [Dest Port]      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_IPV6_TCP        | inner:[Source IPv6], [Dest IPv6], [Source Port], [Dest Port]      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_IPV6         | inner:[Source IPv6], [Dest IPv6]                                  |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_IPV6_UDP     | inner:[Source IPv6], [Dest IPv6], [Source Port], [Dest Port]      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_IPV6_TCP     | inner:[Source IPv6], [Dest IPv6], [Source Port], [Dest Port]      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_UL_IPV6      | inner:[Source IPv6], [Dest IPv6]                                  |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_UL_IPV6_UDP  | inner:[Source IPv6], [Dest IPv6], [Source Port], [Dest Port]      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_UL_IPV6_TCP  | inner:[Source IPv6], [Dest IPv6], [Source Port], [Dest Port]      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_UL_IPV6      | inner:[Source IPv6], [Dest IPv6]                                  |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_UL_IPV6_UDP  | inner:[Source IPv6], [Dest IPv6], [Source Port], [Dest Port]      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GTPU_EH_UL_IPV6_TCP  | inner:[Source IPv6], [Dest IPv6], [Source Port], [Dest Port]      |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | IPV4/IPV6+GRE+IPV4/IPV6      |MAC_IPV4_GRE_IPV4             | [Inner Source IP], [Inner Dest IP], [Inner DSCP]                  |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_GRE_IPV4             | [Inner Source IP], [Inner Dest IP], [Inner DSCP]                  |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GRE_IPV6             | [Inner Source IP], [Inner Dest IP], [Inner TC]                    |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_GRE_IPV6             | [Inner Source IP], [Inner Dest IP], [Inner TC]                    |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | IPV4/IPV6+GRE+IPV4/IPV6+TCP  |MAC_IPV4_GRE_IPV4_TCP         | [Inner Source IP], [Inner Dest IP], [Inner DSCP],                 |
    |                              |                              | [Inner Source Port], [Inner Dest Port]                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_GRE_IPV4_TCP         | [Inner Source IP], [Inner Dest IP], [Inner DSCP],                 |
    |                              |                              | [Inner Source Port], [Inner Dest Port]                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GRE_IPV6_TCP         | [Inner Source IP], [Inner Dest IP], [Inner TC],                   |
    |                              |                              | [Inner Source Port], [Inner Dest Port]                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_GRE_IPV6_TCP         | [Inner Source IP], [Inner Dest IP], [Inner TC],                   |
    |                              |                              | [Inner Source Port], [Inner Dest Port]                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    | IPV4/IPV6+GRE+IPV4/IPV6+UDP  |MAC_IPV4_GRE_IPV4_UDP         | [Inner Source IP], [Inner Dest IP], [Inner DSCP],                 |
    |                              |                              | [Inner Source Port], [Inner Dest Port]                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_GRE_IPV4_UDP         | [Inner Source IP], [Inner Dest IP], [Inner DSCP],                 |
    |                              |                              | [Inner Source Port], [Inner Dest Port]                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV4_GRE_IPV6_UDP         | [Inner Source IP], [Inner Dest IP], [Inner TC],                   |
    |                              |                              | [Inner Source Port], [Inner Dest Port]                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+
    |                              |MAC_IPV6_GRE_IPV6_UDP         | [Inner Source IP], [Inner Dest IP], [Inner TC],                   |
    |                              |                              | [Inner Source Port], [Inner Dest Port]                            |
    +------------------------------+------------------------------+-------------------------------------------------------------------+


Supported function type
-----------------------

    validate
    create
    destroy
    flush
    list

Supported action type
---------------------

    queue index
    drop
    rss queues
    passthru
    mark
    mark/rss


Prerequisites
=============

1. Hardware:
   columbiaville_25g/columbiaville_100g

2. Software:
   DPDK: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/intel/ice/ddp/ice.pkg
   Then reboot server, and compile DPDK

4. Generate 2 VFs on each PF and set mac address for each VF::

    echo 2 > /sys/bus/pci/devices/0000:86:00.0/sriov_numvfs
    echo 2 > /sys/bus/pci/devices/0000:86:00.1/sriov_numvfs
    ip link set enp134s0f0 vf 0 mac 00:11:22:33:44:55
    ip link set enp134s0f0 vf 1 mac 00:11:22:33:44:66
    ip link set enp134s0f1 vf 0 mac 00:11:22:33:44:77
    ip link set enp134s0f1 vf 1 mac 00:11:22:33:44:88

   0000:86:00.0 generate 0000:86:01.0 and 0000:86:01.1
   0000:86:00.1 generate 0000:86:11.0 and 0000:86:11.1
   define 86:01.0 as vf00, 86:01.1 as vf01, 86:11.0 as vf10, 86:11.1 as vf11.
   assign mac address of pf0 is 68:05:ca:a3:1a:60,
   assign mac address of pf1 is 68:05:ca:a3:1a:61.

5. Bind VFs to dpdk driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 86:01.0 86:01.1 86:11.0 86:11.1

5. Launch the app ``testpmd`` with the following arguments::

    ./testpmd -c 0xff -n 6 -a 86:01.0 -a 86:01.1 --file-prefix=vf -- -i --rxq=16 --txq=16
    testpmd> set fwd rxonly
    testpmd> set verbose 1

6. on tester side, copy the layer python file to /root::

    cp pfcp.py to /root

   then import layers when start scapy::

    >>> import sys
    >>> sys.path.append('/root')
    >>> from pfcp import PFCP
    >>> from scapy.contrib.gtp import *
    >>> from scapy.contrib.mpls import *


Default parameters
------------------

   VF00 MAC::

    [Dest MAC]: 00:11:22:33:44:55

   VF01 MAC::

    [Dest MAC]: 00:11:22:33:44:66

   VF10 MAC::

    [Dest MAC]: 00:11:22:33:44:77

   VF11 MAC::

    [Dest MAC]: 00:11:22:33:44:88

   outer/inner IPv4::

    [Source IP]: 192.168.0.20
    [Dest IP]: 192.168.0.21
    [IP protocol]: 255
    [TTL]: 2
    [DSCP]: 4

   outer/inner IPv6::

    [Source IPv6]: 2001::2
    [Dest IPv6]: CDCD:910A:2222:5498:8475:1111:3900:2020
    [IP protocol]: 0
    [TTL]: 2
    [TC]: 1

   UDP/TCP/SCTP::

    [Source Port]: 22
    [Dest Port]: 23

   GTP-U data packet::

    [TEID]: 0x12345678
    [QFI]: 0x34

   L2 Ethertype::

    [Ethertype]: 0x8863 0x8864 0x0806 0x8100 0x88f7

   PFCP::

    [Dest Port]: 8805
    [S-field]: 0/1


Send packets
------------

* MAC_IPV4_PAY

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=255, ttl=2, tos=4)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.1.21", proto=255, ttl=2, tos=4) / Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1, ttl=2, tos=4) / Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=3, tos=4) / Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=9) / Raw('x' * 80)],iface="enp134s0f1")

* MAC_IPV4_UDP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=21,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

* MAC_IPV4_TCP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=21,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

* MAC_IPV4_SCTP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=21,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4)/Raw('x' * 80)],iface="enp134s0f1")

* MAC_IPV6_PAY

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::1", nh=0, tc=1, hlim=2)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=2, tc=1, hlim=2)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=2, hlim=2)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=5)/("X"*480)], iface="enp134s0f1")

* MAC_IPV6_UDP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=21,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=24)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")

* MAC_IPV6_TCP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/TCP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=21,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=24)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")

* MAC_IPV6_SCTP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=21,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=24)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/("X"*480)], iface="enp134s0f1")

* MAC_IPV4_GTPU_EH

   matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP(frag=1)/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP()/UDP()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP()/TCP(sport=22,dport=23)/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP()/ICMP()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IPv6()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IPv6(nh=44)/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu9 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IPv6()/TCP(sport=22,dport=23)/Raw('x'*20)
    p_gtpu10 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IPv6()/ICMP()/Raw('x'*20)
    p_gtpu11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/Raw('x'*20)

   mismatched packets::

    p_gtpu12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP()/Raw('x'*20)
    p_gtpu13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x35)/IP()/Raw('x'*20)
    p_gtpu14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw('x'*20)

* MAC_IPV4_GTPU

   matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=1)/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/ICMP()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6(nh=44)/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu9 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu10 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/ICMP()/Raw('x'*20)
    p_gtpu11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/Raw('x'*20)

   mismatched packets::

    p_gtpu15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IP()/Raw('x'*20)

* MAC_IPV6_GTPU_EH

   matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(frag=1)/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/ICMP()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu9 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu10 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/ICMP()/Raw('x'*20)

   mismatched packets::

    p_gtpu11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw('x'*20)
    p_gtpu12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)
    p_gtpu13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/ICMP()/Raw('x'*20)
    p_gtpu14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP()/Raw('x'*20)
    p_gtpu15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw('x'*20)

* MAC_IPV6_GTPU

   matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=1)/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/ICMP()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu9 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu10 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/ICMP()/Raw('x'*20)

   mismatched packets::

    p_gtpu11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IP()/Raw('x'*20)
    p_gtpu12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP()/Raw('x'*20)
    p_gtpu13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw('x'*20)

* L2 Ethertype

   PPPoED packets::

    sendp([Ether(dst="00:11:22:33:44:55")/PPPoED()/PPP()/IP()/Raw('x' *80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55", type=0x8863)/IP()/Raw('x' * 80)],iface="enp134s0f1")

   PPPoE packets::

    sendp([Ether(dst="00:11:22:33:44:55")/PPPoE()/PPP(proto=0x0021)/IP()/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55", type=0x8864)/IP()/Raw('x' * 80)],iface="enp134s0f1")

   ARP packets::

    sendp([Ether(dst="00:11:22:33:44:55")/ARP(pdst="192.168.1.1")],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55", type=0x0806)/Raw('x' *80)],iface="enp134s0f1")

   EAPS packets::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8100)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)],iface="enp134s0f1")

   ieee1588 packet::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x88f7)/"\\x00\\x02"], iface="enp134s0f1")

* PFCP

   MAC_IPV4_PFCP_NODE::

    sendp(Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=22, dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")

   MAC_IPV4_PFCP_SESSION::

    sendp(Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=22, dport=8805)/PFCP(Sfield=1, SEID=123),iface="enp134s0f1")

   MAC_IPV6_PFCP_NODE::

    sendp(Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=22, dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")

   MAC_IPV6_PFCP_NODE::

    sendp(Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=22, dport=8805)/PFCP(Sfield=1, SEID=256),iface="enp134s0f1")

* MAC_IPV4_L2TPv3

   matched packets::

    sendp(Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.3', proto=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IP(src='192.168.1.3', proto=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480),iface="enp134s0f1")
   
   mismatched packets::
    
    sendp(Ether(dst='00:11:22:33:44:55')/IP(src='192.168.0.3', proto=115)/L2TP('\\x00\\x00\\x00\\x12')/Raw('x'*480),iface="enp134s0f1")

* MAC_IPV6_L2TPv3

   matched packets::

    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888',nh=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:9999',nh=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480),iface="enp134s0f1")
   
   mismatched packets::
    
    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src='1111:2222:3333:4444:5555:6666:7777:8888',nh=115)/L2TP('\\x00\\x00\\x00\\x12')/Raw('x'*480),iface="enp134s0f1")

* MAC_IPV4_ESP

   matched packets::

    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.0.20",dst="192.168.0.21",proto=50)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")

   mismatched packets::
    
    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.0.22",dst="192.168.0.21",proto=50)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.0.20",dst="192.168.0.11",proto=50)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.0.20",dst="192.168.0.21",proto=50)/ESP(spi=17)/Raw('x'*480),iface="enp134s0f1")

* MAC_IPV6_ESP

   matched packets::

    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="2001::1",dst="2001::2",nh=50)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")

   mismatched packets::
    
    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="2001::8",dst="2001::2",nh=50)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="2001::1",dst="2001::9",nh=50)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="2001::1",dst="2001::2",nh=50)/ESP(spi=17)/Raw('x'*480),iface="enp134s0f1")

* MAC_IPV4_AH

   matched packets::

    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.0.3",proto=51)/AH(spi=7)/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.1.3",proto=51)/AH(spi=7)/Raw('x'*480),iface="enp134s0f1")
   
   mismatched packets::
    
    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.0.3",proto=51)/AH(spi=17)/Raw('x'*480),iface="enp134s0f1")

* MAC_IPV6_AH

   matched packets::

    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",nh=51)/AH(spi=7)/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:9999",nh=51)/AH(spi=7)/Raw('x'*480),iface="enp134s0f1")
   
   mismatched packets::
    
    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",nh=51)/AH(spi=17)/Raw('x'*480),iface="enp134s0f1")

* MAC_IPV4_NAT-T-ESP

   matched packets::

    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")
   
   mismatched packets::
    
    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.0.22",dst="192.168.0.21")/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.0.20",dst="192.168.0.11")/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(dport=4500)/ESP(spi=17)/Raw('x'*480),iface="enp134s0f1")

* MAC_IPV6_NAT-T-ESP

   matched packets::

    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="2001::1",dst="2001::2")/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")
   
   mismatched packets::
    
    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="2001::8",dst="2001::2")/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="2001::1",dst="2001::9")/UDP(dport=4500)/ESP(spi=7)/Raw('x'*480),iface="enp134s0f1")
    sendp(Ether(dst='00:11:22:33:44:55')/IPv6(src="2001::1",dst="2001::2")/UDP(dport=4500)/ESP(spi=17)/Raw('x'*480),iface="enp134s0f1")

* MAC_IPV4_GTPU_IPV4

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21", frag=1)/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP()/Raw('x'*20)
    pkt4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/ICMP()/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.22", dst="192.168.0.23")/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP()/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/Raw('x'*20)

* MAC_IPV4_GTPU_IPV4_TCP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.22", dst="192.168.0.23")/TCP(sport=24, dport=25)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_IPV4_UDP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.22", dst="192.168.0.23")/UDP(sport=24, dport=25)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/UDP(sport=22, dport=23)/Raw('x'*20)

* MAC_IPV4_GTPU_EH_IPV4

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21", frag=1)/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP()/Raw('x'*20)
    pkt4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/ICMP()/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.22", dst="192.168.0.23")/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_IPV4_TCP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.22", dst="192.168.0.23")/TCP(sport=25, dport=24)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_IPV4_UDP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.22", dst="192.168.0.23")/UDP(sport=25, dport=24)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/UDP(sport=22, dport=23)/Raw('x'*20)

* MAC_IPV4_GTPU_EH_DL_IPV4

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21", frag=1)/Raw('x'*20)
    pkt4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP()/Raw('x'*20)
    pkt5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/ICMP()/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.22", dst="192.168.0.23")/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_DL_IPV4_TCP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.22", dst="192.168.0.23")/TCP(sport=25, dport=24)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_DL_IPV4_UDP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.22", dst="192.168.0.23")/UDP(sport=25, dport=24)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/UDP(sport=22, dport=23)/Raw('x'*20)

* MAC_IPV4_GTPU_EH_UL_IPV4

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21", frag=1)/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP()/Raw('x'*20)
    pkt4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/ICMP()/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.22", dst="192.168.0.23")/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/SCTP()/Raw('x'*20)
    pkt16 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/Raw('x'*20)
    pkt17 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_UL_IPV4_TCP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.22", dst="192.168.0.23")/TCP(sport=25, dport=24)/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/Raw('x'*20)
    pkt16 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt17 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_UL_IPV4_UDP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.22", dst="192.168.0.23")/UDP(sport=25, dport=24)/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/Raw('x'*20)
    pkt16 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
    pkt17 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/UDP(sport=22, dport=23)/Raw('x'*20)


* MAC_IPV4_GTPU_IPV6

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP()/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_IPV6_TCP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/TCP(sport=24, dport=25)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_IPV6_UDP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/UDP(sport=24, dport=25)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/UDP(sport=22, dport=23)/Raw('x'*20)

* MAC_IPV4_GTPU_EH_IPV6

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP()/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_IPV6_TCP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/TCP(sport=24, dport=25)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_IPV6_UDP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/UDP(sport=24, dport=25)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP(sport=22, dport=23)/Raw('x'*20)

* MAC_IPV4_GTPU_EH_DL_IPV6

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/Raw('x'*20)
    pkt5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)


   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_DL_IPV6_TCP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/TCP(sport=24, dport=25)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_DL_IPV6_UDP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/UDP(sport=24, dport=25)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/UDP(sport=22, dport=23)/Raw('x'*20)

* MAC_IPV4_GTPU_EH_UL_IPV6

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP()/Raw('x'*20)
    pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP()/Raw('x'*20)
    pkt16 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_UL_IPV6_TCP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/TCP(sport=24, dport=25)/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt16 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt17 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/Raw('x'*20)

* MAC_IPV4_GTPU_EH_UL_IPV6_UDP

   matched packets::

    pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)

   mismatched packets::

    pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::4", dst="CDCD:910A:2222:5498:8475:1111:3900:2024")/UDP(sport=24, dport=25)/Raw('x'*20)
    pkt14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
    pkt16 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
    pkt17 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/UDP(sport=22, dport=23)/Raw('x'*20)

* MAC_IPV4_GRE_IPV4

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=4)/Raw('x' * 80)],iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.22",dst="192.168.0.21", tos=4)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.23", tos=4)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=8)/Raw('x' * 80)],iface="enp134s0f1")

* MAC_IPV6_GRE_IPV4

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=4)/Raw('x' * 80)],iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP(src="192.168.0.22",dst="192.168.0.21", tos=4)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP(src="192.168.0.20",dst="192.168.0.23", tos=4)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=8)/Raw('x' * 80)],iface="enp134s0f1")

* MAC_IPV4_GRE_IPV6

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1)/Raw('x' * 80)],iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2", tc=1)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::3", tc=1)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=2)/Raw('x' * 80)],iface="enp134s0f1")

* MAC_IPV4_GRE_IPV4_TCP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.22",dst="192.168.0.21", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.23", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=8)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=4)/TCP(sport=21,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IP(src="192.168.0.20",dst="192.168.0.21", tos=4)/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")

* MAC_IPV4_GRE_IPV6_TCP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2", tc=1)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::3", tc=1)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=2))/TCP(sport=22,dport=23)Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1)/TCP(sport=21,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/GRE()/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1)/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")

Test case: flow validation
==========================

1. validate MAC_IPV4_PAY with queue index action::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end

   get the message without any error message::

    Flow rule validated

2. repeat step 1 with all patterns in pattern and input set table,
   get the same result.

3. repeat step 1-2 with action rss queues/drop/passthru/mark/mark+rss,
   get the same result.

4. repeate step 1-3 with combined use of actions::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark / end
    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 0 1 end / mark / end
    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark / end
    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark / rss / end

   get the message without any error message::

    Flow rule validated

5. check the flow list::

    testpmd> flow list 0

   there is no rule listed.

Test case: negative validation
==============================
Note: some of the error messages may be differernt.

1. only count action::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions count / end

   get the error message::

    Invalid input action: Invalid argument

2. void action::

    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions end

   Failed to create flow, report message::

    Emtpy action: Invalid argument

3. conflict action::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 2 3 end / rss / end

   get the message::

    Unsupported action combination: Invalid argument

4. invalid mark id::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / mark id 4294967296 / end

   get the message::

    Bad arguments

5. invalid input set::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tc is 4 / end actions queue index 1 / end

   get the message::

    Bad arguments

6. invalid queue index::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 16 / end

   get the message::

    Invalid input action: Invalid argument

7. invalid rss queues parameter

   Invalid number of queues::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end
    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 end / end
    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues end / end

   get the message::

    Invalid input action: Invalid argument

   Discontinuous queues::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end

   get the message::

    Discontinuous queue region: Invalid argument

   invalid rss queues index::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 15 16 end / end

   get the message::

    Invalid queue region indexes.: Invalid argument

8. Invalid value of input set::

    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x100 / end actions queue index 1 / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc qfi is 0x5 / end actions queue index 2 / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / end actions queue index 1 / end

   get the message::

    Bad arguments

9. unsupported pattern,validate GTPU rule with OS default package::

    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end

   get the message::

    Add filter rule failed.: Operation not permitted

10. invalid port::

      flow validate 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end

   get the message::

    No such device: No such device

11. check the flow list::

      testpmd> flow list 0

   there is no rule listed.

Test case: MAC_IPV4_PAY pattern
===============================

Subcase 1: MAC_IPV4_PAY queue index
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1 without FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 1 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 1 without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_PAY rss queues
----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 2 3 end / end

2. send matched packets, check the packets are distributed to queue 2 or 3 without without FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 2 or 3 without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not distributed to queue 2 or 3 without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_PAY passthru
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / end

2. send matched packets, check the packets are distributed by RSS without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID=0x0.
   check there is no rule listed.

Subcase 4: MAC_IPV4_PAY drop
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / end

2. send matched packets, check the packets are dropped
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_PAY mark+rss
--------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_PAY mark
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 7: MAC_IPV4_PAY protocal
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 1 / end actions queue index 1 / mark id 1 / end
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 17 / end actions passthru / mark id 3 / end

2. send matched packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1)/Raw('x' * 80)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=1)/Raw('x' * 80)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw('x' * 80)
    pkt4 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, ttl=2, tos=4)/UDP(sport=22,dport=23)/Raw('x' * 80)
    pkt5 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=17, ttl=2, tos=4)/Raw('x' * 80)
    pkt6 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=17, ttl=2, tos=4)/Raw('x' * 80)

   check the pkt1 and pkt2 are redirected to queue 1 with FDIR matched ID=0x1.
   check the pkt3-pkt6 are distributed by RSS with FDIR matched ID=0x3.
   send mismatched packets::

    pkt7 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", proto=1)/Raw('x' * 80)
    pkt8 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=6)/UDP(sport=22,dport=23)/Raw('x' * 80)
    pkt9 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)
    pkt10 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1)/TCP(sport=22,dport=23)/Raw('x' * 80)

   check the packets received have not FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets have not FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV4_UDP pattern
===============================

Subcase 1: MAC_IPV4_UDP queue index
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end

2. send matched packets, check the packets is distributed to queue 1 with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_UDP rss queues
----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 4294967294 / end

2. send matched packets, check the packets is distributed to queue 0-3 with FDIR matched ID=0xfffffffe.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_UDP passthru
--------------------------------

1. create filter rule with mark::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_UDP drop
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions drop / end

2. send matched packet, check the packet is dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packet is dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_UDP mark+rss
--------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark id 2 / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x2
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_UDP mark
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark id 1 / end

2. repeat the step 2-3 of in subcase 3,
   get the same result.

Test case: MAC_IPV4_TCP pattern
===============================

1. replace "udp" with "tcp" in all the subcases of MAC_IPV4_UDP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_UDP pattern.
3. get the same result.

Test case: MAC_IPV4_SCTP pattern
================================

1. replace "udp" with "sctp" in all the subcases of MAC_IPV4_UDP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_UDP pattern.
3. get the same result.


Test case: MAC_IPV6_PAY pattern
===============================

Subcase 1: MAC_IPV6_PAY queue index
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions queue index 15 / mark / end

2. send matched packets, check the packets is distributed to queue 15 with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV6_PAY rss queues
----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark / end

2. send matched packets, check the packets is distributed to queue 8-15 with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV6_PAY passthru
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions passthru / mark / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are destributed to the same queue without FDIR matched ID .
   check there is no rule listed.

Subcase 4: MAC_IPV6_PAY drop
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packet is dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV6_PAY mark+rss
--------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV6_PAY mark
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark / end

2. repeat the steps of passthru with mark part in subcase 3,
   get the same result.

Subcase 7: MAC_IPV6_PAY protocal
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 44 / end actions rss queues 5 6 end / mark id 0 / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 6 / end actions mark id 2 / rss / end

2. send matched packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=44, tc=1, hlim=2)/("X"*480)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment(100)/("X"*480)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=44)/TCP(sport=22,dport=23)/("X"*480)
    pkt4 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment(100)/TCP(sport=22,dport=23)/("X"*480)
    pkt5 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/("X"*480)
    pkt6 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)

   check pkt1-pkt4 are redirected to queue 5 or queue 6 with FDIR matched ID=0x0.
   check pkt5 and pkt6 are distributed by RSS with FDIR matched ID=0x2.
   send mismatched packets::

    pkt7 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", nh=44)/("X"*480)
    pkt8 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)
    pkt9 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=17)/TCP(sport=22,dport=23)/("X"*480)

   check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   check there is no rule listed.

Test case: MAC_IPV6_UDP pattern
===============================

Subcase 1: MAC_IPV6_UDP queue index
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end

2. send matched packets, check the packets is distributed to queue 1 with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV6_UDP rss queues
----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss queues 2 3 end / mark / end

2. send matched packets, check the packets is distributed to queue 2 or queue 3 with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV6_UDP passthru
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are destributed to the same queue without FDIR matched ID .
   check there is no rule listed.

Subcase 4: MAC_IPV6_UDP drop
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packet is dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV6_UDP mark+rss
--------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV6_UDP mark
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark id 0 / end

2. repeat the steps of passthru with mark part in subcase 3,
   get the same result.


Test case: MAC_IPV6_TCP pattern
===============================

1. replace "udp" with "tcp" in all the subcases of MAC_IPV6_UDP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV6_UDP pattern.
3. get the same result.

Test case: MAC_IPV6_SCTP pattern
================================

1. replace "udp" with "sctp" in all the subcases of MAC_IPV6_UDP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV6_UDP pattern.
3. get the same result.


Test case: MAC_IPV4_GTPU_EH pattern
===================================
IAVF doesn't support RSS for GTPU by default,
so we need to set RSS rule for GTPU with extention header::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types l3-src-only end key_len 0 queues end / end

Now, IAVF doesn't support RSS for GTPU without extention header

Subcase 1: MAC_IPV4_GTPU_EH queue index
---------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 1 with FDIR matched ID=0x1.
   send mismatched packets, check the packets are not distributed to queue 1 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 2: MAC_IPV4_GTPU_EH rss queues
--------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 2 or queue 3 with FDIR matched ID=0x1.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 3: MAC_IPV4_GTPU_EH passthru
------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 4: MAC_IPV4_GTPU_EH drop
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   Then check there is no rule listed.

Subcase 5: MAC_IPV4_GTPU_EH mark+rss
------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss / mark / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 6: MAC_IPV4_GTPU_EH mark
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / end

2. repeat the steps of passthru with mark part in subcase 3,
   get the same result.

Subcase 7: MAC_IPV4_GTPU_EH QFI queue index / mark
--------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 3 / end

2. send matched packets, check the packet is redirected to queue 1 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x34)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet received has not FDIR::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x35)/IP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet received has not FDIR.
   Then check there is no rule listed.

Subcase 8: MAC_IPV4_GTPU_EH without QFI rss queues / mark
---------------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / end actions rss queues 2 3 end / mark id 1 / end

2. send matched packets, check the packet is distributed to queue 2 or queue 3 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=1)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet received has no FDIR::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=1)/IP()/TCP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet are received without FDIR.
   Then check there is no rule listed.


Subcase 9: MAC_IPV4_GTPU_EH 4 tuple queue index
-----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 10 / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 10 with FDIR matched ID=0x1.

   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 10: MAC_IPV4_GTPU_EH 4 tuple queue group
------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 11: MAC_IPV4_GTPU_EH 4 tuple passthru
---------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 12: MAC_IPV4_GTPU_EH 4 tuple drop
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 13: MAC_IPV4_GTPU_EH 4 tuple mark/rss
---------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 14: MAC_IPV4_GTPU_EH outer dst ip queue index
-----------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc  / end actions queue index 10 / mark id 1 / end

2. send matched packets, check the packet is redirected to queue 1 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet is distributed by RSS without FDIR matched ID::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 15: MAC_IPV4_GTPU_EH outer dst ip queue group
-----------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 16: MAC_IPV4_GTPU_EH outer dst ip passthru
--------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 17: MAC_IPV4_GTPU_EH outer dst ip drop
----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 18: MAC_IPV4_GTPU_EH outer dst ip mark/rss
--------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 19: MAC_IPV4_GTPU_EH outer src ip queue index
-----------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc  / end actions queue index 1 / mark id 3 / end

2. send matched packets, check the packet is redirected to queue 1 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet is distributed by RSS without FDIR matched ID::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 20: MAC_IPV4_GTPU_EH outer src ip queue group
-----------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 21: MAC_IPV4_GTPU_EH outer src ip passthru
--------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 22: MAC_IPV4_GTPU_EH outer src ip drop
----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 23: MAC_IPV4_GTPU_EH outer src ip mark/rss
--------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV4_GTPU pattern
================================

Subcase 1: MAC_IPV4_GTPU queue index
------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions queue index 1 / mark / end

2. send matched packets, check the packets are distributed to queue 1 with FDIR matched ID=0x0.
   send mismatched packets, check the packets are not distributed to queue 1 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 1 without FDIR matched ID.
   Then check there is no rule listed.

Subcase 2: MAC_IPV4_GTPU rss queues
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions rss queues 2 3 end / mark / end

2. send matched packets, check the packets are received with FDIR matched ID=0x0.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 3: MAC_IPV4_GTPU passthru
---------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions passthru / mark / end

2. send matched packets, check the packets are received with FDIR matched ID=0x0.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 4: MAC_IPV4_GTPU drop
-----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   Then check there is no rule listed.

Subcase 5: MAC_IPV4_GTPU mark+rss
---------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are received with FDIR matched ID=0x1.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 6: MAC_IPV4_GTPU mark
-----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark / end

2. repeat the steps of passthru with mark part in subcase 3,
   get the same result.

Subcase 7: MAC_IPV4_GTPU 3 tuple queue index
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678  / end actions queue index 10 / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 10 with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 8: MAC_IPV4_GTPU 3 tuple queue group
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 9: MAC_IPV4_GTPU 3 tuple passthru
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678  / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 10: MAC_IPV4_GTPU 3 tuple drop
--------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678  / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 11: MAC_IPV4_GTPU 3 tuple mark/rss
------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / gtpu teid is 0x12345678  / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 12: MAC_IPV4_GTPU outer dst ip queue index
--------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu  / end actions queue index 1 / mark id 3 / end

2. send matched packets, check the packet is redirected to queue 1 with FDIR matched ID=0x3.
   send mismatched packets, check the packet is distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 13: MAC_IPV4_GTPU outer dst ip queue group
--------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu  / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 14: MAC_IPV4_GTPU outer dst ip passthru
-----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu  / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 15: MAC_IPV4_GTPU outer dst ip drop
-------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 16: MAC_IPV4_GTPU outer dst ip mark/rss
-----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp / gtpu / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 17: MAC_IPV4_GTPU outer src ip queue index
--------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions queue index 1 / mark id 3 / end

2. send matched packets, check the packet is redirected to queue 1 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.22")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet is distributed by RSS without FDIR matched ID::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 18: MAC_IPV4_GTPU outer src ip queue group
--------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 19: MAC_IPV4_GTPU outer src ip passthru
-----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu   / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 20: MAC_IPV4_GTPU outer src ip drop
-------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu  / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 21: MAC_IPV4_GTPU outer src ip mark/rss
-----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 / udp / gtpu  / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV6_GTPU_EH pattern
===================================

Subcase 1: MAC_IPV6_GTPU_EH 4 tuple queue index
-----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 10 / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 10 with FDIR matched ID=0x1.

   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 2: MAC_IPV6_GTPU_EH 4 tuple queue group
-----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 3: MAC_IPV6_GTPU_EH 4 tuple passthru
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 4: MAC_IPV6_GTPU_EH 4 tuple drop
----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 5: MAC_IPV6_GTPU_EH 4 tuple mark/rss
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV6_GTPU_EH outer dst ipv6 queue index
------------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc  / end actions queue index 1 / mark id 3 / end

2. send matched packets, check the packet is redirected to queue 1 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet is distributed by RSS without FDIR matched ID::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 7: MAC_IPV6_GTPU_EH outer dst ipv6 queue group
------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 8: MAC_IPV6_GTPU_EH outer dst ipv6 passthru
---------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 9: MAC_IPV6_GTPU_EH outer dst ipv6 drop
-----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 10: MAC_IPV6_GTPU_EH outer dst ipv6 mark/rss
----------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 11: MAC_IPV6_GTPU_EH outer src ipv6 queue index
-------------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc  / end actions queue index 1 / mark id 3 / end

2. send matched packets, check the packet is redirected to queue 1 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet is distributed by RSS without FDIR matched ID::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 12: MAC_IPV6_GTPU_EH outer src ipv6 queue group
-------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 13: MAC_IPV6_GTPU_EH outer src ipv6 passthru
----------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu  / gtp_psc  / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 14: MAC_IPV6_GTPU_EH outer src ipv6 drop
------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 15: MAC_IPV6_GTPU_EH outer src ipv6 mark/rss
----------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / gtp_psc  / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV6_GTPU pattern
================================

Subcase 1: MAC_IPV6_GTPU 4 tuple queue index
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions queue index 10 / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 10 with FDIR matched ID=0x1.

   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 2: MAC_IPV6_GTPU 4 tuple queue group
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 3: MAC_IPV6_GTPU 4 tuple passthru
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 4: MAC_IPV6_GTPU 4 tuple drop
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 5: MAC_IPV6_GTPU 4 tuple mark/rss
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu teid is 0x12345678 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV6_GTPU outer dst ipv6 queue index
---------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions queue index 1 / mark id 3 / end

2. send matched packets, check the packet is redirected to queue 1 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet is distributed by RSS without FDIR matched ID::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 7: MAC_IPV6_GTPU outer dst ipv6 queue group
---------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 8: MAC_IPV6_GTPU outer dst ipv6 passthru
------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu  / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 9: MAC_IPV6_GTPU outer dst ipv6 drop
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 10: MAC_IPV6_GTPU outer dst ipv6 mark/rss
-------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth /  ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp / gtpu / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 11: MAC_IPV6_GTPU outer src ipv6 queue index
----------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions queue index 1 / mark id 3 / end

2. send matched packets, check the packet is redirected to queue 1 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet is distributed by RSS without FDIR matched ID::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::3", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 12: MAC_IPV6_GTPU outer src ipv6 queue group
----------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 13: MAC_IPV6_GTPU outer src ipv6 passthru
-------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 14: MAC_IPV6_GTPU outer src ipv6 drop
---------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 15: MAC_IPV6_GTPU outer src ipv6 mark/rss
-------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::2 / udp / gtpu / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Test case: Layer3 co-exist GTPU
===============================

Subcase 1: Layer3 co-exist GTP EH fdir + dst
--------------------------------------------

Rules::

    #1  flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.31 / udp / gtpu / gtp_psc / end actions rss queues 1 2 end / mark id 1 / end
    #2  flow create 0 ingress pattern eth / ipv6 dst is ::32 / udp / gtpu / gtp_psc / end actions rss queues 3 4 5 6 end / mark id 2 / end
    #3  flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.33 / udp / gtpu / gtp_psc / end actions queue index 7 / mark id 3 / end
    #4  flow create 0 ingress pattern eth / ipv6 dst is ::14 / udp / gtpu / gtp_psc / end actions queue index 8 / mark id 4 / end
    #5  flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.35 / udp / gtpu / gtp_psc / end actions passthru / mark id 5 / end
    #6  flow create 0 ingress pattern eth / ipv6 dst is ::36 / udp / gtpu / gtp_psc / end actions passthru / mark id 6 / end
    #7  flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.37 / udp / gtpu / gtp_psc / end actions drop / end
    #8  flow create 0 ingress pattern eth / ipv6 dst is ::38 / udp / gtpu / gtp_psc / end actions drop / end

Matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/TCP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IP()/TCP()/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IP()/ICMP()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

Mismatched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/TCP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.34")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::15")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IP()/TCP()/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IP()/ICMP()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::39")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

1. Create above filter rules.

2. Send matched packets.

3. Check result::

    Check p_gtpu1 is distributed to queue 1 or 2 with FDIR matched ID=0x1.
    Check p_gtpu2 is distributed to queue 3 or 4 or 5 or 6 with FDIR matched ID=0x2.
    Check p_gtpu3 is distributed to queue 7 with FDIR matched ID=0x3.
    Check p_gtpu4 is distributed to queue 8 with FDIR matched ID=0x4.
    Check p_gtpu5 is distributed by RSS with FDIR matched ID=0x5.
    Check p_gtpu6 is distributed by RSS with FDIR matched ID=0x6.
    Check p_gtpu7 is dropped.
    Check p_gtpu8 is dropped.

4. Send mismatched packets.

5. Check result::

    Check p_gtpu1 is distributed by RSS without FDIR matched ID=0x1.
    Check p_gtpu2 is distributed by RSS without FDIR matched ID=0x2.
    Check p_gtpu3 is distributed by RSS without FDIR matched ID=0x3.
    Check p_gtpu4 is distributed by RSS without FDIR matched ID=0x4.
    Check p_gtpu5 is distributed by RSS without FDIR matched ID=0x5.
    Check p_gtpu6 is distributed by RSS without FDIR matched ID=0x6.
    Check p_gtpu7 is not dropped, distributed by RSS.
    Check p_gtpu8 is not dropped, distributed by RSS.

6. Verify rules can be listed and destroyed::

    testpmd> flow list 0

7. Flush the rule, check there is no rule listed::

    testpmd> flow flush 0

8. Send matched packets.

9. Verify matched packets are distributed by RSS without FDIR matched ID.

10. Repeate above steps.

Subcase 2: Layer3 co-exist GTP fdir + dst
-----------------------------------------

Rules::

    #1  flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.31 / udp / gtpu / end actions rss queues 1 2 end / mark id 1 / end
    #2	flow create 0 ingress pattern eth / ipv6 dst is ::32 / udp / gtpu / end actions rss queues 3 4 5 6 end / mark id 2 / end
    #3	flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.33 / udp / gtpu / end actions queue index 7 / mark id 3 / end
    #4	flow create 0 ingress pattern eth / ipv6 dst is ::14 / udp / gtpu / end actions queue index 8 / mark id 4 / end
    #5	flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.35 / udp / gtpu / end actions passthru / mark id 5 / end
    #6	flow create 0 ingress pattern eth / ipv6 dst is ::36 / udp / gtpu / end actions passthru / mark id 6 / end
    #7	flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.37 / udp / gtpu / end actions drop / end
    #8	flow create 0 ingress pattern eth / ipv6 dst is ::38 / udp / gtpu / end actions drop / end

Matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/TCP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/TCP()/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

Mismatched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/TCP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.34")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::15")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/TCP()/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::39")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

Test steps as subcase 1.

Subcase 3: Layer3 co-exist GTP EH fdir + src
--------------------------------------------

Rules::

    #1  flow create 0 ingress pattern eth / ipv4 src is 192.168.0.21 / udp / gtpu / gtp_psc / end actions rss queues 1 2 end / mark id 1 / end
    #2	flow create 0 ingress pattern eth / ipv6 src is ::12 / udp / gtpu / gtp_psc / end actions rss queues 3 4 5 6 end / mark id 2 / end
    #3	flow create 0 ingress pattern eth / ipv4 src is 192.168.0.23 / udp / gtpu / gtp_psc / end actions queue index 7 / mark id 3 / end
    #4	flow create 0 ingress pattern eth / ipv6 src is 2001::4 / udp / gtpu / gtp_psc / end actions queue index 8 / mark id 4 / end
    #5	flow create 0 ingress pattern eth / ipv4 src is 192.168.0.25 / udp / gtpu / gtp_psc / end actions passthru / mark id 5 / end
    #6	flow create 0 ingress pattern eth / ipv6 src is ::16 / udp / gtpu / gtp_psc / end actions passthru / mark id 6 / end
    #7	flow create 0 ingress pattern eth / ipv4 src is 192.168.0.27 / udp / gtpu / gtp_psc / end actions drop / end
    #8	flow create 0 ingress pattern eth / ipv6 src is 2001::8 / udp / gtpu / gtp_psc / end actions drop / end

Matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/TCP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IP()/TCP()/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IP()/ICMP()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

Mismatched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.22", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::13", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/TCP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.24", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::5", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IP()/TCP()/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.26", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::17", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IP()/ICMP()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.28", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::9", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

Test steps as subcase 1.

Subcase 4: Layer3 co-exist GTP fdir + src
-----------------------------------------

Rules::

    #1  flow create 0 ingress pattern eth / ipv4 src is 192.168.0.21 / udp / gtpu / end actions rss queues 1 2 end / mark id 1 / end
    #2	flow create 0 ingress pattern eth / ipv6 src is ::12 / udp / gtpu / end actions rss queues 3 4 5 6 end / mark id 2 / end
    #3	flow create 0 ingress pattern eth / ipv4 src is 192.168.0.23 / udp / gtpu / end actions queue index 7 / mark id 3 / end
    #4	flow create 0 ingress pattern eth / ipv6 src is 2001::4 / udp / gtpu / end actions queue index 8 / mark id 4 / end
    #5	flow create 0 ingress pattern eth / ipv4 src is 192.168.0.25 / udp / gtpu / end actions passthru / mark id 5 / end
    #6	flow create 0 ingress pattern eth / ipv6 src is ::16 / udp / gtpu / end actions passthru / mark id 6 / end
    #7	flow create 0 ingress pattern eth / ipv4 src is 192.168.0.27 / udp / gtpu / end actions drop / end
    #8	flow create 0 ingress pattern eth / ipv6 src is 2001::8 / udp / gtpu / end actions drop / end

Matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/TCP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/TCP()/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

Mismatched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.22", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::13", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/TCP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.24", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::5", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/TCP()/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.26", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::17", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.28", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::9", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

Test steps as subcase 1.

Subcase 5: Layer3 co-exist GTP with/without EH fdir + src/dst
-------------------------------------------------------------

Rules::

    #1  flow create 0 ingress pattern eth / ipv4 src is 192.168.0.21 dst is 192.168.0.31 / udp / gtpu / gtp_psc / end actions rss queues 1 2 end / mark id 1 / end
    #2	flow create 0 ingress pattern eth / ipv6 src is ::12 dst is ::32 / udp / gtpu / gtp_psc / end actions rss queues 3 4 5 6 end / mark id 2 / end
    #3	flow create 0 ingress pattern eth / ipv4 src is 192.168.0.23 dst is 192.168.0.33 / udp / gtpu / gtp_psc / end actions queue index 7 / mark id 3 / end
    #4	flow create 0 ingress pattern eth / ipv6 src is 2001::4 dst is ::14 / udp / gtpu / gtp_psc / end actions queue index 8 / mark id 4 / end
    #5	flow create 0 ingress pattern eth / ipv4 src is 192.168.0.25 dst is 192.168.0.35 / udp / gtpu / end actions passthru / mark id 5 / end
    #6	flow create 0 ingress pattern eth / ipv6 src is ::16 dst is ::36 / udp / gtpu / end actions passthru / mark id 6 / end
    #7	flow create 0 ingress pattern eth / ipv4 src is 192.168.0.27 dst is 192.168.0.37 / udp / gtpu / end actions drop / end
    #8	flow create 0 ingress pattern eth / ipv6 src is 2001::8 dst is ::38 / udp / gtpu / end actions drop / end

Matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.21", dst="192.168.0.31")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::12", dst="::32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/TCP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.23", dst="192.168.0.33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::4", dst="::14")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IP()/TCP()/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.25", dst="192.168.0.35")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::16", dst="::36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.27", dst="192.168.0.37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::8", dst="::38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

Mismatched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.22", dst="192.168.0.32")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::13", dst="::33")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/TCP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.24", dst="192.168.0.34")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=1, qos_flow=0x33)/IPv6()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::5", dst="::15")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x33)/IP()/TCP()/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.26", dst="192.168.0.36")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="::17", dst="::37")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IP()/ICMP()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.28", dst="192.168.0.38")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IPv6(src="2001::9", dst="::39")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12)/IPv6()/IPv6ExtHdrFragment()/Raw('x'*20)

Test steps as subcase 1.


Test case: L2 Ethertype pattern
===============================

Subcase 1: L2 Ethertype queue index
-----------------------------------

1. create rule for PPPoED::

    flow create 0 ingress pattern eth type is 0x8863 / end actions queue index 1 / mark id 1 / end

   send PPPoED packet,
   check the packets are distributed to expected queue with specific FDIR matched ID.

2. create rule for PPPoE::

    flow create 0 ingress pattern eth type is 0x8864 / end actions queue index 2 / mark id 2 / end

   send PPPoE packet,
   check the packets are distributed to expected queue with specific FDIR matched ID.

3. create rule for ARP::

    flow create 0 ingress pattern eth type is 0x0806 / end actions queue index 3 / mark id 3 / end

   send ARP packet,
   Check the packets are distributed to expected queue with specific FDIR matched ID.

4. create rule for EAPS::

    flow create 0 ingress pattern eth type is 0x8100 / end actions queue index 4 / mark id 4 / end

   send EAPS packet,
   check the packets are distributed to expected queue with specific FDIR matched ID.

5. create rule for ieee1588::

    flow create 0 ingress pattern eth type is 0x88f7 / end actions queue index 5 / mark id 5 / end

   send ieee1588 packet,
   check the packets are distributed to expected queue with specific FDIR matched ID.

6. send a mismatched packet::

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8847)/MPLS(label=0xee456)/IP()],iface="enp134s0f1")

   check the packet received has not FDIR matched ID.

7. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the 5 rules listed.
   flush all the rules::

    testpmd> flow flush 0

8. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 2: L2 Ethertype rss queues
----------------------------------

1. create rules for PPPoED with rss queues action::

    flow create 0 ingress pattern eth type is 0x8863 / end actions rss queues 2 3 end / mark id 2 / end

2. send matched packet,
   check the packets received have FDIR matched ID=0x2,
   the packets are directed to queue 0,
   because L2 Ethertype are not supported by RSS.

3. Repeat step 1-2 with PPPoE/ARP/EAPS/ieee1588,
   get the same result.

4. repeat step 6-7 of subcase 1.

5. verify matched packets received have not FDIR matched ID.
   Then check there is no rule listed.

Subcase 3: L2 Ethertype passthru
--------------------------------

1. create rules for PPPoED with passthru action::

    flow create 0 ingress pattern eth type is 0x8863 / end actions passthru / mark id 2 / end

2. send matched packet,
   check the packets received have FDIR matched ID=0x2,
   the packets are directed to queue 0,
   because L2 Ethertype are not supported by RSS.

3. Repeat step 1-2 with PPPoE/ARP/EAPS/ieee1588,
   get the same result.

4. repeat step 6-7 of subcase 1.

5. verify matched packets received have not FDIR matched ID.
   Then check there is no rule listed.

Subcase 4: L2 Ethertype drop
----------------------------

1. create rules for PPPoED with drop action::

    flow create 0 ingress pattern eth type is 0x8863 / end actions drop / end

2. send matched packet,
   check the packets are dropped,

3. Repeat step 1-2 with PPPoE/ARP/EAPS/ieee1588,
   get the same result.

4. repeat step 6-7 of subcase 1.

5. verify matched packets are received.
   Then check there is no rule listed.

Subcase 5: L2 Ethertype mark+rss
--------------------------------

1. create rules for PPPoED with rss queues action::

    flow create 0 ingress pattern eth type is 0x8863 / end actions mark id 1 / rss / end

2. send matched packet,
   check the packets received have FDIR matched ID=0x1,
   the packets are directed to queue 0,
   because L2 Ethertype are not supported by RSS.

3. Repeat step 1-2 with PPPoE/ARP/EAPS/ieee1588,
   get the same result.

4. repeat step 6-7 of subcase 1.

5. verify matched packets received have not FDIR matched ID.
   Then check there is no rule listed.

Subcase 6: L2 Ethertype mark
----------------------------

1. create rules for PPPoED with mark action::

    flow create 0 ingress pattern eth type is 0x8863 / end actions mark / end

2. send matched packet,
   check the packets received have FDIR matched ID=0x0,

3. Repeat step 1-2 with PPPoE/ARP/EAPS/ieee1588,
   get the same result.

4. repeat step 6-7 of subcase 1.

5. verify matched packets received have not FDIR matched ID.
   Then check there is no rule listed.


Test case: PFCP pctype
======================
patterns:
MAC_IPV4_PFCP_NODE
MAC_IPV4_PFCP_SESSION
MAC_IPV6_PFCP_NODE
MAC_IPV6_PFCP_SESSION

RSS for PFCP are not supported by default.
so if it's not opened, the PFCP packet will be sent to queue 0 by RSS.

Subcase 1: PFCP queue index
---------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / end
    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / end

2. send matched packets, check the packets are redirected to expected queue.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rules.
   destroy the rules::

    testpmd> flow flush 0

4. verify matched packets are not redirected to expected queue.
   Then check there is no rule listed.

Subcase 2: PFCP rss queues
--------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions rss queues 2 3 end / mark id 0 / end
    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions rss queues 4 5 6 7 end / mark id 1 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark id 2 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions rss queues 3 4 5 6 end / mark id 3 / end

   open PFCP RSS function::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp / end actions rss types pfcp end key_len 0 queues end / end

2. send matched packets,
   PFCP SESSION packets are redirected to expected queues with specified mark ID.
   PFCP NODE packets are redirected to queue 0 with specified mark ID.
   send a ipv4-udp packet, check the packet is distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP PFCP => RSS MARK
    1       0       0       i--     ETH IPV4 UDP PFCP => RSS MARK
    2       0       0       i--     ETH IPV6 UDP PFCP => RSS MARK
    3       0       0       i--     ETH IPV6 UDP PFCP => RSS MARK
    4       0       0       i--     ETH IPV4 UDP PFCP => RSS
    5       0       0       i--     ETH IPV6 UDP PFCP => RSS

   destroy the fdir rules::

    flow destroy 0 rule 0
    flow destroy 0 rule 1
    flow destroy 0 rule 2
    flow destroy 0 rule 3

4. verify PFCP SESSION packets are distributed by RSS without FDIR matched ID.
   PFCP NODE packets are redirecte to queue 0 without FDIR matched ID.

5. disable PFCP RSS function::

    flow destroy 0 rule 4
    flow destroy 0 rule 5

6. verify PFCP SESSION packets are distributed to queue 0 without FDIR matched ID.
   PFCP NODE packets are distributed to queue 0 without FDIR matched ID.
   Then check there is no rule listed.

Subcase 3: PFCP passthru
------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions passthru / mark id 0 / end
    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions passthru / mark id 1 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions passthru / mark id 2 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions passthru / mark id 3 / end

2. send matched packets, check the packets are distributed by RSS with expected FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 4: PFCP drop
--------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions drop / end
    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions drop / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions drop / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   Then check there is no rule listed.

Subcase 5: PFCP mark+rss
------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions mark / rss / end
    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions mark id 1 / rss / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions mark id 2 / rss / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions mark id 3 / rss / end

2. send matched packets, check the packets are distributed by RSS with expected FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 6: PFCP mark
--------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions mark / end
    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions mark id 1 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions mark id 2 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions mark id 4294967294 / end

2. repeat the steps of passthru with mark part in subcase 3,
   get the same result.


Test case: MAC_IPV4_L2TPv3 pattern
==================================

Subcase 1: MAC_IPV4_L2TPv3 queue index
--------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions queue index 13 / mark id 7 / end

2. send matched packets, check the packets are distributed to queue 13 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 13 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 13 without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_L2TPv3 rss queues
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions rss queues 1 2 3 4 end / mark id 6 / end

2. send matched packets, check the packets are distributed to queue 1 or 2 or 3 or 4 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_L2TPv3 mark
-------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions mark id 15 / end

2. send matched packets, check the packets are received with FDIR matched ID.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV6_L2TPv3 pattern
==================================

Subcase 1: MAC_IPV6_L2TPv3 queue index
--------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions queue index 13 / mark id 7 / end

2. send matched packets, check the packets are distributed to queue 13 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 13 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 13 without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV6_L2TPv3 rss queues
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 17 / end actions rss queues 1 2 3 4 end / mark id 6 / end

2. send matched packets, check the packets are distributed to queue 1 or 2 or 3 or 4 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV6_L2TPv3 mark
-------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / l2tpv3oip session_id is 17 / end actions mark id 15 / end

2. send matched packets, check the packets are received with FDIR matched ID.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV4_ESP pattern
===============================

Subcase 1: MAC_IPV4_ESP queue index
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions queue index 13 / mark id 7 / end

2. send matched packets, check the packets are distributed to queue 13 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 13 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 13 without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_ESP rss queues
----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end

2. send matched packets, check the packets are distributed to queue 1 or 2 or 3 or 4 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_ESP passthru
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_ESP drop
-------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions drop / end

2. send matched packets, check the packets are dropped
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_ESP mark+rss
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions mark id 2 / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_ESP mark
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / esp spi is 7 / end actions mark id 15 / end

2. send matched packets, check the packets are received with FDIR matched ID.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   check there is no rule listed.

Test case: MAC_IPV6_ESP pattern
===============================

Subcase 1: MAC_IPV6_ESP queue index
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is 2001::1 dst is 2001::2 / esp spi is 7 / end actions queue index 13 / mark id 7 / end

2. send matched packets, check the packets are distributed to queue 13 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 13 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 13 without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV6_ESP rss queues
----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is 2001::1 dst is 2001::2 / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end

2. send matched packets, check the packets are distributed to queue 1 or 2 or 3 or 4 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV6_ESP passthru
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is 2001::1 dst is 2001::2 / esp spi is 7 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV6_ESP drop
-------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is 2001::1 dst is 2001::2 / esp spi is 7 / end actions drop / end

2. send matched packets, check the packets are dropped
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV6_ESP mark+rss
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is 2001::1 dst is 2001::2 / esp spi is 7 / end actions mark id 2 / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV6_ESP mark
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is 2001::1 dst is 2001::2 / esp spi is 7 / end actions mark id 15 / end

2. send matched packets, check the packets are received with FDIR matched ID.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV4_AH pattern
==============================

Subcase 1: MAC_IPV4_AH queue index
----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / ah spi is 7 / end actions queue index 13 / mark id 7 / end

2. send matched packets, check the packets are distributed to queue 13 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 13 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 13 without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_AH rss queues
---------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / ah spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end

2. send matched packets, check the packets are distributed to queue 1 or 2 or 3 or 4 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_AH mark
---------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / ah spi is 7 / end actions mark id 15 / end

2. send matched packets, check the packets are received with FDIR matched ID.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV6_AH pattern
==============================

Subcase 1: MAC_IPV6_AH queue index
----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / ah spi is 7 / end actions queue index 13 / mark id 7 / end

2. send matched packets, check the packets are distributed to queue 13 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 13 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 13 without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV6_AH rss queues
---------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / ah spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end

2. send matched packets, check the packets are distributed to queue 1 or 2 or 3 or 4 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV6_AH mark
---------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / ah spi is 7 / end actions mark id 15 / end

2. send matched packets, check the packets are received with FDIR matched ID.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV4_NAT-T-ESP pattern
=====================================

Subcase 1: MAC_IPV4_NAT-T-ESP queue index
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions queue index 13 / mark id 7 / end

2. send matched packets, check the packets are distributed to queue 13 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 13 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 13 without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_NAT-T-ESP rss queues
----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end

2. send matched packets, check the packets are distributed to queue 1 or 2 or 3 or 4 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_NAT-T-ESP passthru
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_NAT-T-ESP drop
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions drop / end

2. send matched packets, check the packets are dropped
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_NAT-T-ESP mark+rss
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions mark id 2 / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_NAT-T-ESP mark
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp / esp spi is 7 / end actions mark id 15 / end

2. send matched packets, check the packets are received with FDIR matched ID.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV6_NAT-T-ESP pattern
=====================================

Subcase 1: MAC_IPV6_NAT-T-ESP queue index
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions queue index 13 / mark id 7 / end

2. send matched packets, check the packets are distributed to queue 13 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 13 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 13 without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV6_NAT-T-ESP rss queues
----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions rss queues 1 2 3 4 end / mark id 6 / end

2. send matched packets, check the packets are distributed to queue 1 or 2 or 3 or 4 with FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not distributed to queue 1 or 2 or 3 or 4 without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV6_NAT-T-ESP passthru
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV6_NAT-T-ESP drop
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions drop / end

2. send matched packets, check the packets are dropped
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV6_NAT-T-ESP mark+rss
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions mark id 2 / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV6_NAT-T-ESP mark
----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 src is 2001::1 dst is 2001::2 / udp / esp spi is 7 / end actions mark id 15 / end

2. send matched packets, check the packets are received with FDIR matched ID.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   check there is no rule listed.


Test case: negative cases
=========================

Subcase 1: invalid parameters of queue index
--------------------------------------------

1. Invalid parameters::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 16 / end

   Failed to create flow, report message::

    Invalid queue for FDIR.: Invalid argument

2. check there is no rule listed.

Subcase 2: invalid parameters of rss queues
-------------------------------------------

1. Invalid number of queues::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end

   Failed to create flow, report message::

    The region size should be any of the following values:1, 2, 4, 8, 16, 32, 64, 128 as long as the total number of queues do not exceed the VSI allocation.: Invalid argument

   Invalid number of queues::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 end / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues end / end

   Failed to create flow, report message::

    Queue region size can't be 0 or 1.: Invalid argument

2. Discontinuous queues::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end

   Failed to create flow, report message::

    Discontinuous queue region: Invalid argument

3. invalid queue index::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 15 16 end / end

   Failed to create flow, report message::

    Invalid queue region indexes.: Invalid argument

4. "--rxq=7 --txq=7", set queue group 8 queues::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 1 2 3 4 5 6 7 end / end

   Failed to create flow, report message::

    Invalid queue region indexes.: Invalid argument

5. check there is no rule listed.

Subcase 3: Invalid parameters of GTPU input set
-----------------------------------------------

1. Invalid value of teid and qfi::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x100 / end actions queue index 1 / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc qfi is 0x5 / end actions queue index 2 / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / end actions queue index 1 / end

   Failed to create flow, report message "Bad arguments"

2. check there is no rule listed.

Subcase 4: unsupported type of L2 ethertype
-------------------------------------------

1. create rules for IP/IPV6::

    flow create 0 ingress pattern eth type is 0x0800 / end actions queue index 1 / end
    flow create 0 ingress pattern eth type is 0x86dd / end actions queue index 1 / end

   Failed to create flow, report the error message::

    Unsupported ether_type.: Invalid argument

2. check there is no rule listed.

Subcase 5: Duplicated rules
---------------------------

1. Create a FDIR rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end

   the rule is created successfully.

2. Create the same rule again, Failed to create flow, report message::

    Add filter rule failed.: Operation not permitted

3. check there is only one rule listed.

Subcase 6: conflicted rules
---------------------------

1. Create a FDIR rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / mark / end

   the rule is created successfully.

2. Create a rule with same input set but different action::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 2 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions drop / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 2 / mark / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions rss queues 2 3 end / mark / end

   Failed to create the two flows, report message::

    iavf_fdir_add(): Failed to add rule request due to the rule is already existed
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

3. Create a rule with same pattern but different input set::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 3 / mark / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2021 / end actions mark / end

   Failed to create the flow, report message::

    iavf_fdir_add(): Failed to add rule request due to the rule is conflict with existing rule
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

3. Create a rule with conflicted patterns::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.22 / udp src is 10 dst is 20 / end actions queue index 4 / mark id 4 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.23 ttl is 2 tos is 4 / udp src is 10 dst is 20 / end actions queue index 5 / mark id 5 / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::3 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end

   Failed to create the two flows, report message::

    iavf_fdir_add(): Failed to add rule request due to the rule is conflict with existing rule
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Failed to create parser engine.: Invalid argument

3. check there is only one rule listed.

Subcase 7: conflicted actions
-----------------------------

1. Create a rule with two conflicted actions::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / rss queues 2 3 end / end

   Failed to create flow, report message::

    Unsupported action combination: Invalid argument

2. check there is no rule listed.

Subcase 8: void action
----------------------

1. Create a rule with void action::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions end

   Failed to create flow, report message::

    Emtpy action: Invalid argument

2. check there is no rule listed.

Subcase 9: delete a non-existent rule
-------------------------------------

1. show the rule list of port 0::

    flow list 0

   There is no rule listed.
   show the rule list of port 1::

    testpmd> flow list 1
    Invalid port 1

2. destroy rule 0 of port 0::

    flow destroy 0 rule 0

   There is no error message reported.
   destroy rule 0 of port 1::

    testpmd> flow destroy 1 rule 0
    Invalid port 1

3. flush rules of port 0::

    flow flush 0

   There is no error message reported.
   flush rules of port 1::

    testpmd> flow flush 1
    port_flow_complain(): Caught PMD error type 1 (cause unspecified): No such device: No such device

Subcase 10: unsupported input set field
---------------------------------------

1. Create a IPV4_PAY rule with TC input set::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tc is 2 / end actions queue index 1 / end

   Failed to create flow, report message::

    Bad arguments

2. check there is no rule listed.

Subcase 11: void input set value
--------------------------------

1. Create a IPV4_PAY rule with void input set value::

    flow create 0 ingress pattern eth / ipv4 / end actions queue index 1 / end

   Failed to create flow, report message::

    Invalid input set: Invalid argument

2. check there is no rule listed.

Subcase 12: unsupported pattern with OS package
-----------------------------------------------

1. Create a GTPU rule with OS default package::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end

   Failed to create flow, report error message::

    Add filter rule failed.: Operation not permitted

2. check there is no rule listed.

3. Create a L2TPv3 rule with OS default package::

    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 17 / end actions queue index 3 / mark id 7 / end

   Failed to create flow, report error message::

    Add filter rule failed.: Operation not permitted

4. check there is no rule listed.

5. Create a ESP rule with OS default package::

    flow create 0 ingress pattern eth / ipv6 / udp / esp spi is 17 / end actions rss queues 2 3 end / mark id 7 / end

   Failed to create flow, report error message::

    Add filter rule failed.: Operation not permitted

6. check there is no rule listed.

Subcase 13: invalid port
------------------------

1. Create a rule with invalid port::

    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end

   Failed to create flow, report message::

    No such device: No such device

2. check there is no rule listed on port 0,
   check on port 1::

    testpmd> flow list 1
    Invalid port 1

Test case: pf vf combination
============================

Subcase 1: same rules
---------------------

1. create the same rule on pf0 and pf1 successfully::

    # ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1
    Added rule with ID 15359
    # ethtool -N enp134s0f1 flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1
    Added rule with ID 15359

2. show the rules::

    # ethtool -n enp134s0f0
    112 RX rings available
    Total 1 rules

    Filter: 15359
            Rule Type: TCP over IPv4
            Src IP addr: 192.168.0.20 mask: 0.0.0.0
            Dest IP addr: 192.168.0.21 mask: 0.0.0.0
            TOS: 0x0 mask: 0xff
            Src port: 22 mask: 0x0
            Dest port: 23 mask: 0x0
            Action: Direct to VF 0 queue 1

    # ethtool -n enp134s0f1
    112 RX rings available
    Total 1 rules

    Filter: 15359
            Rule Type: TCP over IPv4
            Src IP addr: 192.168.0.20 mask: 0.0.0.0
            Dest IP addr: 192.168.0.21 mask: 0.0.0.0
            TOS: 0x0 mask: 0xff
            Src port: 22 mask: 0x0
            Dest port: 23 mask: 0x0
            Action: Direct to VF 0 queue 1

3. start testpmd on vf00 and vf01::

    ./testpmd -c 0xff -n 6 -a 86:01.0 -a 86:01.1 --file-prefix=vf0 -- -i --rxq=16 --txq=16

   create same rules with pf::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end

   list the rules::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => QUEUE
    testpmd> flow list 1
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => QUEUE

4. start testpmd on vf10 and vf11::

    ./testpmd -c 0xff00 -n 6 -a 86:11.0 -a 86:11.1 --file-prefix=vf1 -- -i --rxq=16 --txq=16

   create same rules with pf::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end

   list the rules::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => QUEUE
    testpmd> flow list 1
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => QUEUE

5. send matched packets to pf0 and pf1::

    sendp([Ether(dst="68:05:ca:a3:1a:60")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="68:05:ca:a3:1a:61")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f0")

   check the pf0 statistics::

    ethtool -S enp134s0f0

    rx_queue_1_packets: 1
    rx_queue_1_bytes: 134

   check the pf1 statistics::

    ethtool -S enp134s0f1

    rx_queue_1_packets: 1
    rx_queue_1_bytes: 134

   send mismatched packets to pf0 and pf1,
   check the packets are redirected not to queue 1.

6. send matched packets to vfs::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f0")

   check the first packet is redirected to vf00 queue 1.
   check the second packet is redirected to vf01 queue 1.
   check the third packet is redirected to vf10 queue 1.
   check the fourth packet is redirected to vf11 queue 1.

7. send mismatched packets to vfs::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f0")

   check the packets are redirected to same vf in order, but not queue 1.

8. flush all the rules on vfs, and delete rules on pfs::

    # ethtool -N enp134s0f0 delete 15359
    # ethtool -N enp134s0f1 delete 15359
    # ethtool -n enp134s0f0
    112 RX rings available
    Total 0 rules
    # ethtool -n enp134s0f1
    112 RX rings available
    Total 0 rules

9. send matched packets to pfs and vfs,
   all the packets are not redirected to expected queue.

Subcase 2: same input set, different actions
--------------------------------------------

1. create the same rule on pf0 and pf 1 successfully::

    # ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1
    Added rule with ID 15359
    # ethtool -N enp134s0f1 flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 2
    Added rule with ID 15359

2. start testpmd on vf00 and vf01::

    ./testpmd -c 0xff -n 6 -a 86:01.0 -a 86:01.1 --file-prefix=vf0 -- -i --rxq=16 --txq=16

   create same rules with pf::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 3 4 end / mark / end

3. start testpmd on vf10 and vf11::

    ./testpmd -c 0xff00 -n 6 -a 86:11.0 -a 86:11.1 --file-prefix=vf1 -- -i --rxq=16 --txq=16

   create same rules with pf::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end

4. send matched packets to vfs::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f0")

   check pkt1 to queue 1 of vf00 with FDIR matched ID=0x1,
   pkt2 to queue 3 or 4 of vf01 with FDIR matched ID=0x0,
   pkt3 is dropped by vf10, pkt4 is received with FDIR matched ID=0x1

5. send mismatched packets to vfs::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f0")

   check the packets are received without FDIR matched ID.

6. send matched packets to pf0 and pf1::

    sendp([Ether(dst="68:05:ca:a3:1a:60")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="68:05:ca:a3:1a:61")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f0")

   check packet 1 is redirected to queue 1 of pf0,
   packet 2 is redirected to queue 2 of pf1.
   send mismatched packets to pf0 and pf1,
   check the packets are not redirected to expected queue.

7. flush all the rules on pfs and vfs, send the matched packets,
   check the packets send to vfs are received without FDIR matched ID.
   check the packets send to pfs are received but not redirected to expected queue.

Subcase 3: different patterns, different actions
------------------------------------------------

1. create the same rule on pf0 and pf 1 successfully::

    # ethtool -N enp134s0f0 flow-type tcp4 src-ip 192.168.0.20 dst-ip 192.168.0.21 src-port 22 dst-port 23 action 1
    Added rule with ID 15358
    # ethtool -N enp134s0f1 flow-type udp4 src-ip 192.168.0.22 dst-ip 192.168.0.23 src-port 22 dst-port 23 action -1
    Added rule with ID 15359

2. start testpmd on vf00 and vf01::

    ./testpmd -c 0xff -n 6 -a 86:01.0 -a 86:01.1 --file-prefix=vf0 -- -i --rxq=16 --txq=16

   create same rules with pf::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.22 dst is 192.168.0.23 / udp src is 22 dst is 23 / end actions queue index 5 / mark / end

3. start testpmd on vf10 and vf11::

    ./testpmd -c 0xff00 -n 6 -a 86:11.0 -a 86:11.1 --file-prefix=vf1 -- -i --rxq=16 --txq=16

   create same rules with pf::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.22 dst is 192.168.0.23 / udp src is 22 dst is 23 / end actions queue index 5 / mark id 1 / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.22 dst is 192.168.0.23 tos is 4 / tcp src is 22 dst is 23 / end actions drop / end

4. send matched packets to vfs::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.22",dst="192.168.0.23")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.22",dst="192.168.0.23")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.22",dst="192.168.0.23",tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f0")

   check pkt1 to queue 2 or 3 of vf00 without FDIR matched ID,
   pkt2 to queue 5 of vf01 with FDIR matched ID=0x0,
   pkt3 to queue 5 of vf10 with FDIR matched ID=0x1,
   pkt4 is dropped by vf11.

5. send mismatched packets to vfs::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:77")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:88")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp134s0f0")

   check the packets are received without FDIR matched ID.

6. send matched packets to pf0 and pf1::

    sendp([Ether(dst="68:05:ca:a3:1a:60")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="68:05:ca:a3:1a:61")/IP(src="192.168.0.22",dst="192.168.0.23")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f0")

   check packet 1 is redirected to queue 1 of pf0::

    rx_queue_1_packets: 1
    rx_queue_1_bytes: 134

   packet 2 is dropped by pf1::

    rx_dropped: 1

   send mismatched packets to pf0 and pf1,
   check the packets are received but not redirected to expected queue.

7. flush all the rules on pfs and vfs, send the matched packets,
   check the packets send to vfs are received without FDIR matched ID.
   check the packets send to pfs are received but not redirected to expected queue.

Test case: Max number
=====================
All the max number cases are designed based on 2*100G NIC.
If the hardware is 4*25G NIC, the guaranteed rule number of PF is 512.
So in subcase 3 and subcase 4, there can be created at most 14848 rules on 1pf and 2vfs.

Subcase 1: 128 profiles
-----------------------

1. create 16 vfs on pf0::

    echo 16 > /sys/bus/pci/devices/0000:86:00.0/sriov_numvfs

   bind them to dpdk driver::

    ./usertools/dpdk-devbind.py -b vfio-pci 86:01.0 86:01.1 86:01.2 86:01.3 86:01.4 86:01.5 86:01.6 86:01.7
    ./usertools/dpdk-devbind.py -b vfio-pci 86:02.0 86:02.1 86:02.2 86:02.3 86:02.4 86:02.5 86:02.6 86:02.7

   then start testpmd::

    ./testpmd -c 0xf -n 6 --file-prefix=vf -- -i --rxq=4 --txq=4

2. create 8 rules with different patterns on each port::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / sctp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth type is 0x8863 / end actions queue index 1 / mark id 1 / end
    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 2 / end

   created successfully on port 0-12,
   failed from rule 6 on port 13::

    testpmd> flow create 13 ingress pattern eth type is 0x8863 / end actions queue index 1 / mark id 1 / end
    eth
    iavf_execute_vf_cmd(): No response or return failure (-5) for cmd 47
    iavf_fdir_add(): fail to execute command OP_ADD_FDIR_FILTER
    iavf_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 2 (flow rule (handle)): Add filter rule failed.: Operation not permitted

3. list the rules on port 0-12::

    testpmd> flow list 12
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => QUEUE MARK
    1       0       0       i--     ETH IPV4 TCP => QUEUE MARK
    2       0       0       i--     ETH IPV4 SCTP => QUEUE MARK
    3       0       0       i--     ETH IPV6 UDP => QUEUE MARK
    4       0       0       i--     ETH IPV6 TCP => QUEUE MARK
    5       0       0       i--     ETH IPV6 SCTP => QUEUE MARK
    6       0       0       i--     ETH => QUEUE MARK
    7       0       0       i--     ETH IPV4 UDP PFCP => QUEUE

   list the rules on port 13, there are only 6 rules listed.
   list the rules on port 14/15, there is no rule listed.
   110 rules can be created successfully, which applied 110 profiles.

   Note: there are 128 profiles in total.
   each pf apply for 8 profiles when kernel driver init,
   4 for non-tunnel packet, 4 for tunnel packet.
   profile 0 and profile 1 are default profile for specific packet.
   we design case with 2*100G card, so 110 profiles can be used for vf.
   if we use 4*25G card, only 94 profiles can be used for vf.

4. send matched packets to vf 12,
   the packets are redirected to the expected queue.

5. flush rules on vf port 12::

    flow flush 12

   there is no rule listed on port 12.
   all the rule can be listed correctly in other ports.
   send matched packets to port 12,
   the packets are received without FDIR matched ID.

6. create rule on port 13 again::

    testpmd> flow create 13 ingress pattern eth type is 0x8863 / end actions queue index 1 / mark id 1 / end

   the rule can be created successfully.
   send the matched packet port 13,
   the packets are redirected to the expected queue.

Test case: Stress test
======================

Subcase 1: port stop/port start
-------------------------------

1. create a rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark / end

2. list the rule and send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") / Raw('x' * 80)],iface="enp134s0f1")

   check the packet are redirected to queue 1 with FDIR matched ID=0x0

3. stop the port, then start the port::

    testpmd> port stop 0
    testpmd> port start 0

4. show the rule list, there is no rule listed.

5. verify matched packet is distributed by RSS without FDIR matched ID.

Subcase 2: delete rules
-----------------------

1. create 3 rules and destory the first rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 24 / end actions queue index 2 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 25 / end actions queue index 3 / mark / end

   there are rule 0/1/2 listed::

    flow list 0

   send packets match rule 0, rule 1 and rule 2,
   Verify all packets can be redirected to expected queue and FDIR matched ID.
   destory the first rule::

    flow destroy 0 rule 0

   list the rules, verify there are only rule 1 and rule 2 listed.
   send packet matched rule 0, verify it is received without FDIR matched ID.
   send packets matched rule 1 and rule 2, Verify all packets be redirected with FDIR matched ID.
   flush rules::

    flow flush 0

   send packets match rule 0, rule 1 and rule 2, verify all packets received without FDIR matched ID.

2. create 3 rules and destory the second rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 24 / end actions queue index 2 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 25 / end actions queue index 3 / mark / end

   there are rule 0/1/2 listed::

    flow list 0

   send packets match rule 0, rule 1 and rule 2,
   Verify all packets can be redirected to expected queue and FDIR matched ID.
   destory the second rule::

    flow destroy 0 rule 1

   list the rules, verify there are only rule 0 and rule 2 listed.
   send packet matched rule 1, verify it is received without FDIR matched ID.
   send packets matched rule 0 and rule 2, Verify all packets be redirected with FDIR matched ID.
   flush rules::

    flow flush 0

   send packets match rule 0, rule 1 and rule 2, verify all packets received without FDIR matched ID.

3. create 3 rules and destory the third rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 24 / end actions queue index 2 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 25 / end actions queue index 3 / mark / end

   there are rule 0/1/2 listed::

    flow list 0

   send packets match rule 0, rule 1 and rule 2,
   Verify all packets can be redirected to expected queue with FDIR matched ID.
   destory the last rule::

    flow destroy 0 rule 2

   list the rules, verify there are only rule 0 and rule 1 listed.
   send packet matched rule 2, verify it is received without FDIR matched ID.
   send packets matched rule 0 and rule 1, Verify all packets be redirected with FDIR matched ID.
   flush rules::

    flow flush 0

   send packets match rule 0, rule 1 and rule 2, verify all packets are received without FDIR matched ID.

Subcase 3: VF port reset and create a new rule
----------------------------------------------

1. create a rule on vf00 and vf01::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / mark / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / mark / end

2. send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   check the packet is redirected to queue 5 of port 0 and port 1 with FDIR matched ID=0x0.

3. vf reset::

    port stop 0
    port reset 0
    port start 0

   the port can be stop/reset/start normally without error message.

4. check there is not rule listed on port 0.
   the rule of port 1 is still be listed.
   send matched packet to vf0, check the packet is distributed by RSS.
   send matched packet to vf1, check the packet is redirected to queue 5 with FDIR matched ID=0x0.

5. create rule 0 on port 0 again, the rule can be created successfully.
   send matched packet to port 0, the packet can be redirected to queue 5 with FDIR matched ID=0x0.

6. quit and relaunch testpmd, create same rules successfully.

7. send matched packets, check them redirected to expected queue with FDIR matched ID.

Subcase 4: VF port reset and delete the rule
--------------------------------------------

1. create a rule on vf00 and vf01::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / mark / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / mark / end

2. send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   check the packet is redirected to queue 5 of port 0 and port 1 with FDIR matched ID=0x0.

3. vf reset::

    port stop 1
    port reset 1
    port start 1

   the port can be stop/reset/start normally without error message.

4. check there is not rule listed on port 1.
   the rule of port 0 is still be listed.
   send matched packet to vf0, check the packet is redirected to queue 5 with FDIR matched ID=0x0.
   send matched packet to vf1, check the packet is distributed by RSS.

5. destroy rule 0 of vf0 successfully.
   send matched packet to vf0, check the packet is redirected by RSS without FDIR matched ID.
   send matched packet to vf1, check the packet is redirected by RSS without FDIR matched ID.

6. quit and relaunch testpmd, create same rules successfully.

7. send matched packets, check them redirected to expected queue with FDIR matched ID.

Subcase 5: PF reset VF and create a new rule
--------------------------------------------

1. create a rule on vf00 and vf01::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / mark / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / mark / end

2. send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   check the packet is redirected to queue 5 with FDIR matched ID=0x0.

3. pf trigger vf reset::

    ip link set enp134s0f0 vf 0 mac 00:11:22:33:44:56

4. testpmd shows::

    Port 0: reset event

   then vf reset::

    port stop 0
    port reset 0
    port start 0

   the port can be stop/reset/start normally without error message.

5. check there is not rule listed on vf0.
   send matched packet to vf0 with new mac address, check the packet is redirected by RSS without FDIR matched ID.
   send matched packet to vf1, check the packet is redirected to queue 5 with FDIR matched ID=0x0.

6. create a new rule on port 0, the rule can be created successfully::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.1 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 6 / mark id 1 / end

   send matched packet to port 0, the packet can be redirected to queue 6 with FDIR matched ID=0x1.

7. quit and relaunch testpmd, then create same rules successfully.

8. send matched packets, check them redirected to expected queue with FDIR matched ID.

Subcase 6: PF reset VF and delete the rule
------------------------------------------

1. create a rule on vf00 and vf01::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / mark / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 5 / mark / end

2. send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:66")/IP(src="192.168.0.0",dst="192.1.0.0", tos=4)/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp134s0f1")

   check the packet is redirected to queue 5 with FDIR matched ID=0x0.

3. pf trigger vf reset::

    ip link set enp134s0f0 vf 1 mac 00:11:22:33:44:56

4. testpmd shows::

    Port 1: reset event

   then vf reset::

    port stop 1
    port reset 1
    port start 1

   the port can be stop/reset/start normally without error message.

5. check there is not rule listed on vf1.
   destroy rule 0 of vf0 successfully.
   send matched packet to vf0, check the packet is redirected by RSS without FDIR matched ID.
   send matched packet to vf1, check the packet is redirected by RSS without FDIR matched ID.

6. create rule 1 on port 1 again, the rule can be created successfully.
   send matched packet to port 1, the packet can be redirected to queue 5 with FDIR matched ID=0x0.

7. quit and relaunch testpmd, then create same rules successfully.

8. send matched packets, check them redirected to expected queue with FDIR matched ID.

Subcase 7: check profile delete
-------------------------------

1. create ipv4-tcp and ipv6-udp rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 2 / mark id 2 / end

   return the message::

    Flow rule #0 created
    Flow rule #1 created

   list the rules::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 TCP => QUEUE MARK
    1       0       0       i--     ETH IPV6 UDP => QUEUE MARK

2. send ipv4-pay and ipv6-pay packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw('x' * 80)],iface="enp134s0f1")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1, hlim=2)/("X"*480)], iface="enp134s0f1")

   check the two packets are distributed by RSS without FDIR matched ID.

3. delete the rules, and create a ipv4-other and a ipv6-other rule::

    flow flush 0
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 3 / mark id 3 / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / end actions queue index 4 / mark id 4 / end

4. send the two packets again,
   check ipv4-pay packet is redirected to queue 3 with FDIR matched ID=0x3
   check ipv6-pay packet is redirected to queue 4 with FDIR matched ID=0x4

5. delete the rules, and create ipv4-tcp and ipv6-udp rules again::

    flow flush 0
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 2 / mark id 2 / end

6. send the two packets again,
   check the two packets are distributed by RSS without FDIR matched ID.

Test case: PFCP coverage test
=============================
Subcase 1: PFCP FDIR vlan strip on HW checksum offload check
------------------------------------------------------------
1. start testpmd on vf00::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 6 -a 86:01.0 --file-prefix=vf -- -i --rxq=16 --txq=16 --enable-rx-cksum --port-topology=loop

2. Enable vlan filter and receipt of VLAN packets with VLAN Tag Identifier 1 on port 0.
   Enable vlan strip on port 0::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> vlan set strip on 0

3. enable hardware checksum::

    testpmd> set fwd csum
    Set csum packet forwarding mode
    testpmd> port stop all
    testpmd> csum set ip hw 0
    testpmd> csum set udp hw 0
    testpmd> port start all
    testpmd> set verbose 1
    testpmd> start

4. DUT create fdir rules for MAC_IPV4_PFCP_NODE/MAC_IPV4_PFCP_SESSION/MAC_IPV6_PFCP_NODE/MAC_IPV6_PFCP_SESSION with queue index and mark::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / mark id 1 / end
    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / mark id 2 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / mark id 3 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / mark id 4 / end

   DUT check the packets are redirected to expected queue with mark id on port 0.

5. Tester send matched packets with VLAN tag "1" and incorrect checksum::

    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(chksum=0xf)/UDP(sport=22, dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(chksum=0xf)/UDP(sport=22, dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP()/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP()/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6()/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6()/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(Sfield=1),iface="enp134s0f1")

6. DUT check the packets are redirected to expected queue with mark id on port 0 with "PKT_RX_VLAN_STRIPPED",
   and report the checksum error::

    PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_GOOD

   or::

    PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD

   verify that the same number of packet are correctly received on the traffic generator side port A without VLAN tag "1".
   And IPv4 checksum, UDP checksum need be validated as pass by the tester.
   The IPv4 source address will not be changed by testpmd.

7. DUT verify rule can be listed and destroyed::

    testpmd> flow list 0

   destroy the rules::

    testpmd> flow flush 0

8. Tester send matched packets with VLAN tag "1" and incorrect checksum.
   DUT check all the packets are distributed to queue 0 without mark id.
   all the received packets are with "PKT_RX_VLAN_STRIPPED", and report the checksum error,
   verify that the same number of packet are correctly received on the traffic generator side port A without VLAN tag "1".
   And IPv4 checksum, UDP checksum need be validated as pass by the tester.
   The IPv4 source address will not be changed by testpmd.

subcase 2: PFCP FDIR vlan strip off SW checksum offload check
-------------------------------------------------------------
1. start testpmd on vf00::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 6 -a 86:01.0 --file-prefix=vf -- -i --rxq=16 --txq=16 --enable-rx-cksum --port-topology=loop

2. Enable vlan filter and receipt of VLAN packets with VLAN Tag Identifier 1 on port 0.
   Disable vlan strip on port 0::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> vlan set strip off 0

3. enable software checksum::

    testpmd> set fwd csum
    Set csum packet forwarding mode
    testpmd> port stop all
    testpmd> csum set ip sw 0
    testpmd> csum set udp sw 0
    testpmd> port start all
    testpmd> set verbose 1
    testpmd> start

4. DUT create fdir rules for MAC_IPV4_PFCP_NODE/MAC_IPV4_PFCP_SESSION/MAC_IPV6_PFCP_NODE/MAC_IPV6_PFCP_SESSION with queue index and mark::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / mark id 1 / end
    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / mark id 2 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / mark id 3 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / mark id 4 / end

5. Tester send matched packets with VLAN tag "1" and incorrect checksum::

    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(chksum=0xf)/UDP(sport=22, dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(chksum=0xf)/UDP(sport=22, dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP()/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP()/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6()/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6()/UDP(sport=22, dport=8805, chksum=0xf)/PFCP(Sfield=1),iface="enp134s0f1")

6. DUT check the packets are redirected to expected queue with mark id on port 0 without "PKT_RX_VLAN_STRIPPED",
   and report the checksum error::

    PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_GOOD

   or::

    PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD

   verify that the same number of packet are correctly received on the traffic generator side port A with VLAN tag "1".
   And UDP checksum need be validated as pass by the tester.
   The checksum is indeed recalculated by software algorithms.

7. DUT verify rule can be listed and destroyed::

    testpmd> flow list 0

   destroy the rule::

    testpmd> flow flush 0

8. Tester send matched packets with VLAN tag "1" and incorrect checksum.

9. DUT check the packets are distributed to queue 0 without mark id without "PKT_RX_VLAN_STRIPPED", and report the checksum error.
   verify that the same number of packet are correctly received on the traffic generator side port A with VLAN tag "1".
   And UDP checksum need be validated as pass by the tester.
   The checksum is indeed recalculated by software algorithms.

subcase 3: PFCP FDIR vlan insert on
-----------------------------------
1. start testpmd on vf00::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 6 -a 86:01.0 --file-prefix=vf -- -i --rxq=16 --txq=16

2. Enable vlan filter and insert VLAN Tag Identifier 1 to vlan packet sent from port 0::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> port stop all
    testpmd> tx_vlan set 0 1
    testpmd> port start all
    testpmd> set fwd mac

3. DUT create fdir rules for MAC_IPV4_PFCP_NODE/MAC_IPV4_PFCP_SESSION/MAC_IPV6_PFCP_NODE/MAC_IPV6_PFCP_SESSION with queue index and mark::

    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 0 / end actions queue index 1 / mark id 1 / end
    flow create 0 ingress pattern eth / ipv4 / udp / pfcp s_field is 1 / end actions queue index 2 / mark id 2 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 0 / end actions queue index 3 / mark id 3 / end
    flow create 0 ingress pattern eth / ipv6 / udp / pfcp s_field is 1 / end actions queue index 4 / mark id 4 / end

4. Tester send matched packets without VLAN tag::

    sendp(Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=22, dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=22, dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=22, dport=8805)/PFCP(Sfield=0),iface="enp134s0f1")
    sendp(Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=22, dport=8805)/PFCP(Sfield=1),iface="enp134s0f1")

5. DUT check the packets are redirected to expected queue with mark id on port 0 without "PKT_RX_VLAN_STRIPPED",
   verify that the same number of packet are correctly received on the traffic generator side port A with VLAN tag "1".

6. DUT verify rule can be listed and destroyed::

    testpmd> flow list 0

   destroy the rule::

    testpmd> flow destroy 0 rule 0
    testpmd> flow destroy 0 rule 1
    testpmd> flow destroy 0 rule 2
    testpmd> flow destroy 0 rule 3

7. Tester send matched packets without VLAN tag "1".

8. DUT check the packets are not distributed to expected queue without mark id without "PKT_RX_VLAN_STRIPPED",
   verify that the same number of packet are correctly received on the traffic generator side port A with VLAN tag "1".
   And UDP checksum need be validated as pass by the tester.

Test case: without input set test
=================================

Support ipv4 and ipv6 tcp/udp flow director rule without input set.
The packets are for testing without input set cases.

* MAC_IPV4_TCP

    matched packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)

    mismatched packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())/SCTP()],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/TCP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)

* MAC_IPV4_UDP

    matched packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)

    mismatched packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP(src=RandIP(), dst=RandIP())/SCTP()],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)

* MAC_IPV6_TCP

    matched packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/TCP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)

    mismatched packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/SCTP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)

* MAC_IPV6_UDP

    matched packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)

    mismatched packets::

        sendp([Ether(dst="00:11:22:33:44:55")/IP()/TCP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/TCP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)
        sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/SCTP(sport=RandShort(),dport=RandShort())],iface='ens192f1',count=100)

Test Case: MAC_IPV4_TCP_WITHOUT_INPUT_SET
-----------------------------------------

Subcase 1: MAC_IPV4_TCP queue index
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions queue index 1 / end

2. send ``MAC_IPV4_TCP`` matched packets, check all packets are distributed to queue 1.
   send the mismatched packets, check all packets are distributed to all queues.

3. verify rules can be listed and destroyed::

      testpmd> flow list 0

   check the rule listed.
   destroy the rule::

      testpmd> flow destroy 0 rule 0

4. verify matched packets are distributed to all queues.
   check there is no rule listed.

Subcase 2: MAC_IPV4_TCP rss queue
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss queues 0 1 2 3 end / end

2. send ``MAC_IPV4_TCP`` matched packets, check all packets are distributed to queue 0-3.
   send the mismatched packets, check all packets are distributed to all queues.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to all queues.
   check there is no rule listed.

Subcase 3: MAC_IPV4_TCP passthru
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions passthru / mark id 1 / end

2. send ``MAC_IPV4_TCP`` matched packets, check all packets are distributed to all queue with FDIR matched ID=0x1.
   send the mismatched packets, check all packets are distributed to all queues without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to all queues without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_TCP drop
>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions drop / end

2. send ``MAC_IPV4_TCP`` matched packets, check all packets are dropped.
   send the mismatched packets, check all packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_TCP mark+rss
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions mark id 2 / rss / end

2. send ``MAC_IPV4_TCP`` matched packets, check all packets are distributed to all queue with FDIR matched ID=0x2.
   send the mismatched packets, check all packets are distributed to all queues without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to all queues without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_TCP mark
>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions mark id 1 / end

2. repeat the step 2-3 of in subcase 3,
   get the same result.

Test Case: MAC_IPV4_UDP_WITHOUT_INPUT_SET
-----------------------------------------

1. replace "tcp" with "udp" in all the subcases of MAC_IPV4_TCP_WITHOUT_INPUT_SET pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_TCP_WITHOUT_INPUT_SET pattern.
3. get the same result.

Test Case: MAC_IPV6_TCP_WITHOUT_INPUT_SET
-----------------------------------------

Subcase 1: MAC_IPV6_TCP queue index
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / tcp / end actions queue index 1 / end

2. send ``MAC_IPV6_TCP`` matched packets, check all packets are distributed to queue 1.
   send the mismatched packets, check all packets are distributed to all queues.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

      testpmd> flow destroy 0 rule 0

4. verify matched packets are distributed to all queues.
   check there is no rule listed.

Subcase 2: MAC_IPV6_TCP rss queue
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss queues 0 1 2 3 end / end

2. send ``MAC_IPV6_TCP`` matched packets, check all packets are distributed to queue 0-3.
   send the mismatched packets, check all packets are distributed to all queues.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to all queues.
   check there is no rule listed.

Subcase 3: MAC_IPV6_TCP passthru
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / tcp / end actions passthru / mark id 1 / end

2. send ``MAC_IPV6_TCP`` matched packets, check all packets are distributed to all queue with FDIR matched ID=0x1.
   send mismatched packets, check all packets are distributed to all queues without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to all queues without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV6_TCP drop
>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / tcp / end actions drop / end

2. send ``MAC_IPV6_TCP`` matched packets, check all packets are dropped.
   send the mismatched packets, check all packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV6_TCP mark+rss
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / tcp / end actions mark id 2 / rss / end

2. send ``MAC_IPV6_TCP`` matched packets, check all packets are distributed to all queue with FDIR matched ID=0x2.
   send the mismatched packets, check all packets are distributed to all queues without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to all queues without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV6_TCP mark
>>>>>>>>>>>>>>>>>>>>>>>>>>>>

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions mark id 1 / end

2. repeat the step 2-3 of in subcase 3,
   get the same result.

Test Case: MAC_IPV6_UDP_WITHOUT_INPUT_SET
-----------------------------------------

1. replace "tcp" with "udp" in all the subcases of MAC_IPV6_TCP_WITHOUT_INPUT_SET pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV6_TCP_WITHOUT_INPUT_SET pattern.
3. get the same result.

Test case: MAC_IPV4_GTPU_IPV4 pattern
=====================================

Subcase 1: MAC_IPV4_GTPU_IPV4 inner src ip queue index
------------------------------------------------------
all index cases steps and expected result are the same

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 1 with FDIR matched ID=0x1.
   send mismatched packets, check the packets are not distributed to queue 1 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 2: MAC_IPV4_GTPU_IPV4 inner src ip rss queues
-----------------------------------------------------
all rss queues cases steps and expected result are the same

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / end actions rss queues 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 2 or queue 3 with FDIR matched ID=0x1.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 3: MAC_IPV4_GTPU_IPV4 inner src ip passthru
---------------------------------------------------
all passthru cases steps and expected result are the same

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 4: MAC_IPV4_GTPU_IPV4 inner src ip drop
-----------------------------------------------
all drop cases steps and expected result are the same

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   Then check there is no rule listed.

Subcase 5: MAC_IPV4_GTPU_IPV4 inner src ip mark+rss
---------------------------------------------------
all mark+rss cases steps and expected result are the same

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / end actions rss / mark / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are received without FDIR matched ID.
   Then check there is no rule listed.

Subcase 6: MAC_IPV4_GTPU_IPV4 inner dst ip queue index
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of subcase 1.

Subcase 7: MAC_IPV4_GTPU_IPV4 inner dst ip rss queues
-----------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of subcase 2.

Subcase 8: MAC_IPV4_GTPU_IPV4 inner dst ip passthru
---------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / end actions passthru / mark id 1 / end

replace rule and repeat step of subcase 3.

Subcase 9: MAC_IPV4_GTPU_IPV4 inner dst ip drop
------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / end actions drop / end

replace rule and repeat step of subcase 4.

Subcase 10: MAC_IPV4_GTPU_IPV4 inner dst ip mark+rss
----------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / end actions rss / mark / end

replace rule and repeat step of subcase 5.

Subcase 11: MAC_IPV4_GTPU_IPV4 2 tuple queue index
--------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 12: MAC_IPV4_GTPU_IPV4 2 tuple queue group
--------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 13: MAC_IPV4_GTPU_IPV4 2 tuple passthru
-----------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark id 1 / end

replace rule and repeat step of subcase 3.

Subcase 14: MAC_IPV4_GTPU_IPV4 2 tuple drop
-------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end

replace rule and repeat step of subcase 4.

Subcase 15: MAC_IPV4_GTPU_IPV4 2 tuple mark/rss
-----------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss / mark / end

replace rule and repeat step of subcase 5.

Test case: MAC_IPV4_GTPU_IPV4_TCP pattern
=========================================

Subcase 1: MAC_IPV4_GTPU_IPV4_TCP inner src ip queue index
----------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / tcp / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 2: MAC_IPV4_GTPU_IPV4_TCP inner src ip rss queues
---------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / tcp / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 3: MAC_IPV4_GTPU_IPV4_TCP inner src ip passthru
-------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / tcp / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 4: MAC_IPV4_GTPU_IPV4_TCP inner src ip drop
---------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / tcp / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 5: MAC_IPV4_GTPU_IPV4_TCP inner src ip mark+rss
-------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 / tcp / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 6: MAC_IPV4_GTPU_IPV4_TCP inner dst ip queue index
----------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / tcp / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 7: MAC_IPV4_GTPU_IPV4_TCP inner dst ip rss queues
---------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / tcp / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 8: MAC_IPV4_GTPU_IPV4_TCP inner dst ip passthru
-------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / tcp / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 9: MAC_IPV4_GTPU_IPV4_TCP inner dst ip drop
----------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / tcp / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 10: MAC_IPV4_GTPU_IPV4_TCP inner dst ip mark+rss
--------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 dst is 192.168.0.21 / tcp / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 11: MAC_IPV4_GTPU_IPV4_TCP 4 tuple queue index
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 12: MAC_IPV4_GTPU_IPV4_TCP 4 tuple queue group
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 13: MAC_IPV4_GTPU_IPV4_TCP 4 tuple passthru
---------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 14: MAC_IPV4_GTPU_IPV4_TCP 4 tuple drop
-----------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 15: MAC_IPV4_GTPU_IPV4_TCP 4 tuple mark/rss
---------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss/ mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 16: MAC_IPV4_GTPU_IPV4_TCP inner src port queue index
-------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 17: MAC_IPV4_GTPU_IPV4_TCP inner src port queue group
-------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 18: MAC_IPV4_GTPU_IPV4_TCP inner src port passthru
----------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 19: MAC_IPV4_GTPU_IPV4_TCP inner src port drop
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 20: MAC_IPV4_GTPU_IPV4_TCP inner src port mark/rss
----------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp src is 22 / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 21: MAC_IPV4_GTPU_IPV4_TCP inner dst port queue index
-------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 22: MAC_IPV4_GTPU_IPV4_TCP inner dst port queue group
-------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 23: MAC_IPV4_GTPU_IPV4_TCP inner dst port passthru
----------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 24: MAC_IPV4_GTPU_IPV4_TCP inner dst port drop
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 25: MAC_IPV4_GTPU_IPV4_TCP inner dst port mark/rss
----------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp dst is 23 / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 26: MAC_IPV4_GTPU_IPV4_TCP without inputset queue index
---------------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/TCP()/("X"*480)], iface="ens192f0")

   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/UDP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/SCTP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IP()/ICMP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/IPv6()/TCP()/("X"*480)], iface="ens192f0")

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 27: MAC_IPV4_GTPU_IPV4_TCP without inputset queue group
---------------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src / udp / gtpu / ipv4 / tcp / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets of subcase 26, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets of subcase 26, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 28: MAC_IPV4_GTPU_IPV4_TCP without inputset passthru
------------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions passthru / mark id 1 / end

2. send matched packets of subcase 26, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets of subcase 26, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 29: MAC_IPV4_GTPU_IPV4_TCP without inputset drop
--------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions drop / end

2. send matched packets of subcase 26, check the packets are dropped.
   send mismatched packets of subcase 26, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 30: MAC_IPV4_GTPU_IPV4_TCP without inputset mark/rss
------------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss / mark / end

2. send matched packets of subcase 26, check the packets are redirected by RSS with FDIR matched ID=0x0.
   send mismatched packets of subcase 26, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Test case: MAC_IPV4_GTPU_IPV4_UDP pattern
=========================================

1. replace "tcp" with "udp" in all the subcases of MAC_IPV4_GTPU_IPV4_TCP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_IPV4_TCP pattern.
3. get the same result.

Test case: MAC_IPV4_GTPU_EH_IPV4 pattern
========================================

Subcase 1: MAC_IPV4_GTPU_EH_IPV4 inner src ip queue index
---------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 2: MAC_IPV4_GTPU_EH_IPV4 inner src ip rss queues
--------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 3: MAC_IPV4_GTPU_EH_IPV4 inner src ip passthru
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 4: MAC_IPV4_GTPU_EH_IPV4 inner src ip drop
--------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 5: MAC_IPV4_GTPU_EH_IPV4 inner src ip mark+rss
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 6: MAC_IPV4_GTPU_EH_IPV4 inner dst ip queue index
---------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 7: MAC_IPV4_GTPU_EH_IPV4 inner dst ip rss queues
--------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 8: MAC_IPV4_GTPU_EH_IPV4 inner dst ip passthru
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 9: MAC_IPV4_GTPU_EH_IPV4 inner dst ip drop
--------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 10: MAC_IPV4_GTPU_EH_IPV4 inner dst ip mark+rss
-------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 11: MAC_IPV4_GTPU_EH_IPV4 2 tuple queue index
-----------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 12: MAC_IPV4_GTPU_EH_IPV4 2 tuple queue group
-----------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 13: MAC_IPV4_GTPU_EH_IPV4 2 tuple passthru
--------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 14: MAC_IPV4_GTPU_EH_IPV4 2 tuple drop
----------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 15: MAC_IPV4_GTPU_EH_IPV4 2 tuple mark/rss
--------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark id 1 / rss / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.


Test case: MAC_IPV4_GTPU_EH_IPV4_TCP pattern
============================================

Subcase 1: MAC_IPV4_GTPU_EH_IPV4_TCP inner src ip queue index
-------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / tcp / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 2: MAC_IPV4_GTPU_EH_IPV4_TCP inner src ip rss queues
------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / tcp / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 3: MAC_IPV4_GTPU_EH_IPV4_TCP inner src ip passthru
----------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / tcp / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 4: MAC_IPV4_GTPU_EH_IPV4_TCP inner src ip drop
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / tcp / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 5: MAC_IPV4_GTPU_EH_IPV4_TCP inner src ip mark+rss
----------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 / tcp / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 6: MAC_IPV4_GTPU_EH_IPV4_TCP inner dst ip queue index
-------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / tcp / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 7: MAC_IPV4_GTPU_EH_IPV4_TCP inner dst ip rss queues
------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / tcp / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 8: MAC_IPV4_GTPU_EH_IPV4_TCP inner dst ip passthru
----------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / tcp / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 9: MAC_IPV4_GTPU_EH_IPV4_TCP inner dst ip drop
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / tcp / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 10: MAC_IPV4_GTPU_EH_IPV4_TCP inner dst ip mark+rss
-----------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 dst is 192.168.0.21 / tcp / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 11: MAC_IPV4_GTPU_EH_IPV4_TCP 4 tuple queue index
---------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 12: MAC_IPV4_GTPU_EH_IPV4_TCP 4 tuple queue group
---------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 13: MAC_IPV4_GTPU_EH_IPV4_TCP 4 tuple passthru
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 14: MAC_IPV4_GTPU_EH_IPV4_TCP 4 tuple drop
--------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 15: MAC_IPV4_GTPU_EH_IPV4_TCP 4 tuple mark/rss
------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 16: MAC_IPV4_GTPU_EH_IPV4_TCP inner src port queue index
----------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 17: MAC_IPV4_GTPU_EH_IPV4_TCP inner src port queue group
----------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 18: MAC_IPV4_GTPU_EH_IPV4_TCP inner src port passthru
-------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 19: MAC_IPV4_GTPU_EH_IPV4_TCP inner src port drop
---------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 20: MAC_IPV4_GTPU_EH_IPV4_TCP inner src port mark/rss
-------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp src is 22 / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 21: MAC_IPV4_GTPU_EH_IPV4_TCP inner dst port queue index
----------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions queue index 1 / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 1.

Subcase 22: MAC_IPV4_GTPU_EH_IPV4_TCP inner dst port queue group
----------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions rss queues 2 3 end / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 2.

Subcase 23: MAC_IPV4_GTPU_EH_IPV4_TCP inner dst port passthru
-------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions passthru / mark id 1 / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 3.

Subcase 24: MAC_IPV4_GTPU_EH_IPV4_TCP inner dst port drop
---------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions drop / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 4.

Subcase 25: MAC_IPV4_GTPU_EH_IPV4_TCP inner dst port mark/rss
-------------------------------------------------------------

rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp dst is 23 / end actions rss / mark / end

replace rule and repeat step of MAC_IPV4_GTPU_IPV4 pattern subcase 5.

Subcase 26: MAC_IPV4_GTPU_EH_IPV4_TCP without inputset queue index
------------------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/TCP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/TCP()/("X"*480)], iface="ens192f0")

   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/UDP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/SCTP()("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/ICMP()("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IPv6()/TCP()/("X"*480)], iface="ens192f0")

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 27: MAC_IPV4_GTPU_EH_IPV4_TCP without inputset queue group
------------------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets of subcase 26, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets of subcase 26, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 28: MAC_IPV4_GTPU_EH_IPV4_TCP without inputset passthru
---------------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions passthru / mark id 1 / end

2. send matched packets of subcase 26, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets of subcase 26, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 29: MAC_IPV4_GTPU_EH_IPV4_TCP without inputset drop
-----------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions drop / end

2. send matched packets of subcase 26, check the packets are dropped.
   send mismatched packets of subcase 26, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 30: MAC_IPV4_GTPU_EH_IPV4_TCP without inputset mark/rss
---------------------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss / mark / end

2. send matched packets of subcase 26, check the packets are redirected by RSS with FDIR matched ID=0x0.
   send mismatched packets of subcase 26, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH_IPV4_UDP pattern
============================================

1. replace "tcp" with "udp" in all the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
3. get the same result.

Test case: MAC_IPV4_GTPU_EH_DL_IPV4_TCP pattern
===============================================

without inputset match packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/TCP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP()/("X"*480)], iface="ens192f0")

without inputset mismatch packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/TCP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/UDP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/ICMP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6()/TCP()/("X"*480)], iface="ens192f0")

1. replace "gtp_psc" with "gtp_psc pdu_t is 0" in all the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
2. replace without inputset packets in the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
4. get the same result.

Test case: MAC_IPV4_GTPU_EH_DL_IPV4_UDP pattern
===============================================

1. replace "tcp" with "udp" in all the subcases of MAC_IPV4_GTPU_EH_DL_IPV4_TCP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_DL_IPV4_TCP pattern.
3. get the same result.

Test case: MAC_IPV4_GTPU_EH_UL_IPV4 pattern
===========================================

1. replace "gtp_psc" with "gtp_psc pdu_t is 1" in all the subcases of MAC_IPV4_GTPU_EH_IPV4 pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_IPV4 pattern.
3. get the same result.

Test case: MAC_IPV4_GTPU_EH_UL_IPV4_TCP pattern
===============================================

without inputset match packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/TCP()/("X"*480)], iface="ens192f0")

without inputset mismatch packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP()/TCP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer()/IP()/TCP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/UDP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/SCTP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP()/ICMP()/("X"*480)], iface="ens192f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6()/TCP()/("X"*480)], iface="ens192f0")

1. replace "gtp_psc" with "gtp_psc pdu_t is 1" in all the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
2. replace without inputset packets in the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
4. get the same result.

Test case: MAC_IPV4_GTPU_EH_UL_IPV4_UDP pattern
===============================================
1. replace "tcp" with "udp" in all the subcases of MAC_IPV4_GTPU_EH_UL_IPV4_TCP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_UL_IPV4_TCP pattern.
3. get the same result.

Test case: MAC_IPV4_GTPU_IPV6 pattern
=====================================
1. replace inner "ipv4" with "ipv6" in all the subcases of MAC_IPV4_GTPU_IPV4 pattern.
2. replace inner ipv4 src/dst ip with ipv6 src/dst value in all the subcases of MAC_IPV4_GTPU_IPV4 pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_IPV4 pattern.
4. get the same result

Test case: MAC_IPV4_GTPU_IPV6_TCP pattern
=========================================
1. replace inner "ipv4" with "ipv6" in all the subcases of MAC_IPV4_GTPU_IPV4_TCP pattern.
2. replace inner ipv4 src/dst ip with ipv6 src/dst value in all the subcases of MAC_IPV4_GTPU_IPV4_TCP pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_IPV4_TCP pattern.
4. get the same result

Test case: MAC_IPV4_GTPU_IPV6_UDP pattern
=========================================
1. replace inner "ipv4" with "ipv6" in all the subcases of MAC_IPV4_GTPU_IPV4_UDP pattern.
2. replace inner ipv4 src/dst ip with ipv6 src/dst value in all the subcases of MAC_IPV4_GTPU_IPV4_UDP pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_IPV4_UDP pattern.
4. get the same result

Test case: MAC_IPV4_GTPU_EH_IPV6_TCP pattern
============================================
1. replace inner "ipv4" with "ipv6" in all the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
2. replace inner ipv4 src/dst ip with ipv6 src/dst value in all the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_IPV4_TCP pattern.
4. get the same result

Test case: MAC_IPV4_GTPU_EH_IPV6_UDP pattern
============================================
1. replace inner "ipv4" with "ipv6" in all the subcases of MAC_IPV4_GTPU_EH_IPV6_UDP pattern.
2. replace inner ipv4 src/dst ip with ipv6 src/dst value in all the subcases of MAC_IPV4_GTPU_EH_IPV6_UDP pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_IPV6_UDP pattern.
4. get the same result.

Test case: MAC_IPV4_GTPU_EH_DL_IPV6_TCP pattern
===============================================
1. replace inner "ipv4" with "ipv6" in all the subcases of MAC_IPV4_GTPU_EH_DL_IPV4_TCP pattern.
2. replace inner ipv4 src/dst ip with ipv6 src/dst value in all the subcases of MAC_IPV4_GTPU_EH_DL_IPV4_TCP pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_DL_IPV4_TCP pattern.
4. get the same result

Test case: MAC_IPV4_GTPU_EH_DL_IPV6_UDP pattern
===============================================
1. replace inner "ipv4" with "ipv6" in all the subcases of MAC_IPV4_GTPU_EH_DL_IPV6_UDP pattern.
2. replace inner ipv4 src/dst ip with ipv6 src/dst value in all the subcases of MAC_IPV4_GTPU_EH_DL_IPV6_UDP pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_DL_IPV6_UDP pattern.
4. get the same result.

Test case: MAC_IPV4_GTPU_EH_UL_IPV6_TCP pattern
===============================================
1. replace inner "ipv4" with "ipv6" in all the subcases of MAC_IPV4_GTPU_EH_UL_IPV4_TCP pattern.
2. replace inner ipv4 src/dst ip with ipv6 src/dst value in all the subcases of MAC_IPV4_GTPU_EH_UL_IPV4_TCP pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_UL_IPV4_TCP pattern.
4. get the same result.

Test case: MAC_IPV4_GTPU_EH_UL_IPV6_UDP pattern
===============================================
1. replace inner "ipv4" with "ipv6" in all the subcases of MAC_IPV4_GTPU_EH_UL_IPV6_UDP pattern.
2. replace inner ipv4 src/dst ip with ipv6 src/dst value in all the subcases of MAC_IPV4_GTPU_EH_UL_IPV6_UDP pattern.
3. Then repeat all the steps in all the subcases of MAC_IPV4_GTPU_EH_UL_IPV6_UDP pattern.
4. get the same result.

Test case: GTPU inner co-exist test
===================================

Subcase 1: inner IPv4 gtpu conflict rule
-----------------------------------------

Rules::

   #1 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end
   #2 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #3 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #4 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end
   #5 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #6 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #7 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end
   #8 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #9 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #10 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 10 / mark id 1 / end
   #11 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #12 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end

packets::

   pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
   pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
   pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
   pkt4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
   pkt5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
   pkt6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
   pkt7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
   pkt8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
   pkt9 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)
   pkt10 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/Raw('x'*20)
   pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/TCP(sport=22, dport=23)/Raw('x'*20)
   pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(sport=22, dport=23)/Raw('x'*20)

1. First create #1 rule, verify #2/3 rule create failed and #4 create successfully.
   send match packets(pkt1/4), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

2. destroy #1 rule, verify #5-12 any rule create failed and #2 create successfully.
   send match packets(pkt2/4), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

3. destroy #4 rule, verify #1 rule create failed and #5 create successfully.
   send match packets(pkt2/5), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

4. destroy #2 rule, verify #4/7/8/10/11 rule create failed and #6 create successfully.
   send match packets(pkt5/6), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

5. destroy #5 rule, verify #4/7/9/10/12 rule create failed and #8 create successfully.
   send match packets(pkt6/8), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

6. destroy #6 rule, verify #4/5/7 rule create failed and #9 create successfully.
   send match packets(pkt8/9), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

7. destroy #8 rule, verify #4/6/7 rule create failed and #10 create successfully.
   send match packets(pkt9/10), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

8. destroy #9 rule, verify #4/5/6/11/12 rule create failed and #7 create successfully.
   send match packets(pkt7/10), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

9. destroy #10 rule, verify #4/5/6/8/9 rule create failed and #11 create successfully.
   send match packets(pkt7/11), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

10. verify #4/5/6/8/9/10 rule create failed and #12 create successfully.
    send match packets(pkt7/11/12), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

11. verify #4/5/6/8/9/10 rule create failed and #3 create successfully.
    send match packets(pkt3/7/11/12), check the packets are distributed to queue 10 with FDIR matched ID=0x1.

Subcase 2: inner IPv6 gtpu conflict rule
----------------------------------------

Rules::

   #1 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end
   #2 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #3 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #4 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end
   #5 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #6 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #7 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end
   #8 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #9 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #10 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / end actions queue index 10 / mark id 1 / end
   #11 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / tcp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end
   #12 flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 src is 2001::2 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 / udp src is 22 dst is 23 / end actions queue index 10 / mark id 1 / end

packets::

   pkt1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
   pkt2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
   pkt3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
   pkt4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
   pkt5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
   pkt6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer()/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
   pkt7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
   pkt8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
   pkt9 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=0)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)
   pkt10 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/Raw('x'*20)
   pkt11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/Raw('x'*20)
   pkt12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header()/GTPPDUSessionContainer(type=1)/IPv6(src="2001::2", dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/Raw('x'*20)

repeat step 1-12 of subcase 1.

Test case: MAC_IPV4_GRE_IPV4 pattern
====================================

Subcase 1: MAC_IPV4_GRE_IPV4 queue index
----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1 without FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 1 without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are not distributed to queue 1 without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_GRE_IPV4 rss queues
---------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions rss queues 2 3 end / end

2. send matched packets, check the packets are distributed to queue 2 or 3 without FDIR matched ID.
   send mismatched packets, check the packets are not distributed to queue 2 or 3 without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not distributed to queue 2 or 3 without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_GRE_IPV4 passthru
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions passthru / end

2. send matched packets, check the packets are distributed by RSS without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID=0x0.
   check there is no rule listed.

Subcase 4: MAC_IPV4_GRE_IPV4 drop
---------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions drop / end

2. send matched packets, check the packets are dropped
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_GRE_IPV4 mark+rss
-------------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions mark / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_GRE_IPV4 mark
---------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / end actions mark / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Test case: MAC_IPV6_GRE_IPV4 pattern
====================================

Subcase 1: MAC_IPV6_GRE_IPV4 queue index
----------------------------------------

Subcase 2: MAC_IPV6_GRE_IPV4 rss queues
---------------------------------------

Subcase 3: MAC_IPV6_GRE_IPV4 passthru
-------------------------------------

Subcase 4: MAC_IPV6_GRE_IPV4 drop
---------------------------------

Subcase 5: MAC_IPV6_GRE_IPV4 mark+rss
-------------------------------------

Subcase 6: MAC_IPV6_GRE_IPV4 mark
---------------------------------

each subcase is the same as the subcase of Test case: MAC_IPV4_GRE_IPV4 pattern, just only pattern is different,
replace it with 'eth / ipv6 / gre / ipv4'

Test case: MAC_IPV4_GRE_IPV6 pattern
====================================

Subcase 1: MAC_IPV4_GRE_IPV6 queue index
----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions queue index 15 / mark / end

2. send matched packets, check the packets is distributed to queue 15 with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_GRE_IPV6 rss queues
---------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions rss queues 8 9 10 11 12 13 14 15 end / mark id 1/ end

2. send matched packets, check the packets is distributed to queue 8-15 with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_GRE_IPV6 passthru
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions passthru / mark / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are destributed to the same queue without FDIR matched ID .
   check there is no rule listed.

Subcase 4: MAC_IPV4_GRE_IPV6 drop
---------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packet is dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_GRE_IPV6 mark+rss
-------------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions mark / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_GRE_IPV6 mark
---------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / end actions mark / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are destributed to the same queue without FDIR matched ID .
   check there is no rule listed.

Test case: MAC_IPV6_GRE_IPV6 pattern
====================================

Subcase 1: MAC_IPV6_GRE_IPV6 queue index
----------------------------------------

Subcase 2: MAC_IPV6_GRE_IPV6 rss queues
---------------------------------------

Subcase 3: MAC_IPV6_GRE_IPV6 passthru
-------------------------------------

Subcase 4: MAC_IPV6_GRE_IPV6 drop
---------------------------------

Subcase 5: MAC_IPV4_GRE_IPV6 mark+rss
-------------------------------------

Subcase 6: MAC_IPV6_GRE_IPV6 mark
---------------------------------

each subcase is the same as the subcase of Test case: MAC_IPV4_GRE_IPV6 pattern, just only pattern is different,
replace it with 'eth / ipv6 / gre / ipv6'

Test case: MAC_IPV4_GRE_IPV4_TCP pattern
========================================

Subcase 1: MAC_IPV4_GRE_IPV4_TCP queue index
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end

2. send matched packets, check the packets is distributed to queue 1 with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_GRE_IPV4_TCP rss queues
-------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions rss queues 1 2 3 4 end / mark id 4294967294 / end

2. send matched packets, check the packets is distributed to queue 1-4 with FDIR matched ID=0xfffffffe.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_GRE_IPV4_TCP passthru
-----------------------------------------

1. create filter rule with mark::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_GRE_IPV4_TCP drop
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions drop / end

2. send matched packet, check the packet is dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packet is dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_GRE_IPV4_TCP mark+rss
-----------------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 2 / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x2
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_GRE_IPV4_TCP mark
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 1 / end

2. repeat the step 2-3 of in subcase 3,
   get the same result.

Test case: MAC_IPV6_GRE_IPV4_TCP pattern
========================================

Subcase 1: MAC_IPV6_GRE_IPV4_TCP queue index
--------------------------------------------

Subcase 2: MAC_IPV6_GRE_IPV4_TCP rss queues
-------------------------------------------

Subcase 3: MAC_IPV6_GRE_IPV4_TCP passthru
-----------------------------------------

Subcase 4: MAC_IPV6_GRE_IPV4_TCP drop
-------------------------------------

Subcase 5: MAC_IPV6_GRE_IPV4_TCP mark+rss
-----------------------------------------

Subcase 6: MAC_IPV6_GRE_IPV4_TCP mark
-------------------------------------

each subcase is the same as the subcase of Test case: MAC_IPV4_GRE_IPV4_TCP pattern, just only pattern is different,
replace it with 'eth / ipv6 / gre / ipv4 / tcp'

Test case: MAC_IPV4_GRE_IPV6_TCP pattern
========================================

Subcase 1: MAC_IPV4_GRE_IPV6_TCP queue index
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / end

2. send matched packets, check the packets is distributed to queue 1 with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_GRE_IPV6_TCP rss queues
-------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions rss queues 4 5 6 7 end / mark id 4294967294 / end

2. send matched packets, check the packets is distributed to queue 4-7 with FDIR matched ID=0xfffffffe.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_GRE_IPV6_TCP passthru
-----------------------------------------

1. create filter rule with mark::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_GRE_IPV6_TCP drop
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions drop / end

2. send matched packet, check the packet is dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packet is dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_GRE_IPV6_TCP mark+rss
-----------------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions mark id 2 / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x2
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_GRE_IPV6_TCP mark
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / gre / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 tc is 1 / tcp src is 22 dst is 23 / end actions mark id 1 / end

2. repeat the step 2-3 of in subcase 3,
   get the same result.

Test case: MAC_IPV6_GRE_IPV6_TCP pattern
========================================

Subcase 1: MAC_IPV6_GRE_IPV6_TCP queue index
--------------------------------------------

Subcase 2: MAC_IPV6_GRE_IPV6_TCP rss queues
-------------------------------------------

Subcase 3: MAC_IPV6_GRE_IPV6_TCP passthru
-----------------------------------------

Subcase 4: MAC_IPV6_GRE_IPV6_TCP drop
-------------------------------------

Subcase 5: MAC_IPV6_GRE_IPV6_TCP mark+rss
-----------------------------------------

Subcase 6: MAC_IPV6_GRE_IPV6_TCP mark
-------------------------------------

each subcase is the same as the subcase of Test case: MAC_IPV4_GRE_IPV6_TCP pattern, just only pattern is different,
replace it with 'eth / ipv6 / gre / ipv6 / tcp'

Test case: MAC_IPV4_GRE_IPV4_UDP pattern
========================================

Subcase 1: MAC_IPV4_GRE_IPV4_UDP queue index
--------------------------------------------

Subcase 2: MAC_IPV4_GRE_IPV4_UDP rss queues
-------------------------------------------

Subcase 3: MAC_IPV4_GRE_IPV4_UDP passthru
-----------------------------------------

Subcase 4: MAC_IPV4_GRE_IPV4_UDP drop
-------------------------------------

Subcase 5: MAC_IPV4_GRE_IPV4_UDP mark+rss
-----------------------------------------

Subcase 6: MAC_IPV4_GRE_IPV4_UDP mark
-------------------------------------

each subcase is the same as the subcase of Test case: MAC_IPV4_GRE_IPV4_TCP pattern, just only pattern is different,
replace "tcp" with "udp" in all the subcases

Test case: MAC_IPV4_GRE_IPV6_UDP pattern
========================================

Subcase 1: MAC_IPV4_GRE_IPV6_UDP queue index
--------------------------------------------

Subcase 2: MAC_IPV4_GRE_IPV6_UDP rss queues
-------------------------------------------

Subcase 3: MAC_IPV4_GRE_IPV6_UDP passthru
-----------------------------------------

Subcase 4: MAC_IPV4_GRE_IPV6_UDP drop
-------------------------------------

Subcase 5: MAC_IPV4_GRE_IPV6_UDP mark+rss
-----------------------------------------

Subcase 6: MAC_IPV4_GRE_IPV6_UDP mark
-------------------------------------

each subcase is the same as the subcase of Test case: MAC_IPV4_GRE_IPV6_TCP pattern, just only pattern is different,
replace "tcp" with "udp" in all the subcases

Test case: MAC_IPV6_GRE_IPV4_UDP pattern
========================================

Subcase 1: MAC_IPV6_GRE_IPV4_UDP queue index
--------------------------------------------

Subcase 2: MAC_IPV6_GRE_IPV4_UDP rss queues
-------------------------------------------

Subcase 3: MAC_IPV6_GRE_IPV4_UDP passthru
-----------------------------------------

Subcase 4: MAC_IPV6_GRE_IPV4_UDP drop
-------------------------------------

Subcase 5: MAC_IPV6_GRE_IPV4_UDP mark+rss
-----------------------------------------

Subcase 6: MAC_IPV6_GRE_IPV4_UDP mark
-------------------------------------

each subcase is the same as the subcase of Test case: MAC_IPV6_GRE_IPV4_TCP pattern, just only pattern is different,
replace "tcp" with "udp" in all the subcases

Test case: MAC_IPV6_GRE_IPV6_UDP pattern
========================================

Subcase 1: MAC_IPV6_GRE_IPV6_UDP queue index
--------------------------------------------

Subcase 2: MAC_IPV6_GRE_IPV6_UDP rss queues
-------------------------------------------

Subcase 3: MAC_IPV6_GRE_IPV6_UDP passthru
-----------------------------------------

Subcase 4: MAC_IPV6_GRE_IPV6_UDP drop
-------------------------------------

Subcase 5: MAC_IPV6_GRE_IPV6_UDP mark+rss
-----------------------------------------

Subcase 6: MAC_IPV6_GRE_IPV6_UDP mark
-------------------------------------

each subcase is the same as the subcase of Test case: MAC_IPV6_GRE_IPV6_TCP pattern, just only pattern is different,
replace "tcp" with "udp" in all the subcases
