.. Copyright (c) <2016-2017>, Intel Corporation
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
