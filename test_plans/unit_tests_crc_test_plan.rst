.. Copyright (c) <2017>, Intel Corporation
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

  # cd ~/dpdk
  # make config T=x86_64-native-linuxapp-gcc
  # make test
  # ./build/build/test/test/test -n 1 -c ffff
  RTE>> crc_autotest

The final output of the test will has to be "Test OK".

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
http://www.intel.com/content/dam/www/public/us/en/documents/white-papers
/fast-crc-computation-generic-polynomials-pclmulqdq-paper.pdf
[2] A PAINLESS GUIDE TO CRC ERROR DETECTION ALGORITHMS
http://www.ross.net/crc/download/crc_v3.txt
