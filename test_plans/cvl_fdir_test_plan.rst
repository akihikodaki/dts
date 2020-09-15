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

================================
CVL:Classification:Flow Director
================================

Enable fdir filter for IPv4/IPv6 + TCP/UDP/SCTP  (OS default package)
Enable fdir filter for UDP tunnel: Vxlan / NVGRE (OS default package)
Enable fdir filter for GTP (comm #1 package)
Enable fdir filter for L2 Ethertype (comm #1 package)

Pattern and input set
---------------------

    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |    Packet Type               |        Pattern             |            Input Set                                                          |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    | IPv4/IPv6 + TCP/UDP/SCTP     |      MAC_IPV4_PAY          | [Dest MAC]，[Source IP], [Dest IP], [IP protocol], [TTL], [DSCP]              |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              |      MAC_IPV4_UDP          | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port] |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              |      MAC_IPV4_TCP          | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port] |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              |      MAC_IPV4_SCTP         | [Dest MAC]，[Source IP], [Dest IP], [TTL], [DSCP], [Source Port], [Dest Port] |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              |      MAC_IPV6_PAY          | [Dest MAC]，[Source IP], [Dest IP], [IP protocol], [TTL], [TC]                |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              |      MAC_IPV6_UDP          | [Dest MAC]，[Source IP], [Dest IP], [TTL], [TC], [Source Port], [Dest Port]   |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              |      MAC_IPV6_TCP          | [Dest MAC]，[Source IP], [Dest IP], [TTL], [TC], [Source Port], [Dest Port]   |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              |      MAC_IPV6_SCTP         | [Dest MAC]，[Source IP], [Dest IP], [TTL], [TC], [Source Port], [Dest Port]   |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    | UDP tunnel: VXLAN inner only | MAC_IPV4_TUN_IPV4_PAY      | [Inner Source IP], [Inner Dest IP]                                            |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV4_TUN_IPV4_UDP      | [Inner Source IP], [Inner Dest IP], [Inner Source Port], [Inner Dest Port]    |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV4_TUN_IPV4_TCP      | [Inner Source IP], [Inner Dest IP], [Inner Source Port], [Inner Dest Port]    |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV4_TUN_IPV4_SCTP     | [Inner Source IP], [Inner Dest IP], [Inner Source Port], [Inner Dest Port]    |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV4_TUN_MAC_IPV4_PAY  | [Inner Source IP], [Inner Dest IP]                                            |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV4_TUN_MAC_IPV4_UDP  | [Inner Source IP], [Inner Dest IP], [Inner Source Port], [Inner Dest Port]    |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV4_TUN_MAC_IPV4_TCP  | [Inner Source IP], [Inner Dest IP], [Inner Source Port], [Inner Dest Port]    |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV4_TUN_MAC_IPV4_SCTP | [Inner Source IP], [Inner Dest IP], [Inner Source Port], [Inner Dest Port]    |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    | IPv4/IPv6 + GTP-U            | MAC_IPV4_GTPU              | [Source IP], [Dest IP], [TEID]                                                |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV4_GTPU_EH           | [Source IP], [Dest IP], [TEID], [QFI]                                         |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV6_GTPU              | [Source IPV6], [Dest IPV6], [TEID]                                            |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV6_GTPU_EH           | [Source IPV6], [Dest IPV6], [TEID], [QFI]                                     |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    | L2 Ethertype                 |      L2 Ethertype          | [Ethertype]                                                                   |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+

.. note::

   1. Enable fdir filter for UDP tunnel: Vxlan / NVGRE (OS default package) , share code not support
      outer header as inputset, so Out Dest IP and VNI/GRE_KEY may not able to be implemented.
   2. For VXLAN case MAC_IPV4_TUN_*** means MAC_IPV4_UDP_VXLAN_***
   3. For Dest MAC, there is package /sharecode limitation on multicast dst mac support for FDIR

Function type
-------------

    validate
    create
    list
    destroy
    flush
    query

Action type
-----------

    queue index
    drop
    rss queues
    passthru
    count identifier 0x1234 shared on|off
    mark
    mark/rss


Prerequisites
=============

1. Hardware:
   columbiaville_25g/columbiaville_100g
   design the cases with 2 ports card.

2. Software:
   DPDK: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/intel/ice/ddp/ice.pkg
   Then reboot server, and compile DPDK

4. Bind the pf to dpdk driver::

    ./usertools/dpdk-devbind.py -b igb_uio 86:00.0 86:00.1

5. Launch the app ``testpmd`` with the following arguments::

    ./testpmd -c 0xff -n 6 -w 86:00.0,,flow-mark-support=1 --log-level="ice,7" -- -i --portmask=0xff --rxq=64 --txq=64 --port-topology=loop
    testpmd> set fwd rxonly
    testpmd> set verbose 1

   If set UDP tunnel flow rule::

    testpmd> port config 0 udp_tunnel_port add vxlan 4789
    testpmd> start

   Notes: if need two ports environment, launch ``testpmd`` with the following arguments::

    ./testpmd -c 0xff -n 6 -w 86:00.0,flow-mark-support=1 -w 86:00.1,flow-mark-support=1 --log-level="ice,7" -- -i --portmask=0xff --rxq=64 --txq=64 --port-topology=loop


