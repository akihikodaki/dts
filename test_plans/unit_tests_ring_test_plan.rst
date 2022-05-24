.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

================
Unit Tests: Ring
================

This is the test plan for the Intel® DPDK ring library.

Description
===========

#. Basic tests (done on one core)

   - Using single producer/single consumer functions:

     - Enqueue one object, two objects, MAX_BULK objects
     - Dequeue one object, two objects, MAX_BULK objects
     - Check that dequeued pointers are correct

   - Using multi producers/multi consumers functions:

     - Enqueue one object, two objects, MAX_BULK objects
     - Dequeue one object, two objects, MAX_BULK objects
     - Check that dequeued pointers are correct

   - Test watermark and default bulk enqueue/dequeue:

     - Set watermark
     - Set default bulk value
     - Enqueue objects, check that -EDQUOT is returned when
       watermark is exceeded
     - Check that dequeued pointers are correct

#. Check quota and watermark

   - Start a loop on another lcore that will enqueue and dequeue
     objects in a ring. It will monitor the value of quota (default
     bulk count) and watermark.
   - At the same time, change the quota and the watermark on the
     master lcore.
   - The slave lcore will check that bulk count changes from 4 to
     8, and watermark changes from 16 to 32.

#. Performance tests

   This test is done on the following configurations:

   - One core enqueuing, one core dequeuing
   - One core enqueuing, other cores dequeuing
   - One core dequeuing, other cores enqueuing
   - Half of the cores enqueuing, the other half dequeuing

   When only one core enqueues/dequeues, the test is done with the
   SP/SC functions in addition to the MP/MC functions.

   The test is done with different bulk size.

   On each core, the test enqueues or dequeues objects during
   TIME_S seconds. The number of successes and failures are stored on
   each core, then summed and displayed.

   The test checks that the number of enqueues is equal to the
   number of dequeues.

#. Change watermark and quota

   Use the command line to change the value of quota and
   watermark. Then dump the status of ring to check that the values
   are correctly updated in the ring structure.

============================
Unit Tests: Ring Performance
============================

This is the test plan for the Intel®  DPDK LPM Method in IPv6.

This section explains how to run the unit tests for LPM in IPv6.The test can be
launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

The steps to run the unit test manually are as follow::

  Build dpdk
  # cd dpdk
  # CC=gcc meson --werror -Denable_kmods=True  -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
  # ninja -C x86_64-native-linuxapp-gcc -j 50

  # ./x86_64-native-linuxapp-gcc/app/test/dpdk-test -n 1 -c ffff
  RTE>> ring_perf_autotest


The final output of the test has to be "Test OK"
