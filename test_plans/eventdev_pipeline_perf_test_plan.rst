.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Marvell International Ltd

============================
Eventdev Pipeline Perf Tests
============================

Prerequisites
==============

Each of the 10Gb/25Gb/40Gb/100Gb Ethernet* ports of the DUT is directly connected in
full-duplex to a different port of the peer Ixia ports(traffic generator).

Using TCL commands, the Ixia can be configured to send and receive traffic on a given set of ports.

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test ::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id
   usertools/dpdk-devbind.py --bind=vfio-pci eventdev_device_bus_id

Build dpdk and examples=eventdev_pipeline:
   CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static <build_target>
   ninja -C <build_target>

   meson configure -Dexamples=eventdev_pipeline <build_target>
   ninja -C <build_target>

Create huge pages
=================
mkdir -p /dev/huge
mount -t hugetlbfs none /dev/huge
echo 24 > /proc/sys/vm/nr_hugepages

Configure limits of Eventdev devices
====================================
Set all eventdev devices sso and ssow limits to zero. Then set eventdev device under tests sso and ssow limits to non-zero values as per cores/queues requriments ::

   echo 0 > /sys/bus/pci/devices/eventdev_device_bus_id/limits/sso
   echo 0 > /sys/bus/pci/devices/eventdev_device_bus_id/limits/ssow

Example ::

   echo 0 > /sys/bus/pci/devices/eventdev_device_bus_id/limits/tim
   echo 1 > /sys/bus/pci/devices/eventdev_device_bus_id/limits/npa
   echo 16 > /sys/bus/pci/devices/eventdev_device_bus_id/limits/sso
   echo 32 > /sys/bus/pci/devices/eventdev_device_bus_id/limits/ssow

- ``eventdev_device_bus_id/limits/sso`` : Max limit `256`
- ``eventdev_device_bus_id/limits/ssow``: Max limit `52`

