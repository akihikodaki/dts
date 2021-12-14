.. Copyright (c) <2010-2019>, Intel Corporation
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   - Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.

   - Neither the name of Intel Corporation nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.

======================
Poll Mode Driver Tests
======================

This document provides benchmark tests for the userland Ethernet Controller Poll Mode Driver (PMD).
The userland PMD application runs the ``IO forwarding mode`` test which described in the PMD test
plan document with different parameters for the configuration of NIC ports.

The core configuration description is:

- 1C/1T: 1 Physical Core, 1 Logical Core per physical core (1 Hyperthread)
  eg: using core #2 (socket 0, 2nd physical core)

- 1C/2T: 1 Physical Core, 2 Logical Cores per physical core (2 Hyperthreads)
  eg: using core #2 and #14 (socket 0, 2nd physical core, 2 Hyperthreads)

- 2C/1T: 2 Physical Cores, 1 Logical Core per physical core
  eg: using core #2 and #4 (socket 0, 2nd and 3rd physical cores)


Prerequisites
=============

Each of the 10Gb/25Gb/40Gb/100Gb Ethernet* ports of the DUT is directly connected in
full-duplex to a different port of the peer traffic generator.

Using interactive commands, the traffic generator can be configured to
send and receive in parallel, on a given set of ports.

The tool ``vtbwrun`` (included in Intel® VTune™ Performance Analyzer)
will be used to monitor memory activities while running network
benchmarks to check the number of ``Memory Partial Writes`` and the
distribution of memory accesses among available Memory Channels.  This
will only be done on the userland application, as the tool requires a
Linux environment to be running in order to be used.

If using vfio the kernel must be >= 3.6+ and VT-d must be enabled in bios.When
using vfio, use the following commands to load the vfio driver and bind it
to the device under test::

   modprobe vfio
   modprobe vfio-pci
   usertools/dpdk-devbind.py --bind=vfio-pci device_bus_id

If using igb_uio::

   modprobe uio
   modprobe igb_uio
   usertools/dpdk-devbind.py --bind=igb_uio device_bus_id

Case config::
   For FVL40g, if test 16 Byte Descriptor, need to set the "CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=y"
   in ./config/common_base and re-build DPDK.

   For CVL25G, if test 16 Byte Descriptor, need to set the "CONFIG_RTE_LIBRTE_ICE_16BYTE_RX_DESC=y"
   in ./config/common_base and re-build DPDK.

Test Case: Packet Checking
==========================

#. Start testpmd and start forwarding::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf0 -n 4 -- -i
    testpmd> start

#. The tester sends packets with different sizes (64, 65, 128, 256, 512, 1024, 1280 and 1518 bytes)
   which will be forwarded by the DUT. The test checks if the packets are correctly forwarded and
   if both RX and TX packet sizes match by `show port all stats`

Test Case: Packet Checking in scalar mode
=========================================

The linuxapp is started with the following parameters:

::
  -c 0x6 -n 4 -a <devid>,scalar_enable=1  -- -i --portmask=<portmask>


This test is applicable for Marvell devices. The tester sends 1 packet at a
time with different sizes (64, 65, 128, 256, 512, 1024, 1280 and 1518 bytes),
using scapy, which will be forwarded by the DUT. The test checks if the packets
are correctly forwarded and if both RX and TX packet sizes match.


Test Case: Descriptors Checking
===============================

#. Start testpmd with descriptor parameters::

   ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0xf0 -n 4 -- -i--rxd={rxd} --txd={txd}

#. The tester sends packets with different sizes (64, 65, 128, 256, 512, 1024, 1280 and 1518 bytes)
   for different values of rxd and txd (128,,256, 512, 1024, 2048 and 4096)
   The packets will be forwarded by the DUT. The test checks if the packets are correctly forwarded.

Test Case: Single Core Performance Benchmarking
===============================================

Snice this case we focus on CPU single core performance, the network aggregated throughput
must grater than single core performance, then the bottleneck will be the core.
Below is an example setup topology for performance test, NIC (one or more) ports connect to
Traffic Generator ports directly::

    Dut Card 0 port 0 ---- Traffic Generator port 0
    Dut Card 1 port 0 ---- Traffic Generator port 1
     ...
    DUT Card n port 0 ---- Traffic Generator port n

In order to trigger the best performance of NIC, there will be specific setting, and the setting vary
from NIC to NIC.

In order to get the best single core performance, Server configuration are required:

- BIOS

  * CPU Power and Performance Policy <Performance>
  * CPU C-state Disabled
  * CPU P-state Disabled
  * Enhanced Intel® Speedstep® Tech
  * Disabled Turbo Boost Disabled

- Grub

  * default_hugepagesz=1G hugepagesz=1G hugepages=8
  * isolcpus=1-21,28-48 nohz_full=1-21,28-48 rcu_nocbs=1-21,28-48

- Other

  * Core and NIC should be in the same socket.

Test steps:

#. Start testpmd and start io forwading::

   ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x1800000000 -n 4 -- -i--portmask=0x3 -txd=2048 --rxd=2048 --txq=2 --rxq=2

#. The tester send packets which will be forwarded by the DUT, record the perfromance numbers.