Default parameters
------------------

   MAC::

    [Dest MAC]: 00:11:22:33:44:55

   IPv4::

    [Source IP]: 192.168.0.20
    [Dest IP]: 192.168.0.21
    [IP protocol]: 255
    [TTL]: 2
    [DSCP]: 4

   IPv6::

    [Source IPv6]: 2001::2
    [Dest IPv6]: CDCD:910A:2222:5498:8475:1111:3900:2020
    [IP protocol]: 1
    [TTL]: 2
    [TC]: 1

   UDP/TCP/SCTP::

    [Source Port]: 22
    [Dest Port]: 23

   VXLAN inner only::

    [Inner Source IP]: 192.168.0.20
    [Inner Dest IP]: 192.168.0.21
    [Inner Source Port]: 22
    [Inner Dest Port]: 23

   GTP-U data packet::

    [TEID]: 0x12345678
    [QFI]: 0x34

   L2 Ethertype::

    [Ethertype]: 0x8863 0x8864 0x0806 0x8100 0x88f7

Send packets
------------

* MAC_IPV4_PAY

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=255, ttl=2, tos=4)/Raw('x' * 80)],iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.1.21", proto=255, ttl=2, tos=4) / Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1, ttl=2, tos=4) / Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=3, tos=4) / Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=9) / Raw('x' * 80)],iface="enp175s0f0")

* MAC_IPV4_UDP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.19",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=21,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=24)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")

* MAC_IPV4_TCP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.19",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=21,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=24)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")

* MAC_IPV4_SCTP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:56")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.19",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=21,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=24)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=64, tos=4) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=1) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4)/Raw('x' * 80)],iface="enp175s0f0")

* MAC_IPV6_PAY

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)], iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:56")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2022", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::1", nh=0, tc=1, hlim=2)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=2, tc=1, hlim=2)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=2, hlim=2)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=5)/("X"*480)], iface="enp175s0f0")

* MAC_IPV6_UDP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:56")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=21,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=24)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

* MAC_IPV6_TCP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:56")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=21,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/TCP(sport=22,dport=24)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

* MAC_IPV6_SCTP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:56")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2002::2",tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=3, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=1)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=21,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/SCTP(sport=22,dport=24)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2",tc=1, hlim=2)/("X"*480)], iface="enp175s0f0")

* MAC_IPV4_TUN_IPV4_PAY/MAC_IPV4_TUN_MAC_IPV4_PAY

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21', frag=1)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.20")/("X"*480)], iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.22')], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.30', dst='192.168.0.21')], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IP(dst="192.168.0.21", src="192.168.0.20")/("X"*480)], iface="enp175s0f0")

* MAC_IPV4_TUN_IPV4_UDP/MAC_IPV4_TUN_MAC_IPV4_UDP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.20")/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.22')/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(src='192.168.0.21', dst='192.168.0.23')/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/UDP(sport=21,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/UDP(sport=22,dport=24)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/TCP(sport=22, dport=23)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IP(dst="192.168.0.21", src="192.168.0.20")/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

* MAC_IPV4_TUN_IPV4_TCP/MAC_IPV4_TUN_MAC_IPV4_TCP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.20")/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.22')/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.23")/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/TCP(sport=21,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/TCP(sport=22,dport=24)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/Raw('x' * 80)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IP(dst="192.168.0.21", src="192.168.0.20")/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

* MAC_IPV4_TUN_IPV4_SCTP/MAC_IPV4_TUN_MAC_IPV4_SCTP

   matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.20")/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

   mismatched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.22')/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", src="192.168.0.23")/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/SCTP(sport=21,dport=23)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/SCTP(sport=22,dport=24)/("X"*480)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst='192.168.1.15')/UDP(sport=200, dport=4790)/VXLAN(flags=0xc)/IP(src='192.168.0.20', dst='192.168.0.21')/UDP(sport=22, dport=23)/Raw('x' * 80)], iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/IP(dst="192.168.0.21", src="192.168.0.20")/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0")

* MAC_IPV4_GTPU_EH

   matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(frag=1)/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/ICMP()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/IPv6ExtHdrFragment(1000)/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu9 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu10 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/ICMP()/Raw('x'*20)

   mismatched packets::

    p_gtpu11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/SCTP()/Raw('x'*20)
    p_gtpu12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/SCTP()/Raw('x'*20)
    p_gtpu13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)
    p_gtpu14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)
    p_gtpu15 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw('x'*20)
    p_gtpu16 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/Raw('x'*20)

* MAC_IPV4_GTPU

   matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=1)/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/ICMP()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment(1000)/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu9 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu10 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/ICMP()/Raw('x'*20)
    p_gtpu11 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)

   mismatched packets::

    p_gtpu12 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/Raw('x'*20)
    p_gtpu13 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/SCTP()/Raw('x'*20)
    p_gtpu14 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/SCTP()/Raw('x'*20)
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


Test case: flow validation
==========================

1. validate MAC_IPV4_PAY with queue index action::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end

   get the message::

    Flow rule validated

2. repeat step 1 with all patterns in pattern and input set table,
   get the same result.

3. repeat step 1-2 with action rss queues/drop/passthru/mark/mark+rss,
   get the same result.

4. validate combined use of actions::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions count / end
    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark / count / end
    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 0 1 end / mark id 1 / count identifier 0x1234 shared on / end
    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark id 2 / count identifier 0x34 shared off / end
    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark id 3 / rss / count shared on / end
    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / count shared off / end

   get the message::

    Flow rule validated

