.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2022 Intel Corporation

===========================
AddressSanitizer Smoke Test
===========================

Description
===========

AddressSanitizer (ASan) is a fast memory error detector,it is a widely-used debugging tool to detect memory access errors.

 - `AddressSanitizer<https://github.com/google/sanitizers/wiki/AddressSanitizer>`
 - It finds use-after-free, various kinds of buffer overruns in dpdk, and print out detailed debug information
   whenever an error is detected.
 - ASan is integrated with gcc and clang, and use meson option '-Db_sanitize=address' to enable.

Prerequisites
=============

1. NIC requires:

   - Intel ethernet cards: 82599/X710/XXV710/XL710/E810,etc

2. Software::

      dpdk: http://dpdk.org/git/dpdk.
      scapy: http://www.secdev.org/projects/scapy/

Test Case: RX/TX test with ASan enable
======================================

1. Build dpdk with ASan tool, add "-Dbuildtype=debug -Db_lundef=false -Db_sanitize=address"
   in meson build system could enable ASan tool, such as below::

      CC=gcc meson -Denable_kmods=True -Dlibdir=lib -Dbuildtype=debug -Db_lundef=false -Db_sanitize=address --default-library=static x86_64-native-linuxapp-gcc
      ninja -C x86_64-native-linuxapp-gcc -j 70

2. Bind NIC port to vfio-pci.

3. Setup testpmd, check testpmd could launch successfully and don't have "heap-buffer-overflow", "use-after-free" memory errors.

4. Set mac forward mode.

5. Send packet and check testpmd forward packet successfully.