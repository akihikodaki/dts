.. Copyright (c) <2019>, Intel Corporation
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   - Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.

   - Neither the name of Intel Corporation nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.

=============================
CompressDev QAT PMD Tests
=============================

Description
-------------------
The QAT compression PMD provides poll mode compression & decompression
driver support for the following hardware accelerator devices:

    Intel QuickAssist Technology C62x

    Intel QuickAssist Technology C3xxx

    Intel QuickAssist Technology DH895x

The supported Compression/Decompression algorithm:

    DEFLATE - using Fixed and Dynamic Huffman encoding

For more details, please reference to dpdk online programming guide.
http://doc.dpdk.org/guides/compressdevs/qat_comp.html

Prerequisites
----------------------
Intel QAT devices should be available in the platform.
The QAT compression PMD is built by default with a standard DPDK build
It depends on a QAT kernel driver.

A compress performance test app is added into DPDK to test CompressDev.

Calgary corpus is a collection of text and binary data files,commonly used
for comparing data compression algorithms.

Software
--------

dpdk: http://dpdk.org/git/dpdk
Intel QuickAssist Technology Driver: https://01.org/packet-processing/intel%C2%AE-quickassist-technology-drivers-and-patches

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

Test Case: Compressdev QAT PMD Unit test
----------------------------------------------------------------
Start test application and run qat pmd unit test::

    ./x86_64-native-linuxapp-gcc/app/test/dpdk-test -l1 -n1 -a qat_device_bus_id --log-level=qat:8
    RTE>>compressdev_autotest

Verify all test cases passed in the test.

Test Case: Compressdev QAT PMD fixed function test
----------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name \
    --compress-level level --num-iter number --huffman-enc fixed

Perform the test with fixed huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev QAT PMD dynamic function test
-----------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name \
    --compress-level level --num-iter number --huffman-enc dynamic

Perform the test with dynamic huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev QAT PMD big sgl fixed function test
--------------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name --seg-sz segsize \
    --compress-level level --num-iter number --extended-input-sz size \
    --max-num-sgl-segs seg --huffman-enc fixed

Perform the test with big max-num-sgl-segs and fixed huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev QAT PMD big sgl dynamic function test
--------------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name --seg-sz segsize \
    --compress-level level --num-iter number --extended-input-sz size \
    --max-num-sgl-segs seg --huffman-enc dynamic

Perform the test with big max-num-sgl-segs and dynamic huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev QAT PMD big seg-sz fixed function test
--------------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name --seg-sz segsize \
    --compress-level level --num-iter number --extended-input-sz size \
    --max-num-sgl-segs seg --huffman-enc fixed

Perform the test with big seg-sz and fixed huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev QAT PMD big seg-sz dynamic function test
---------------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name --seg-sz segsize \
    --compress-level level --num-iter number --extended-input-sz size \
    --max-num-sgl-segs seg --huffman-enc dynamic

Perform the test with big seg-sz and dynamic huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev QAT PMD external mbufs fixed function test
-------------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name \
    --compress-level level --num-iter number --external-mbufs \
    --huffman-enc fixed

Perform the test with external-mbufs option and fixed huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev QAT PMD external mbufs dynamic function test
--------------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name \
    --compress-level level --num-iter number --external-mbufs \
    --huffman-enc dynamic

Perform the test with external-mbufs option and dynamic huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev QAT PMD im buffer split op fixed function test
-------------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name \
    --compress-level level --num-iter number --seg-sz segsize \
    --max-num-sgl-segs seg --extended-input-sz size \
    --huffman-enc fixed

Perform the test with extended-input-sz, max-num-sgl-segs option and fixed huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev QAT PMD im buffer split op dynamic function test
--------------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name \
    --compress-level level --num-iter number --seg-sz segsize \
    --max-num-sgl-segs seg --extended-input-sz size \
    --huffman-enc dynamic

Perform the test with extended-input-sz, max-num-sgl-segs option and dynamic huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev QAT PMD fixed performance test
--------------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name \
    --compress-level level --num-iter number --huffman-enc fixed

Perform the test with fixed huffman-enc and calgary file.

Run the test with seg-sz 1k, 2k, 4k, 8k, 16k and 32k respectively.

Test Case: Compressdev QAT PMD dynamic performance test
---------------------------------------------------------------------------
Run Compressdev qat pmd test with below sample commands::

    ./x86_64-native-linuxapp-gcc/app/dpdk-test-compress-perf  -a qat_device_bus_id -l 4 \
    -- --driver-name compress_qat --input-file file_name \
    --compress-level level --num-iter number --huffman-enc dynamic

Perform the test with dynamic huffman-enc and calgary file.

Run the test with seg-sz 1k, 2k, 4k, 8k, 16k and 32k respectively.
