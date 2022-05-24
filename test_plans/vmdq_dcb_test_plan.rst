.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

====================================================================================
Intel® Ethernet 700 Series: Support of RX Packet Filtering using VMDQ & DCB Features
====================================================================================

The Intel Network Interface Card(e.g. XL710), supports a number of
packet filtering functions which can be used to distribute incoming packets
into a number of reception (RX) queues. VMDQ & DCB is a pair of such filtering
functions which operate on VLAN-tagged packets to distribute those packets
to RX queues.

The feature itself works by:

- splitting the incoming packets up into different "pools" - each with its own
  set of RX queues - based upon the VLAN ID within the VLAN tag of the packet.
- assigning each packet to a specific queue within the pool, based upon the
  user priority field within the VLAN tag.

The VMDQ & DCB features are enabled in the ``vmdq_dcb`` example application
contained in the DPDK, and this application should be used to validate
the feature.

Prerequisites
=============

- The DPDK is compiled for the appropriate target type in each case, and
  the VMDQ & DCB example application is compiled and linked with that DPDK
  instance
- Two ports are connected to the test system, one to be used for packet reception,
  the other for transmission
- The traffic generator being used is configured to send to the application RX
  port a stream of packets with VLAN tags, where the VLAN IDs increment from 0
  to the pools numbers(inclusive) and the VLAN user priority field increments from
  0 to 7 (inclusive) for each VLAN ID.
- Build vmdq_dcb example,
    meson: ./<build_target>/examples/dpdk-vmdq_dcb -c 0xff -n 4 -- -p 0x3 --nb-pools 32 --nb-tcs 4 --enable-rss

Test Case 1: Verify VMDQ & DCB with 32 Pools and 4 TCs
======================================================

1. Run the application as the following::

    meson: ./<build_target>/examples/dpdk-vmdq_dcb -c 0xff -n 4 -- -p 0x3 --nb-pools 32 --nb-tcs 4 --enable-rss

2. Start traffic transmission using approx 10% of line rate.
3. After a number of seconds, e.g. 15, stop traffic, and ensure no traffic
   loss (<0.001%) has occurred.
4. Send a hangup signal (SIGHUP) to the application to have it print out the
   statistics of how many packets were received per RX queue::

     kill -s SIGHUP  `pgrep -fl vmdq_dcb_app | awk '{print $1}'`

Expected Result:

- No packet loss is expected.
- Every RX queue should have received approximately (+/-15%) the same number of
  incoming packets
- verify queue id should be equal "vlan user priority value % 4".

Test Case 2: Verify VMDQ & DCB with 16 Pools and 8 TCs
======================================================

1. change RTE_LIBRTE_I40E_QUEUE_NUM_PER_VM to 8 in "./config/rte_config.h", rebuild DPDK.
    meson: change "#define RTE_LIBRTE_I40E_QUEUE_NUM_PER_VM 4" to 8 in config/rte_config.h, rebuild DPDK.

2. Repeat Test Case 1, with `--nb-pools 16` and `--nb-tcs 8` of the sample application::

    meson: ./<build_target>/examples/dpdk-vmdq_dcb -c 0xff -n 4 -- -p 0x3 --nb-pools 16 --nb-tcs 8 --enable-rss

Expected result:
- No packet loss is expected
- Every RX queue should have received approximately (+/-15%) the same number of incoming packets
- verify queue should be equal "vlan user priority value"

3. change CONFIG_RTE_LIBRTE_I40E_QUEUE_NUM_PER_VM to 16 in "./config/common_linuxapp", rebuild DPDK.
    meson: change "#define RTE_LIBRTE_I40E_QUEUE_NUM_PER_VM 4" to 16 in config/rte_config.h, rebuild DPDK.

4. Repeat Test Case 1, with `--nb-pools 16` and `--nb-tcs 8` of the sample application::

    meson: ./<build_target>/examples/dpdk-vmdq_dcb -c 0xff -n 4 -- -p 0x3 --nb-pools 16 --nb-tcs 8 --enable-rss

Expected result:
- No packet loss is expected
- Every RX queue should have received approximately (+/-15%) the same number of incoming packets
- verify queue id should be in [vlan user priority value * 2, vlan user priority value * 2 + 1]

(NOTE: SIGHUP output will obviously change to show 8 columns per row, with only 16 rows)
