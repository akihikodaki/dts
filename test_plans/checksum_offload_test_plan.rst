.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation
   Copyright(c) 2018-2019 The University of New Hampshire

============================
RX/TX Checksum Offload Tests
============================

The support of RX/TX L3/L4 Checksum offload features by Poll Mode Drivers consists in:

On the RX side:

- Verify IPv4 checksum by hardware for received packets.
- Verify UDP/TCP/SCTP checksum by hardware for received packets.

On the TX side:

- IPv4 checksum insertion by hardware in transmitted packets.
- IPv4/UDP checksum insertion by hardware in transmitted packets.
- IPv4/TCP checksum insertion by hardware in transmitted packets.
- IPv4/SCTP checksum insertion by hardware in transmitted packets (sctp
  length in 4 bytes).
- IPv6/UDP checksum insertion by hardware in transmitted packets.
- IPv6/TCP checksum insertion by hardware in transmitted packets.
- IPv6/SCTP checksum insertion by hardware in transmitted packets (sctp
  length in 4 bytes).

RX/TX side, the insertion of a L3/L4 checksum by hardware can be enabled with the
following command of the ``testpmd`` application and running in a dedicated
tx checksum mode::

   set fwd csum
   csum set ip|tcp|udp|sctp|outer-ip|outer-udp hw|sw port_id

The transmission of packet is done with the ``start`` command of the ``testpmd``
application that will receive packets and then transmit the packet out on all
configured ports. 


Prerequisites
=============

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

Assuming that ports ``0`` and ``2`` are connected to a traffic generator,
launch the ``testpmd`` with the following arguments::

  ./build/app/dpdk-testpmd -cffffff -n 1 -- -i --burst=1 --txpt=32 \
  --txht=8 --txwt=0 --txfreet=0 --rxfreet=64 --mbcache=250 --portmask=0x5
  enable-rx-cksum

Set the verbose level to 1 to display information for each received packet::

  testpmd> set verbose 1


Test Case: Insert IPv4/IPv6 UDP/TCP/SCTP checksum on the transmit packet
========================================================================

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Start the packet forwarding::

  testpmd> port stop all
  testpmd> csum set ip hw 0
  testpmd> csum set udp hw 0
  testpmd> csum set tcp hw 0
  testpmd> csum set sctp hw 0
  testpmd> port start all
  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Start a packet capture on the tester in the background::

   tcpdump -i <iface> -s 65535 -w /tmp/tester/test_checksum_capture.pcap &

Send the following multiple packets from tester for with scapy 
combination: IPv4/UDP, IPv4/TCP, IPv4/SCTP, IPv6/UDP, IPv6/TCP::

   sendp([Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/IP(chksum=0x0)/UDP(chksum=0xf)/("X"*46),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/IP(chksum=0x0)/TCP(chksum=0xf)/("X"*46),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/IP(chksum=0x0)/SCTP(chksum=0x0)/("X"*48),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/IPv6(src="::1")/UDP(chksum=0xf)/("X"*46),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/IPv6(src="::1")/TCP(chksum=0xf)/("X"*46)],
   iface="ens192f0",count=4,inter=0,verbose=False)

Then verify that the same number of packet are correctly received on the tester. 

Inspect the pcap file from the packet capture and verify the checksums.


Test Case: Do not insert IPv4/IPv6 UDP/TCP checksum on the transmit packet
==========================================================================

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Start the packet forwarding::

  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Start a packet capture on the tester in the background::

   tcpdump -i <iface> -s 65535 -w /tmp/tester/test_checksum_capture.pcap &

Send the following multiple packets from tester for with scapy 
combination: IPv4/UDP, IPv4/TCP, IPv6/UDP, IPv6/TCP::
   
   sendp([Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/IP(src="10.0.0.1",chksum=0x0)/UDP(chksum=0xf)/("X"*46),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/IP(src="10.0.0.1",chksum=0x0)/TCP(chksum=0xf)/("X"*46),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/IPv6(src="::1")/UDP(chksum=0xf)/("X"*46),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/IPv6(src="::1")/TCP(chksum=0xf)/("X"*46)],
   iface="ens192f0",count=4,inter=0,verbose=False)

Then verify that the same number of packet are correctly received on the tester.  

Inspect the pcap file from the packet capture and verify the checksums.

