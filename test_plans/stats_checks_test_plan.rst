.. # BSD LICENSE
    #
    # Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
    # Copyright © 2018[, 2019] The University of New Hampshire. All rights reserved.
    # All rights reserved.
    #
    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions
    # are met:
    #
    #   * Redistributions of source code must retain the above copyright
    #     notice, this list of conditions and the following disclaimer.
    #   * Redistributions in binary form must reproduce the above copyright
    #     notice, this list of conditions and the following disclaimer in
    #     the documentation and/or other materials provided with the
    #     distribution.
    #   * Neither the name of Intel Corporation nor the names of its
    #     contributors may be used to endorse or promote products derived
    #     from this software without specific prior written permission.
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    # A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    # OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    # SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    # LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    # DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    # THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

=================
Stats Check tests
=================

The support of stats checks by Poll Mode Drivers consists of the ability
of the driver to properly report statistics upon request. Such statistics
should include number of packets and bytes sent and recieved, as well as
the number of dropped packets and transmission errors.

.. note::

   Maximum Packet Length = MTU(Maximum Transmission Unit) + 14(src mac + dst mac) + 4(CRC)
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

  ./build/app/testpmd -c ffffff -n 6 -- -i --portmask=0x3 --max-pkt-len=9600 \
  --tx-offloads=0x00008000

The -n command is used to select the number of memory channels. It should match the number of memory channels on that setup.

Setting tx-offload to 0x8000 and the maximum packet length
to 9600 (CRC included) makes input Jumbo Frames to be stored in multiple
buffers by the hardware RX engine.

Start packet forwarding in the ``testpmd`` application with the ``start``
command. Then, for each port on the target make the Traffic Generator
transmit a packet to the port of arbitrary size less than the MTU of
the target port, checking that the same amount of frames and bytes
are received back by the Traffic Generator from the port.

Functional Tests of Status Checks
=================================

Testing the support of Status Checks in Poll Mode Drivers consists of
configuring the gathering the initial status of a port, sending a
packet to that port, and checking the status of the port. The initial
status and the new status are then compared for expected differences.
The fields checked are RX-packets, RX-bytes, RX-errors, TX-packets,
TX-errors, and TX-bytes.

Test Case: Status Checks
====================================================

Check the initial state of the ports (Single example port shown)::

  testpmd> show port stats all
    ######################## NIC statistics for port 0  ########################
    RX-packets: 0        RX-missed: 0         RX-bytes:  0
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:            0
    Tx-pps:            0
    ############################################################################

Send a packet with size 50 bytes (Single example port show) ::

  testpmd> show port stats all
    ######################## NIC statistics for port 0  ########################
    RX-packets: 1        RX-missed: 0         RX-bytes:  50
    RX-errors: 0
    RX-nombuf:  0
    TX-packets: 0          TX-errors: 0          TX-bytes:  0

    Throughput (since last show)
    Rx-pps:            0
    Tx-pps:            0
    ############################################################################


Verify that the increase in RX-bytes and RX-packets is as-expected, and no other information changed.
