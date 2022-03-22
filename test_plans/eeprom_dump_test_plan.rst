.. # BSD LICENSE
    #
    # Copyright(c) 2020 Intel Corporation. All rights reserved
    # Copyright © 2020 The University of New Hampshire. All rights reserved.
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
EEPROM Dump Test
=================

The EEPROM Dump Test checks the ability to output EEPROM information on
testpmd when requested. Then compares with output from ethtool to verify
that both output information is the same. When finished, all the files
created during testing will be deleted. The difference of the two files
can be found in the log file.

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

   ./<build>/app/dpdk-testpmd -- -i --portmask=0x3

Test Case : EEPROM Dump
=======================

1. Use testpmd to show the EEPROM information on selected port::

    testpmd> show port <PORT_ID> eeprom

2. Quit the testpmd to have access of ethtool, then use ethtool
   to get EEPROM information on selected port::

    ethtool -e <interface_name> raw on length <length> >> <file_name>.txt

3. If nic is columbiaville, store the output of the first 1000 lines from testpmd and ethtool into two files,
   else store the output from testpmd and ethtool into two files. Then compare both files, verify they are the same.

4. Delete all the files created during testing.


Test Case : Module EEPROM Dump
===============================

1. Use testpmd to show the EEPROM information on selected port::

    testpmd> show port <PORT_ID> module_eeprom

2. Quit the testpmd to have access of ethtool, then use ethtool
   to get EEPROM information on selected port::

    ethtool -m <interface_name> raw on length <length> >> <file_name>.txt

3. If nic is columbiaville, store the output of the first 16 lines from testpmd and ethtool into two files,
   else store the output from testpmd and ethtool into two files. Then compare both files, verify they are the same.

4. Delete all the files created during testing.
