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
    | GTP-U data packet types      |                            |                                                                               |
    | IPv4 transport, IPv4 payload | MAC_IPV4_GTPU              | [TEID]                                                                        |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+
    |                              | MAC_IPV4_GTPU_EH           | [TEID], [QFI]                                                                 |
    +------------------------------+----------------------------+-------------------------------------------------------------------------------+

Notes: 1. Enable fdir filter for UDP tunnel: Vxlan / NVGRE (OS default package) , share code not
          support outer header as inputset, so Out Dest IP and VNI/GRE_KEY may not able to be implemented.
       2. For VXLAN case MAC_IPV4_TUN_*** means MAC_IPV4_UDP_VXLAN_***
       3. For Dest MAC, there is package /sharecode limitation on multicast dst mac support for FDIR

Function type
-------------

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

2. Software:
   DPDK: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Copy specific ice package to /lib/firmware/intel/ice/ddp/ice.pkg
   Then reboot server, and compile DPDK

4. Bind the pf to dpdk driver::

    ./usertools/dpdk-devbind.py -b igb_uio 86:00.0 86:00.1

5. Launch the app ``testpmd`` with the following arguments::

    ./testpmd -c 0xff -n 6 -w 86:00.0 -- -i --portmask=0xff --rxq=64 --txq=64 --port-topology=loop
    testpmd> set fwd rxonly
    testpmd> set verbose 1

   If set UDP tunnel flow rule::

    testpmd> port config 0 udp_tunnel_port add vxlan 4789
    testpmd> start

   Notes: if need two ports environment, launch ``testpmd`` with the following arguments::

    ./testpmd -c 0xff -n 6 -w 86:00.0 -w 86:00.1 -- -i --portmask=0xff --rxq=64 --txq=64 --port-topology=loop

   If create rules with mark actions, please add the following parameters in testpmd command line::

    -w 86:00.0,flow-mark-support=1 -w 86:00.1,flow-mark-support=1


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

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP(frag=1)/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/UDP()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/ICMP()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/IPv6ExtHdrFragment(1000)/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu9 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu10 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/ICMP()/Raw('x'*20)

   mismatched packets::

    p_gtpu11 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/SCTP()/Raw('x'*20)
    p_gtpu12 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IPv6()/SCTP()/Raw('x'*20)
    p_gtpu13 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)
    p_gtpu14 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)
    p_gtpu15 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw('x'*20)
    p_gtpu16 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/Raw('x'*20)

* MAC_IPV4_GTPU

   matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP(frag=1)/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/UDP()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/ICMP()/Raw('x'*20)
    p_gtpu6 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/Raw('x'*20)
    p_gtpu7 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/IPv6ExtHdrFragment(1000)/Raw('x'*20)
    p_gtpu8 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/UDP()/Raw('x'*20)
    p_gtpu9 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP( dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/TCP(sport=22, dport=23)/Raw('x'*20)
    p_gtpu10 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/ICMP()/Raw('x'*20)
    p_gtpu11 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)

   mismatched packets::

    p_gtpu12 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/Raw('x'*20)
    p_gtpu13 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/SCTP()/Raw('x'*20)
    p_gtpu14 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IPv6()/SCTP()/Raw('x'*20)
    p_gtpu15 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IP()/Raw('x'*20)

Test case: MAC_IPV4_PAY queue index
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV4_PAY selected inputset queue index
=====================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 1 / end actions queue index 1 / end
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 17 / end actions queue index 2 / end

2. send matched packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=1) / Raw('x' * 80)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=1) / Raw('x' * 80)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)
    pkt4 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)
    pkt5 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=17, ttl=2, tos=4)/Raw('x' * 80)
    pkt6 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1, proto=17, ttl=2, tos=4)/Raw('x' * 80)

   check the pkt1 and pkt2 are redirected to queue 1.
   check the pkt3-pkt6 are redirected to queue 2
   send mismatched packets::

    pkt7 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.22", proto=1) / Raw('x' * 80)
    pkt8 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", proto=6) / Raw('x' * 80)
    pkt9 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/TCP(sport=22,dport=23)/ Raw('x' * 80)
    pkt10 = Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", frag=1)/TCP(sport=22,dport=23)/ Raw('x' * 80)

   check the packets are not distributed to queue 1 or queue 2.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow flush 0

   verify matched packets are not distributed to expected queue.
   check there is no rule listed.

