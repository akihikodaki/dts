.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

==================================
ICE Enable basic HQoS on PF driver
==================================

Description
===========
A switch chip help to fan out network ports because of Intel NIC didn't have so much ports.
In this solution, NIC might be configured to 4x10G or 4x25G or 100G mode, all these connect to a switch chip.
Outside switch port's bandwidth lower than NIC, might be 1G and 10G. Therefore, NIC should limit flow bandwidth to each switch port.
To support this opportunity, we need 3 level tx scheduler:

   - queue (each CPU core have 1 queue for outside switch port)
   - queue group (map to outside switch port)
   - port (local MAC port)

The PMD is required to support the below features:

   - Support at least 3 layers Tx scheduler, (Port--> Queue --> Queue Group)
   - Support SP or RR Scheduling on queue groups
   - Support SP or RR Scheduling or WFQ Scheduling on queues
   - Support Bandwith configure on each layer.

..Note::

   Node priority 0 is highest priority, 7 is lowest priority.
   SP: Strict Priority arbitration scheme.
   RR: Round Robin arbitration scheme.
   WFQ: Weighted Fair Queue arbitration scheme.

Prerequisites
=============

Topology
--------
one port from ICE_100G-E810C_QSFP(NIC-1), two ports from ICE_25G-E810_XXV_SFP(NIC-2);

one 100G cable, one 10G cable;

The connection is as below table::

    +---------------------------------+
    |  DUT           |  IXIA          |
    +=================================+
    |               100G              |
    | NIC-1,Port-1  ---  IXIA, Port-1 |
    |               10G               |
    | NIC-2,Port-1  ---  NIC-2,Port-2 |
    +---------------------------------+

Hardware
--------
1. one NIC ICE_100G-E810C_QSFP(NIC-1), one NIC ICE_25G-E810_XXV_SFP(NIC-2);
   one 100G cable, one 10G cable;
   Assume that device ID and pci address of NIC-1,Port-1 are ens785f0 and 18:00.0,
   device ID and pci address of NIC-2,Port-1 are ens802f0 and 86:00.0.
2. one 100Gbps traffic generator, assume that as an IXIA port to design case.

Software
--------
dpdk: http://dpdk.org/git/dpdk

runtime command: https://doc.dpdk.org/guides/testpmd_app_ug/testpmd_funcs.html

General Set Up
--------------
1. Copy specific ice package to /lib/firmware/updates/intel/ice/ddp/ice.pkg,
   then load driver::

      # cp <ice package> /lib/firmware/updates/intel/ice/ddp/ice.pkg
      # rmmod ice
      # insmod <ice build dir>/ice.ko

2. Compile DPDK::

      # CC=gcc meson --werror -Denable_kmods=True -Dlibdir=lib --default-library=static <dpdk build dir>
      # ninja -C <dpdk build dir> -j 110

3. Get the pci device id and interface of DUT and tester.
   For example, device ID and pci address of NIC-1,Port-1 are ens785f0 and 18:00.0,
   device ID and pci address of NIC-2,Port-1 are ens802f0 and 86:00.0.
   Bind the DUT port to dpdk::

      <dpdk dir># ./usertools/dpdk-devbind.py -b vfio-pci 18:00.1 86:00.0

4. launch testpmd with 8 or 16 queues due to case design::

      <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -c 0x3fffe -n 4 -- -i --rxq=16 --txq=16

Test Case
=========
Common Steps
------------
IXIA Sends 8 streams(1-8) with different pkt size(64/128/256/512/1024/1518/512/1024).
Stream2 has UP1, stream3 has UP2, other streams has UP0.
Linerate is 100Gbps, each stream occupied 12.5%Max linerate.
The 10Gbps cable limited TX rate of NIC-2,Port-1 to 10Gbps.
Check the actual TX throughput of ens802f0(86:00.0) is about 8.25Gbps.
When check the throughput ratio of each queue group and queue,
stop the forward, and check the TX-packets ratio of queues.
The TX-packets ratio of queues is same as TX throughput ratio of queues.

Test Case 1: queuegroup_RR_queue_WFQ_RR_nolimit
-----------------------------------------------
RR Scheduling on queue groups.
WFQ Scheduling on queue group 0, RR Scheduling on queue group 1.
No bandwidth limit.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 8 queues::

      <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -c 0x3fffe -n 4 -- -i --rxq=8 --txq=8

