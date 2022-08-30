.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2015-2017 Intel Corporation

==========
VF Offload
==========


Prerequisites for checksum offload
==================================

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios. When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

IP link set VF trust on and spoofchk off on DUT::

   ip link set $PF_INTF vf 0 trust on
   ip link set $PF_INTF vf 0 spoofchk off

Assuming that ports ``0`` and ``1`` are connected to a traffic generator,
enable hardware rx checksum offload with "--enable-rx-cksum",
launch the ``testpmd`` with the following arguments::

  ./build/app/dpdk-testpmd -cffffff -n 1 -- -i --burst=1 --txpt`=32 \
  --txht=8 --txwt=0 --txfreet=0 --rxfreet=64 --mbcache=250 --portmask=0x5
  --enable-rx-cksum

Set the verbose level to 1 to display information for each received packet::

  testpmd> set verbose 1

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

Verify that how many packets found with Bad-ipcsum or Bad-l4csum::

  testpmd> stop
  ---------------------- Forward statistics for port 0  ----------------------
  RX-packets: 0              RX-dropped: 0             RX-total: 0
  Bad-ipcsum: 0              Bad-l4csum: 0
  TX-packets: 0              TX-dropped: 0             TX-total: 0
  ----------------------------------------------------------------------------


Test Case: HW checksum offload check
====================================
Start testpmd and enable checksum offload on rx port.

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Enable the IPv4/UDP/TCP/SCTP HW checksum offload on port 0::

  testpmd> port stop all
  testpmd> csum set ip hw 0
  testpmd> csum set tcp hw 0
  testpmd> csum set udp hw 0
  testpmd> csum set sctp hw 0
  testpmd> port start all
  testpmd> set promisc 0 on
  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Configure the traffic generator to send the multiple packets for the following
combination: IPv4/UDP, IPv4/TCP, IPv4/SCTP, IPv6/UDP, IPv6/TCP.

Send packets with incorrect checksum,
verify dpdk can rx it and report the checksum error,
verify that the same number of packet are correctly received on the traffic
generator side. And IPv4 checksum, TCP checksum, UDP checksum, SCTP checksum need
be validated as pass by the tester.

The IPv4 source address will not be changed by testpmd.


Test Case: SW checksum offload check
====================================

Enable SW checksum offload, send same packet with incorrect checksum
and verify checksum is valid.

Setup the ``csum`` forwarding mode::

  testpmd> set fwd csum
  Set csum packet forwarding mode

Enable the IPv4/UDP/TCP/SCTP SW checksum offload on port 0::

  testpmd> port stop all
  testpmd> csum set ip sw 0
  testpmd> csum set tcp sw 0
  testpmd> csum set udp sw 0
  testpmd> csum set sctp sw 0
  testpmd> port start all
  testpmd> set promisc 0 on
  testpmd> start
    csum packet forwarding - CRC stripping disabled - packets/burst=32
    nb forwarding cores=1 - nb forwarding ports=10
    RX queues=1 - RX desc=128 - RX free threshold=64
    RX threshold registers: pthresh=8 hthresh=8 wthresh=4
    TX queues=1 - TX desc=512 - TX free threshold=0
    TX threshold registers: pthresh=32 hthresh=8 wthresh=8

Configure the traffic generator to send the multiple packets for the following
combination: IPv4/UDP, IPv4/TCP, IPv6/UDP, IPv6/TCP.

Send packets with incorrect checksum,
verify dpdk can rx it and report the checksum error,
verify that the same number of packet are correctly received on the traffic
generator side. And IPv4 checksum, TCP checksum, UDP checksum need
be validated as pass by the tester.

The first byte of source IPv4 address will be increased by testpmd. The checksum
is indeed recalculated by software algorithms.

Prerequisites for TSO
=====================

The DUT must take one of the Ethernet controller ports connected to a port on another
device that is controlled by the Scapy packet generator.

The Ethernet interface identifier of the port that Scapy will use must be known.
On tester, all offload feature should be disabled on tx port, and start rx port capture::

  ethtool -K <tx port> rx off tx off tso off gso off gro off lro off
  ip l set <tx port> up
  tcpdump -n -e -i <rx port> -s 0 -w /tmp/cap


On DUT, run pmd with parameter "--enable-rx-cksum". Then enable TSO on tx port
and checksum on rx port. The test commands is below::

  # Enable hw checksum on rx port
  testpmd> port stop all
  testpmd> csum set ip hw 0
  testpmd> csum set tcp hw 0
  testpmd> csum set udp hw 0
  testpmd> csum set sctp hw 0
  testpmd> port start all
  testpmd> set promisc 0 on
  testpmd> set fwd csum

  # Enable TSO on tx port
  testpmd> tso set 800 1


Test case: csum fwd engine, use TSO
===================================

This test uses ``Scapy`` to send out one large TCP package. The dut forwards package
with TSO enable on tx port while rx port turns checksum on. After package send out
by TSO on tx port, the tester receives multiple small TCP package.

Turn off tx port by ethtool on tester::

  ethtool -K <tx port> rx off tx off tso off gso off gro off lro off
  ip l set <tx port> up

Capture package rx port on tester::

  tcpdump -n -e -i <rx port> -s 0 -w /tmp/cap

Launch the userland ``testpmd`` application on DUT as follows::

  testpmd> set verbose 1
  # Enable hw checksum on rx port
  testpmd> port stop all
  testpmd> csum set ip hw 0
  testpmd> csum set tcp hw 0
  testpmd> csum set udp hw 0
  testpmd> csum set sctp hw 0
  testpmd> set promisc 0 on
  testpmd> port start all

  # Enable TSO on tx port
  testpmd> tso set 800 1
  # Set fwd engine and start

  testpmd> set fwd csum
  testpmd> start

Test IPv4() in scapy::

    sendp([Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="192.168.1.1",dst="192.168.1.2")/UDP(sport=1021,dport=1021)/Raw(load="\x50"*%s)], iface="%s")

Test IPv6() in scapy::

    sendp([Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="FE80:0:0:0:200:1FF:FE00:200", dst="3555:5555:6666:6666:7777:7777:8888:8888")/UDP(sport=1021,dport=1021)/Raw(load="\x50"*%s)], iface="%s")