Test Case: Validate RX checksum valid flags on the receive packet
=================================================================

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Start the packet forwarding::

  testpmd> port stop all
  testpmd> csum set ip hw 0
  testpmd> csum set udp hw 0
  testpmd> csum set tcp hw 0
  testpmd> csum set sctp hw 0
  testpmd> port start all
  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Configure the traffic generator to send the multiple packets with the following
combination: good/bad ip checksum + good/bad udp/tcp checksum.

Send a packet ptypes is IP/UDP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=int(0x7ca0))/UDP(chksum=int(0x1126))/('X'*50), iface=iface)

   Check the Rx checksum flags consistent with expected flags.

   port=0, mbuf=0x168d06200, pkt_len=88, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=8
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/TCP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=int(0xf19f))/TCP(chksum=int(0x165f))/('X'*50), iface=iface)

   Check the Rx checksum flags consistent with expected flags.

   port=0, mbuf=0x168be5100, pkt_len=100, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/SCTP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=int(0xf127))/SCTP(chksum=int(0x2566b731))/('X'*50), iface=iface)

   Check the Rx checksum flags consistent with expected flags.

   port=0, mbuf=0x168be7600, pkt_len=94, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=132 l4_len=0 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_SCTP_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IPV6/UDP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPv6(src="::1")/UDP(chksum=int(0xf27))/('X'*50), iface=iface)

   Check the Rx checksum flags consistent with expected flags.

   port=0, mbuf=0x168d058c0, pkt_len=108, nb_segs=1:
   rx: l2_len=14 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=40 m->l4_len=8
   tx: flags=RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV6

Send a packet ptypes is IPV6/TCP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPv6(src="::1")/TCP(chksum=int(0x9f5f))/('X'*50), iface=iface)

   Check the Rx checksum flags consistent with expected flags.

   port=0, mbuf=0x168d033c0, pkt_len=120, nb_segs=1:
   rx: l2_len=14 ethertype=86dd l3_len=40 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=40 m->l4_len=20
   tx: flags=RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV6

Send a packet ptypes is IP/UDP with a bad IP/UDP checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=0x0)/UDP(chksum=0xf)/('X'*50), iface=iface)

   Check the Rx checksum flags consistent with expected flags.

   port=0, mbuf=0x168d00ec0, pkt_len=88, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_BAD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=8
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/TCP with a bad IP/TCP checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=0x0)/TCP(chksum=0xf)/('X'*50), iface=iface)

   Check the Rx checksum flags consistent with expected flags.

   port=0, mbuf=0x168cfe9c0, pkt_len=100, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_BAD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/SCTP with a bad IP/SCTP checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=0x0)/SCTP(chksum=0xf)/('X'*50), iface=iface)

   Check the Rx checksum flags consistent with expected flags.

   port=0, mbuf=0x168cfc4c0, pkt_len=94, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=132 l4_len=0 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_BAD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_SCTP_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IPV6/UDP with a bad UDP checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPv6(src="::1")/UDP(chksum=0xf)/('X'*50), iface=iface)

   Check the Rx checksum flags consistent with expected flags.

   port=0, mbuf=0x168cf9fc0, pkt_len=108, nb_segs=1:
   rx: l2_len=14 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=40 m->l4_len=8
   tx: flags=RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV6

Send a packet ptypes is IPV6/TCP with a bad TCP checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPv6(src="::1")/TCP(chksum=0xf)/('X'*50), iface=iface)

   Check the Rx checksum flags consistent with expected flags.

   port=0, mbuf=0x168cf9fc0, pkt_len=108, nb_segs=1:
   rx: l2_len=14 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=40 m->l4_len=8
   tx: flags=RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV6

Test Case: Hardware Checksum Check L4 RX
===========================================
This test involves testing many different scenarios with a L4 checksum.
A variety of tunneling protocols, L3 protocols and L4 protocols are combined
to test as many scenarios as possible. Currently, UDP, TCP and SCTP are used
as L4 protocols, with IP and IPv6 being used at level 3. The tested tunneling
protocols are VXLAN and GRE.

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Start the packet forwarding::

  testpmd> port stop all
  testpmd> csum set ip hw 0
  testpmd> csum set udp hw 0
  testpmd> csum set tcp hw 0
  testpmd> csum set sctp hw 0
  testpmd> port start all
  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Send a packet ptypes is IP/UDP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP()/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_L4_CKSUM_GOOD in the packet received

   port=0, mbuf=0x2269df8780, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD  RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP(chksum=0xf)/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_L4_CKSUM_BAD in the packet received

   port=0, mbuf=0x2269df7e40, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_BAD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/TCP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/TCP()/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_L4_CKSUM_GOOD in the packet received

   port=0, mbuf=0x2269df8780, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD  RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/TCP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/TCP(chksum=0xf)/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_L4_CKSUM_BAD in the packet received

   port=0, mbuf=0x2269df7e40, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_BAD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/SCTP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/SCTP()/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_L4_CKSUM_GOOD in the packet received

   port=0, mbuf=0x2269df8780, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD  RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/SCTP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/SCTP(chksum=0xf)/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_L4_CKSUM_BAD in the packet received

   port=0, mbuf=0x2269df7e40, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_BAD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Verify flags are as expected.