Test case: MAC_IPV4_UDP queue index
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 1 / end

2. send matched packets, check the packets is distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV4_TCP queue index
===================================

1. create filter rules::

   flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 63 / end

2. send matched packets, check the packets is distributed to queue 63.
   send mismatched packets, check the packets are not distributed to queue 63.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is not distributed to queue 63.
   check there is no rule listed.

Test case: MAC_IPV4_SCTP queue index
====================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 tag is 1 / end actions queue index 2 / end

2. send matched packets, check the packets is distributed to queue 2.
   send mismatched packets, check the packets are not distributed to queue 2.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is not distributed to queue 2.
   check there is no rule listed

Test case: MAC_IPV6_PAY queue index
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 0 hop is 2 tc is 1 / end actions queue index 1 / end

2. send matched packets, check the packets is distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV6_PAY selected inputset queue index
=====================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 44 / end actions queue index 1 / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 proto is 6 / end actions queue index 2 / end

2. send matched packets::

    pkt1 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=44, tc=1, hlim=2)/("X"*480)
    pkt2 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment(1000)/("X"*480)
    pkt3 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=44)/TCP(sport=22,dport=23)/("X"*480)
    pkt4 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment(1000)/TCP(sport=22,dport=23)/("X"*480)
    pkt5 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=6)/("X"*480)
    pkt6 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)

   check pkt1-pkt4 are redirected to queue 1.
   check pkt5 and pkt6 are redirected to queue 2.
   send mismatched packets::

    pkt7 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2021", nh=44)/("X"*480)
    pkt8 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)
    pkt9 = Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", nh=17)/("X"*480)

   check the packets are not distributed to queue 1 or queue 2.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet are not distributed to expected queue.
   check there is no rule listed.

Test case: MAC_IPV6_UDP queue index
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 1 / end

2. send matched packets, check the packets is distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV6_TCP queue index
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 1 / end

2. send matched packets, check the packets is distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV6_SCTP queue index
====================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions queue index 1 / end

2. send matched packets, check the packets is distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_PAY queue index
============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_UDP queue index
============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_TCP queue index
============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_SCTP queue index
=============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_PAY queue index
================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_UDP queue index
================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_TCP queue index
================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue 1.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_SCTP queue index
=================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue 1.
   check there is no rule listed.

Test case: queue index wrong parameters
=======================================

1. invalid parameters::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 64 / end

   failed to be created.

2. same pattern items, different action::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 2 / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / end

   flow 1 can be created successfully,
   flow 2 and flow 3 failed to be created cause of confliction.

Test case: MAC_IPV4_PAY passthru/count
======================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / count / end

2. send matched packets, check the packets are redirected by RSS
   send mismatched packets, check the packets are redirected by RSS
   check the count number::

    flow query 0 0 count
    count:
     hits_set: 1
     bytes_set: 0
     hits: 2
     bytes: 0

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are redirected to the same queue.
   check there is no rule listed.

Test case: MAC_IPV4_PAY passthru/mark
=====================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_UDP passthru/mark
=====================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions passthru / end

2. send matched packets, check the packets are redirected by RSS.
   send mismatched packets, check the packets are redirected by RSS.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue.
   check there is no rule listed.

Test case: MAC_IPV4_TCP passthru/mark
=====================================

1. create filter rules::

   flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_SCTP passthru/mark
======================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 tag is 1 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV6_PAY passthru/mark
=====================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 1 hop is 2 tc is 1 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV6_UDP passthru/mark
=====================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV6_TCP passthru/mark
=====================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV6_SCTP passthru/mark
======================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_PAY passthru/mark
==============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_UDP passthru/mark
==============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_TCP passthru/mark
==============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_SCTP passthru/mark
===============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_PAY passthru/mark
==================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_UDP passthru/mark
==================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_TCP passthru/mark
==================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_SCTP passthru/mark
===================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_PAY mark/rss
================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_UDP mark/rss
================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions mark / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 0.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 0.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TCP mark/rss
================================

