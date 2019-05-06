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

Prerequisites
----------------------
In order to enable this virtual compression PMD, user must:

    Set CONFIG_RTE_LIBRTE_PMD_ISAL=y in config/common_base.

A compress performance test app is added into DPDK to test CompressDev.

Calgary corpus is a collection of text and binary data files, commonly used
for comparing data compression algorithms.

Test Case: Compressdev ISA-L PMD Unit test
----------------------------------------------------------------
Start test application and run isal pmd unit test::

    ./app/test -l1 -n1 -w vdev_bus_id --vdev=compress_isal
    RTE>>compressdev_autotest

Verify all test cases passed in the test.

Test Case: Compressdev ISA-L PMD test
---------------------------------------------------------
Run Compressdev isal pmd test with below sample commands::

    ./app/dpdk-test-compress-perf  -w vdev_bus_id -l 4 \
    --vdev=compress_isal -- --driver-name compress_isal --input-file file_name \
    --compress-level level --num-iter number --huffman-enc fixed

Perform the test with huffman-enc fixed and dynamic accordingly.

Test all the file types in calgary corpus, all files should pass the test.
