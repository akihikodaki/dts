.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2014-2017 Intel Corporation

====================
Unit Tests: Ring Pmd
====================

This is the test plan for the Intel® DPDK Ring poll mode driver feature.

This section explains how to run the unit tests for ring pmd. The test can be
launched independently using the command line interface.
This test is implemented as a linuxapp environment application and config
RTE_LIBRTE_PMD_RING should be modified to 'Y'.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

Ring pmd unit test required two pair of virtual ethernet devices and one
virtual ethernet devices with full rx&tx functions.

The steps to run the unit test manually are as follow::

  Build dpdk
  # cd dpdk
  # CC=gcc meson --werror -Denable_kmods=True  -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
  # ninja -C x86_64-native-linuxapp-gcc -j 50

  # ./x86_64-native-linuxapp-gcc/app/test/dpdk-test -n 1 -c ffff --vdev='net_ring0'
      --vdev='net_ring1'
  RTE>> ring_pmd_autotest

The final output of the test has to be "Test OK"
