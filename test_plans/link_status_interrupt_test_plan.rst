.. Copyright (c) <2010-2017>, Intel Corporation
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

===========================
Link Status Detection Tests
===========================

This tests for Detect Link Status feature can be run on linux userspace.
It is to check if the userspace interrupt can be received after plugging
in/out the cable/fiber on specified NIC port, and if the link status can
be updated correctly. Furthermore, it would be better to check if packets
can be received and sent on a specified port after its link has just up.
So it may need layer 2 forwarding at the same time.

For layer 2 forwarding, a packet received on a RX port (RX_PORT), it would
be transmitted from a TX port (TX_PORT=RX_PORT+1) if RX_PORT is even;
otherwise from a TX port (TX_PORT=RX_PORT-1) if RX_PORT is odd. Before
being transmitted, the source mac address of the packet would be replaced
by the mac address of the TX port, while the destination mac address would
be replaced by 00:09:c0:00:00:TX_PORT_ID. The test application should be
run with the wanted paired ports configured using the coremask parameter
via the command line. i.e. port 0 and 1 is a valid pair, while port 1 and
2 isn't. The test is performed by running the test application and using a
traffic generator.

The ``link_status_interrupt`` application is run with EAL parameters and
parameters for the application itself. This application supports three
parameters for itself.

- ``-p PORTMASK``: hexadecimal bitmask of ports to config
- ``-q NQ``: number of queue per lcore (default is 1)
- ``-T PERIOD``: refresh period in seconds (0/10/86400: disable/default/maximum)

Prerequisites
=============

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

The test app need add a cmdline, ``--vfio-intr=int_x``.

Assume port 0 and 1 are connected to the remote ports, e.g. packet generator.
To run the test application in linuxapp environment with 4 lcores, 2 ports and
2 RX queues per lcore::

    $ ./link_status_interrupt -c f -- -q 2 -p 0x3

Also, if the ports need to be tested are different, the port mask should be
changed. The lcore used to run the test application and the number of queues
per lcore could be changed.

Test Case: Link Status Change
=============================

Run the test application as above command. Then plug out the cable/fiber, or
simulate a disconnection. After several seconds, check if the link is actually
off. Then plug in the cable/fiber, or simulate a connection. After several seconds,
check if the link is actually up, and print its information about duplex and speed.

Test Case: Port available
=========================

Run the test application as above command with cable/fiber plugged out from both
port 0 and 1, then plug it in. After several seconds and the link of all the ports
is up. Together with packet generator, do layer 2 forwarding, and check if the
packets can be received on port 0/1 and sent out on port 1/0.
