.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2020 Intel Corporation
   Copyright(c) 2018-2019 The University of New Hampshire

=======================
Firmware Version Test
=======================

The Firmware Version Test checks the firmware version from the device info and
compares to the firmware version defined by user. This test case is driver
restricted since each driver will have different version format.


Prerequisites
=============

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

Assuming that ports are up and working, then launch the ``testpmd`` application
with the following arguments::

  ./build/app/dpdk-testpmd -- -i --portmask=0x3

Ensure the ```firmware_version.cfg``` file have the correct name and firmware
version.

Test Case : Firmware Version Test
===================================

1. Use testpmd to show the port info that contained the firmware version::

      testpmd> show port info <PORT_ID>

2. Compares the outputted firmware version with the firmware version listed in the
    ```firmware_version.cfg``` file. Different driver will have different version
    format.
    Currently support: i40e, mlx5, bnxt

    Example below:
    {'i40e' : ['5.01', '0x80002341', '1.1.1']}
    {'mlx5' : ['12.14.3462', 'MT_2416545656']}
    {'bnxt' : ['236.0.222.0', '216.3.254.0']}


3. Verifies they matches.