Test Case: Hardware Checksum Check L3 RX
===========================================
This test involves testing L3 checksum hardware offload.
Due to the relative dominance of IPv4 and IPv6 as L3 protocols, and IPv6's
lack of a checksum, only IPv4's checksum is tested.

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Start the packet forwarding::

  testpmd> port stop all
  testpmd> csum set ip hw 0
  testpmd> csum set udp hw 0
  testpmd> csum set tcp hw 0
  testpmd> csum set sctp hw 0
  testpmd> csum set 0xf 0
  testpmd> port start all
  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Send a packet ptypes is IP/UDP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP()/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_IP_CKSUM_GOOD in the packet received

   port=0, mbuf=0x2269df8780, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD  RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=0xf)/UDP()/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_IP_CKSUM_BAD in the packet received

   port=0, mbuf=0x2269df7e40, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_BAD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/TCP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/TCP()/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_IP_CKSUM_GOOD in the packet received

   port=0, mbuf=0x2269df8780, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD  RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/TCP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=0xf)/TCP()/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_IP_CKSUM_BAD in the packet received

   port=0, mbuf=0x2269df7e40, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_BAD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/SCTP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/SCTP()/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_IP_CKSUM_GOOD in the packet received

   port=0, mbuf=0x2269df8780, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD  RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Send a packet ptypes is IP/SCTP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=0xf)/SCTP()/('X'*50), iface=iface)

   check the packet received, the flag RTE_MBUF_F_RX_IP_CKSUM_BAD in the packet received

   port=0, mbuf=0x2269df7e40, pkt_len=96, nb_segs=1:
   rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_BAD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: flags=RTE_MBUF_F_TX_L4_NO_CKSUM RTE_MBUF_F_TX_IPV4

Verify flags are as expected.

Test Case: Hardware Checksum Check L4 TX
===========================================
This test involves testing many different scenarios with a L4 checksum.
A variety of tunneling protocols, L3 protocols and L4 protocols are combined
to test as many scenarios as possible. Currently, UDP and TCP are used
as L4 protocols, with IP and IPv6 being used at level 3. The tested tunneling
protocols are VXLAN and GRE. This test is used to determine whether the
hardware offloading of checksums works properly.

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Start the packet forwarding::

  testpmd> port stop all
  testpmd> csum set ip hw 0
  testpmd> csum set udp hw 0
  testpmd> csum set tcp hw 0
  testpmd> csum set sctp hw 0
  testpmd> port start all
  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8


Start a packet capture on the tester in the background::

   # tcpdump -i <iface> -s 65535 -w /tmp/tester/test_hardware_checksum_check_l4_tx_capture.pcap &

