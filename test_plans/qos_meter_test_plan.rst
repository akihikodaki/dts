.. Copyright (c) <2011-2019>, Intel Corporation
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

==================
QoS Metering Tests
==================
The QoS meter sample application is an example that demonstrates the use of
DPDK to provide QoS marking and metering, as defined by RFC2697 for Single
Rate Three Color Marker (srTCM) and RFC 2698 for Two Rate Three Color
Marker (trTCM) algorithm.

The detailed description of the application items and mode can be found in
https://doc.dpdk.org/guides/sample_app_ug/qos_metering.html

Prerequisites
=============
The DUT must have two 10G Ethernet ports connected to two ports of IXIA.

Assume two DUT 10G Ethernet ports' pci device id is as the following,

dut_port_0 : "0000:05:00.0"
dut_port_1 : "0000:05:00.1"

1. Compile DPDK and sample

2. Bind two ports to dpdk igb_uio driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0 05:00.1

3. The default metering mode is::

    APP_MODE_SRTCM_COLOR_BLIND

Test Case: srTCM blind
======================
1. The application is constrained to use a single core in the EAL core mask
   and 2 ports only in the application port mask (first port from the port
   mask is used for RX and the other port in the core mask is used for TX)::

    ./build/qos_meter -c 1 -n 4 -- -p 0x3

2. Assuming the input traffic is generated at line rate and all packets
   are 64 bytes Ethernet frames (IPv4 packet size of 46 bytes) and green,
   the expected output traffic should be marked as shown in the following
   table:

   +-------------+--------------+---------------+------------+
   |     Mode    | Green (Mpps) | Yellow (Mpps) | Red (Mpps) |
   +-------------+--------------+---------------+------------+
   | srTCM blind | 1            | 1             | 12.88      |
   +-------------+------------------------------+------------+
   | srTCM color | 1            | 1             | 12.88      |
   +-------------+------------------------------+------------+
   | trTCM blind | 1            | 0.5           | 13.38      |
   +-------------+------------------------------+------------+
   | trTCM color | 1            | 0.5           | 13.38      |
   +-------------+------------------------------+------------+
   |     FWD     | 14.88        | 0             | 0          |
   +-------------+------------------------------+------------+

3. Use the default setting, the packets are 64 bytes Ethernet frames,
   and the metering mode is srTCM blind.
   The green packets are dropped.
   So the valid frames received on the peer IXIA port is 13.88(Mpps).