5. check the flow list::

    testpmd> flow list 0

   there is no rule listed.

Test case: negative validation
==============================
Note: there may be error message change.

1. void action::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / and actions end

   get the message::

    Invalid argument

2. conflict action::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 2 3 end / rss / end

   get the message::

    Unsupported action combination: Invalid argument

3. invalid mark id::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / mark id 4294967296 / end

   get the message::

    Bad arguments

4. invalid input set::

    flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tc is 4 / end actions queue index 1 / end

   get the message::

    Bad arguments

5. invalid queue index::

    flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 64 / end

   get the message::

    Invalid input action: Invalid argument

6. invalid rss queues parameter

   Invalid number of queues::

    flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end
    flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 end / end
    flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues end / end

   get the message::

    Invalid input action: Invalid argument

   Discontinuous queues::

    flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end

   get the message::

    Discontinuous queue region: Invalid argument

   invalid rss queues index::

    flow validate 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 63 64 end / end

   get the message::

    Invalid queue region indexes.: Invalid argument

7. Invalid value of input set::

    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x100 / end actions queue index 1 / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc qfi is 0x5 / end actions queue index 2 / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / end actions queue index 1 / end

   get the message::

    Bad arguments

8. unsupported pattern,validate GTPU rule with OS default package::

    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end

   get the message::

    Bad arguments

9. invalid port::

     flow validate 2 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end

   get the message::

    No such device: No such device

10. check the flow list::

     testpmd> flow list 0

   there is no rule listed.


Test case: MAC_IPV4_PAY pattern
===============================

Subcase 1: MAC_IPV4_PAY queue index
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1 without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the rule listed.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_PAY rss queues
----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 2 3 end / end

2. send matched packets, check the packets are distributed to queue 2 or 3 without without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_PAY passthru
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / end

2. send matched packets, check the packets are distributed by RSS without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID=0x0.
   check there is no rule listed.

Subcase 4: MAC_IPV4_PAY drop
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / end

2. send matched packets, check the packets are dropped
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_PAY mark+rss
--------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed to the same queue without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_PAY mark
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark id 1 / end

2. repeat the steps of passthru with mark part in subcase 3,
   get the same result.

Subcase 7: MAC_IPV4_PAY protocal
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 1 / end actions queue index 1 / mark id 1 / end
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 17 / end actions passthru / mark id 3 / end

2. send matched packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1) / Raw('x' * 80)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=1) / Raw('x' * 80)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)
    pkt4 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)
    pkt5 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=17, ttl=2, tos=4)/Raw('x' * 80)
    pkt6 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=17, ttl=2, tos=4)/Raw('x' * 80)

   check the pkt1 and pkt2 are redirected to queue 1 with FDIR matched ID=0x1.
   check the pkt3-pkt6 are distributed by RSS with FDIR matched ID=0x3.
   send mismatched packets::

    pkt7 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", proto=1) / Raw('x' * 80)
    pkt8 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=6) / Raw('x' * 80)
    pkt9 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/ Raw('x' * 80)
    pkt10 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1)/TCP(sport=22,dport=23)/ Raw('x' * 80)

   check the packets received are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV4_UDP pattern
===============================

Subcase 1: MAC_IPV4_UDP queue index
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 63 / mark id 0 / end

2. send matched packets, check the packets is distributed to queue 63 with FDIR matched ID=0x0.
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

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 4294967294 / end

2. send matched packets, check the packets is distributed to queue 0-3 with FDIR matched ID=0xfffffffe.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_UDP passthru
--------------------------------

1. create filter rule with mark::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_UDP drop
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions drop / end

2. send matched packet, check the packet is dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packet is dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_UDP mark+rss
--------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark id 2 / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x2
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_UDP mark
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark id 1 / end

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

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions queue index 1 / mark / end

2. send matched packets, check the packets is distributed to queue 1 with FDIR matched ID=0x0.
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

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end \
    actions rss queues 56 57 58 59 60 61 62 63 end / mark / end

2. send matched packets, check the packets is distributed to queue 56-63 with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV6_PAY passthru
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions passthru / mark / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are destributed by RSS without FDIR matched ID .
   check there is no rule listed.

Subcase 4: MAC_IPV6_PAY drop
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packet is dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV6_PAY mark+rss
--------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV6_PAY mark
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions mark / end

2. repeat the steps of passthru in subcase 3,
   get the same result.

Subcase 7: MAC_IPV6_PAY protocal
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 44 / end actions rss queues 5 6 end / mark id 1 / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 6 / end actions mark id 2 / rss / end

2. send matched packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010", nh=44, tc=1, hlim=2)/("X"*480)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/IPv6ExtHdrFragment(b'1000')/("X"*480)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010", nh=44)/TCP(sport=22,dport=23)/("X"*480)
    pkt4 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="ABAB:910A:2222:5498:8475:1111:3900:1010")/IPv6ExtHdrFragment(b'1000')/TCP(sport=22,dport=23)/("X"*480)
    pkt5 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/("X"*480)
    pkt6 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)

   check pkt1-pkt4 are redirected to queue 5 or queue 6 with FDIR matched ID=0x1.
   check pkt5 and pkt6 are distributed by RSS with FDIR matched ID=0x2.
   send mismatched packets::

    pkt8 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)
    pkt9 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=17)/("X"*480)

   check the packets are distributed by RSS have not FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.