1. create filter rules::

   flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_SCTP mark/rss
=================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 tag is 1 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV6_PAY mark/rss
================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 1 hop is 2 tc is 1 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV6_UDP mark/rss
================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV6_TCP mark/rss
================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV6_SCTP mark/rss
=================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_PAY mark/rss
=========================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 0.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 0.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_UDP mark/rss
=========================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_TCP mark/rss
=========================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_SCTP mark/rss
==========================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_PAY mark/rss
=============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_UDP mark/rss
=============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_TCP mark/rss
=============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_SCTP mark/rss
==============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packet is redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: mark/rss wrong parameters
====================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions rss / end

2. The rule failed to be created, report proper error message.

3. list the flow::

    testpmd> flow list 0

   there is no flow listed.

Test case: MAC_IPV4_PAY drop
============================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify matched packets are not dropped.

Test case: MAC_IPV4_UDP drop
============================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packet dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packet hit the rule is not dropped.

Test case: MAC_IPV4_TCP drop
============================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packet dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packet hit the rule is not dropped.

Test case: MAC_IPV4_SCTP drop
=============================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packet dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packet hit the rule is not dropped.

Test case: MAC_IPV6_PAY drop
============================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 1 hop is 2 tc is 1 \
    / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packet hit the rule is not dropped.

Test case: MAC_IPV6_UDP drop
============================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packet dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packet hit the rule is not dropped.

Test case: MAC_IPV6_TCP drop
============================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packet dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packet hit the rule is not dropped.

Test case: MAC_IPV6_SCTP drop
=============================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packet dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packet hit the rule is not dropped.

Test case: MAC_IPV4_TUN_IPV4_PAY drop
=====================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packets hit the rule are not dropped.

Test case: MAC_IPV4_TUN_IPV4_UDP drop
=====================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packets hit the rule are not dropped.

Test case: MAC_IPV4_TUN_IPV4_TCP drop
=====================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packets hit the rule are not dropped.

Test case: MAC_IPV4_TUN_IPV4_SCTP drop
======================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packets hit the rule are not dropped.

Test case: MAC_IPV4_TUN_MAC_IPV4_PAY drop
=========================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packets hit the rule are not dropped.

Test case: MAC_IPV4_TUN_MAC_IPV4_UDP drop
=========================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packets hit the rule are not dropped.

Test case: MAC_IPV4_TUN_MAC_IPV4_TCP drop
=========================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packets hit the rule are not dropped.

Test case: MAC_IPV4_TUN_MAC_IPV4_SCTP drop
==========================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions drop / end

2. send matched packets, check the packets dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   check there is no rule listed.
   verify the packets hit the rule are not dropped.

Test case: MAC_IPV4_PAY queue group
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 1 end / end

2. send matched packets, check the packets are distributed to queue 0 or 1.
   send mismatched packets, check the packets are not distributed to queue 0 or 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify pkt1 and pkt2 are not distributed to queue 0 or 1.
   check there is no rule listed.

Test case: MAC_IPV4_UDP queue group
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions rss queues 1 2 3 4 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV4_TCP queue group
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions rss queues 56 57 58 59 60 61 62 63 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV4_SCTP queue group
====================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 tag is 1 / end actions rss queues 0 1 2 3 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV6_PAY queue group
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 1 hop is 2 tc is 1 / end actions rss queues 1 2 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV6_UDP queue group
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss queues 1 2 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV6_TCP queue group
===================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions rss queues 1 2 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV6_SCTP queue group
====================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions rss queues 1 2 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_PAY queue group
============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_UDP queue group
============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 38 39 40 41 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_TCP queue group
============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 1 2 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_SCTP queue group
=============================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions rss queues 1 2 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_PAY queue group
================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions rss queues 1 2 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_UDP queue group
================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 1 2 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_TCP queue group
================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions rss queues 1 2 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_SCTP queue group
=================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions rss queues 1 2 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify the packets hit rule are not distributed to queue group.
   check there is no rule listed.

