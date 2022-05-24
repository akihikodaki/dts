.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

==========
VMDQ Tests
==========

The 1G, 10G 82599 and 40G Intel® Ethernet 700 Series Network Interface Card (NIC),
supports a number of packet filtering functions which can be used to distribute
incoming packets into a number of reception (RX) queues. VMDQ is a  filtering
functions which operate on VLAN-tagged packets to distribute those packets
among up to 512 RX queues.

The feature itself works by:

- splitting the incoming packets up into different "pools" - each with its own
  set of RX queues - based upon the MAC address and VLAN ID within the VLAN tag of the packet.
- assigning each packet to a specific queue within the pool, based upon the
  user priority field within the VLAN tag and MAC address.

The VMDQ features are enabled in the ``vmdq`` example application
contained in the DPDK, and this application should be used to validate
the feature.

Prerequisites
=============
- All tests assume a linuxapp setup.
- The port ids of the two 10G or 40G ports to be used for the testing are specified
  in the commandline. it use a portmask.
- The DPDK is compiled for the appropriate target type in each case, and
  the VMDQ  example application is compiled and linked with that DPDK
  instance
- Two ports are connected to the test system, one to be used for packet
  reception, the other for transmission
- The traffic generator being used is configured to send to the application RX
  port a stream of packets with VLAN tags, where the VLAN IDs increment from 0
  to the pools numbers(e.g: for Intel® Ethernet Converged Network Adapter XL710-QDA2,
  it's 63, inclusive) as well as the MAC address from 52:54:00:12:[port_index]:00 to
  52:54:00:12:[port_index]:3e and the VLAN user priority field increments from 0 to 7
  (inclusive) for each VLAN ID. In our case port_index = 0 or 1.

Test Case: Measure VMDQ pools queues
------------------------------------
1. Put different number of pools: in the case of 10G 82599 Nic is 64, in the case
   of Intel® Ethernet Converged Network Adapter XL710-QDA2 is 63,in case of Intel®
   Ethernet Converged Network Adapter X710-DA4 is 34.
2. Start traffic transmission using approx 10% of line rate.
3. After a number of seconds, e.g. 15, stop traffic, and ensure no traffic
   loss (<0.001%) has occurred.
4. Send a hangup signal (SIGHUP) to the application to have it print out the
   statistics of how many packets were received per RX queue

Expected Result:

- No packet loss is expected
- Every RX queue should have received approximately (+/-15%) the same number of
  incoming packets

Test Case: Measure VMDQ Performance
-----------------------------------

1. Compile VMDQ  example application as in first test above.
2. Run application using a core mask for the appropriate thread and core
   settings given in the following list:

  * 1S/1C/1T
  * 1S/2C/1T
  * 1S/2C/2T
  * 1S/4C/1T

3. Measure maximum RFC2544 performance throughput for bi-directional traffic for
   all standard packet sizes.

Output Format:
The output format should be as below, or any similar table-type, with figures
given in mpps:

+------------+----------+----------+----------+----------+
| Frame size | 1S/1C/1T | 1S/2C/1T | 1S/2C/2T | 1S/4C/1T |
+============+==========+==========+==========+==========+
| 64         | 19.582   | 42.222   | 53.204   | 73.768   |
+------------+----------+----------+----------+----------+
| 128        | 20.607   | 42.126   | 52.964   | 67.527   |
+------------+----------+----------+----------+----------+
| 256        | 15.614   | 33.849   | 36.232   | 36.232   |
+------------+----------+----------+----------+----------+
| 512        | 11.794   | 18.797   | 18.797   | 18.797   |
+------------+----------+----------+----------+----------+
| 1024       | 9.568    | 9.579    | 9.579    | 9.579    |
+------------+----------+----------+----------+----------+
| 1280       | 7.692    | 7.692    | 7.692    | 7.692    |
+------------+----------+----------+----------+----------+
| 1518       | 6.395    | 6.502    | 6.502    | 6.502    |
+------------+----------+----------+----------+----------+
