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

===============================================================
Sample Application Tests: Basic Forwarding/Skeleton Application
===============================================================

The Basic Forwarding sample application is a simple *skeleton* example of a
forwarding application.

It is intended as a demonstration of the basic components of a DPDK forwarding
application. For more detailed implementations see the L2 and L3 forwarding
sample applications.

Build DPDK and example skeleton
===============================

    cd dpdk
    CC=gcc meson --werror -Denable_kmods=True  -Dlibdir=lib --default-library=static x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc -j 50

    meson configure -Dexamples=skeleton x86_64-native-linuxapp-gcc
    ninja -C x86_64-native-linuxapp-gcc

Running the Application
=======================

To run the example in a linux environment::

    ./build/examples/dpdk-skeleton -c 2 -n 4

Refer to *DPDK Getting Started Guide* for general information on running
applications and the Environment Abstraction Layer (EAL) options.

Test case: skeleton
====================

Running::

     ./x86_64-native-linuxapp-gcc/examples/dpdk-skeleton  /build/basicfwd -c 2 -n 4

waked up::

     Core X forwarding packets.

Send one packet from port0, check the received packet on port1.
It should receive the packet sent from port0.