Test case: MAC_IPV6_UDP pattern
===============================

Subcase 1: MAC_IPV6_UDP queue index
-----------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end

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

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss / end

2. send matched packets, check the packets is distributed by RSS without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID too.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV6_UDP passthru
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are destributed by RSS without FDIR matched ID .
   check there is no rule listed.

Subcase 4: MAC_IPV6_UDP drop
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packet is dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV6_UDP mark+rss
--------------------------------
Note: This combined action is mark with RSS which is without queues specified.

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV6_UDP mark
----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark / end

2. repeat the steps of passthru in subcase 3,
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


Test case: MAC_IPV4_TUN_IPV4_PAY pattern
========================================

Subcase 1: MAC_IPV4_TUN_IPV4_PAY queue index
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1 without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_TUN_IPV4_PAY rss queues
-------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 end / mark / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_TUN_IPV4_PAY passthru
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_TUN_IPV4_PAY drop
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. check there is no rule listed.
   verify the packets hit the rule are not dropped.

Subcase 5: MAC_IPV4_TUN_IPV4_PAY mark/rss
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_TUN_IPV4_PAY mark
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark / end

2. repeat the steps of passthru in subcase 3,
   get the same result.


Test case: MAC_IPV4_TUN_IPV4_UDP pattern
========================================

Subcase 1: MAC_IPV4_TUN_IPV4_UDP queue index
--------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 1 with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_TUN_IPV4_UDP rss queues
-------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 38 39 40 41 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_TUN_IPV4_UDP passthru
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_TUN_IPV4_UDP drop
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are received without FDIR matched ID.

Subcase 5: MAC_IPV4_TUN_IPV4_UDP mark/rss
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_TUN_IPV4_UDP mark
-------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions mark id 1 / end

2. repeat the steps of passthru in subcase 3,
   get the same result.


Test case: MAC_IPV4_TUN_IPV4_TCP pattern
========================================

1. replace inner "udp" with "tcp" in all the subcases of MAC_IPV4_TUN_IPV4_UDP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_TUN_IPV4_UDP pattern.
3. get the same result.

Test case: MAC_IPV4_TUN_IPV4_SCTP pattern
=========================================

1. replace inner "udp" with "sctp" in all the subcases of MAC_IPV4_TUN_IPV4_UDP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_TUN_IPV4_UDP pattern.
3. get the same result.


Test case: MAC_IPV4_TUN_MAC_IPV4_PAY pattern
============================================

Subcase 1: MAC_IPV4_TUN_MAC_IPV4_PAY queue index
------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 0 / end

2. send matched packets, check the packets are distributed to queue 0 without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_TUN_MAC_IPV4_PAY rss queues
-----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 0 1 end / end

2. send matched packets, check the packets are distributed to queue group without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_TUN_MAC_IPV4_PAY passthru
---------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / end

2. send matched packets, check the packets are distributed by RSS without FDIR matched ID.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_TUN_MAC_IPV4_PAY drop
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are not dropped.
   check there is no rule listed.

Subcase 5: MAC_IPV4_TUN_MAC_IPV4_PAY mark/rss
---------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark / rss / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_TUN_MAC_IPV4_PAY mark
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark / end

2. repeat the steps of passthru in subcase 3,
   get the same result.

Test case: MAC_IPV4_TUN_MAC_IPV4_UDP pattern
============================================

Subcase 1: MAC_IPV4_TUN_MAC_IPV4_UDP queue index
------------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 15 / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 15 with FDIR matched ID=0x1.
   send mismatched packets, check the packets are received without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 2: MAC_IPV4_TUN_MAC_IPV4_UDP rss queues
-----------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 3: MAC_IPV4_TUN_MAC_IPV4_UDP passthru
---------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_TUN_MAC_IPV4_UDP drop
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / mark id 1 / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 5: MAC_IPV4_TUN_MAC_IPV4_UDP mark/rss
---------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss / mark id 1 / end

2. send matched packets, check the packets are distributed by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify the packets hit rule are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_TUN_MAC_IPV4_UDP mark
-----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions mark id 1 / end

2. repeat the steps of passthru in subcase 3,
   get the same result.


Test case: MAC_IPV4_TUN_MAC_IPV4_TCP pattern
============================================

1. replace inner "udp" with "tcp" in all the subcases of MAC_IPV4_TUN_MAC_IPV4_UDP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_TUN_MAC_IPV4_UDP pattern.
3. get the same result.

Test case: MAC_IPV4_TUN_MAC_IPV4_SCTP pattern
=============================================

1. replace inner "udp" with "sctp" in all the subcases of MAC_IPV4_TUN_MAC_IPV4_UDP pattern.
2. Then repeat all the steps in all the subcases of MAC_IPV4_TUN_MAC_IPV4_UDP pattern.
3. get the same result.

Test case: MAC_IPV4_GTPU_EH pattern
===================================

Subcase 1: MAC_IPV4_GTPU_EH queue index
---------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 1 / end

2. send matched packets, check the packets are distributed to queue 1 with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 2: MAC_IPV4_GTPU_EH queue group
---------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 2 3 end / mark id 1 / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x1.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 3: MAC_IPV4_GTPU_EH passthru
------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark id 1 / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR ID.
   check there is no rule listed.

