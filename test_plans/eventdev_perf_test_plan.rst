.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Marvell International Ltd

==============
Eventdev Tests
==============

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

Test Case: Performance 1port atomic_atq test
=============================================
Description: Execute performance test with Atomic_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_atq --stlist=A --wlcores=23

    Parameters::

       -l CORELIST        : List of cores to run on
                            The argument format is <c1>[-c2][,c3[-c4],...]
                            where c1, c2, etc are core indexes between 0 and 24
       -a --pci-allowlist : Add a PCI device in allow list.
                            Only use the specified PCI devices. The argument format
                            is <[domain:]bus:devid.func>. This option can be present
                            several times (once per device).
       --prod_type_ethdev : use ethernet device as producer.
       --nb_pkts          : number of packets to produce, 0 implies no limit
       --test             : name of the test application to run
       --stlist           : list of scheduled types of the stages
       --wlcores          : list of lcore ids for workers

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 1port parallel_atq test
==============================================
Description: Execute performance test with Parallel_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_atq --stlist=P --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 1port ordered_atq test
=============================================
Description: Execute performance test with Ordered_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_atq --stlist=O --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 1port atomic_queue test
==============================================
Description: Execute performance test with Atomic_queue type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_queue --stlist=A --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 1port parallel_queue test
================================================
Description: Execute performance test with Parallel_queue type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_queue --stlist=P --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 1port ordered_queue test
===============================================
Description: Execute performance test with Ordered_queue type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_queue --stlist=O --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 2port atomic_atq test
=============================================
Description: Execute performance test with Atomic_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_atq --stlist=A --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 2port parallel_atq test
==============================================
Description: Execute performance test with Parallel_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_atq --stlist=P --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 2port ordered_atq test
=============================================
Description: Execute performance test with Ordered_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_atq --stlist=O --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 2port atomic_queue test
==============================================
Description: Execute performance test with Atomic_queue type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_queue --stlist=A --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 2port parallel_queue test
================================================
Description: Execute performance test with Parallel_queue type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_queue --stlist=P --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 2port ordered_queue test
===============================================
Description: Execute performance test with Ordered_queue type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_queue --stlist=O --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.


Test Case: Performance 4port atomic_atq test
=============================================
Description: Execute performance test with Atomic_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -w device2_bus_id -a device3_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_atq --stlist=A --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 4port parallel_atq test
==============================================
Description: Execute performance test with Parallel_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -a device2_bus_id -a device3_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_atq --stlist=P --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 4port ordered_atq test
=============================================
Description: Execute performance test with Ordered_atq type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -a device2_bus_id -a device3_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_atq --stlist=O --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 4port atomic_queue test
==============================================
Description: Execute performance test with Atomic_queue type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -a device2_bus_id -a device3_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_queue --stlist=A --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 4port parallel_queue test
================================================
Description: Execute performance test with Parallel_queue type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -a device2_bus_id -a device3_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_queue --stlist=P --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.

Test Case: Performance 4port ordered_queue test
===============================================
Description: Execute performance test with Ordered_queue type of stage in multi-flow situation for various cores.

1. Run the sample with below command::

   # ./<build_target>/app/dpdk-test-eventdev -l 22-23 -a eventdev_device_bus_id -a device0_bus_id -a device1_bus_id -a device2_bus_id -a device3_bus_id -- --prod_type_ethdev --nb_pkts=0 --verbose 2 --test=pipeline_queue --stlist=O --wlcores=23

2. Use Ixia to send huge number of packets(with same 5-tuple and different 5-tuple)

3. Observe the speed of packets received(Rx-rate) on Ixia.