2. configure 2 groups: group 0(queue 0 to queue 3),group 1(queue 4 to queue 7).
   RR scheduler algo between group 0 and group 1.
   WFQ scheduler within group 0(1:2:3:4) and RR within group 1::

      testpmd> add port tm node shaper profile 1 1 100000000 0 100000000 0 0 0
      testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0
      testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 -1 1 0 0
      testpmd> add port tm nonleaf node 1 800000 900000 0 1 2 -1 1 0 0
      testpmd> add port tm nonleaf node 1 700000 800000 0 1 3 -1 1 0 0
      testpmd> add port tm nonleaf node 1 600000 800000 0 1 3 -1 1 0 0
      testpmd> add port tm leaf node 1 0 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 1 700000 0 2 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 2 700000 0 3 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 3 700000 0 4 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 4 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 5 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 6 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 7 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> port tm hierarchy commit 1 no
      testpmd> start

3. Send streams from IXIA

4. Check the TX throughput of port 1::

      testpmd> show port stats 1

   Check the throughput ratio of each queue group and queue::

      testpmd> stop

   The TX throughput of Queue group 0 and group 1 are the same.
   The TX throughput of queue 0-3 is 1:2:3:4
   The TX throughput of queue 4-7 is 1:1:1:1.

Test Case 2: queuegroup_SP_queue_WFQ_RR_nolimit
-----------------------------------------------
SP Scheduling on queue groups.
WFQ Scheduling on queue group 0, RR Scheduling on queue group 1.
No bandwidth limit.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 8 queues::

      <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -c 0x3fffe -n 4 -- -i --rxq=8 --txq=8

2. configure 2 groups: group 0(queue 0 to queue 3),group 1(queue 4 to queue 7).
   SP scheduler algo between group 0 and group 1(0/1).
   WFQ scheduler within group 0(1:2:3:4) and RR within group 1::

      testpmd> add port tm node shaper profile 1 1 100000000 0 100000000 0 0 0
      testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0
      testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 -1 1 0 0
      testpmd> add port tm nonleaf node 1 800000 900000 0 1 2 -1 1 0 0
      testpmd> add port tm nonleaf node 1 700000 800000 0 1 3 -1 1 0 0
      testpmd> add port tm nonleaf node 1 600000 800000 1 1 3 -1 1 0 0
      testpmd> add port tm leaf node 1 0 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 1 700000 0 2 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 2 700000 0 3 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 3 700000 0 4 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 4 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 5 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 6 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 7 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> port tm hierarchy commit 1 no
      testpmd> start

3. Send streams from IXIA

4. Check the TX throughput of port 1::

      testpmd> show port stats 1

   Check the throughput ratio of each queue group and queue::

      testpmd> stop

   Queue group 1 has not TX throughput
   The TX throughput of queue 0-3 is 1:2:3:4

Test Case 3: queuegroup_RR_queue_WFQ_RR
---------------------------------------
RR Scheduling on queue groups.
WFQ Scheduling on queue group 0, RR Scheduling on queue group 1.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 8 queues::

      <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -c 0x3fffe -n 4 -- -i --rxq=8 --txq=8

2. configure 2 groups: group 0(queue 0 to queue 3),group 1(queue 4 to queue 7).
   RR scheduler algo between group 0 and group 1.
   WFQ scheduler within group 0(1:2:3:4) and RR within group 1.
   Set rate limit on group 1 to 300MBps::

      testpmd> add port tm node shaper profile 1 1 300000000 0 300000000 0 0 0
      testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0
      testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 -1 1 0 0
      testpmd> add port tm nonleaf node 1 800000 900000 0 1 2 -1 1 0 0
      testpmd> add port tm nonleaf node 1 700000 800000 0 1 3 -1 1 0 0
      testpmd> add port tm nonleaf node 1 600000 800000 0 1 3 1 1 0 0
      testpmd> add port tm leaf node 1 0 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 1 700000 0 2 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 2 700000 0 3 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 3 700000 0 4 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 4 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 5 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 6 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 7 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> port tm hierarchy commit 1 no
      testpmd> start

3. Send streams from IXIA

4. Check the TX throughput of port 1::

      testpmd> show port stats 1

   Check the throughput ratio of each queue group and queue::

      testpmd> stop

   Check the TX throughput of queue group 1 is limited to 2.4Gbps.
   The TX throughput of queue 0-3 is 1:2:3:4.
   The TX throughput of queue 4-7 is 1:1:1:1.