Subcase 4: MAC_IPV4_GTPU_EH drop
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 5: MAC_IPV4_GTPU_EH mark/rss
------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x1.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   check there is no rule listed.

Subcase 6: MAC_IPV4_GTPU_EH mark
--------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / end

2. repeat the steps of passthru in subcase 3,
   get the same result.

Subcase 7: MAC_IPV4_GTPU_EH QFI queue index / mark
--------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / end actions queue index 1 / mark id 3 / end

2. send matched packets, check the packet is redirected to queue 1 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet is distributed by RSS without FDIR matched ID::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 8: MAC_IPV4_GTPU_EH without QFI rss queues / mark
---------------------------------------------------------

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / end actions rss queues 2 3 end / mark id 1 / end

2. send matched packets, check the packet is distributed to queue 2 or queue 3 with FDIR matched ID=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packet are distributed by RSS without FDIR matched ID::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0)/IP()/TCP()/Raw('x'*20)

3. repeat step 3 of subcase 1.

4. verify matched packet is distributed by RSS without FDIR matched ID.
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
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 2: MAC_IPV4_GTPU queue group
------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 end / mark / end

2. send matched packets, check the packets are distributed to queue group with FDIR matched ID=0x0.
   send mismatched packets, check the packets are distributed by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 3: MAC_IPV4_GTPU passthru
---------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 4: MAC_IPV4_GTPU drop
-----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. repeat step 3 of subcase 1.

4. verify matched packets are not dropped without FDIR matched ID.
   Then check there is no rule listed.

Subcase 5: MAC_IPV4_GTPU mark/rss
---------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR matched ID=0x0.
   send mismatched packets, check the packets are redirected by RSS without FDIR matched ID.

3. repeat step 3 of subcase 1.

4. verify matched packets are distributed by RSS without FDIR matched ID.
   Then check there is no rule listed.

Subcase 6: MAC_IPV4_GTPU mark
-----------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark / end

2. repeat the steps of passthru in subcase 3,
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

    sendp([Ether(dst="00:11:22:33:44:55",type=0x8847)],iface="enp134s0f1")

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

Subcase 7: unsupported Ethertype
--------------------------------

1. create rules for IP/IPV6::

    flow create 0 ingress pattern eth type is 0x0800 / end actions queue index 1 / end
    flow create 0 ingress pattern eth type is 0x86dd / end actions queue index 1 / end

   the two rules can be created successfully, but report below message::

    ice_flow_create(): Succeeded to create (2) flow
    Flow rule #0 created

   the number "2" stands for switch rule, fdir doesn't support IPV4/IPV6 ethertype.

Test case: negative cases
=========================
Note: the error message may be changed.

Subcase 1: invalid parameters of queue index
--------------------------------------------

1. Invalid parameters::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 64 / end

   Failed to create flow, report message::

    Invalid queue for FDIR.: Invalid argument

2. check there is no rule listed.

Subcase 2: invalid parameters of rss queues
-------------------------------------------

1. Invalid number of queues::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 end / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 end / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues end / end

   Failed to create flow, report message::

    Invalid input action: Invalid argument

2. Discontinuous queues::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end

   Failed to create flow, report message::

    Discontinuous queue region: Invalid argument

3. invalid queue index::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 63 64 end / end

   Failed to create flow, report message::

    Invalid queue region indexes.: Invalid argument

4. "--rxq=7 --txq=7", set queue group 8 queues::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 1 2 3 4 5 6 7 end / end

   Failed to create flow, report message::

    Invalid queue region indexes.: Invalid argument

5. check there is no rule listed.

6. "--rxq=8 --txq=8", set queue group 8 queues,
   create the 8 queues flow successfully.
   send matched packets, check the packets are distributed to queue 0-7.
   send mismatched packets, check the packets are distributed to queue 0-7 too.

Subcase 3: Invalid parameters of input set
------------------------------------------

1. Invalid value of teid and qfi::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x100 / end actions queue index 1 / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc qfi is 0x5 / end actions queue index 2 / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / end actions queue index 1 / end

   Failed to create flow, report message "Bad arguments"

2. check there is no rule listed.

Subcase 4: Invalid parameters of mark ID
----------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark id 4294967296 / end

   Failed to create flow, report message "Bad arguments"

2. check there is no rule listed.

Subcase 5: Duplicated rules
---------------------------

1. Create a FDIR rule::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end

   the rule is created successfully.

2. Create the same rule again, Failed to create flow, report message::

    Rule already exists!: File exists

3. check there is only one rule listed.

Subcase 6: conflicted rules
---------------------------

1. Create a FDIR rule::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / mark / end

   the rule is created successfully.

2. Create a rule with same input set but different action or with different input set::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 2 / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions drop / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 3 / mark / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 3 / mark / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 2 / mark / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions rss queues 2 3 end / mark / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2021 / end actions mark / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end

   Failed to create the two flows, report message::

    Rule already exists!: File exists

   or::

    Invalid input action number: Invalid argument

3. check there is only one rule listed.

Subcase 7: conflicted actions
-----------------------------

1. Create a rule with two conflicted actions::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions queue index 1 / rss queues 2 3 end / end

   Failed to create flow, report message::

    Invalid input action: Invalid argument

