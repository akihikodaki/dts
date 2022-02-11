.. Copyright (c) <2022>, Intel Corporation
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