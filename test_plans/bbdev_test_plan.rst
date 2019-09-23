.. Copyright (c) <2018>, Intel Corporation
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

=============================================================
Wireless device for ICX-D (bbdev) for Turbo decoding/encoding
=============================================================
Description
===========

   The Wireless Baseband library provides a common programming framework that
   abstracts HW accelerators based on FPGA and/or Fixed Function Accelerators
   that assist with 3gpp Physical Layer processing. Furthermore, it decouples
   the application from the compute-intensive wireless functions by abstracting
   their optimized libraries to appear as virtual bbdev devices.
   The functional scope of the BBDEV library are those functions in relation to
   the 3gpp Layer 1 signal processing (channel coding, modulation, ...).
   The framework currently only supports Turbo Code FEC function.
   The Wireless Baseband library follows the same ideology of DPDK's Ethernet
   Device and Crypto Device frameworks. Wireless Baseband provides a generic
   acceleration abstraction framework which supports both physical (hardware)
   and virtual (software) wireless acceleration functions.

   Physical bbdev devices are discovered during the PCI probe/enumeration of
   the EAL function which is executed at DPDK initialization, based on
   their PCI device identifier, each unique PCI BDF (bus/bridge, device,
   function).
   Virtual devices can be created by two mechanisms, either using the EAL
   command line options or from within the application using an EAL API
   directly.
   so it is required to perform validation of the framework divided into
   2 stages:
   Stage 1: Validation of the SW-only solution (turbo_sw)
   Stage 2: Validation of the HW-accelerated solution (ICX-D TIP) on an ICX-D
   platform.
   We now only support stage 1.

Prerequisites
=============

1. OS and Hardware

   (a) An AVX2 supporting machine
   (b) Windriver TS 2 or CentOS 7 operating systems
       (Fedora 25 and Ubuntu 16.04 is ok.)
   (c) Intel ICC compiler installed

2. FlexRAN SDK Libraries

   To build DPDK with the *turbo_sw* PMD the user is required to download
   the export controlled ``FlexRAN SDK`` Libraries.
   An account at Intel Resource Design Center needs to be registered from
   https://www.intel.com/content/www/us/en/design/resource-design-center.html
   Direct download link from Intel RDC ->
   https://cdrd.intel.com/v1/dl/getContent/575367
   After download is complete, the user needs to unpack and compile on their
   system before building DPDK.
   You can refer to the file dpdk/doc/guides/bbdevs/turbo_sw.rst.

3. PMD setting

   Current BBDEV framework is en-suited with two vdev PMD drivers:
   null and turbo_sw.
   1) Null PMD is similar to cryptodev Null PMD, which is an empty driver to
   measure the overhead added by the framework.
   2) Turbo_sw is a sw-only driver wrapper for FlexRAN SDK optimized Turbo
   coding libraries.
   It can be enabled by setting

   ``CONFIG_RTE_LIBRTE_PMD_BBDEV_TURBO_SW=y``

   The offload cases can be enabled by setting

   ``CONFIG_RTE_BBDEV_OFFLOAD_COST=y``

   They are both located in the build configuration file ``common_base``.

4. Test tool

   A test suite for BBDEV is packaged with the framework to ease the
   validation needs for various functions and use cases.
   The tool to use for validation and testing is called: test-bbdev,
   that is packaged with test vectors that are ready-to-use.
   Test-bbdev tool is located at this location:
   app/test-bbdev/
   The command-line options you can refer to:
   dpdk/doc/guides/tools/testbbdev.rst


Test case 1: bbdev null device
==============================

Executing bbdev null device with *bbdev_null.data* helps in measuring
the overhead introduced by the bbdev framework::

    ./test-bbdev.py -e="--vdev=baseband_null0"
    -v ./test_vectors/bbdev_null.data

bbdev_null device does not have to be defined explicitly as it is created
by default. so the command-line can be written as::

    ./test-bbdev.py -v ./test_vectors/bbdev_null.data

The case only cover unittest, all the other cases are skipped.
The "bbdev_null.data" can be omitted::

    ./test-bbdev.py

or you can define the specific test defined::

    ./test-bbdev.py -c validation

