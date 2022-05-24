.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

===============
Unit Tests: KNI
===============

This is the test plan for the Intel® DPDK KNI library.

This section explains how to run the unit tests for KNI. The test can be
launched independently using the command line interface.
This test is implemented as a linuxapp environment application.

The complete test suite is launched automatically using a python-expect
script (launched using ``make test``) that sends commands to
the application and checks the results. A test report is displayed on
stdout.

Case config::

   For enable KNI features, need to add "-Denable_kmods=True" when build DPDK by meson.
   CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static x86_64-native-linuxapp-gcc
   ninja -C x86_64-native-linuxapp-gcc -j 50

   rte_kni.ko is located at ./x86_64-native-linuxapp-gcc/kernel/linux/kni/

The steps to run the unit test manually are as follow::

  # mkdir -p x86_64-native-linuxapp-gcc/kmod
  # cp ./x86_64-native-linuxapp-gcc/kernel/linux/kni/rte_kni.ko x86_64-native-linuxapp-gcc/kmod/
  # cp ./x86_64-native-linuxapp-gcc/kernel/linux/igb_uio/igb_uio.ko x86_64-native-linuxapp-gcc/kmod/
  # lsmod | grep rte_kni
  # insmod ./<TARGET>/kmod/igb_uio.ko
  # insmod ./<TARGET>/kmod/rte_kni.ko lo_mode=lo_mode_fifo
  # ./x86_64-native-linuxapp-gcc/app/test/dpdk-test  -n 1 -c ffff
  RTE>> kni_autotest
  RTE>> quit
  # rmmod rte_kni
  # rmmod igb_uio


The final output of the test has to be "Test OK"