Test Case 4: queuegroup_SP_queue_WFQ_SP
---------------------------------------
SP Scheduling on queue groups.
WFQ Scheduling on queue group 0, SP Scheduling on queue group 1.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 12 queues::

      <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -c 0x3fffe -n 4 -- -i --rxq=12 --txq=12

2. configure 2 groups: group 0(queue 0 to queue 3),group 1(queue 4 to queue 11).
   SP scheduler algo between group 0 and group 1(0/1).
   WFQ scheduler within group 0(1:2:3:4) and SP within group 1(0/2/1/2/3/3/5/7).
   Set rate limit on group 0 to 300MBps,
   set rate limit on group 1 to (10/10/100/20/300/400/no/10MBps)::

      testpmd> add port tm node shaper profile 1 1 300 0 300000000 0 0 0
      testpmd> add port tm node shaper profile 1 2 300 0 100000000 0 0 0
      testpmd> add port tm node shaper profile 1 3 300 0 10000000 0 0 0
      testpmd> add port tm node shaper profile 1 4 300 0 20000000 0 0 0
      testpmd> add port tm node shaper profile 1 5 200 0 400000000 0 0 0
      testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0
      testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 -1 1 0 0
      testpmd> add port tm nonleaf node 1 800000 900000 0 1 2 -1 1 0 0
      testpmd> add port tm nonleaf node 1 700000 800000 0 1 3 1 1 0 0
      testpmd> add port tm nonleaf node 1 600000 800000 7 1 3 -1 1 0 0
      testpmd> add port tm leaf node 1 0 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 1 700000 0 2 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 2 700000 0 3 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 3 700000 0 4 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 4 600000 0 1 4 3 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 5 600000 2 1 4 3 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 6 600000 1 1 4 2 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 7 600000 2 1 4 4 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 8 600000 3 1 4 1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 9 600000 3 1 4 5 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 10 600000 5 1 4 3 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 11 600000 7 1 4 3 0 0xffffffff 0 0
      testpmd> port tm hierarchy commit 1 no
      testpmd> start

3. Send streams from IXIA

4. Check the TX throughput of port 1::

      testpmd> show port stats 1

   Check the throughput ratio of each queue group and queue::

      testpmd> stop

   Check the TX throughput of queue group 0 is limited to 2.4Gbps.
   The TX throughput of queue 0-3 is 1:2:3:4.
   The throughput of queue 4 is limited to 80Mbps,
   queue 5 is limited to 80Mbps,
   queue 6 is limited to 800Mbps,
   queue 7 is limited to 160Mbps,
   queue 8 and queue 9 has rest throughput of queue group 1,
   and the two queue has the same throughput,
   queue 10 and queue 11 has little throughput.

Test Case 5: queuegroup_RR_queue_RR_SP_WFQ
------------------------------------------
RR Scheduling on queue groups.
RR Scheduling on queue group 0, SP Scheduling on queue group 1,
WFQ Scheduling on queue group 2.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 16 queues::

      <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -c 0x3fffe -n 4 -- -i --rxq=16 --txq=16

2. configure 2 groups: group 0(queue 0 to queue 3),group 1(queue 4 to queue 7),group 2(queue 8 to queue 15).
   RR scheduler algo between group 0, group 1 and group 2.
   RR scheduler  within group 0(1:1:1:1), SP within group 1(0/4/1/7) and WFQ within group 2(4:2:2:100:3:1:5:7).
   Set rate limit on queue4-7 to (100/no/400/100MBps)::

      testpmd> add port tm node shaper profile 1 1 300 0 300000000 0 0 0
      testpmd> add port tm node shaper profile 1 2 100 0 100000000 0 0 0
      testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0
      testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 -1 1 0 0
      testpmd> add port tm nonleaf node 1 800000 900000 0 1 2 -1 1 0 0
      testpmd> add port tm nonleaf node 1 700000 800000 0 1 3 -1 1 0 0
      testpmd> add port tm nonleaf node 1 600000 800000 0 1 3 -1 1 0 0
      testpmd> add port tm nonleaf node 1 500000 800000 0 1 3 -1 1 0 0
      testpmd> add port tm leaf node 1 0 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 1 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 2 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 3 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 4 600000 0 1 4 2 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 5 600000 4 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 6 600000 1 1 4 1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 7 600000 7 1 4 2 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 8 500000 0 4 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 9 500000 0 2 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 10 500000 0 2 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 11 500000 0 100 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 12 500000 0 3 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 13 500000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 14 500000 0 5 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 15 500000 0 7 4 -1 0 0xffffffff 0 0
      testpmd> port tm hierarchy commit 1 no
      testpmd> start

