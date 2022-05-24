.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2013-2017 Intel Corporation

===============================
Eventdev Pipeline SW PMD Tests
===============================

Prerequisites
==============
Build dpdk and examples=eventdev_pipeline
   CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static <build_target>
   ninja -C <build_target>

   meson configure -Dexamples=eventdev_pipeline <build_target>
   ninja -C <build_target>

Test Case: Keep the packets order with default stage in single-flow and multi-flow
====================================================================================
Description: the packets' order which will pass through a same flow should be guaranteed.

1. Run the sample with below command::

    # ./<build_target>/examples/dpdk-eventdev_pipeline /build/eventdev_pipeline --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 -W1000 -D

    Parameters:
    -r2, -t4, -e8: allocate cores to rx, tx and shedular
    -w: allocate cores to workers
    -s1: the sample only contain 1 stage
    -n0: the sample will run forever without a packets num limit

2. Send traffic from ixia device with same 5 tuple(single-link) and with different 5-tuple(multi-flow)

3. Observe the packets received by ixia device, ensure packets in each *flow* remain in order,
   but note that flows may be re-ordered compared to eachother.

Test Case: Keep the packets order with one ordered stage in single-flow and multi-flow
========================================================================================
Description: the sample only guarantee that keep the packets order with only one stage.

1. Run the sample with below command::

    # ./<build_target>/examples/dpdk-eventdev_pipeline /build/eventdev_pipeline --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 -W1000 -o -D

2. Send traffic from ixia device with same 5 tuple(single-link) and with different 5-tuple(multi-flow)

3. Observe the packets received by ixia device, check the packets order.

Test Case: Check load-balance behavior with default type in single-flow and multi-flow situations
===================================================================================================
Description: In multi-flow situation, sample should have a good load-blanced behavior;
in single-flow, the load-balanced behavior is not guaranteed;

1. Run the sample with below command::

    # ./<build_target>/examples/dpdk-eventdev_pipeline /build/eventdev_pipeline --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 -W1000 -D

2. Use traffic generator to send huge number of packets:
In single-flow situation, traffic generator will send packets with the same 5-tuple
which is used to calculate rss value;
In multi-flow situation, traffice generator will send packets with different 5-tuple;

3. Check the load-balance bahavior by the workload of every worker.

Test Case: Check load-balance behavior with order type stage in single-flow and multi-flow situations
=======================================================================================================
Description: A good load-balanced behavior should be guaranteed in both single-flow and multi-flow situations.

1. Run the sample with below command::

    # ./<build_target>/examples/dpdk-eventdev_pipeline /build/eventdev_pipeline --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 -W1000 -o -D

2. Use traffic generator to send huge number of packets:
In single-flow situation, traffic generator will send packets with the same 5-tuple
which is used to calculate rss value;
In multi-flow situation, traffice generator will send packets with different 5-tuple;

3. Check the load-balance bahavior by the workload of every worker.

Test Case: Check load-balance behavior with parallel type stage in single-flow and multi-flow situations
==========================================================================================================
Description: A good load-balanced behavior should be guaranteed in both single-flow and multi-flow situations.

1. Run the sample with below command::

    # ./<build_target>/examples/dpdk-eventdev_pipeline /build/eventdev_pipeline --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 -W1000 -p -D

2. Use traffic generator to send huge number of packets:
In single-flow situation, traffic generator will send packets with the same 5-tuple
which is used to calculate rss value;
In multi-flow situation, traffic generator will send packets with different 5-tuple;

3. Check the load-balance bahavior by the workload of every worker.

Test Case: Performance test for default type of stage
=======================================================
Description: Execute performance test with atomic type of stage in single-flow and multi-flow situation.
We use 4 worker and 2 stage as the test background.

1. Run the sample with below command::

    # ./<build_target>/examples/dpdk-eventdev_pipeline /build/eventdev_pipeline --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s2 -n0 -c32

2. use traffic generator to send huge number of packets(with same 5-tuple and different 5-tuple)

3. observe the speed of packets received.

Test Case: Performance test for parallel type of stage
========================================================
Description: Execute performance test with parallel type of stage in single-flow and multi-flow situation.
We use 4 worker and 2 stage as the test background.

1. Run the sample with below command::

    # ./<build_target>/examples/dpdk-eventdev_pipeline /build/eventdev_pipeline --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s2 -n0 -c32 -p

2. use traffic generator to send huge number of packets(with same 5-tuple and different 5-tuple)

3. observe the speed of packets received.

Test Case: Performance test for ordered type of stage
=======================================================
Description: Execute performance test with ordered type of stage in single-flow and multi-flow situation.
We use 4 worker and 2 stage as the test background.

1. Run the sample with below command::

    # ./<build_target>/examples/dpdk-eventdev_pipeline /build/eventdev_pipeline --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s2 -n0 -c32 -o

2. use traffic generator to send huge number of packets(with same 5-tuple and different 5-tuple)

3. observe the speed of packets received.

Test Case: Basic forward test for all type of stage
=====================================================
Description: Execute basic forward test with all type of stage.

1. Run the sample with below command::

    # ./<build_target>/examples/dpdk-eventdev_pipeline /build/eventdev_pipeline --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32

2. use traffic generator to send some packets and verify the sample could forward them normally
