.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2020 Intel Corporation

=========================================
Sample Application Tests: Packet Ordering
=========================================

This document provides test plan for benchmarking of the Packet Ordering
sample application. This is a simple example app featuring packet processing
using Data Plane Development Kit (DPDK) based on a sliding window using a
sequence number for the packet and a reorder queue.

This app makes use of the librte_reorder library, it requires at least 3 lcores
for RX, Workers (1 or more) and TX threads. Communication between RX-Workers and
Workers-TX is done by using rings. The flow of mbufs is the following:

  * RX thread gets mbufs from driver, set sequence number and enqueue them in ring.
  * Workers dequeue mbufs from ring, do some 'work' and enqueue mbufs in ring.
  * TX dequeue mbufs from ring, inserts them in reorder buffer, drains mbufs from
    reorder and sends them to the driver.

Command Usage::

  ./dpdk-packet_ordering [EAL options] -- [-p PORTMASK] [--insight-worker]

    -p PORTMASK         : hexadecimal bitmask of ports to configure
    --insight-worker    : print per core stats

For example::

  ./dpdk-packet_ordering -l 30-35 -- -p 0x1 --insight-worker

    RX thread stats:
     - Pkts rxd:                            17026944
     - Pkts enqd to workers ring:           17026944

    Worker thread stats on core [31]:
     - Pkts deqd from workers ring:         4486598
     - Pkts enqd to tx ring:                4486598
     - Pkts enq to tx failed:               0

    Worker thread stats on core [32]:
     - Pkts deqd from workers ring:         4014658
     - Pkts enqd to tx ring:                4014658
     - Pkts enq to tx failed:               0

    Worker thread stats on core [33]:
     - Pkts deqd from workers ring:         4694356
     - Pkts enqd to tx ring:                4694356
     - Pkts enq to tx failed:               0

    Worker thread stats on core [34]:
     - Pkts deqd from workers ring:         3831332
     - Pkts enqd to tx ring:                3831332
     - Pkts enq to tx failed:               0

    Worker thread stats:
     - Pkts deqd from workers ring:         17026944
     - Pkts enqd to tx ring:                17026944
     - Pkts enq to tx failed:               0

    TX stats:
     - Pkts deqd from tx ring:              17026944
     - Ro Pkts transmitted:                 17026944
     - Ro Pkts tx failed:                   0
     - Pkts transmitted w/o reorder:        0
     - Pkts tx failed w/o reorder:          0

    Port 0 stats:
     - Pkts in:   17026944
     - Pkts out:  17026944
     - In Errs:   0
     - Out Errs:  0
     - Mbuf Errs: 0


Prerequisites
=============

1x Intel® Ethernet Port (710 series, 82599, etc)

Test Case: Packet ordering at different rates
=============================================

The test case will send packets from the external traffic generator through
the sample application which will forward them back to the source port.
Each packet will have a sequential number which could be used to judge
if a packet is in the right order. It's fine to increase packet type, IP dst
addr, etc to generate sequential numbers.
Different traffic rates will be tested. The rate will go from 10% to 100%
with 10% steps.

The results will be presented as a table with the following values:

Reordering: indicate if reorder the traffic.

Mask: used CPU core mask.

Rate: transmission rate.

Sent: number of frames sent from the traffic generator.

Received: number of frames received back.

Captured: number of frames captured.

Reordered ratio: ratio between out of order packets and total sent packets.

+------------+------+------+--------+----------+----------+---------------+
| Reordering | Mask | Rate |  Sent  | Received | Captured | Reorder ratio |
+============+======+======+========+==========+==========+===============+
| Yes        | 0xaa | 10   |        |          |          |               |
+------------+------+------+--------+----------+----------+---------------+
| Yes        | 0xf  | 10   |        |          |          |               |
+------------+------+------+--------+----------+----------+---------------+
| No         | 0xaa | 10   |        |          |          |               |
+------------+------+------+--------+----------+----------+---------------+
| No         | 0xf  | 10   |        |          |          |               |
+------------+------+------+--------+----------+----------+---------------+

Run the app with below sample command::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-packet_ordering -c coremask  -- -p portmask

Test Case: keep the packet ordering
===================================

This is a basic functional test without high speed flows.
Send a series of packet for scapy, and check the packets forwarded out from the
app is ordering.

1. Run the sample with below command::

    ./x86_64-native-linuxapp-gcc/examples/dpdk-packet_ordering -c coremask  -- -p portmask

2. Send 1000 packets with the same 5-tuple traffic from Scapy

3. Observe the packets received and check the packets order.