3. Send streams from IXIA

4. Check the TX throughput of port 1::

      testpmd> show port stats 1

   Check the throughput ratio of each queue group and queue::

      testpmd> stop

   Check the TX throughput ratio of queue group 0/1/2 is 1:1:1.
   The TX throughput of queue 0-3 is 1:1:1:1.
   The throughput of queue 4 is limited to 800Mbps,
   queue 5 has little throughput,
   queue 6 has the rest throughput of queue group 1,
   queue 7 has little throughput.
   Queue 8-15 throughput ratio is align to (4:2:2:100:3:1:5:7).

Test Case 6: queuegroup_SP_queue_RR_SP_WFQ
------------------------------------------
SP Scheduling on queue groups.
RR Scheduling on queue group 0, SP Scheduling on queue group 1,
WFQ Scheduling on queue group 2.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 16 queues::

      <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -c 0x3fffe -n 4 -- -i --rxq=16 --txq=16

2. configure 2 groups: group 0(queue 0 to queue 3),group 1(queue 4 to queue 7),group 2(queue 8 to queue 15).
   SP scheduler algo between group 0, group 1 and group 2(0/1/2).
   RR scheduler  within group 0(1:1:1:1), SP within group 1(0/4/1/7) and WFQ within group 2(4:2:2:100:3:1:5:7).
   Set rate limit on group 0 to 100MBps, set rate limit on group 1 to 100MBps,
   set rate limit on group 2 to 300MBps.
   Set rate limit to queue0, queue1 and queue4 to 300MBps,
   set no rate limit on other queues::

      testpmd> add port tm node shaper profile 1 1 300 0 300000000 0 0 0
      testpmd> add port tm node shaper profile 1 2 100 0 100000000 0 0 0
      testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0
      testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 -1 1 0 0
      testpmd> add port tm nonleaf node 1 800000 900000 0 1 2 -1 1 0 0
      testpmd> add port tm nonleaf node 1 700000 800000 0 1 3 2 1 0 0
      testpmd> add port tm nonleaf node 1 600000 800000 1 1 3 2 1 0 0
      testpmd> add port tm nonleaf node 1 500000 800000 2 1 3 1 1 0 0
      testpmd> add port tm leaf node 1 0 700000 0 1 4 1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 1 700000 0 1 4 1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 2 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 3 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 4 600000 0 1 4 1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 5 600000 4 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 6 600000 1 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 7 600000 7 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 8 500000 0 4 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 9 500000 0 2 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 10 500000 0 2 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 11 500000 0 100 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 12 500000 0 3 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 13 500000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 14 500000 0 5 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 15 500000 0 7 4 -1 0 0xffffffff 0 0
      testpmd> port tm hierarchy commit 1 no
      testpmd> start

3. Send streams from IXIA

4. Check the TX throughput of port 1::

      testpmd> show port stats 1

   Check the throughput ratio of each queue group and queue::

      testpmd> stop

   Check the TX throughput ratio of queue group 0/1/2 is 1:1:3,
   the sum of TX throughput is 4Gbps.
   The TX throughput ratio of queue 0-3 is 1:1:1:1.
   The throughput of queue 4 is limited to 800Mbps,
   queue 5-7 has little throughput,
   Queue 8-15 throughput ratio is align to (4:2:2:100:3:1:5:7).

Test Case 7: queuegroup_RR_queue_WFQ_WFQ
----------------------------------------
RR Scheduling on queue groups.
WFQ Scheduling on queue group 0, WFQ Scheduling on queue group 1.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 8 queues::

      <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -c 0x3fffe -n 4 -- -i --rxq=8 --txq=8