Test case: queue group wrong parameters
=======================================

1. invalid number of queues::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 1 2 end / end

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 0 end / end

2. Discontinuous queues::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 1 2 3 5 end / end

3. invalid queue index::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions rss queues 63 64 end / end

4. "--rxq=32 --txq=32", set queue group 64 queues::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 end / end

all the above five rules are failed to created.

5. "--rxq=64 --txq=64", set queue group 64 queues,
   create the 64 queues flow successfully.
   send matched packets, check the packets are distributed to queue 0-63.
   send mismatched packets, check the packets are distributed to queue 0-63 too.

Test case: MAC_IPV4_GTPU_EH queue index
=======================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are not distributed to queue 1.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH passthru/mark
=========================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH mark/rss
====================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH drop
================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are not dropped.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH queue group
=======================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions rss queues 0 1 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are not distributed to queue group.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU queue index
====================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions queue index 1 / end

2. send matched packets, check the packets are distributed to queue 1.
   send mismatched packets, check the packets are not distributed to queue 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are not distributed to queue 1.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU passthru/mark
======================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions passthru / mark / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_GTPU mark/rss
=================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions mark id 1 / rss / end

2. send matched packets, check the packets are redirected by RSS with FDIR ID 1.
   send mismatched packets, check the packets are redirected by RSS without FDIR ID 1.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are redirected to the same queue without FDIR ID.
   check there is no rule listed.

Test case: MAC_IPV4_GTPU drop
=============================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions drop / end

2. send matched packets, check the packets are dropped.
   send mismatched packets, check the packets are not dropped.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are not dropped.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU queue group
====================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 end / end

2. send matched packets, check the packets are distributed to queue group.
   send mismatched packets, check the packets are not distributed to queue group.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are not distributed to queue group.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH mark/count/query
============================================
1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 2 / mark id 2 / count / end

2. send matched packets, check the packets are distributed to queue 2, the FDIR=0x2.
   send mismatched packets, check the packets are not distributed to queue 2, no FDIR.
   check the count number::

    flow query 0 0 count
    count:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are not distributed to queue 2, and no FDIR.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU mark/count/query
=========================================

1. create filter rules on port 1::

    flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 end / mark id 100 / count / end

2. send matched packets, check the packets are distributed to queue in 0-63, the FDIR=0x64::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/IP()/Raw('x'*20)

   send mismatched packets, check the packets have not FDIR::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/IP()/Raw('x'*20)

   check the count number::

    flow query 1 0 count
    count:
     hits_set: 1
     bytes_set: 0
     hits: 2
     bytes: 0

3. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 1 rule 0

   verify matched packets are distributed to queue in 0-63, and no FDIR.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH QFI mark/count/query
================================================

1. create filter rules on port 1::

    flow create 1 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc qfi is 0x34 / end actions drop / mark id 3 / count / end

2. send matched packets, check the packets are dropped::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packets are not dropped, no FDIR::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)

   check the count number::

    flow query 1 0 count
    count:
     hits_set: 1
     bytes_set: 0
     hits: 1
     bytes: 0

3. verify rules can be listed and destroyed::

    testpmd> flow list 1

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 1 rule 0

   verify matched packets are not dropped, and no FDIR.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH without QFI mark/count/query
========================================================

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc / end actions queue index 15 / mark id 3 / count / end

2. send matched packets, check the packets are distributed to queue 15, the FDIR=0x3::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0)/IP()/TCP()/Raw('x'*20)

   send mismatched packets, check the packets are not distributed to queue 15, no FDIR::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0)/IP()/TCP()/Raw('x'*20)

   check the count number::

    flow query 0 0 count
    count:
     hits_set: 1
     bytes_set: 0
     hits: 1
     bytes: 0

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are not distributed to queue 15, and no FDIR.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH multirules
======================================

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x35 / end actions queue index 2 / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x1234567 / gtp_psc qfi is 0x35 / end actions queue index 3 / end

   the three rules are created successfully.
   then create the following rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x1234567 / gtp_psc qfi is 0x35 / end actions queue index 3 / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x1234567 / gtp_psc qfi is 0x35 / end actions queue index 4 / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x1234567 / gtp_psc qfi is 0x75 / end actions queue index 4 / end

   the three rules are failed to created.
   then create the following rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x1234567 / gtp_psc qfi is 0x34 / end actions queue index 3 / end

   the rule is created successfully.

