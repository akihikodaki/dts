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
CompressDev ZLIB PMD Tests
=============================

Description
-------------------
The ZLIB PMD (librte_pmd_zlib) provides poll mode compression & decompression
driver based on SW zlib library.

The supported Compression/Decompression algorithm:

    DEFLATE - using Fixed and Dynamic Huffman encoding

For more details, please reference to dpdk online programming guide.

Prerequisites
----------------------
In order to enable this virtual compression PMD, user must:

    Set CONFIG_RTE_LIBRTE_PMD_ZLIB=y in config/common_base.

and enable compressdev unit test:

    Set CONFIG_RTE_COMPRESSDEV_TEST=y in config/common_base.

A compress performance test app is added into DPDK to test CompressDev.

Calgary corpus is a collection of text and binary data files, commonly used
for comparing data compression algorithms.

Test Case: Compressdev ZLIB PMD Unit test
----------------------------------------------------------------
Start test application and run zlib pmd unit test::

    ./app/test -l1 -n1 -a vdev_bus_id --vdev=compress_zlib
    RTE>>compressdev_autotest

Verify all test cases passed in the test.

Test Case: Compressdev ZLIB PMD fixed function test
-------------------------------------------------------------
Run Compressdev zlib pmd test with below sample commands::

    ./app/dpdk-test-compress-perf  -a vdev_bus_id -l 4 \
    --vdev=compress_zlib -- --driver-name compress_zlib --input-file file_name \
    --compress-level level --num-iter number --huffman-enc fixed

Perform the test with fixed huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev ZLIB PMD dynamic function test
-------------------------------------------------------------
Run Compressdev zlib pmd test with below sample commands::

    ./app/dpdk-test-compress-perf  -a vdev_bus_id -l 4 \
    --vdev=compress_zlib -- --driver-name compress_zlib --input-file file_name \
    --compress-level level --num-iter number --huffman-enc dynamic

Perform the test with dynamic huffman-enc.

Test all the file types in calgary corpus, all files should pass the test.

Test Case: Compressdev ZLIB PMD fixed performance test
----------------------------------------------------------------------------
Run Compressdev zlib pmd performance test with below sample commands::

    ./app/dpdk-test-compress-perf  -a vdev_bus_id -l 4 \
    --vdev=compress_zlib -- --driver-name compress_zlib --input-file file_name \
    --compress-level level --seg-sz size --num-iter number --huffman-enc fixed

Perform the test with fixed huffman-enc and calgary file.

Run the test with seg-sz 1k, 2k, 4k, 8k, 16k and 32k respectively.

Test Case: Compressdev ZLIB PMD dynamic performance test
---------------------------------------------------------------------------
Run Compressdev zlib pmd performance test with below sample commands::

    ./app/dpdk-test-compress-perf  -a vdev_bus_id -l 4 \
    --vdev=compress_zlib -- --driver-name compress_zlib --input-file file_name \
    --compress-level level --seg-sz size --num-iter number --huffman-enc dynamic

Perform the test with dynamic huffman-enc and calgary file.

Run the test with seg-sz 1k, 2k, 4k, 8k, 16k and 32k respectively.
