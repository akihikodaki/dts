.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

=============================
CompressDev ISA-L PMD Tests
=============================

Description
-------------------
The ISA-L PMD (librte_pmd_isal_comp) provides poll mode compression &
decompression driver support for utilizing Intel ISA-L library, which implements
the deflate algorithm for both Deflate(compression) and Inflate(decompression).

The supported Compression/Decompression algorithm:

    DEFLATE - using Fixed and Dynamic Huffman encoding

For more details, please reference to dpdk online programming guide.
http://doc.dpdk.org/guides/compressdevs/isal.html

Prerequisites
----------------------

A compress performance test app is added into DPDK to test CompressDev.
RTE_COMPRESS_ISAL and RTE_LIB_COMPRESSDEV is enabled by default in meson  build.
Calgary corpus is a collection of text and binary data files, commonly used
for comparing data compression algorithms.

Software
--------

dpdk: http://dpdk.org/git/dpdk
multi-buffer library: https://github.com/01org/intel-ipsec-mb
Intel QuickAssist Technology Driver: https://01.org/packet-processing/intel%C2%AE-quickassist-technology-drivers-and-patches
Intel’s ISA-L library: https://github.com/01org/isa-l

General set up
--------------
1, Compile DPDK::

    CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 110

2, Get the pci device id of QAT::

   ./dpdk/usertools/dpdk-devbind.py --status-dev crypto

3, Bind QAT VF port to dpdk::

   ./dpdk/usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:1a:01.0 0000:1a:01.1

Test case
=========

Test Case: Compressdev ISA-L PMD Unit test
----------------------------------------------------------------
Start test application and run isal pmd unit test::

    ./x86_64-native-linuxapp-gcc/app/test/dpdk-test -l1 -n1 -a vdev_bus_id --vdev=compress_isal
    RTE>>compressdev_autotest

Verify all test cases passed in the test.

Test Case: Compressdev ISA-L PMD fixed function test
---------------------------------------------------------
Run Compressdev isal pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a vdev_bus_id -l 4 \
    --vdev=compress_isal -- --driver-name compress_isal --input-file file_name \
    --compress-level level --num-iter number --huffman-enc fixed

Perform the test with fixed huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev ISA-L PMD dynamic function test
---------------------------------------------------------
Run Compressdev isal pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a vdev_bus_id -l 4 \
    --vdev=compress_isal -- --driver-name compress_isal --input-file file_name \
    --compress-level level --num-iter number --huffman-enc dynamic

Perform the test with dynamic huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev ISA-L PMD fixed performance test
-----------------------------------------------------------
Run Compressdev isal pmd performance test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a vdev_bus_id -l 4 \
    --vdev=compress_isal -- --driver-name compress_isal --input-file file_name \
    --compress-level level --seg-sz size --num-iter number --huffman-enc fixed

Perform the test with fixed huffman-enc and calgary file.

Run the test with seg-sz 1k, 2k, 4k, 8k, 16k and 32k respectively.

Test Case: Compressdev ISA-L PMD dynamic performance test
----------------------------------------------------------------
Run Compressdev isal pmd performance test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a vdev_bus_id -l 4 \
    --vdev=compress_isal -- --driver-name compress_isal --input-file file_name \
    --compress-level level --seg-sz size --num-iter number --huffman-enc dynamic

Perform the test with dynamic huffman-enc and calgary file.

Run the test with seg-sz 1k, 2k, 4k, 8k, 16k and 32k respectively.