2. configure 2 groups: group 0(queue 0 to queue 3),group 1(queue 4 to queue 7).
   RR scheduler algo between group 0 and group 1.
   WFQ scheduler  within group 0(1:2:3:4), WFQ within group 1(1:2:3:4).
   Set bandwidth limit on queues of group 1 to (10/10/40/no)MBps
   Set bandwidth limit on queues of group 1 to (40/30/no/no)MBps::

      testpmd> add port tm node shaper profile 1 1 10000000 0 10000000 0 0 0
      testpmd> add port tm node shaper profile 1 2 20000000 0 20000000 0 0 0
      testpmd> add port tm node shaper profile 1 3 30000000 0 30000000 0 0 0
      testpmd> add port tm node shaper profile 1 4 40000000 0 40000000 0 0 0
      testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0
      testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 -1 1 0 0
      testpmd> add port tm nonleaf node 1 800000 900000 0 1 2 -1 1 0 0
      testpmd> add port tm nonleaf node 1 700000 800000 0 1 3 -1 1 0 0
      testpmd> add port tm nonleaf node 1 600000 800000 0 1 3 -1 1 0 0
      testpmd> add port tm leaf node 1 0 700000 0 1 4 1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 1 700000 0 2 4 1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 2 700000 0 3 4 4 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 3 700000 0 4 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 4 600000 0 1 4 4 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 5 600000 0 2 4 3 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 6 600000 0 3 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 7 600000 0 4 4 -1 0 0xffffffff 0 0
      testpmd> port tm hierarchy commit 1 no
      testpmd> start

3. Send streams from IXIA

4. Check the TX throughput of port 1::

      testpmd> show port stats 1

   Check the throughput ratio of each queue group and queue::

      testpmd> stop

   Check the TX throughput of queue group 0 and group 1 are the same.
   Check the TX throughput of queue0 is limited to 10MBps,
   queue1 is limited to 10MBps, queue2 is limited to 40MBps,
   queue3 has the rest throughput of queue group 0.
   Queue4 is limited to 40MBps, queue5 is limited to 30MBps,
   queue 6 and queue 7 have the rest throughput of queue group 1,
   the throughput ratio of queue 6 and queue 7 is 3:4.

Test Case 8: negative case
--------------------------
Configure invalid parameters, report expected errors.

Test Steps
~~~~~~~~~~
1. Launch testpmd with 16 queues::

      <dpdk dir># ./<dpdk build dir>/app/dpdk-testpmd -c 0x3fffe -n 4 -- -i --rxq=16 --txq=16

2. configure 2 groups, WFQ scheduler algo between group 0 and group 1(1:2)::

      testpmd> add port tm node shaper profile 1 1 100000000 0 100000000 0 0 0
      testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0
      testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 -1 1 0 0
      testpmd> add port tm nonleaf node 1 800000 900000 0 1 2 -1 1 0 0
      testpmd> add port tm nonleaf node 1 700000 800000 0 1 3 -1 1 0 0
      testpmd> add port tm nonleaf node 1 600000 800000 0 2 3 -1 1 0 0
      ice_tm_node_add(): weight != 1 not supported in level 3

3. Configure RR scheduler algo on groups, and set queue 3 weight to 201::

      testpmd> port stop 1
      testpmd> del port tm node 1 600000
      testpmd> add port tm nonleaf node 1 600000 800000 0 1 3 -1 1 0 0
      testpmd> port start 1
      testpmd> add port tm leaf node 1 0 700000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 1 700000 0 2 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 2 700000 0 3 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 3 700000 0 201 4 -1 0 0xffffffff 0 0
      node weight: weight must be between 1 and 200 (error 21)

4.  reset queue 3 weight to 200, set queue 11 node priority to 8::

      testpmd> add port tm leaf node 1 3 700000 0 200 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 4 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 5 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 6 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 7 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 8 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 9 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 10 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 11 600000 8 1 4 -1 0 0xffffffff 0 0
      node priority: priority should be less than 8 (error 20)

5. reset queue 11 node priority to 7,
   set queue 4-15 (>8 queues) to queue group 1 and commit::

      testpmd> add port tm leaf node 1 11 600000 7 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 12 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 13 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 14 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> add port tm leaf node 1 15 600000 0 1 4 -1 0 0xffffffff 0 0
      testpmd> port tm hierarchy commit 1 no
      ice_move_recfg_lan_txq(): move lan queue 12 failed
      ice_hierarchy_commit(): move queue 12 failed
      cause unspecified: (no stated reason) (error 1)

6. Check all the reported errors as expected.
