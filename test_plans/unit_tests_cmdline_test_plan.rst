.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

===================
Unit Tests: Cmdline
===================
This is the test plan for the Intel® DPDK Random Early Detection feature.

This section explains how to run the unit tests for cmdline. The test can be launched
independently using the command line interface.
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
  RTE>> cmdline_autotest

The final output of the test has to be "Test OK"