2. check there is no rule listed.

Subcase 8: void action
----------------------

1. Create a rule with void action::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions end

   Failed to create flow, report message::

    Invalid input action: Invalid argument

2. check there is no rule listed.

Subcase 9: delete a non-existent rule
--------------------------------------

1. show the rule list of port 0::

    flow list 0

   There is no rule listed.

2. destroy rule 0 of port 0::

    flow destroy 0 rule 0

   There is no error message reported.

3. check there is no rule listed.

4. flush rules of port 0::

    flow flush 0

   There is no error message reported.

5. check there is no rule listed.

Subcase 10: unsupported input set field
---------------------------------------

1. Create a IPV4_PAY rule with TC input set::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 tc is 2 / end actions queue index 1 / end

   Failed to create flow, report message::

    Bad arguments

2. check there is no rule listed.

Subcase 11: invalid port
------------------------

1. Create a rule on port 2::

    flow create 2 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / end

   Failed to create flow, report message::

    No such device: No such device

2. check there is no rule listed on port 2::

    testpmd> flow list 2
    Invalid port 2

Subcase 12: unsupported pattern
-------------------------------

1. Create a GTPU rule with OS default package::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end

   Failed to create flow, report error message.

2. check there is no rule listed.

Subcase 13: conflict patterns
-----------------------------

Note: MAC_IPV4_UDP packet can match MAC_IPV4_PAY rule if ip address can match.
so if there is a MAC_IPV4_PAY rule existing,
MAC_IPV4_UDP rule will be set to switch rule.
set "--log-level=ice,7", then check::

    ice_flow_create(): Succeeded to create (1) flow -> FDIR
    ice_flow_create(): Succeeded to create (2) flow -> switch

1. set MAC_IPV4_PAY rule firstly::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / end actions queue index 1 / end

   the first flow rule is set to fdir filter, send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22, dport=23)/ Raw('x' * 80)],iface="enp175s0f0", count=10)

   the two packets are both redirected to queue 1.
   then create MAC_IPV4_UDP flow, it is set to switch filter::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 2 / end

   send same packets, MAC_IPV4_PAY packet to queue 1, MAC_IPV4_UDP packet to queue 2.

2. flush the rules.

3. set MAC_IPV4_UDP rule firstly::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 2 / end

   the first rule is set to fdir filter, send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22, dport=23)/ Raw('x' * 80)],iface="enp175s0f0", count=10)

   the packet is redirected to queue 2.
   then create MAC_IPV4_PAY rule, it is set to switch filter::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / end actions queue index 1 / end

   send same packet, it is redirected to queue 1, because the packet match switch filter first.


Test case: count/query
======================

Subcase 1: count for 1 rule
---------------------------

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / count / end
    flow create 1 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions count / end

2. send matched packets to port0 and port1,
   the packets received by port0 are redirected to queue 1.
   the packets received by port1 are distributed by RSS.
   send mismatched packets, check the packets are redirected by RSS.
   check the count number::

    flow query 0 0 count
    count:
     hits_set: 1
     bytes_set: 0
     hits: 2
     bytes: 0

    flow query 1 0 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 2
     bytes: 0

3. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow list 1

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0
    testpmd> flow destroy 1 rule 0

   verify matched packets are redirected by RSS.
   check there is no rule listed.

4.  check the count number::

     testpmd> flow query 0 0 count
     Flow rule #0 not found
     testpmd> flow query 1 0 count
     Flow rule #0 not found

Subcase 2: count query identifier share
---------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions queue index 1 / count identifier 0x1234 shared on / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / end actions rss queues 2 3 end / count identifier 0x1234 shared on / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 / end actions passthru / mark / count identifier 0x1234 shared off / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.4 / end actions mark id 1 / rss / count identifier 0x1234 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.5 / end actions queue index 5 / count shared on / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.6 / end actions drop / count shared on / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.7 / end actions drop / count identifier 0x1235 shared on / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.8 / end actions rss / count / end

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.5",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.6",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.8",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)

   check the packets,
   packet 1 to queue 1, packet 2 to queue 2 or queue 3,
   packet 3 is distributed by RSS with FDIR matched ID=0x0,
   packet 4 is distributed by RSS with FDIR matched ID=0x1,
   packet 5 to queue 5,
   packet 6 dropped, packet 7 dropped.
   packet 8 is distributed by RSS.

3. query count::

    testpmd> flow query 0 0 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 20
     bytes: 0
    testpmd> flow query 0 1 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 20
     bytes: 0
    testpmd> flow query 0 2 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 0 3 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 0 4 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 20
     bytes: 0
    testpmd> flow query 0 5 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 20
     bytes: 0
    testpmd> flow query 0 6 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 0 7 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0

4. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow flush 0

5. check there is no rule listed,
   send matched packets, query count, flow rule not found.

