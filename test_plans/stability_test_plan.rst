.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2011-2017 Intel Corporation

===============
Stability Tests
===============

This is the test report for the Intel® DPDK Linux user space stability tests
described in the test plan document.

Test Case: Stress test
======================

Run under heavy traffic for a long time. At the end of the test period, check
that the traffic is still flowing and there is no drop in the throughput rate.

Recommended test configuration: testpmd application using a single logical core
to handle line rate traffic from two 10GbE ports. Recommended test duration:
24 hours.

Test Case: Repetitive system restart
====================================

Check that the system is still working after the application is shut down and
restarted repeatedly under heavy traffic load. After the last test iteration,
the traffic should still be flowing through the system with no drop in the
throughput rate.

Recommended test configuration: testpmd application using a single logical core
to handle line rate traffic from two 10GbE ports.

Test Case: Packet integrity test
================================

Capture output packets selectively and check that the packet headers are as
expected, with the payload not corrupted or truncated.

Recommended test configuration: testpmd application using a single logical core
to handle line rate traffic from two 10GbE ports.

Test Case: Cable removal test
=============================

Check that the traffic stops when the cable is removed and resumes with no drop
in the throughput rate after the cable is reinserted.

Test Case: Mix of different NIC types
=====================================

Check that a mix of different NIC types is supported. The system should
recognize all the NICs that are part of the system and are supported by the
DPDK PMD. Check that ports from NICs of different type can send and
receive traffic at the same time.

Recommended test configuration: testpmd application using a single logical core
to handle line rate traffic from two 1GbE ports (e.g. Intel 82576 NIC) and
two 10GbE ports (e.g. Intel 82599 NIC).

Test Case: Coexistence of kernel space drivers with Poll Mode Drivers
=====================================================================

Verify that DPDK PMD running in user space can work with the kernel
space space NIC drivers.

Recommended test configuration: testpmd application using a single logical core
to handle line rate traffic from two 1GbE ports (e.g. Intel 82576 NIC) and
two 10GbE ports (e.g. Intel 82599 NIC). Kernel space driver for Intel 82576 NIC
used for management.
