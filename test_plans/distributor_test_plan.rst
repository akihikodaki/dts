.. Copyright (c) <2017>, Intel Corporation
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

============================================
Sample Application Tests: Packet distributor
============================================

Packet Distributor library is a library designed to be used for dynamic
load balancing of traffic while supporting single packet at a time operation.
When using this library, the logical cores in use are to be considered in
several roles: 

rx lcore: responsible for receive packets from different ports and enqueue

distributor lcore: responsible for load balancing or distributing packets

worker locres: responsible for receiving the packets from the distributor
               and operating on them.

tx lcore: responsible for dequeue packets from distrbutor and transmit them


Test Case: Distributor unit test
================================
Start test application and run distributor unit test::

	   test -c f -n 4 -- -i
	   RTE>>distributor_autotest

Verify burst distributor API unit test passed

Test Case: Distributor performance unit test
============================================
Start test application and run distributor unit test::

	   test -c f -n 4 -- -i
	   RTE>>distributor_perf_autotest

Compared CPU cycles for normal distributor and burst API

Verify burst distributor API cost much less cycles then normal version

Test Case: Distributor packet check
===================================
Start distributor sample with one worker::

	distributor_app -c 0x7c  -n 4 -- -p 0x1

Send few packets (less then burst size) with sequence index which indicated in
ip dst address

Check forwarded packets are all in sequence and content not changed

Send packets equal to burst size with sequence index

Check forwarded packets are all in sequence and content not changed

Send packets over burst size with sequence index

Check forwarded packets are all in sequence and content not changed

Test Case: Distributor with workers
===================================
Start distributor sample with two workers::

	distributor_app -c 0xfc  -n 4 -- -p 0x1
	
Send several packets with ip address increasing

Check packets distributed to different workers

Check all packets have been sent back from tx lcore

Repeat step 1 to step4 with 4(3fc)/8(3ffc)/16(0x3ffffc)/32(0xffff0003ffffc)
workers

Test case: Distribute with maximum workers
==========================================
Start distributor sample with 63(0xeffffffffffffffff0) workers

Send several packets with ip address increasing

Check packets distributed to different workers

Check all packets have been sent back from tx lcore

Test Case: Distributor with multiple input ports
================================================
Start distributor sample with two workers and two ports::

	distributor_app -c 0x7c -n 4 -- -p 0x3

Send packets with sequence indicated in udp port id

Check forwarded packets are all in sequence and content not changed

Test case: Distribute performance
=================================
The number of workers are configured through the command line interface of the
application:

The test report should provide the measurements(mpps and % of the line rate)
for each action in lcores as listed in the table below::

	+----+---------+------------------+------------------+------------------+------------------+------------------+------------------+
	| #  |Number of| Throughput Rate  | Throughput Rate  | Throughput Rate  | Throughput Rate  | Throughput Rate  | Throughput Rate  |
	|    |workers  | Rx received      | Rx core enqueued | Distributor sent | Tx core dequeued | Tx transmitted   | Pkts out         |
	|    |         +------------------+------------------+------------------+------------------+------------------+------------------+
	|    |         |  mpps  |    %    |  mpps  |    %    |  mpps  |    %    |  mpps  |    %    |  mpps  |    %    |  mpps  |    %    |
	+----+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+
	| 1  |    1    |        |         |        |         |        |         |        |         |        |         |        |         |
	+----+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+
	| 2  |    2    |        |         |        |         |        |         |        |         |        |         |        |         |
	+----+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+
	| 3  |    3    |        |         |        |         |        |         |        |         |        |         |        |         |
	+----+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+
	| 4  |    4    |        |         |        |         |        |         |        |         |        |         |        |         |
	+----+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+
	| 5  |    8    |        |         |        |         |        |         |        |         |        |         |        |         |
	+----+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+
	| 6  |    16   |        |         |        |         |        |         |        |         |        |         |        |         |
	+----+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+
	| 7  |    32   |        |         |        |         |        |         |        |         |        |         |        |         |
	+----+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+
	| 8  |    63   |        |         |        |         |        |         |        |         |        |         |        |         |
	+----+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+--------+---------+