Subcase 3: multi patterns mark count query
------------------------------------------

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 0 / count / end
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / mark id 1 / count / end
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions rss queues 62 63 end / mark id 2 / count / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / mark id 3 / count / end
    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 3 / mark id 4 / count / end
    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 / tcp dst is 23 / end actions queue index 4 / count / mark id 5 / end
    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 5 / mark id 6 / count / end
    flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 \
    32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 end / mark id 100 / count / end

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /TCP(sport=22, dport=23)/ Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22, dport=23)/ Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /SCTP(sport=22, dport=23)/ Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)], iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=4790)/VXLAN(flags=0xc)/IP(dst="192.168.0.21", src="192.168.0.20")/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20")/TCP(dport=23)/("X"*480)], iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw('x'*20)], iface="enp175s0f0", count=10)

   check the packets,
   packet 1 to queue 1, packet 2 dropped, packet 3 to queue 62-63, packet 4 to queue 1, packet 5 to queue 3,
   packet 6 to queue 4, packet 7 to queue 5, packet 8 is distributed by RSS.
   all the packets are received with FDIR matched ID.

3. query count::

    testpmd> flow query 0 0 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 0 1 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 0 2 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 0 3 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 0 4 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 0 5 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 0 6 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 1 0 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0

4. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow flush 0

5. check there is no rule listed,
   send matched packets, query count, flow rule not found.

Subcase 4: max count number
---------------------------

1. create 257 flows with count::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions drop / count / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / end actions drop / count / end
    ……
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.255 / end actions drop / count / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 / end actions drop / count / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.1.2 / end actions drop / count / end

   the last one failed to create, report the error message::

    No free counter found

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.1.1",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)

   check the packet dropped.

3. query count::

    testpmd> flow query 0 255 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0

4. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check that 256 rules listed.
   destroy the rule::

    testpmd> flow flush 0

   verify matched packet are not dropped.
   check there is no rule listed.

Test case: two ports
====================

Subcase 1: same rule on two ports
---------------------------------

1. create filter rules on two ports::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark / end
    flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / mark / end

   send matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:11:22:33:44:55")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152) \
    /GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)

   send the packet to two ports, both are distributed to queue 1 with FDIR matched ID=0x0.

2. list the rules on two ports::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC => QUEUE MARK
    testpmd> flow list 1
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC => QUEUE MARK

3. destroy rule 0 on port 0::

    testpmd> flow destroy 0 rule 0
    Flow rule #0 destroyed

   list the rules on two ports::

    testpmd> flow list 0
    testpmd> flow list 1
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC => QUEUE MARK

4. send the matched packet to port 0, it is redirected by RSS without FDIR matched ID.
   send the matched packet to port 1, it is still redirected to queue 1 with FDIR matched ID=0x0.

5. destroy rule 0 on port 1::

    testpmd> flow destroy 1 rule 0
    Flow rule #0 destroyed

   list the rules on two ports::

    testpmd> flow list 0
    testpmd> flow list 1

   there is no rule listed on both ports.
   send the matched packet to port 0/1, it is redirected by RSS without FDIR matched ID.

Subcase 2: same input set, different actions on two ports
---------------------------------------------------------

1. create filter rules on two ports::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end
    flow create 1 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / mark id 1 / end

   send matched packets to two ports::

    pkt = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)

   the packet sent to port 0 is redirected to queue 1 with FDIR matched ID=0x1,
   the packet sent to port 1 is redirected to queue 2 or queue 3 with FDIR matched ID=0x1.

2. destroy rule 0 on both ports::

    testpmd> flow flush 0
    testpmd> flow flush 1

   list the rules on two ports::

    testpmd> flow list 0
    testpmd> flow list 1

   there is no rule listed on both ports.
   send the matched packet to port 0/1, it is redirected by RSS without FDIR matched ID.

Subcase 3: two ports multi patterns count query
-----------------------------------------------

1. create filter rules::

    flow create 1 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 255  tos is 4 / end actions queue index 1 / mark id 1 / count identifier 0x1234 shared on / end
    flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions rss queues 6 7 end / mark id 2 / count identifier 0x1234 shared on / end
    flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss queues 6 7 end / mark id 1 / count / end
    flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 2 / mark / count / end
    flow create 1 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / count / end
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions drop / count / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / mark id 1 / count identifier 0x1234 shared on / end

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=255, ttl=2, tos=4) / Raw('x' * 80)],iface="enp175s0f1", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1, hlim=2)/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f1", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1, hlim=2)/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f1", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", tc=1, hlim=2)/TCP(sport=22,dport=23)/("X"*480)], iface="enp175s0f1", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN()/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')/("X"*480)], iface="enp175s0f1", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", ttl=2, tos=4)/TCP(sport=22,dport=23)/Raw(load="X"*480)], iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)], iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(dst="192.168.0.21", ttl=2, tos=4)/TCP(sport=22,dport=23)/Raw(load="X"*480)], iface="enp175s0f1", count=10)

   check the packets,
   packet 1 to queue 1 of port 1, packet 2 to queue 6-7 of port 1, packet 3 to queue 6-7 of port 1,
   packet 4 to queue 2 of port 1, packet 5 dropped of port 1,
   packet 6 to dropped of port 0, packet 7 to queue 1 of port 0.
   packet 8 received by port 1.
   all the received packets have specified FDIR matched ID.

3. query count::

    testpmd> flow query 1 0 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 20
     bytes: 0
    testpmd> flow query 1 1 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 20
     bytes: 0
    testpmd> flow query 1 2 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
    testpmd> flow query 1 3 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 1 4 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 0 0 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
    testpmd> flow query 0 1 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10

4. verify rules can be listed correctly::

    testpmd> flow list 0
    testpmd> flow list 1

