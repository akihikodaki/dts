.. Copyright (c) < 2019 >, Intel Corporation
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:

    - Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.

    - Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in
        the documentation and / or other materials provided with the
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
     SERVICES
     LOSS OF USE, DATA, OR PROFITS
     OR BUSINESS INTERRUPTION)
    HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
    STRICT LIABILITY, OR TORT(INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
    OF THE POSSIBILITY OF SUCH DAMAGE.

===================
L2fwd Jobstats Test
===================

The L2 Forwarding sample application, which can operate in real and virtualized
environments, performs L2 forwarding for each packet that is received. The destination
port is the adjacent port from the enabled portmask, that is, if the first four
ports are enabled (portmask 0x3), ports 0 and 1 forward into each other. Also,
the MAC addresses are affected as follows:

- The source MAC address is replaced by the TX port MAC address
- The destination MAC address is replaced by 02:00:00:00:00:TX_PORT_ID

Prerequisites
=============

Use the following commands to load the dpdk driver and bind it to the device under test::

    modprobe DPDK-Drivername
    usertools/dpdk-devbind.py --bind=DPDK-Drivername device_bus_id

e.g.
if DPDK-Drivername is vfio-pci::

    modprobe vfio
    modprobe vfio-pci
    usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

note: If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.

The application requires a number of command line options::

    ./build/l2fwd-jobstats [EAL options] -- -p PORTMASK [-q NQ] [-l]

The ``l2fwd-jobstats`` application is run with EAL parameters and parameters for
the application itself. For details about the EAL parameters, see the relevant
DPDK **Getting Started Guide**. This application supports three parameters for
itself.

- p PORTMASK: A hexadecimal bitmask of the ports to configure
- q NQ: A number of queues (=ports) per lcore (default is 1)
- l: Use locale thousands separator when formatting big numbers.

Test Case: L2fwd jobstats check
================================================

Assume port 0 and 1 are connected to the traffic generator, to run the test
application in linuxapp environment with 2 lcores, 2 ports and 2 RX queues
per lcore::

    ./examples/l2fwd-jobstats/build/l2fwd-jobstats -c 0x03 -n 4  -- -q 2 -p 0x03 -l

Then send 100, 000 packet to port 0 and 100, 000 packets to port 1, check the
NIC packets number reported by sample is the same with what we set at the packet
generator side.
