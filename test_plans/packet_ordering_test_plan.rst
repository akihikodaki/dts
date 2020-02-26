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



===============
Packet Ordering
===============

This document provides test plan for benchmarking of the Packet Ordering
sample application. This is a simple example app featuring packet processing
using Intel® Data Plane Development Kit (Intel® DPDK) based on a sliding window
using a sequence number for the packet and a reorder queue.


Prerequisites
-------------------

1x Intel® 82599 (Niantic) NICs (1x 10GbE full duplex optical ports per NIC)
plugged into the available PCIe Gen2 8-lane slot.

Test Case: Packet ordering at different rates
=============================================

The test case will send packets from the external traffic generator through
the sample application which will forward them back to the source port.
Each packet will have a sequential number which could be used to judge
if a packet is in the right order.
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

    ./examples/packet_ordering/build/packet_ordering -c coremask  -- -p portmask

Test Case: keep the packet ordering
===================================

This is a basic functional test.
The packets order which will pass through a same flow should be guaranteed.

1. Run the sample with below command::

    ./examples/packet_ordering/build/packet_ordering -c coremask  -- -p portmask

2. Send 1000 packets with the same 5-tuple traffic from Scapy

3. Observe the packets received and check the packets order.