Send a packet ptypes is IP/UDP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP(chksum=0xb161)/Raw(load=b'x'), iface=iface)

   port=0, mbuf=0x168d06200, pkt_len=90, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=8
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP(chksum=0xf)/Raw(load=b'x'), iface=iface)

   port=0, mbuf=0x168d06b40, pkt_len=90, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=8
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/TCP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/TCP(chksum=0x4904)/Raw(load=b'x'), iface=iface)

   port=0, mbuf=0x168d07480, pkt_len=102, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/TCP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/TCP(chksum=0xf)/Raw(load=b'x'), iface=iface)

   port=0, mbuf=0x168be47c0, pkt_len=102, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/UDP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPv6()/UDP(chksum=0xaf62)/Raw(load=b'x'), iface=iface)

   port=0, mbuf=0x168be5100, pkt_len=110, nb_segs=1:
   rx: l2_len=14 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=40 m->l4_len=8
   tx: flags=RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV6

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPv6()/UDP(chksum=0xf)/Raw(load=b'x'), iface=iface)

   port=0, mbuf=0x168be5a40, pkt_len=110, nb_segs=1:
   rx: l2_len=14 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=40 m->l4_len=8
   tx: flags=RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV6

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/TCP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPv6()/TCP(chksum=0x4705)/Raw(load=b'x'), iface=iface)

   port=0, mbuf=0x168be6380, pkt_len=122, nb_segs=1:
   rx: l2_len=14 ethertype=86dd l3_len=40 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=40 m->l4_len=20
   tx: flags=RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV6

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/TCP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPv6()/TCP(chksum=0xf)/Raw(load=b'x'), iface=iface)

   port=0, mbuf=0x168be6cc0, pkt_len=122, nb_segs=1:
   rx: l2_len=14 ethertype=86dd l3_len=40 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=40 m->l4_len=20
   tx: flags=RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV6

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/UDP/VXLAN/IP/UDP inner UDP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP()/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IP()/UDP(chksum=0x9949)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168be7600, pkt_len=140, nb_segs=1:
   rx: l2_len=30 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=30 m->l3_len=20 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/UDP/VXLAN/IP/UDP inner UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP()/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IP()/UDP(chksum=0xf)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168be7600, pkt_len=140, nb_segs=1:
   rx: l2_len=30 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=30 m->l3_len=20 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/UDP/VXLAN/IP/UDP outer UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP(chksum=0xf)/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IP()/UDP()/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168be7600, pkt_len=140, nb_segs=1:
   rx: l2_len=30 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=30 m->l3_len=20 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/UDP/VXLAN/IP/UDP inter UDP and outer UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP(chksum=0xf)/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IP()/UDP(chksum=0xf)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168be7600, pkt_len=140, nb_segs=1:
   rx: l2_len=30 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=30 m->l3_len=20 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/UDP/VXLAN/IP/TCP inner TCP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP()/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IP()/TCP(chksum=0x30ec)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168d058c0, pkt_len=152, nb_segs=1:
   rx: l2_len=30 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=30 m->l3_len=20 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/UDP/VXLAN/IP/TCP inner TCP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP()/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IP()/TCP(chksum=0xf)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168d04f80, pkt_len=152, nb_segs=1:
   rx: l2_len=30 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=30 m->l3_len=20 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/UDP/VXLAN/IP/TCP outer UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP(chksum=0xf)/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IP()/TCP()/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168d04640, pkt_len=152, nb_segs=1:
   rx: l2_len=30 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=30 m->l3_len=20 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/UDP/VXLAN/IP/TCP outer UDP and inner TCP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/UDP(chksum=0xf)/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IP()/TCP(chksum=0xf)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168d03d00, pkt_len=152, nb_segs=1:
   rx: l2_len=30 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=30 m->l3_len=20 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/UDP/VXLAN/IPV6/UDP inner UDP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/UDP()/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IPV6()/UDP(chksum=0x9949)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168d033c0, pkt_len=180, nb_segs=1:
   rx: l2_len=30 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=86dd outer_l3_len=40
   tx: m->l2_len=30 m->l3_len=40 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=40
   tx: flags=RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV6 RTE_MBUF_F_TX_OUTER_IPV6 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/UDP/VXLAN/IPV6/UDP inner UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/UDP()/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IPV6()/UDP(chksum=0xf)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168d02a80, pkt_len=180, nb_segs=1:
   rx: l2_len=30 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=86dd outer_l3_len=40
   tx: m->l2_len=30 m->l3_len=40 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=40
   tx: flags=RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV6 RTE_MBUF_F_TX_OUTER_IPV6 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/UDP/VXLAN/IPV6/UDP outer UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/UDP(chksum=0xf)/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IPV6()/UDP()/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168d02140, pkt_len=180, nb_segs=1:
   rx: l2_len=30 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=86dd outer_l3_len=40
   tx: m->l2_len=30 m->l3_len=40 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=40
   tx: flags=RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV6 RTE_MBUF_F_TX_OUTER_IPV6 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/UDP/VXLAN/IPV6/UDP inter UDP and outer UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/UDP(chksum=0xf)/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IPV6()/UDP(chksum=0xf)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168d01800, pkt_len=180, nb_segs=1:
   rx: l2_len=30 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=86dd outer_l3_len=40
   tx: m->l2_len=30 m->l3_len=40 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=40
   tx: flags=RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV6 RTE_MBUF_F_TX_OUTER_IPV6 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/UDP/VXLAN/IPV6/TCP inner TCP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/UDP()/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IPV6()/TCP(chksum=0x30ec)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168d00ec0, pkt_len=192, nb_segs=1:
   rx: l2_len=30 ethertype=86dd l3_len=40 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=86dd outer_l3_len=40
   tx: m->l2_len=30 m->l3_len=40 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=40
   tx: flags=RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV6 RTE_MBUF_F_TX_OUTER_IPV6 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/UDP/VXLAN/IPV6/TCP inner TCP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/UDP()/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IPV6()/TCP(chksum=0xf)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168d00580, pkt_len=192, nb_segs=1:
   rx: l2_len=30 ethertype=86dd l3_len=40 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=86dd outer_l3_len=40
   tx: m->l2_len=30 m->l3_len=40 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=40
   tx: flags=RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV6 RTE_MBUF_F_TX_OUTER_IPV6 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/UDP/VXLAN/IPV6/TCP outer UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/UDP(chksum=0xf)/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IPV6()/TCP()/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168cffc40, pkt_len=192, nb_segs=1:
   rx: l2_len=30 ethertype=86dd l3_len=40 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=86dd outer_l3_len=40
   tx: m->l2_len=30 m->l3_len=40 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=40
   tx: flags=RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV6 RTE_MBUF_F_TX_OUTER_IPV6 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/UDP/VXLAN/IPV6/TCP outer UDP and inner TCP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/UDP(chksum=0xf)/VXLAN()/
   Ether(dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00')/IPV6()/TCP(chksum=0xf)/Raw(load=b'Y'), iface=iface)

   port=0, mbuf=0x168cff300, pkt_len=192, nb_segs=1:
   rx: l2_len=30 ethertype=86dd l3_len=40 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=86dd outer_l3_len=40
   tx: m->l2_len=30 m->l3_len=40 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=40
   tx: flags=RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV6 RTE_MBUF_F_TX_OUTER_IPV6 RTE_MBUF_F_TX_TUNNEL_VXLAN RTE_MBUF_F_TX_OUTER_UDP_CKSUM

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/GRE/IP/UDP inner UDP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/GRE()/IP()/UDP(chksum=0x8131)/Raw(load=b'Z'), iface=iface)

   port=0, mbuf=0x168cfe9c0, pkt_len=114, nb_segs=1:
   rx: l2_len=4 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=4 m->l3_len=20 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_GRE

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/GRE/IP/UDP inner UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/GRE()/IP()/UDP(chksum=0xf)/Raw(load=b'Z'), iface=iface)

   port=0, mbuf=0x168cfe080, pkt_len=114, nb_segs=1:
   rx: l2_len=4 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=4 m->l3_len=20 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_GRE

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/GRE/IP/TCP inner TCP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/GRE()/IP()/TCP(chksum=0x18d4)/Raw(load=b'Z'), iface=iface)

   port=0, mbuf=0x168cfd740, pkt_len=126, nb_segs=1:
   rx: l2_len=4 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=4 m->l3_len=20 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_GRE

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/GRE/IP/TCP inner TCP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP()/GRE()/IP()/TCP(chksum=0xf)/Raw(load=b'Z'), iface=iface)

   port=0, mbuf=0x168cfce00, pkt_len=126, nb_segs=1:
   rx: l2_len=4 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=4 m->l3_len=20 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_GRE

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/GRE/IPV6/UDP inner UDP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/GRE()/IPV6()/UDP(chksum=0x8131)/Raw(load=b'Z'), iface=iface)

   port=0, mbuf=0x168cfe9c0, pkt_len=114, nb_segs=1:
   rx: l2_len=4 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=4 m->l3_len=20 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_GRE

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/GRE/IPV6/UDP inner UDP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/GRE()/IPV6()/UDP(chksum=0xf)/Raw(load=b'Z'), iface=iface)

   port=0, mbuf=0x168cfe080, pkt_len=114, nb_segs=1:
   rx: l2_len=4 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=4 m->l3_len=20 m->l4_len=8
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_UDP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_GRE

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/GRE/IPV6/TCP inner TCP with a good checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/GRE()/IPV6()/TCP(chksum=0x18d4)/Raw(load=b'Z'), iface=iface)

   port=0, mbuf=0x168cfd740, pkt_len=126, nb_segs=1:
   rx: l2_len=4 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=4 m->l3_len=20 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_GRE

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IPV6/GRE/IPV6/TCP inner TCP with a bad checksum::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IPV6()/GRE()/IPV6()/TCP(chksum=0xf)/Raw(load=b'Z'), iface=iface)

   port=0, mbuf=0x168cfce00, pkt_len=126, nb_segs=1:
   rx: l2_len=4 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_BAD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   rx: outer_l2_len=14 outer_ethertype=800 outer_l3_len=20
   tx: m->l2_len=4 m->l3_len=20 m->l4_len=20
   tx: m->outer_l2_len=14 m->outer_l3_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4 RTE_MBUF_F_TX_OUTER_IP_CKSUM RTE_MBUF_F_TX_OUTER_IPV4 RTE_MBUF_F_TX_TUNNEL_GRE

   Inspect the pcap file from the packet capture and verify the checksums.

