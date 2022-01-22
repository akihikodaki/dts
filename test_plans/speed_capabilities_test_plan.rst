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

=======================
Speed Capabilities Test
=======================

The Speed Capabilities Test checks the speeds that the device lists and compares
it to a user-defined set of expected speeds set in the ``speed_capabilities.cfg``.

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

  ./<build_target>/app/dpdk-testpmd -- -i --portmask=0x3

Start packet forwarding in the ``testpmd`` application with the ``start``
command. Then, for each port on the target make the Traffic Generator
transmit a packet to the port of arbitrary size less than the MTU of
the target port, checking that the same amount of frames and bytes
are received back by the Traffic Generator from the port.

Ensure that the ``speed_capabilities.cfg`` file correctly reflects the speeds
the device is expected to run at.


Test Case : Speed Capabilities Test
===================================

1. Use testpmd to retrieve the speed information that the interface is linked at::

      testpmd> show port info <PORT_ID>

2. Compares the speed value against the rate in the speed_capabilities.cfg file.
   The supported options for expected speeds are 1G, 10G, 25G, 40G, and 100G. Each interface must have an expected speed associated with it.
   Example file below::

      [suite]
      expected_speeds={'interface1': '10G', 'interface2': '100M'}


3. Verifies that the speeds matches accordingly.

4. Repeats the verification for each NIC and interface found on the system.