Test Case: Performance 1port atomic test
========================================
Description: Execute performance test with Atomic_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/examples/dpdk-eventdev_pipeline -c 0xe00000 -a eventdev_device_bus_id -a device_bus_id -- -w 0xc00000 -n=0 --dump

    Parameters::

        -c, COREMASK         : Hexadecimal bitmask of cores to run on
        -a, --pci-allowlist  : Add a PCI device in allow list.
                               Only use the specified PCI devices. The argument format
                               is <[domain:]bus:devid.func>. This option can be present
                               several times (once per device).
        EAL Commands
        -w, --worker-mask=core mask : Run worker on CPUs in core mask
        -n, --packets=N             : Send N packets (default ~32M), 0 implies no limit
        -D, --dump                   Print detailed statistics before exit

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 1port parallel test
==========================================
Description: Execute performance test with Parallel_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/examples/dpdk-eventdev_pipeline -c 0xe00000 -a eventdev_device_bus_id -a device_bus_id -- -w 0xc00000 -n=0 -p --dump

    Parameters::

        -c, COREMASK         : Hexadecimal bitmask of cores to run on
        -a, --pci-allowlist  : Add a PCI device in allow list.
                               Only use the specified PCI devices. The argument format
                               is <[domain:]bus:devid.func>. This option can be present
                               several times (once per device).
        EAL Commands
        -w, --worker-mask=core mask : Run worker on CPUs in core mask
        -n, --packets=N             : Send N packets (default ~32M), 0 implies no limit
        -p, --parallel              : Use parallel scheduling
        -D, --dump                  : Print detailed statistics before exit

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 1port ordered test
=========================================
Description: Execute performance test with Ordered_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/examples/dpdk-eventdev_pipeline -c 0xe00000 -a eventdev_device_bus_id -a device_bus_id -- -w 0xc00000 -n=0 -o --dump

    Parameters::

        -c, COREMASK         : Hexadecimal bitmask of cores to run on
        -a, --pci-allowlist  : Add a PCI device in allow list.
                               Only use the specified PCI devices. The argument format
                               is <[domain:]bus:devid.func>. This option can be present
                               several times (once per device).
        EAL Commands
        -w, --worker-mask=core mask : Run worker on CPUs in core mask
        -n, --packets=N             : Send N packets (default ~32M), 0 implies no limit
        -o, --ordered                Use ordered scheduling
        -D, --dump                  : Print detailed statistics before exit

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 2port atomic test
========================================
Description: Execute performance test with Atomic_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/examples/dpdk-eventdev_pipeline -c 0xe00000 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -- -w 0xc00000 -n=0 --dump

    Parameters::

        -c, COREMASK         : Hexadecimal bitmask of cores to run on
        -a, --pci-allowlist  : Add a PCI device in allow list.
                               Only use the specified PCI devices. The argument format
                               is <[domain:]bus:devid.func>. This option can be present
                               several times (once per device).
        EAL Commands
        -w, --worker-mask=core mask : Run worker on CPUs in core mask
        -n, --packets=N             : Send N packets (default ~32M), 0 implies no limit
        -D, --dump                   Print detailed statistics before exit

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 2port parallel test
==========================================
Description: Execute performance test with Parallel_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/examples/dpdk-eventdev_pipeline -c 0xe00000 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -- -w 0xc00000 -n=0 -p --dump

    Parameters::

        -c, COREMASK         : Hexadecimal bitmask of cores to run on
        -a, --pci-allowlist  : Add a PCI device in allow list.
                               Only use the specified PCI devices. The argument format
                               is <[domain:]bus:devid.func>. This option can be present
                               several times (once per device).
        EAL Commands
        -w, --worker-mask=core mask : Run worker on CPUs in core mask
        -n, --packets=N             : Send N packets (default ~32M), 0 implies no limit
        -p, --parallel              : Use parallel scheduling
        -D, --dump                  : Print detailed statistics before exit

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 2port ordered test
=========================================
Description: Execute performance test with Ordered_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/examples/dpdk-eventdev_pipeline -c 0xe00000 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -- -w 0xc00000 -n=0 -o --dump

    Parameters::

        -c, COREMASK         : Hexadecimal bitmask of cores to run on
        -a, --pci-allowlist  : Add a PCI device in allow list.
                               Only use the specified PCI devices. The argument format
                               is <[domain:]bus:devid.func>. This option can be present
                               several times (once per device).
        EAL Commands
        -w, --worker-mask=core mask : Run worker on CPUs in core mask
        -n, --packets=N             : Send N packets (default ~32M), 0 implies no limit
        -o, --ordered                Use ordered scheduling
        -D, --dump                  : Print detailed statistics before exit

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 4port atomic test
========================================
Description: Execute performance test with Atomic_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/examples/dpdk-eventdev_pipeline -c 0xe00000 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -a device2_bus_id -a device3_bus_id -- -w 0xc00000 -n=0 --dump

    Parameters::

        -c, COREMASK         : Hexadecimal bitmask of cores to run on
        -a, --pci-allowlist  : Add a PCI device in allow list.
                               Only use the specified PCI devices. The argument format
                               is <[domain:]bus:devid.func>. This option can be present
                               several times (once per device).
        EAL Commands
        -w, --worker-mask=core mask : Run worker on CPUs in core mask
        -n, --packets=N             : Send N packets (default ~32M), 0 implies no limit
        -D, --dump                   Print detailed statistics before exit

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 4port parallel test
==========================================
Description: Execute performance test with Parallel_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/examples/dpdk-eventdev_pipeline -c 0xe00000 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -a device2_bus_id -a device3_bus_id -- -w 0xc00000 -n=0 -p --dump

    Parameters::

        -c, COREMASK         : Hexadecimal bitmask of cores to run on
        -a, --pci-allowlist  : Add a PCI device in allow list.
                               Only use the specified PCI devices. The argument format
                               is <[domain:]bus:devid.func>. This option can be present
                               several times (once per device).
        EAL Commands
        -w, --worker-mask=core mask : Run worker on CPUs in core mask
        -n, --packets=N             : Send N packets (default ~32M), 0 implies no limit
        -p, --parallel              : Use parallel scheduling
        -D, --dump                  : Print detailed statistics before exit

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 4port ordered test
=========================================
Description: Execute performance test with Ordered_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/examples/dpdk-eventdev_pipeline -c 0xe00000 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -a device2_bus_id -a device3_bus_id -- -w 0xc00000 -n=0 -o --dump

    Parameters::

        -c, COREMASK         : Hexadecimal bitmask of cores to run on
        -a, --pci-allowlist  : Add a PCI device in allow list.
                               Only use the specified PCI devices. The argument format
                               is <[domain:]bus:devid.func>. This option can be present
                               several times (once per device).
        EAL Commands
        -w, --worker-mask=core mask : Run worker on CPUs in core mask
        -n, --packets=N             : Send N packets (default ~32M), 0 implies no limit
        -o, --ordered                Use ordered scheduling
        -D, --dump                  : Print detailed statistics before exit

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.
