.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2014 Intel Corporation
   Copyright(c) 2018-2019 The University of New Hampshire

=================
MTU Check Tests
=================

The support of jumbo frames by Poll Mode Drivers consists in enabling a port
to receive Jumbo Frames with a configurable maximum packet length that is
greater than the standard maximum Ethernet frame length (1518 bytes), up to
a maximum value imposed by the hardware.

.. note::

   Maximum Packet Length = MTU(Maximum Transmission Unit) + 14(src mac + dst mac + LEN/TYPE) + 4(CRC)
   e.g., 1518 = 1500 + 14 + 4

Prerequisites
=============

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

Assuming that ports ``0`` and ``1`` of the test target are directly connected
to the traffic generator, launch the ``testpmd`` application with the following
arguments::

  ./build/app/dpdk-testpmd -c ffffff -n 6 -- -i --portmask=0x3 --max-pkt-len=9600 \
  --tx-offloads=0x00008000

The -n command is used to select the number of memory channels. It should match the number of memory channels on that setup.

Setting tx-offload to 0x8000 and the maximum packet length
to 9600 (CRC included) makes input Jumbo Frames to be stored in multiple
buffers by the hardware RX engine.

Start packet forwarding in the ``testpmd`` application with the ``start``
command.

Functional Tests of MTU Checks
================================

Testing the support of MTU Size Checks in Poll Mode Drivers consists of
configuring the MTU to a given value, and then checking that DPDK
registers the change in MTU size. Then, a packet is sent that is the
size of the MTU, validating that no error was produced. A packet is
then sent which is larger than the MTU by 100 bytes, validating that
an error is produced. All tests are identical, ignoring the change
in MTU and packet size. As such, only 1 test case has been included
for brevity. The sized given below are the size of the IP header and
the payload of the IP Packet. Each test will set the MTU to that value,
then send 1 packet of exactly that size that should work properly.
Then, the test will send a packet that is 100 bytes larger than the
MTU, which should not be received.

#. MTU = 1500
#. MTU = 2400
#. MTU = 4800
#. MTU = 9000

Test Case: MTU of 1500
====================================================

Stop all ports::

    testpmd> port stop all
    Stopping ports...
    Checking link statuses...
    Done

Set MTU size to 1500 ::

    testpmd> port config mtu 0 1500
    testpmd> port config mtu 1 1500

Restart the ports ::

    testpmd> port start all
    Port 0: 3C:FD:FE:B2:AC:F8
    Port 1: 3C:FD:FE:B2:AC:F9
    Port 2: 3C:FD:FE:B2:AC:FA
    Port 3: 3C:FD:FE:B2:AC:FB
    Checking link statuses...
    Done

Send a packet with size 1500 bytes ::

  testpmd> show port stats 0
    ######################## NIC statistics for port 0  ########################
    RX-packets: 0          RX-errors: 0         RX-bytes: 0
    TX-packets: 1          TX-errors: 0         TX-bytes: 1500
    ############################################################################

  testpmd> show port stats 1

    ######################## NIC statistics for port 1  ########################
    RX-packets: 1          RX-errors: 0         RX-bytes: 1500
    TX-packets: 0          TX-errors: 0         TX-bytes: 0
    ############################################################################

Verify that TX-bytes on port 0 and RX-bytes on port 1 are 1500


Send a packet with size 1600 bytes ::

  testpmd> show port stats 0

    ######################## NIC statistics for port 0  ########################
    RX-packets: 0          RX-errors: 0         RX-bytes: 0
    TX-packets: 1          TX-errors: 0         TX-bytes: 1500
    ############################################################################

  testpmd> show port stats 1

    ######################## NIC statistics for port 1  ########################
    RX-packets: 1          RX-errors: 0         RX-bytes: 1500
    TX-packets: 0          TX-errors: 0         TX-bytes: 0
    ############################################################################

Verify that TX-bytes on port 0 and RX-bytes on port 1 are 1500