2. send matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)
    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)
    p_gtpu4 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)

   check the packets, p_gtpu1 to queue 1, p_gtpu2 to queue 3, p_gtpu3 to queue 2, p_gtpu4 to queue 3.
   send mismatched packets, check the packets are not distributed to queue 1-3::

    p_gtpu5 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x1234567)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x36)/IP()/Raw('x'*20)

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow flush 0

   verify matched packets are not distributed to same queue.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH two ports
=====================================

1. create filter rules on two ports::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / end
    flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / end

   send matched packets::

    p_gtpu1 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)

   send the packet to two ports, both are distributed to queue 1.

2. create filter rules on two ports::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x35 / end actions queue index 2 / end
    flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x35 / end actions queue index 3 / end

   send matched packets::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)

   send the packet to two ports, both are distributed to expected queue.

3. flush the rules::

    flow flush 0
    flow flush 1

4. create filter rules on two ports::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x34 / end actions queue index 1 / end
    flow create 1 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / end actions queue index 2 / end

   send matched packets::

    p_gtpu2 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x35)/IP()/Raw('x'*20)
    p_gtpu3 = Ether(src="a4:bf:01:51:27:ca", dst="00:00:00:00:01:03")/IP(src="192.168.0.20", dst="192.168.0.21")/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345678)/GTP_PDUSession_ExtensionHeader(pdu_type=0, qos_flow=0x34)/IP()/Raw('x'*20)

   send the packets to two ports,
   p_gtpu2 is not distributed to queue 1 of port 0, it is distributed to queue 2 of port 1.
   p_gtpu3 is distributed to queue 2 of port 1, it is distributed to queue 1 of port 0.

5. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow list 1

   check the existing rules.
   destroy the rule::

    testpmd> flow destroy 0 rule 0
    testpmd> flow destroy 1 rule 0

   verify matched packets are not distributed to expected queue.
   Then check there is no rule listed.

Test case: MAC_IPV4_GTPU_EH wrong parameters
============================================

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x12345678 / gtp_psc qfi is 0x100 / end actions queue index 1 / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / gtp_psc qfi is 0x5 / end actions queue index 2 / end

   the two flows can not be created successfully, report proper error message.

2. list the flow::

    testpmd> flow list 0

   there is no flow listed.

Test case: MAC_IPV4_GTPU wrong parameters
=========================================

1. create filter rules on port 0::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu teid is 0x100000000 / end actions queue index 1 / end

   the flow can not be created successfully.

2. list the flow::

    testpmd> flow list 0

   there is no flow listed.

Test case: count query identifier share
=======================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions queue index 1 / count identifier 0x1234 shared on / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / end actions queue index 2 / count identifier 0x1234 shared on / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 / end actions queue index 3 / count identifier 0x1234 shared off / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.4 / end actions queue index 4 / count identifier 0x1234 / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.5 / end actions queue index 5 / count shared on / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.6 / end actions drop / count shared on / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.7 / end actions drop / count identifier 0x1235 shared on / end

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.1",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.2",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.4",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.5",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.6",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.21") / Raw('x' * 80)],iface="enp175s0f0", count=10)

   check the packets,
   packet 1 to queue 1, packet 2 to queue 2, packet 3 to queue 3, packet 4 to queue 4, packet 5 to queue 5,
   packet 6 dropped, packet 7 dropped.

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

4. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow flush 0

   verify matched packet are not distributed to same queue.
   check there is no rule listed.

Test case: multi patterns count query
=====================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / count / end
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions drop / count / end
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions rss queues 62 63 end / count / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / count / end
    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 3 / count / end
    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 / tcp dst is 23 / end actions queue index 4 / count / end
    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 5 / count / end

