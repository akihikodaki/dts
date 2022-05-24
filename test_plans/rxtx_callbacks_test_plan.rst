.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2016-2017 Intel Corporation

=========================================
Sample Application Tests: RX/TX Callbacks
=========================================

The RX/TX Callbacks sample application is a packet forwarding application that
demonstrates the use of user defined callbacks on received and transmitted
packets. The application performs a simple latency check, using callbacks, to
determine the time packets spend within the application.

In the sample application a user defined callback is applied to all received
packets to add a timestamp. A separate callback is applied to all packets
prior to transmission to calculate the elapsed time, in CPU cycles.

Running the Application
=======================

Build dpdk and examples=rxtx_callbacks:
   CC=gcc meson -Denable_kmods=True -Dlibdir=lib  --default-library=static <build_target>
   ninja -C <build_target>

   meson configure -Dexamples=rxtx_callbacks <build_target>
   ninja -C <build_target>

To run the example in a ``linuxapp`` environment::

    ./<build_target>/examples/dpdk-rxtx_callbacks -c 2 -n 4

Refer to *DPDK Getting Started Guide* for general information on running
applications and the Environment Abstraction Layer (EAL) options.

Test Case:rxtx callbacks
==========================

Run the example::

     ./<build_target>/examples/dpdk-rxtx_callbacks -c 2 -n 4

waked up:::

     Core X forwarding packets.

Send one packet from port0,check the received packet on port1.
Should receive the packet sent from port0.