Test Case: Hardware Checksum Check L3 TX
===========================================
This test involves testing L3 checksum hardware offload.
Due to the relative dominance of IPv4 and IPv6 as L3 protocols, and IPv6's
lack of a checksum, only IPv4's checksum is tested.

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Start the packet forwarding::

  testpmd> port stop all
  testpmd> csum set ip hw 0
  testpmd> csum set udp hw 0
  testpmd> csum set tcp hw 0
  testpmd> csum set sctp hw 0
  testpmd> port start all
  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Start a packet capture on the tester in the background::

   # tcpdump -i <iface> -s 65535 -w /tmp/tester/test_hardware_checksum_check_l3_tx_capture.pcap &

Send a packet ptypes is IP/TCP with a good checksum with a 1 in it's payload::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=0x7ccc)/TCP()/Raw(load=b'1'), iface=iface)

   port=0, mbuf=0x168d06200, pkt_len=60, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_GOOD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4

   Inspect the pcap file from the packet capture and verify the checksums.

Send a packet ptypes is IP/TCP with a bad checksum with a 0 in it's payload::

   sendp(Ether(dst='23:00:00:00:00:00', src='52:00:00:00:00:00')/IP(chksum=0xf)/TCP()/Raw(load=b'1'), iface=iface)

   port=0, mbuf=0x168d06b40, pkt_len=60, nb_segs=1:
   rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=6 l4_len=20 flags=RTE_MBUF_F_RX_L4_CKSUM_GOOD RTE_MBUF_F_RX_IP_CKSUM_BAD RTE_MBUF_F_RX_OUTER_L4_CKSUM_UNKNOWN
   tx: m->l2_len=14 m->l3_len=20 m->l4_len=20
   tx: flags=RTE_MBUF_F_TX_IP_CKSUM RTE_MBUF_F_TX_TCP_CKSUM RTE_MBUF_F_TX_IPV4

   Inspect the pcap file from the packet capture and verify the checksums.

