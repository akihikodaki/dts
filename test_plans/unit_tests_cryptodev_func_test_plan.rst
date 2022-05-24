.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2016-2017 Intel Corporation

=====================
Unit Tests: Cryptodev
=====================


Description
===========

This document provides the plan for testing Cryptodev API via Cryptodev unit tests.
Unit tests include supported Hardware and Software PMD(polling mode device) and supported algorithms.
Cryptodev API provides ability to do encryption/decryption by integrating QAT(Intel@ QuickAssist
Technology) into DPDK. The QAT provides poll mode crypto driver support for
Intel@ QuickAssist Adapter 8950 hardware accelerator.

The testing of Crytpodev API should be tested under either Intel QuickAssist Technology DH895xxC hardware
accelerator or AES-NI library.

This test suite will run all cryptodev related unit test cases. Alternatively, you could execute
the unit tests manually by app/test DPDK application.

Unit Test List
==============

- cryptodev_qat_autotest
- cryptodev_aesni_mb_autotest
- cryptodev_openssl_autotest
- cryptodev_aesni_gcm_autotest
- cryptodev_null_autotest
- cryptodev_sw_snow3g_autotest
- cryptodev_sw_kasumi_autotest
- cryptodev_sw_zuc_autotest
- cryptodev_scheduler_autotest


Test Case Setup
===============

#. Build DPDK and app/test app
    CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

#. Bind cryptodev devices to vfio-pci driver when test cryptodev_qat_autotest
   ./dpdk/usertools/dpdk-devbind.py --status-dev crypto
   ./dpdk/usertools/dpdk-devbind.py --force --bind=vfio-pci 000:1a:01.0

#. Manually verify the app/test by this command, as example, in your build folder::

     ./x86_64-native-linuxapp-gcc/app/test/dpdk-test -c 1 -n 1
     RTE>> cryptodev_qat_autotest

All Unit Test Cases are listed above.

Expected all tests could pass in testing.
