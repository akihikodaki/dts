.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2014-2017 Intel Corporation

===========================
Unit Tests: PMD Performance
===========================


Prerequisites
=============
One 10Gb Ethernet port of the DUT is directly connected and link is up.


Continuous Mode Performance
===========================

This is the test plan for unit test to measure cycles/packet in NIC loopback
mode.

This section explains how to run the unit tests for pmd performance with
continues stream control mode.
The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The final output of the test will be average cycles of IO used per packet.


Burst Mode Performance
======================

This is the test plan for unit test to measure cycles/packet in NIC loopback
mode.

This section explains how to run the unit tests for pmd performance with
burst stream control mode. For get accurate scalar fast performance, need
disable INC_VECTOR in configuration file first.


The test can be launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The final output of the test will be matrix of average cycles of IO used per
packet.

        +--------+------+--------+--------+
        | Mode   | rxtx | rxonly | txonly |
        +========+======+========+========+
        | vector | 58   | 34     | 23     |
        +--------+------+--------+--------+
        | scalar | 89   | 51     | 38     |
        +--------+------+--------+--------+
        | full   | 73   | 31     | 42     |
        +--------+------+--------+--------+
        | hybrid | 59   | 35     | 23     |
        +--------+------+--------+--------+
