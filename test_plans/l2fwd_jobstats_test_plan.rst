.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

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

    ./<build_target>/examples/dpdk-l2fwd-jobstats [EAL options] -- -p PORTMASK [-q NQ] [-l]

The ``l2fwd-jobstats`` application is run with EAL parameters and parameters for
the application itself. For details about the EAL parameters, see the relevant
DPDK **Getting Started Guide**. This application supports three parameters for
itself.

- p PORTMASK: A hexadecimal bitmask of the ports to configure
- q NQ: A number of queues (=ports) per lcore (default is 1)
- l: Use locale thousands separator when formatting big numbers.

Build dpdk and examples=l2fwd-jobstats:
   CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static <build_target>
   ninja -C <build_target>

   meson configure -Dexamples=l2fwd-jobstats <build_target>
   ninja -C <build_target>

Test Case: L2fwd jobstats check
================================================

Assume port 0 and 1 are connected to the traffic generator, to run the test
application in linuxapp environment with 2 lcores, 2 ports and 2 RX queues
per lcore::

    ./<build_target>/examples/dpdk-l2fwd-jobstats -c 0x03 -n 4  -- -q 2 -p 0x03 -l

Then send 100, 000 packet to port 0 and 100, 000 packets to port 1, check the
NIC packets number reported by sample is the same with what we set at the packet
generator side.
