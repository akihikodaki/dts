.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

=======================
Scattered Packets Tests
=======================

The support of scattered packets by Poll Mode Drivers consists in making
it possible to receive and to transmit scattered multi-segments packets
composed of multiple non-contiguous memory buffers.
To enforce the receipt of scattered packets, the DMA rings of port RX queues
must be configured with mbuf data buffers whose size is lower than the maximum
frame length.
The forwarding of scattered input packets naturally enforces the transmission
of scattered packets by PMD transmit functions.

Configuring the size of mbuf data buffers
=========================================

The size of mbuf data buffers is configured with the parameter ``--mbuf-size``
that is supplied in the set of parameters when launching the ``testpmd``
application.
The default size of the mbuf data buffer is 2048 so that a full 1518-byte
(CRC included) Ethernet frame can be stored in a mono-segment packet.

Functional Tests of Scattered Packets
=====================================

Testing the support of scattered packets in Poll Mode Drivers consists in
sending to the test machine packets whose length is greater than the size
of mbuf data buffers used to populate the DMA rings of port RX queues.

First, the receipt and the transmission of scattered packets must be tested
with the ``CRC stripping`` option enabled, which guarantees that scattered
packets only contain packet data.

In addition, the support of scattered packets must also be performed with
the ``CRC stripping`` option disabled, to check the special cases of scattered
input packets whose last buffer only contains the whole CRC or part of it.
In such cases, PMD receive functions must free the last buffer when removing
the CRC from the packet before returning it.

As a whole, the following packet lengths (CRC included) must be tested to
check all packet memory configurations:

1) packet length < mbuf data buffer size

2) packet length = mbuf data buffer size

3) packet length = mbuf data buffer size + 1

4) packet length = mbuf data buffer size + 4

5) packet length = mbuf data buffer size + 5

In cases 1) and 2), the hardware RX engine stores the packet data and the CRC
in a single buffer.

In case 3), the hardware RX engine stores the packet data and the 3 first bytes
of the CRC in the first buffer, and the last byte of the CRC in a second buffer.

In case 4), the hardware RX engine stores all the packet data in the first
buffer, and the CRC in a second buffer.

In case 5), the hardware RX engine stores part of the packet data in the first
buffer, and the last data byte plus the CRC in a second buffer.

Prerequisites
=============

Assuming that ports ``0`` and ``1`` of the test target are directly connected
to a Traffic Generator, launch the ``testpmd`` application with the following
arguments::

  ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x6 -n 4 -- -i --mbcache=200 \
  --mbuf-size=2048 --portmask=0x1 --max-pkt-len=9000 --port-topology=loop \
  --tx-offloads=DEV_TX_OFFLOAD_MULTI_SEGS

The -n command is used to select the number of memory channels. It should match
the number of memory channels on that setup.

DEV_TX_OFFLOAD_MULTI_SEGS is a TX offload capability, means device supports
multi segment send. Defined in DPDK code lib/librte_ethdev/rte_ethdev.h::

  #define DEV_TX_OFFLOAD_MULTI_SEGS       0x00008000

Test Case: Scatter Mbuf 2048
============================

Start packet forwarding in the ``testpmd`` application with the ``start`` command.
Send 5 packets,the lengths are mbuf-size + offset (CRC included).
The offset are -1, 0, 1, 4, 5 respectively.
Check that the same amount of frames and bytes are received back by the Traffic
Generator from it's port connected to the target's port 1.
