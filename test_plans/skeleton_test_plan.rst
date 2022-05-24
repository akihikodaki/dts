.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

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
