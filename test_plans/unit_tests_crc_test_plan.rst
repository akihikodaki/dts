.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2017 Intel Corporation

===============
Unit Tests: CRC
===============

the unit test compare the results of scalar and sse4.2 versions individually
with the known crc results. Some of these crc results and corresponding test
vectors are based on the test string mentioned in ethernet specification doc
and x.25 doc

This section explains how to run the unit tests for crc computation. The test
can be launched independently using the command line interface.
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
  RTE>> crc_autotest

The final output of the test will have to be "Test OK".

Algorithm Description
=====================

In some applications, CRC (Cyclic Redundancy Check) needs to be computed
or updated during packet processing operations. This patchset adds software
implementation of some common standard CRCs (32-bit Ethernet CRC as per
Ethernet/[ISO/IEC 8802-3] and 16-bit CCITT-CRC [ITU-T X.25]).
Two versions of each 32-bit and 16-bit CRC calculation are proposed.

The first version presents a fast and efficient CRC generation on
IA processors by using the carry-less multiplication instruction PCLMULQDQ
(i.e SSE4.2 intrinsics). In this implementation, a parallelized folding
approach has been used to first reduce an arbitrary length buffer to a small
fixed size length buffer (16 bytes) with the help of precomputed constants.
The resultant single 16-bytes chunk is further reduced by Barrett reduction
method to generate final CRC value. For more details on the implementation,
see reference [1].

The second version presents the fallback solution to support the
CRC generation without needing any specific support from CPU (for examples-
SSE4.2 intrinsics). It is based on generic Look-Up Table(LUT) algorithm
that uses precomputed 256 element table as explained in reference[2].

During initialization, all the data structures required for CRC computation
are initialized. Also, x86 specific crc implementation
(if supported by the platform) or scalar version is enabled.

References:
[1] Fast CRC Computation for Generic Polynomials Using PCLMULQDQ Instruction
http://www.intel.com/content/dam/www/public/us/en/documents/allow-papers
/fast-crc-computation-generic-polynomials-pclmulqdq-paper.pdf
[2] A PAINLESS GUIDE TO CRC ERROR DETECTION ALGORITHMS
http://www.ross.net/crc/download/crc_v3.txt
