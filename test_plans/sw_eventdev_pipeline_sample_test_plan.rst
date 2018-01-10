.. Copyright (c) <2013-2017>, Intel Corporation
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

===============================
Eventdev Pipeline SW PMD Tests
===============================

Prerequistites
==============

Test Case 1: Keep the packets order with one ordered stage in single-flow and multi-flow
========================================================================================
Description: the sample only guarantee that keep the packets order with only one stage.

1. Run the sample with below command:
# ./build/eventdev_pipeline_sw_pmd --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 -W1000 -o -D
Parameters: 
-r2, -t4, -e8: allocate cores to rx, tx and shedular
-w: allocate cores to workers
-s1: the sample only contain 1 stage
-n0: the sample will run forever without a packets num limit

2. Send traffic from ixia device with same 5 tuple(single-link) and with different 5-tuple(multi-flow)

3. Observe the packets received by ixia device, check the packets order.

Test Case 2: Keep the packets order with atomic stage in single-flow and multi-flow
===================================================================================
Description: the packets' order which will pass through a same flow should be guaranteed.

1. Run the sample with below command:
# ./build/eventdev_pipeline_sw_pmd --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s2 -n0 -c32 -W1000 -a -D

2. Send traffic from ixia device with same 5 tuple(single-link) and with different 5-tuple(multi-flow)

3. Observe the packets received by ixia device, ensure packets in each *flow* remain in order, but note that flows may be re-ordered compared to eachother.


Test Case 3: Check load-balance behavior with atomic type in single-flow and multi-flow situations
==================================================================================================
Description: In multi-flow situation, sample should have a good load-blanced behavior; in single-flow, the load-balanced behavior is not guaranteed;

1. Run the sample with below command:
# ./build/eventdev_pipeline_sw_pmd --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 -W1000 -a -D

2. Use traffic generator to send huge number of packets:
In single-flow situation, traffic generator will send packets with the same 5-tuple which is used to calculate rss value;
In multi-flow situation, traffice generator will send packets with different 5-tuple;

3. Check the load-balance bahavior by the workload of every worker.

Test Case 4: Check load-balance behavior with order type stage in single-flow and multi-flow situations
=======================================================================================================
Description: A good load-balanced behavior should be guaranteed in both single-flow and multi-flow situations.

1. Run the sample with below command:
# ./build/eventdev_pipeline_sw_pmd --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 -W1000 -o -D

2. Use traffic generator to send huge number of packets:
In single-flow situation, traffic generator will send packets with the same 5-tuple which is used to calculate rss value;
In multi-flow situation, traffice generator will send packets with different 5-tuple;

3. Check the load-balance bahavior by the workload of every worker.

Test Case 5: Check load-balance behavior with parallel type stage in single-flow and multi-flow situations 
==========================================================================================================
Description: A good load-balanced behavior should be guaranteed in both single-flow and multi-flow situations.

1. Run the sample with below command:
# ./build/eventdev_pipeline_sw_pmd --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 -W1000 -p -D

2. Use traffic generator to send huge number of packets:
In single-flow situation, traffic generator will send packets with the same 5-tuple which is used to calculate rss value;
In multi-flow situation, traffic generator will send packets with different 5-tuple;

3. Check the load-balance bahavior by the workload of every worker.

Test Case 6: Performance test for atomic type of stage
======================================================
Description: Execute performance test with atomic type of stage in single-flow and multi-flow situation.
We use 4 worker and 2 stage as the test background.

1. Run the sample with below command:
# ./build/eventdev_pipeline_sw_pmd --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 

2. use traffic generator to send huge number of packets(with same 5-tuple and different 5-tuple)

3. observe the speed of packets received.

Test Case 7: Performance test for parallel type of stage
========================================================
Description: Execute performance test with atomic type of stage in single-flow and multi-flow situation.
We use 4 worker and 2 stage as the test background.

1. Run the sample with below command:
# ./build/eventdev_pipeline_sw_pmd --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 

2. use traffic generator to send huge number of packets(with same 5-tuple and different 5-tuple)

3. observe the speed of packets received.

Test Case 8: Performance test for ordered type of stage
=======================================================
Description: Execute performance test with atomic type of stage in single-flow and multi-flow situation.
We use 4 worker and 2 stage as the test background.

1. Run the sample with below command:
# ./build/eventdev_pipeline_sw_pmd --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 

2. use traffic generator to send huge number of packets(with same 5-tuple and different 5-tuple)

3. observe the speed of packets received.

Test Case 9: Basic forward test for all type of stage
=====================================================
Description: Execute basic forward test with all type of stage.

1. Run the sample with below command:
# ./build/eventdev_pipeline_sw_pmd --vdev event_sw0 -- -r2 -t4 -e8 -w F0 -s1 -n0 -c32 

2. use traffic generator to send some packets and verify the sample could forward them normally

