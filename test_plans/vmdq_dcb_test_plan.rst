.. Copyright (c) < 2019 >, Intel Corporation
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

===================================================================
Fortville: Support of RX Packet Filtering using VMDQ & DCB Features
===================================================================

The Intel Network Interface Card(e.g. XL710), supports a number of
packet filtering functions which can be used to distribute incoming packets
into a number of reception (RX) queues. VMDQ & DCB is a pair of such filtering
functions which operate on VLAN-tagged packets to distribute those packets
to RX queues.

The feature itself works by:

- splitting the incoming packets up into different "pools" - each with its own
  set of RX queues - based upon the VLAN ID within the VLAN tag of the packet.
- assigning each packet to a specific queue within the pool, based upon the
  user priority field within the VLAN tag.

The VMDQ & DCB features are enabled in the ``vmdq_dcb`` example application
contained in the DPDK, and this application should be used to validate
the feature.

Prerequisites
=============

- The DPDK is compiled for the appropriate target type in each case, and
  the VMDQ & DCB example application is compiled and linked with that DPDK
  instance
- Two ports are connected to the test system, one to be used for packet reception,
  the other for transmission
- The traffic generator being used is configured to send to the application RX
  port a stream of packets with VLAN tags, where the VLAN IDs increment from 0
  to the pools numbers(inclusive) and the VLAN user priority field increments from
  0 to 7 (inclusive) for each VLAN ID.
- Build vmdq_dcb example,
    make: make -C examples/vmdq_dcb RTE_SDK=`pwd` T=x86_64-native-linuxapp-gcc
    meson: ./<build_target>/examples/dpdk-vmdq_dcb -c 0xff -n 4 -- -p 0x3 --nb-pools 32 --nb-tcs 4 --enable-rss

Test Case 1: Verify VMDQ & DCB with 32 Pools and 4 TCs
======================================================

1. Run the application as the following::

    make: ./examples/vmdq_dcb/build/vmdq_dcb_app -c 0xff -n 4 -- -p 0x3 --nb-pools 32 --nb-tcs 4 --enable-rss
    meson: ./<build_target>/examples/dpdk-vmdq_dcb -c 0xff -n 4 -- -p 0x3 --nb-pools 32 --nb-tcs 4 --enable-rss

2. Start traffic transmission using approx 10% of line rate.
3. After a number of seconds, e.g. 15, stop traffic, and ensure no traffic
   loss (<0.001%) has occurred.
4. Send a hangup signal (SIGHUP) to the application to have it print out the
   statistics of how many packets were received per RX queue::

     kill -s SIGHUP  `pgrep -fl vmdq_dcb_app | awk '{print $1}'`

Expected Result:

- No packet loss is expected.
- Every RX queue should have received approximately (+/-15%) the same number of
  incoming packets
- verify queue id should be equal "vlan user priority value % 4".

Test Case 2: Verify VMDQ & DCB with 16 Pools and 8 TCs
======================================================

1. change CONFIG_RTE_LIBRTE_I40E_QUEUE_NUM_PER_VM to 8 in "./config/common_linuxapp", rebuild DPDK.
    meson: change "#define RTE_LIBRTE_I40E_QUEUE_NUM_PER_VM 4" to 8 in config/rte_config.h, rebuild DPDK.

2. Repeat Test Case 1, with `--nb-pools 16` and `--nb-tcs 8` of the sample application::

    make: ./examples/vmdq_dcb/build/vmdq_dcb_app -c 0xff -n 4 -- -p 0x3 --nb-pools 16 --nb-tcs 8 --enable-rss
    meson: ./<build_target>/examples/dpdk-vmdq_dcb -c 0xff -n 4 -- -p 0x3 --nb-pools 16 --nb-tcs 8 --enable-rss

Expected result:
- No packet loss is expected
- Every RX queue should have received approximately (+/-15%) the same number of incoming packets
- verify queue should be equal "vlan user priority value"

3. change CONFIG_RTE_LIBRTE_I40E_QUEUE_NUM_PER_VM to 16 in "./config/common_linuxapp", rebuild DPDK.
    meson: change "#define RTE_LIBRTE_I40E_QUEUE_NUM_PER_VM 4" to 16 in config/rte_config.h, rebuild DPDK.

4. Repeat Test Case 1, with `--nb-pools 16` and `--nb-tcs 8` of the sample application::

    make: ./examples/vmdq_dcb/build/vmdq_dcb_app -c 0xff -n 4 -- -p 0x3 --nb-pools 16 --nb-tcs 8 --enable-rss
    meson: ./<build_target>/examples/dpdk-vmdq_dcb -c 0xff -n 4 -- -p 0x3 --nb-pools 16 --nb-tcs 8 --enable-rss

Expected result:
- No packet loss is expected
- Every RX queue should have received approximately (+/-15%) the same number of incoming packets
- verify queue id should be in [vlan user priority value * 2, vlan user priority value * 2 + 1]

(NOTE: SIGHUP output will obviously change to show 8 columns per row, with only 16 rows)