2. send matched packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /TCP(sport=22, dport=23)/ Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22, dport=23)/ Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /SCTP(sport=22, dport=23)/ Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(dst="CDCD:910A:2222:5498:8475:1111:3900:2020", src="2001::2", nh=0, tc=1, hlim=2)/("X"*480)], iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=4790)/VXLAN(flags=0xc)/IP(dst="192.168.0.21", src="192.168.0.20")/UDP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20")/TCP(dport=23)/("X"*480)], iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP()/VXLAN(vni=2)/Ether()/IP(src='192.168.0.20', dst='192.168.0.21')/SCTP(sport=22,dport=23)/("X"*480)], iface="enp175s0f0", count=10)

   check the packets,
   packet 1 to queue 1, packet 2 dropped, packet 3 to queue 62-63, packet 4 to queue 1, packet 5 to queue 3,
   packet 6 to queue 4, packet 7 to queue 5.

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

4. verify rules can be listed and destroyed::

    testpmd> flow list 0

   There are 7 rules listed.
   destroy the rule 0::

    testpmd> flow destroy 0 rule 0

   verify the packet matching rule 0 is not distributed to queue 1.
   check rule 1-6 listed.

5. destroy the rule 6::

    testpmd> flow destroy 0 rule 6

   verify the packet matching rule 6 is not distributed to queue 5.
   check rule 1-5 listed.

6. destroy the rule 3::

    testpmd> flow destroy 0 rule 3

   verify the packet matching rule 3 is not distributed to queue 1.
   check rule 1/2/4/5 listed.

7. flush the all the rules::

    testpmd> flow flush 0

   verify the matched packets are not distributed to the same queue.
   check no rule listed.

Test case: two ports multi patterns count query
===============================================

1. create filter rules::

    flow create 1 ingress pattern eth / ipv4 dst is 192.168.0.21 proto is 255  tos is 4 / end actions queue index 1 / count / end
    flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions rss queues 6 7 end / count / end
    flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions rss queues 6 7 end / count / end
    flow create 1 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 2 / count / end
    flow create 1 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions drop / count / end
    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 tos is 4 / tcp src is 22 dst is 23 / end actions drop / count / end
    flow create 0 ingress pattern eth / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 / end actions queue index 1 / count / end

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

3. query count::

    testpmd> flow query 1 0 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
     bytes: 0
    testpmd> flow query 1 1 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 10
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

4. verify rules can be listed and destroyed::

    testpmd> flow list 0
    testpmd> flow list 1

   check the existing rule.
   destroy the rule::

    testpmd> flow flush 0
    testpmd> flow flush 1

   verify matched packet are not distributed to same queue.
   check there is no rule listed::

    testpmd> flow list 0
    testpmd> flow list 1

Test case: max count
====================

1. create 257 flows with count::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / end actions drop / count / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 / end actions drop / count / end
    ……
    flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 / end actions drop / count / end
    flow create 0 ingress pattern eth / ipv4 src is 192.168.1.2 / end actions drop / count / end

   the last one failed to create.

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

   check the existing rule.
   destroy the rule::

    testpmd> flow flush 0

   verify matched packet are not dropped.
   check there is no rule listed.

Test case: MAC_IPV4_PAY queue index mark
========================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 proto is 255 ttl is 2 tos is 4 / end actions queue index 1 / mark id 0 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x0" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV4_UDP queue index mark
========================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 0 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 0 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 0 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV4_TCP queue index mark
========================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 4294967294 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0xfffffffe" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV4_SCTP drop mark
==================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 tag is 1 / end actions drop / mark id 1 / end

2. send 1 matched packet, check the packets are dropped.
   send 1 mismatched packet, check the packets are not dropped without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV6_PAY queue index mark
========================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 proto is 1 hop is 2 tc is 1 / end actions queue index 1 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV6_UDP queue index mark
========================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV6_TCP queue index mark
========================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV6_SCTP queue index mark
=========================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 src is 2001::2 hop is 2 tc is 1 / sctp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_PAY queue index mark
=================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_UDP queue group mark
=================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions rss queues 1 2 end / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1-2 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1-2 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_TCP drop mark
==========================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions drop / mark id 1 / end