or::

    ./test-bbdev.py -v test_vectors/bbdev_null.data

All above test cases run with "--vdev=baseband_null0".

Test case 2: Turbo encoding validation
======================================

It runs **validation** test for Turbo encode vector file
Number of operations to process on device is set to 64
and operations timeout is set to 120s
and enqueue/dequeue burst size is set to 8 and to 32.
Moreover a bbdev (*turbo_sw*) device will be created::

    ./test-bbdev.py -p ../../x86_64-native-linuxapp-icc/app/testbbdev \
    -e="--vdev=baseband_turbo_sw" -t 120 -c validation \
    -v ./test_vectors/turbo_enc_c1_k40_r0_e1196_rm.data -n 64 -b 8 32

you can check the result from the detailed printing, and compare
the two results from different burst size.

Test case 3: Turbo decoding validation
======================================

It runs **validation** test for Turbo decode vector file
we use default options::

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" -c validation \
    -v ./test_vectors/turbo_dec_*

you can check the result from the detailed printing.

Test case 4: Turbo encoding latency
===================================

It runs **latency** test for Turbo encode vector file::

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" -c latency \
    -v ./test_vectors/turbo_enc_c1_k40_r0_e1196_rm.data -n 512 -b 64 512

Test calculates three latency metrics:
1) offload_latency_tc
2) offload_latency_empty_q_tc
3) operation_latency_tc
You can compare the three latency from different burst size.

Test case 5: Turbo decoding latency
===================================

It runs **latency** test for Turbo decode vector file::

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" -c latency \
    -v ./test_vectors/turbo_dec_c1_k40_r0_e17280_sbd_negllr.data -n 512 -b 64

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" -c latency \
    -v ./test_vectors/turbo_dec_c1_k40_r0_e17280_sbd_negllr.data -n 128 -b 64

You can compare the three latency from different number of operations.

Test case 6: Turbo encoding throughput
======================================

It runs **throughput** test for Turbo encode vector file::

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" -c throughput \
    -v ./test_vectors/turbo_enc_c1_k40_r0_e1196_rm.data -n 64 -l 16 -b 64

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" -c throughput \
    -v ./test_vectors/turbo_enc_c1_k40_r0_e1196_rm.data -n 64 -l 8 -b 64

You can compare the turbo encode throughput from different number of lcores.
then different burst size::

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" -c throughput \
    -v ./test_vectors/turbo_enc_c1_k40_r0_e1196_rm.data -n 64 -l 16 -b 64

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" -c throughput \
    -v ./test_vectors/turbo_enc_c1_k40_r0_e1196_rm.data -n 64 -l 16 -b 32

You can compare the turbo encode throughput from different burst size.
then different number of operations::

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" -c throughput \
    -v ./test_vectors/turbo_enc_c1_k40_r0_e1196_rm.data -n 64 -l 16 -b 32

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" -c throughput \
    -v ./test_vectors/turbo_enc_c1_k40_r0_e1196_rm.data -n 32 -l 16 -b 32

You can compare the turbo encode throughput from different number of
operations.

Test case 7: Turbo decoding throughput
======================================

It runs **throughput** test for Turbo decode vector file.
you can run the three subcases of test case 6 which just needed to
change the test vector file to decode data file, and
compare the results.

Test case 8: Turbo encoding and decoding offload and latency
============================================================

It runs **offload ** and **latency** test for Turbo encode vector file::

    ./test-bbdev.py -p ../../x86_64-native-linuxapp-icc/app/testbbdev \
    -e="--vdev=baseband_turbo_sw" -t 120 -c offload latency \
    -v ./test_vectors/turbo_enc_c1_k40_r0_e1196_rm.data \
    ./test_vectors/turbo_dec_c1_k40_r0_e17280_sbd_negllr.data -n 64 -l 16 -b 8 32

Compare the results.

Test case 9: Scrum all tests and all vector files
=================================================

It runs all tests and all vector files::

    ./test-bbdev.py -e="--vdev=baseband_turbo_sw" \
    -v ./test_vectors/turbo_enc_c1_k40_r0_e1196_rm.data

Then go through all the .date files.
