.. Copyright (c) <2014-2017>, Intel Corporation
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

====================================
Unit Tests: single port MAC loopback
====================================

According to loopback mode, setup loopback link or not.
If loopback mode is setted, packets will be sent to rx_q from tx_q directly.
Else if loopback mode is disabled, packets will sent to peer port from tx_q.
Loopback mode can be used to support testing task.


Prerequisites
=============

Two 10Gb/25Gb/40Gb Ethernet ports of the DUT are directly connected and link is up.


single port MAC loopback
========================

This is the test plan for unit test to verify if X710/XL710/XXV710 can enable single port
mac loopback.

Test Case: enable loopback mode
===============================

In dpdk/test/test/test_pmd_perf.c
Set::

    .lpbk_mode=1
    #define MAX_TRAFFIC_BURST              32

Then make test
Start test::

    ./test/test/test -c f -n 4 -- -i
    RTE>>pmd_perf_autotest

The final output of the test will be matrix of average cycles of IO used per
packet, and "Test OK" is printed out.
The peer port can't receive any packet.

Test Case: disable lookback mode
================================

In dpdk/test/test/test_pmd_perf.c
Set::

    .lpbk_mode=0
    #define MAX_TRAFFIC_BURST              32

Then make test
Start test::

    ./test/test/test -c f -n 4 -- -i
    RTE>>pmd_perf_autotest

There is not "Test OK" presented.
The peer port can receive all the 32 packets.