5. destroy the rule::

    testpmd> flow flush 0
    testpmd> flow flush 1

   verify matched packet are received without FDIR matched ID.
   check there is no rule listed::

    testpmd> flow list 0
    testpmd> flow list 1

   query the count number, all reported::

    Flow rule #[ID] not found

Test case: Stress test
======================

Subcase 1: port stop/port start/port reset
------------------------------------------

1. create a rule::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark / end

2. list the rule and send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0")

   check the packet are redirected to queue 1 with FDIR matched ID=0x0

3. stop the port, then start the port::

    testpmd> port stop 0
    testpmd> port start 0

4. show the rule list, the rule is still there.

5. verify matched packet can be still redirected to queue 1 with FDIR matched ID=0x0.

6. reset pf::

    testpmd> port stop 0
    testpmd> port reset 0
    testpmd> port start 0

7. show the rule list, the rule is still there.

8. verify matched packet can be still redirected to queue 1 with FDIR matched ID=0x0.

9. add a new rule::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.22 dst is 192.168.0.23 / end actions queue index 2 / mark id 1 / end

10. list the rule and send matched packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.22",dst="192.168.0.23") / Raw('x' * 80)],iface="enp175s0f0")

   check the packet are redirected to queue 2 with FDIR matched ID=0x1

Subcase 2: add/delete rules
---------------------------

1. create two rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 2 3 end / mark id 1 / end

   return the message::

    Flow rule #0 created
    Flow rule #1 created

   list the rules::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP => QUEUE MARK
    1       0       0       i--     ETH IPV4 TCP => RSS MARK

2. delete the rules::

    testpmd> flow flush 0

3. repeate the create and delete operations in step1-2 15360 times.

4. create the two rules one more time, check the rules listed.

5. send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")

   check packet 1 is redirected to queue 1 with FDIR matched ID=0x0
   check packet 2 is redirected to queue 2 or queue 3 with FDIR matched ID=0x1

Subcase 3: delete rules
-----------------------

1. create 3 rules and destory the first rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 24 / end actions queue index 2 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 25 / end actions queue index 3 / mark / end

   there are rule 0/1/2 listed::

    flow list 0

   send packets match rule 0, rule 1 and rule 2,
   Verify all packets can be redirected to expected queue and mark.
   destory the first rule::

    flow destroy 0 rule 0

   list the rules, verify there are only rule 1 and rule 2 listed.
   send packet matched rule 0, verify it is received without FDIR matched ID.
   send packets matched rule 1 and rule 2, Verify all packets be redirected and mark.
   flush rules::

    flow flush 0

   send packets match rule 0, rule 1 and rule 2, verify all packets can not mark.

2. create 3 rules and destory the second rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 24 / end actions queue index 2 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 25 / end actions queue index 3 / mark / end

   there are rule 0/1/2 listed::

    flow list 0

   send packets match rule 0, rule 1 and rule 2,
   Verify all packets can be redirected to expected queue and mark.
   destory the second rule::

    flow destroy 0 rule 1

   list the rules, verify there are only rule 0 and rule 2 listed.
   send packet matched rule 1, verify it is received without FDIR matched ID.
   send packets matched rule 0 and rule 2, Verify all packets be redirected and mark.
   flush rules::

    flow flush 0

   send packets match rule 0, rule 1 and rule 2, verify all packets can not mark.

3. create 3 rules and destory the third rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 24 / end actions queue index 2 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.56.0 dst is 192.1.0.0 tos is 4 / tcp src is 22 dst is 25 / end actions queue index 3 / mark / end

   there are rule 0/1/2 listed::

    flow list 0

   send packets match rule 0, rule 1 and rule 2,
   Verify all packets can be redirected to expected queue and mark.
   destory the last rule::

    flow destroy 0 rule 2

   list the rules, verify there are only rule 0 and rule 1 listed.
   send packet matched rule 2, verify it is received without FDIR matched ID.
   send packets matched rule 0 and rule 1, Verify all packets be redirected and mark.
   flush rules::

    flow flush 0

   send packets match rule 0, rule 1 and rule 2, verify all packets can not mark.

Subcase 4: max rules
--------------------
This case is designed based on 2*100G NIC.
If 4*25 NIC, each PF port has 512 fdir rules guaranteed.
So there can be created 14848 fdir rules on 1 PF port.

1. create 15360 rules on port 0::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.100.20 dst is 192.168.0.0 / end actions queue index 1 / mark / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.100.20 dst is 192.168.0.1 / end actions queue index 1 / mark / end
    ......
    flow create 0 ingress pattern eth / ipv4 src is 192.168.100.20 dst is 192.168.59.255 / end actions queue index 1 / mark / end

   all the rules are created successfully.

2. create one more rule::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.100.20 dst is 192.168.60.0 / end actions queue index 1 / mark / end

   the rule failed to create. return the error message::

    Failed to create flow

3. check the rule list, there are 15360 rules listed.

4. send matched packets for rule 0 and rule 15359::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.100.20",dst="192.168.0.0")/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.100.20",dst="192.168.59.255")/Raw('x' * 80)],iface="enp175s0f0")

   check all packets are redirected to expected queue with FDIR matched ID=0x0

5. flush all the rules, check the rule list,
   there is no rule listed.

6. verify matched packets for rule 0 and rule 15359 received without FDIR matched ID.
