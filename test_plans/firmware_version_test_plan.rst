.. # BSD LICENSE
    #
    # Copyright(c) 2020 Intel Corporation. All rights reserved
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

  ./build/app/testpmd -- -i --portmask=0x3

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