The throughput is measured for each of these combinations of different packet size
(64, 65, 128, 256, 512, 1024, 1280 and 1518 bytes) and different value of rxd and txd(128,,256, 512, 1024, 2048 and 4096)
The results are printed in the following table:

  +-------+---------+------------+--------+---------------------+
  | Frame | TXD/RXD | Throughput |  Rate  | Excepted Throughput |
  | Size  |         |            |        |                     |
  +=======+=========+============+========+=====================+
  |  64   |         |            |        |                     |
  +-------+---------+------------+--------+---------------------+
  |  128  |         |            |        |                     |
  +-------+---------+------------+--------+---------------------+
  |  256  |         |            |        |                     |
  +-------+---------+------------+--------+---------------------+
  |  512  |         |            |        |                     |
  +-------+---------+------------+--------+---------------------+
  |  1024 |         |            |        |                     |
  +-------+---------+------------+--------+---------------------+
  |  1280 |         |            |        |                     |
  +-------+---------+------------+--------+---------------------+
  |  1518 |         |            |        |                     |
  +-------+---------+------------+--------+---------------------+

Test Case: Pmd RSS Performance
==============================

The RSS feature is designed to improve networking performance by load balancing
the packets received from a NIC port to multiple NIC RX queues.

In order to get the best pmdrss performance, Server configuration are required:

- BIOS

 * Intel Hyper-Threading Technology is ENABLED
 * Other: reference to 'Test Case: Single Core Performance Benchmarking'


Run application using a core mask for the appropriate thread and core
settings given in the following:

  +----+----------+-----------+-----------------------+
  |    | Rx Ports | Rx Queues | Sockets/Cores/Threads |
  +====+==========+===========+=======================+
  |  1 |     1    |     2     |      1S/1C/2T         |
  +----+----------+-----------+-----------------------+
  |  2 |     2    |     2     |      1S/2C/1T         |
  +----+----------+-----------+-----------------------+
  |  3 |     2    |     2     |      1S/4C/1T         |
  +----+----------+-----------+-----------------------+
  |  4 |     2    |     2     |      1S/2C/2T         |
  +----+----------+-----------+-----------------------+
  |  5 |     2    |     3     |      1S/3C/2T         |
  +----+----------+-----------+-----------------------+
  |  6 |     2    |     3     |      1S/6C/1T         |
  +----+----------+-----------+-----------------------+

``note``: A queue can be handled by only one core, but one core can handle a couple of queues.

#. Start testpmd and start io forwading with the above parameters.
   For example, 1S/1C/2T::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd -c 0x2000000000000030000000 -n 4 -- -i \
    --portmask=0x3 --txd=512 --rxd=512 --burst=32 --txpt=36 --txht=0 --txwt=0 \
    --txfreet=32 --rxfreet=64 --txrst=32 --mbcache=128 --nb-cores=2 --rxq=2 --txq=2

# Send packet with frame size from 64bytes to 1518bytes with ixia traffic generator,
  record the perfromance numbers:

  +------------+----------+----------+-------------+----------+
  | Frame Size | Rx ports | S/C/T    | Throughput  | Linerate |
  +============+==========+==========+=============+==========+
  | 64         |          |          |             |          |
  +------------+----------+----------+-------------+----------+
  | 128        |          |          |             |          |
  +------------+----------+----------+-------------+----------+
  | 256        |          |          |             |          |
  +------------+----------+----------+-------------+----------+
  | 512        |          |          |             |          |
  +------------+----------+----------+-------------+----------+
  | 1024       |          |          |             |          |
  +------------+----------+----------+-------------+----------+
  | 1280       |          |          |             |          |
  +------------+----------+----------+-------------+----------+
  | 1518       |          |          |             |          |
  +------------+----------+----------+-------------+----------+


The memory partial writes are measured with the ``vtbwrun`` application and printed
in the following table:::


   Sampling Duration: 000000.00 micro-seconds
   ---       Logical Processor 0       ---||---       Logical Processor 1       ---
   ---------------------------------------||---------------------------------------
   ---   Intersocket QPI Utilization   ---||---   Intersocket QPI Utilization   ---
   ---------------------------------------||---------------------------------------
   ---      Reads (MB/s):         0.00 ---||---      Reads (MB/s):         0.00 ---
   ---      Writes(MB/s):         0.00 ---||---      Writes(MB/s):         0.00 ---
   ---------------------------------------||---------------------------------------
   ---  Memory Performance Monitoring  ---||---  Memory Performance Monitoring  ---
   ---------------------------------------||---------------------------------------
   --- Mem Ch 0: #Ptl Wr:      0000.00 ---||--- Mem Ch 0: #Ptl Wr:         0.00 ---
   --- Mem Ch 1: #Ptl Wr:      0000.00 ---||--- Mem Ch 1: Ptl Wr (MB/s):   0.00 ---
   --- Mem Ch 2: #Ptl Wr:      0000.00 ---||--- Mem Ch 2: #Ptl Wr:         0.00 ---
   --- ND0 Mem #Ptl Wr:        0000.00 ---||--- ND1 #Ptl Wr:               0.00 ---