2. send 1 matched packet, check the packets are dropped.
   send 1 mismatched packet, check the packets are not dropped without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are dropped without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV4_TUN_IPV4_SCTP queue index mark
==================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_PAY queue index mark
=====================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / end actions queue index 1 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_UDP queue index mark
=====================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.


Test case: MAC_IPV4_TUN_MAC_IPV4_TCP queue index mark
=====================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / tcp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: MAC_IPV4_TUN_MAC_IPV4_SCTP queue index mark
======================================================

1. create filter rules::

    flow create 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.20 dst is 192.168.0.21 / sctp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end

2. send 1 matched packet, check the packets are distributed to queue 1 with "FDIR matched ID=0x1" printed.
   send 1 mismatched packet, check the packets are not distributed to queue 1 without "FDIR matched" printed.

3. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check the existing rule.
   destroy the rule::

    testpmd> flow destroy 0 rule 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed.

Test case: multirules mark
==========================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / udp src is 22 dst is 23 / end actions queue index 1 / mark id 1 / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / tcp src is 22 dst is 23 / end actions queue index 2 / mark id 1 / end
    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 dst is 192.168.0.21 ttl is 2 tos is 4 / sctp src is 22 dst is 23 / end actions queue index 1 / mark id 2 / count / end

2. send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /UDP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /TCP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21", ttl=2, tos=4) /SCTP(sport=22,dport=23)/Raw('x' * 80)],iface="enp175s0f0")

   check packet 1 to queue 1 with "FDIR matched ID=0x1" printed.
   packet 2 to queue 2 with "FDIR matched ID=0x1" printed.
   packet 3 to queue 1 with "FDIR matched ID=0x2" printed.

3. query count::

    testpmd> flow query 0 2 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 1
     bytes: 0

4. verify rules can be listed and destroyed::

    testpmd> flow list 0

   check 3 rules listed.
   destroy the rule 0::

    testpmd> flow destroy 0 rule 0

   verify packet 1 is distributed to different queue without "FDIR matched" printed.
   Then check there is 2 rules listed.
   packet 2 to queue 2 with "FDIR matched ID=0x1" printed.
   packet 3 to queue 1 with "FDIR matched ID=0x2" printed.
   query count::

    testpmd> flow query 0 2 count
    COUNT:
     hits_set: 1
     bytes_set: 0
     hits: 2
     bytes: 0

   flush rules::

    testpmd> flow flush 0

   verify matched packets are distributed to different queue without "FDIR matched" printed.
   Then check there is no rule listed, and no count exist.

Test case: mark wrong parameters
================================

1. create filter rules::

    flow create 0 ingress pattern eth dst is 00:11:22:33:44:55 / ipv4 src is 192.168.0.20 / end actions queue index 1 / mark id 4294967296 / end

   the flow failed to be created.

2. list the flow::

    testpmd> flow list 0

   Then check there is no rule listed.

Test case: pattern conflict flow
================================

MAC_IPV4_PAY and MAC_IPV4_UDP are conflict patterns.
so if create one, then create the other one, the second flow will be
set to switch filer.
IPV4_UDP packet can match MAC_IPV4_PAY rule.
but IPV4_PAY packet cannot match MAC_IPV4_UDP rule.

1. set MAC_IPV4_PAY firstly::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / end actions queue index 1 / end

   the first flow is set to fdir filter, send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21")/Raw('x' * 80)],iface="enp175s0f0", count=10)
    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22, dport=23)/ Raw('x' * 80)],iface="enp175s0f0", count=10)

   the two type packets both to queue 1.
   then create MAC_IPV4_UDP flow, it is set to switch filer::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 2 / end

   send same packets, IPV4_PAY packet to queue 1, IPV4_UDP packet to queue 2.

2. set MAC_IPV4_UDP firstly::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / udp src is 22 dst is 23 / end actions queue index 2 / end

   send matched packet::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.20",dst="192.168.0.21") /UDP(sport=22, dport=23)/ Raw('x' * 80)],iface="enp175s0f0", count=10)

   packet to queue 2.
   then create MAC_IPV4_PAY flow::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.21 / end actions queue index 1 / end

   send same packet, packet to queue 1, because the packet match switch filter first.
