.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2014 Intel Corporation
   Copyright(c) 2018-2019 The University of New Hampshire

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
