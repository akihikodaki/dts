.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2017 Intel Corporation

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

tx lcore: responsible for dequeue packets from distributor and transmit them


Test Case: Distributor unit test
================================
Start test application and run distributor unit test::

	   ./x86_64-native-linuxapp-gcc/app/test/dpdk-test -c f -n 4
	   RTE>>distributor_autotest

Verify burst distributor API unit test passed

Test Case: Distributor performance unit test
============================================
Start test application and run distributor unit test::

	   ./x86_64-native-linuxapp-gcc/app/test/dpdk-test -c f -n 4
	   RTE>>distributor_perf_autotest

Compared CPU cycles for normal distributor and burst API

Verify burst distributor API cost much less cycles then normal version

Test case: Distribute with maximum workers
==========================================
Start distributor sample with 63(0xeffffffffffffffff0) workers

Send several packets with ip address increasing

Check packets distributed to different workers

Check all packets have been sent back from tx lcore

Test Case: Distributor with multiple input ports
================================================
Start distributor sample with two workers and two ports::

	./x86_64-native-linuxapp-gcc/examples/dpdk-distributor -c 0x7c -n 4 -- -p 0x3

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