Test Case: checksum offload with vlan
=====================================

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Enable the IPv4/UDP/TCP/SCTP checksum offload on port 0::

  testpmd> port stop all
  testpmd> csum set ip hw 0
  testpmd> csum set udp hw 0
  testpmd> csum set tcp hw 0
  testpmd> csum set sctp hw 0
  testpmd> port start all
  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Start a packet capture on the tester in the background::

   tcpdump -i <iface> -s 65535 -w /tmp/tester/test_checksum_capture.pcap &

Send the following multiple packets from tester for with scapy 
combination: IPv4/UDP, IPv4/TCP, IPv6/UDP, IPv6/TCP::

   sendp([Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/Dot1Q(vlan=1)/IP(chksum=0x0)/UDP(chksum=0xf)/("X"*46),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/Dot1Q(vlan=1)/IP(chksum=0x0)/TCP(chksum=0xf)/("X"*46),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/Dot1Q(vlan=1)/IP(chksum=0x0)/SCTP(chksum=0x0)/("X"*48),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/Dot1Q(vlan=1)/IPv6(src="::1")/UDP(chksum=0xf)/("X"*46),
   Ether(dst="52:00:00:00:00:01", src="52:00:00:00:00:00")/Dot1Q(vlan=1)/IPv6(src="::1")/TCP(chksum=0xf)/("X"*46)],
   iface="ens192f0",count=4,inter=0,verbose=False)

Then verify that the same number of packet are correctly received on the tester. 

Inspect the pcap file from the packet capture and verify the checksums.