.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2014-2017 Intel Corporation

====================================
Unit Tests: single port MAC loopback
====================================

According to loopback mode, setup loopback link or not.
If loopback mode is setted, packets will be sent to rx_q from tx_q directly.
Else if loopback mode is disabled, packets will sent to peer port from tx_q.
Loopback mode can be used to support testing task.


Prerequisites
=============

Two 10Gb/25Gb/40Gb Ethernet ports of the DUT are directly connected and link is up.


single port MAC loopback
========================

This is the test plan for unit test to verify if X710/XL710/XXV710 can enable single port
mac loopback.

Test Case: enable loopback mode
===============================

In dpdk/test/test/test_pmd_perf.c
Set::

    .lpbk_mode=1
    #define MAX_TRAFFIC_BURST              32

Then make test
Start test::

    ./x86_64-native-linuxapp-gcc/app/test/dpdk-test -c f -n 4 -- -i
    RTE>>pmd_perf_autotest

The final output of the test will be matrix of average cycles of IO used per
packet, and "Test OK" is printed out.
The peer port can't receive any packet.

Test Case: disable lookback mode
================================

In dpdk/test/test/test_pmd_perf.c
Set::

    .lpbk_mode=0
    #define MAX_TRAFFIC_BURST              32

Then make test
Start test::

    ./x86_64-native-linuxapp-gcc/app/test/dpdk-test -c f -n 4 -- -i
    RTE>>pmd_perf_autotest

There is not "Test OK" presented.
The peer port can receive all the 32 packets.
