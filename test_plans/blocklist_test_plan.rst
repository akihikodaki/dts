.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

====================
Port Blocklist Tests
====================

Prerequisites
=============

Board with at least 2 DPDK supported NICs attached.

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

Test Case
=========

Test Case 1: Testpmd with no blocklisted device
-----------------------------------------------

1. Run testpmd in interactive mode and ensure that at least 2 ports
   are bound and available::

    build/app/dpdk-testpmd -c 3 -- -i
    ....
    EAL: unbind kernel driver /sys/bus/pci/devices/0000:01:00.0/driver/unbind
    EAL: Core 1 is ready (tid=357fc700)
    EAL: bind PCI device 0000:01:00.0 to uio driver
    EAL: Device bound
    EAL: map PCI resource for device 0000:01:00.0
    EAL: PCI memory mapped at 0x7fe6b68c7000
    EAL: unbind kernel driver /sys/bus/pci/devices/0000:01:00.1/driver/unbind
    EAL: bind PCI device 0000:01:00.1 to uio driver
    EAL: Device bound
    EAL: map PCI resource for device 0000:01:00.1
    EAL: PCI memory mapped at 0x7fe6b6847000
    EAL: unbind kernel driver /sys/bus/pci/devices/0000:02:00.0/driver/unbind
    EAL: bind PCI device 0000:02:00.0 to uio driver
    EAL: Device bound
    EAL: map PCI resource for device 0000:02:00.0
    EAL: PCI memory mapped at 0x7fe6b6580000
    EAL: unbind kernel driver /sys/bus/pci/devices/0000:02:00.1/driver/unbind
    EAL: bind PCI device 0000:02:00.1 to uio driver
    EAL: Device bound
    EAL: map PCI resource for device 0000:02:00.1
    EAL: PCI memory mapped at 0x7fe6b6500000
    Interactive-mode selected
    Initializing port 0... done:  Link Up - speed 10000 Mbps - full-duplex
    Initializing port 1... done:  Link Up - speed 10000 Mbps - full-duplex
    Initializing port 2... done:  Link Up - speed 10000 Mbps - full-duplex
    Initializing port 3... done:  Link Up - speed 10000 Mbps - full-duplex

Test Case 2: Testpmd with one port blocklisted
----------------------------------------------

1. Select first available port to be blocklisted and specify it with -b option. For the example above::

    build/app/dpdk-testpmd -c 3 -b 0000:01:00.0 -- -i

2. Check that corresponding device is skipped for binding, and
   only 3 ports are available now:::

    EAL: unbind kernel driver /sys/bus/pci/devices/0000:01:00.1/driver/unbind
    EAL: bind PCI device 0000:01:00.1 to uio driver
    EAL: Device bound
    EAL: map PCI resource for device 0000:01:00.1
    EAL: PCI memory mapped at 0x7f0037912000
    EAL: unbind kernel driver /sys/bus/pci/devices/0000:02:00.0/driver/unbind
    EAL: bind PCI device 0000:02:00.0 to uio driver
    EAL: Device bound
    EAL: map PCI resource for device 0000:02:00.0
    EAL: PCI memory mapped at 0x7f0037892000
    EAL: unbind kernel driver /sys/bus/pci/devices/0000:02:00.1/driver/unbind
    EAL: bind PCI device 0000:02:00.1 to uio driver
    EAL: Device bound
    EAL: map PCI resource for device 0000:02:00.1
    EAL: PCI memory mapped at 0x7f0037812000
    Interactive-mode selected
    Initializing port 0... done:  Link Up - speed 10000 Mbps - full-duplex
    Initializing port 1... done:  Link Up - speed 10000 Mbps - full-duplex
    Initializing port 2... done:  Link Up - speed 10000 Mbps - full-duplex

Test Case 3: Testpmd with all but one port blocklisted
------------------------------------------------------

1. Blocklist all devices except the last one.
   For the example above:::

    build/app/dpdk-testpmd -c 3 -b 0000:01:00.0  -b 0000:01:00.1 -b 0000:02:00.0 -- -i

2. Check that 3 corresponding device is skipped for binding, and
   only 1 ports is available now:::

    EAL: unbind kernel driver /sys/bus/pci/devices/0000:02:00.1/driver/unbind
    EAL: bind PCI device 0000:02:00.1 to uio driver
    EAL: Device bound
    EAL: map PCI resource for device 0000:02:00.1
    EAL: PCI memory mapped at 0x7f22e9aeb000
    Interactive-mode selected
    Initializing port 0... done:  Link Up - speed 10000 Mbps - full-duplex
