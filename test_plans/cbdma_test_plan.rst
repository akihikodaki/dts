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

===============
CBDMA test plan
===============

Sample Application of packet copying using Intel Quick Data Technology
======================================================================

Overview
--------

This sample is intended as a demonstration of the basic components of a DPDK
forwarding application and example of how to use IOAT driver API to make
packets copies. Also, this application can be used to compare performance of
memory copy with different packet size between CPU and DMA engine. The application
will print out statistics each second. The stats shows received/send packets and
packets dropped or failed to copy. The application can be launched in various
configurations depending on provided parameters. Each port can use up to 2 lcores:
one of lcore receives incoming traffic and makes a copy of each packet, the second
lcore then updates MAC address and sends the copy. If one lcore per port is used,
both operations are done sequentially. For each configuration an additional lcore
is needed since master lcore in use which is responsible for configuration,
statistics printing and safe deinitialization of all ports and devices. Also, the
application can use 8 ports in maximum.

Running the Application
-----------------------

In order to run the hardware copy application, the copying device
needs to be bound to user-space IO driver.

Refer to the *IOAT Rawdev Driver for Intel QuickData Technology*
guide for information on using the driver.

The application requires a number of command line options:

.. code-block:: console

    ./build/ioatfwd [EAL options] -- -p MASK [-q NQ] [-s RS] [-c <sw|hw>]
        [--[no-]mac-updating]

where,

*   p MASK: A hexadecimal bitmask of the ports to configure

*   q NQ: Number of Rx queues used per port equivalent to CBDMA channels
    per port

*   c CT: Performed packet copy type: software (sw) or hardware using
    DMA (hw)

*   s RS: Size of IOAT rawdev ring for hardware copy mode or rte_ring for
    software copy mode

*   --[no-]mac-updating: Whether MAC address of packets should be changed
    or not

Packet pipeline: 
================
NIC RX -> copy packet -> free original -> update mac addresses -> NIC TX

Test Case1: CBDMA basic test with differnet size packets
========================================================

1.Bind one cbdma port and one nic port to igb_uio driver.

2.Launch ioatfwd app::

./build/ioatfwd -l 0-1 -n 2 -- -p 0x1 -c hw --mac-updating

3.Send different size packets (64B, 256B, 512B, 1024B, IMIX) from TG to NIC.

4.Check performance from “Total packets Tx” and check log includes "Worker Threads = 1, Copy Mode = hw".

Test Case2: CBDMA test with multi-threads
=========================================

1.Bind one cbdma port and one nic port to igb_uio driver.

2.Launch ioatfwd app with three cores::

./build/ioatfwd -l 0-2 -n 2 -- -p 0x1 -c hw

3. Send different size packets from TG to NIC.

4.Check performance from “Total packets Tx” and check log includes "Worker Threads = 2, Copy Mode = hw".

Test Case3: CBDMA test with multi nic ports
===========================================

1.Bind two cbdma ports and two nic ports to igb_uio driver.

2.Launch ioatfwd app with multi-ports::

./build/ioatfwd -l 0-4 -n 2 -- -p 0x3 -q 1 -c hw

3.Send different size packets (64B, 256B, 512B, 1024B, IMIX) from TG to two NIC ports.

4.Check stats of two ports, each port's performance shows in “Total packets Tx” and each port's log includes "Worker Threads = 2, Copy Mode = hw".

Test Case4: CBDMA test with multi-queues
========================================

1.Bind two cbdma ports and one nic port to igb_uio driver.

2.Launch ioatfwd app with multi-queues::

./build/ioatfwd -l 0-2 -n 2 -- -p 0x1 -q 2 -c hw

3. Send random ip packets (64B, 256B, 512B, 1024B, IMIX) from TG to NIC port.

4. Check stats of ioat app, "Worker Threads = 2, Copy Mode = hw, Rx Queues = 2" and each ioat channel can enqueue packets.

5. Repeat step1 to step4 with queue number 4 and qemu number 8, also bind same number cbdma ports.
Check performance gains status when queue numbers added.

Test Case5: CBDMA performance cmparison between mac-updating and no-mac-updating
================================================================================

1.Bind one cbdma ports and one nic port to igb_uio driver.

2.Launch ioatfwd app::

./build/ioatfwd -l 0-1 -n 2 -- -p 0x1 -q 2 --no-mac-updating -c hw

3. Send random ip 64B packets from TG.

4. Check performance from ioat app::

    Total packets Tx:                   xxx [pps]

5.Launch ioatfwd app::

./build/ioatfwd -l 0-1 -n 2 -- -p 0x1 -q 2 --mac-updating -c hw

6. Send random ip 64B packets from TG.

7. Check performance from ioat app::

    Total packets Tx:                   xxx [pps]
  
Test Case6: CBDMA performance cmparison between HW copies and SW copies using different packet size
===================================================================================================

1.Bind four cbdma pors and one nic port to igb_uio driver.

2.Launch ioatfwd app with three cores::

./build/ioatfwd -l 0-2 -n 2 -- -p 0x1 -q 4  -c hw

3. Send random ip packets from TG.

4. Check performance from ioat app::

    Total packets Tx:                   xxx [pps]

5.Launch ioatfwd app with three cores::

./build/ioatfwd -l 0-2 -n 2 -- -p 0x1 -q 4 -c sw

6. Send random ip packets from TG.

7. Check performance from ioat app and compare with hw copy test::

    Total packets Tx:                   xxx [pps]
