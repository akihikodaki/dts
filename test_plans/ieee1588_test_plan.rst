.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2016-2017 Intel Corporation

====================================
IEEE1588 Precise Time Protocol Tests
====================================

The functional test of the IEEE1588 Precise Time Protocol offload support
in Poll Mode Drivers is done with a specific `ieee1588`` forwarding mode
of the ``testpmd`` application.

In this mode, packets are received one by one and are expected to be
PTP V2 L2 Ethernet frames with the specific Ethernet type ``0x88F7``,
containing PTP ``SYNC`` messages (version 2 at offset 1, and message ID
0 at offset 0).

When started, the test enables the IEEE1588 PTP offload support of each
controller. It makes them automatically filter and timestamp the receipt
of incoming PTP ``SYNC`` messages contained in PTP V2 Ethernet frames.
Conversely, when stopped, the test disables the IEEE1588 PTP offload support
of each controller,

While running, the test checks that each received packet is a valid IEEE1588
PTP V2 Ethernet frame with a message of type ``PTP_SYNC_MESSAGE``, and that
the packet has been identified and timestamped by the hardware.
For this purpose, it checks that the corresponding ``PKT_RX_IEEE1588_PTP``
and ``PKT_RX_IEEE1588_TMST`` flags have been set in the mbufs returned
by the PMD receive function.

Then, the test checks that the two NIC registers holding the timestamp of a
received PTP packet are effectively valid, and that they contain a value
greater than their previous value.

If everything is OK, the test sends the received packet as-is on the same port,
requesting for its transmission to be timestamped by the hardware.
For this purpose, it set the ``PKT_TX_IEEE1588_TMST`` flag of the mbuf before
sending it.
The test finally checks that the two NIC registers holding the timestamp of
a transmitted PTP packet are effectively valid, and that they contain a value
greater than their previous value.


Prerequisites
=============

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

The support of the IEEE1588 Precise Time Protocol in Poll Mode Drivers must
be configured at compile-time with the ``CONFIG_RTE_LIBRTE_IEEE1588`` option.

Configure the packet format for the traffic generator to be IEEE1588 PTP
Ethernet type ``0x88F7`` and containing PTP ``SYNC`` (version 2 at offset 1,
and message ID 0 at offset 0).

Start the ``testpmd`` application with the following parameters::

   -cffffff -n 3 -- -i --rxpt=0 --rxht=0 --rxwt=0 \
   --txpt=39 --txht=0 --txwt=0

The -n command is used to select the number of memory channels. It should match the number of memory channels on that setup.

Test Case: Enable IEEE1588 PTP packet reception and generation
==============================================================

Select the ``ieee1588`` test forwarding mode and start the test::

   testpmd> set fwd ieee1588
   Set ieee1588 packet forwarding mode
   testpmd> start
     ieee1588 packet forwarding - CRC stripping disabled - packets/burst=16
     nb forwarding cores=1 - nb forwarding ports=2
     RX queues=1 - RX desc=128 - RX free threshold=0
     RX threshold registers: pthresh=0 hthresh=0 wthresh=0
     TX queues=1 - TX desc=512 - TX free threshold=0
     TX threshold registers: pthresh=39 hthresh=0 wthresh=0
   testpmd>

On the traffic generator side send one IEEE1588 PTP packet.

Verify that the testpmd application outputs something like this, with a timestamp
different than 0::

   testpmd> Port 8 IEEE1588 PTP V2 SYNC Message filtered by hardware
   Port 8 RX timestamp value 0x78742550448000000
   Port 8 TX timestamp value 0x78742561472000000 validated after 2 micro-seconds
   Port 8 IEEE1588 PTP V2 SYNC Message filtered by hardware
   Port 8 RX timestamp value 0x79165536192000000
   Port 8 TX timestamp value 0x79165545648000000 validated after 2 micro-seconds


Verify that the TX timestamp is bigger than the RX timestamp.
Verify that the second RX timestamp is bigger than the first RX timestamp.
Verify that the TX IEEE1588 PTP packet is received by the traffic generator.


Test Case: Disable IEEE1588 PTP packet reception and generation
===============================================================

Stop the IEEE1588 fwd::

 testpmd> stop
 ...
 testpmd>

 Send one IEEE1588 PTP packet

Verify that the packet is not filtered by the HW (IEEE1588 PTP V2 SYNC Message
is not displayed).  (??? Is it correct? Should we set fwd rxonly ?)
