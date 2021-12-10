.. SPDX-License-Identifier: BSD-3-Clause
   Copyright (C) 2019 Marvell International Ltd.

=======================
Unit Tests: Event Timer
=======================
This is the test plan for Event Timer Adapter auto test.

This section explains how to run the unit tests for event_timer_adapter. The
test can be launched independently using the command line interface.

The steps to run the unit test manually are as follow::

  Build dpdk
  # cd dpdk
  # CC=gcc meson --werror -Denable_kmods=True  -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
  # ninja -C x86_64-native-linuxapp-gcc -j 50

  # ./x86_64-native-linuxapp-gcc/app/test/dpdk-test -n 1 -c ffff -a <timerdev-pci-bus-id>,<devargs>
  RTE>> event_timer_adapter_test

The final output of the test has to be "Test OK"
