.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2020 Intel Corporation
   Copyright(c) 2020 The University of New Hampshire

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

3. If nic is Intel® Ethernet 800 Series, store the output of the first 1000 lines from testpmd and ethtool into two files,
   else store the output from testpmd and ethtool into two files. Then compare both files, verify they are the same.

4. Delete all the files created during testing.


Test Case : Module EEPROM Dump
===============================

1. Use testpmd to show the EEPROM information on selected port::

    testpmd> show port <PORT_ID> module_eeprom

2. Quit the testpmd to have access of ethtool, then use ethtool
   to get EEPROM information on selected port::

    ethtool -m <interface_name> raw on length <length> >> <file_name>.txt

3. If nic is Intel® Ethernet 800 Series, store the output of the first 16 lines from testpmd and ethtool into two files,
   else store the output from testpmd and ethtool into two files. Then compare both files, verify they are the same.

4. Delete all the files created during testing.
