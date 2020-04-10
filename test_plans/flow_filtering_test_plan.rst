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

====================
Flow Filtering Tests
====================

The Basic RTE flow filtering sample application is a simple example
of a creating a RTE flow rule. It is intended as a demonstration
of the basic components RTE flow rules.
The Flow Filtering results are produced using ''flow'' application::

    ./flow -l 1 -n 1

There is a flow rule defined in the sample code.
You can check the detailed information of the flow rule from
http://doc.dpdk.org/guides/sample_app_ug/flow_filtering.html

The matching item is dst IP address: "192.168.1.1".
The match action is entering the queue 1.
The flow example can specify fdir_mode by '--pkt-filter-mode',if not assign fdir_mode, IXGBE will not support flow example.
IGB not support flow example.

Prerequisites
=============
The DUT must have one 10G Ethernet ports connected to one port on
Tester that are controlled by packet generator::

    dut_port_0 <---> tester_port_0

Assume the DUT 10G Ethernet ports' pci device id is as the following::

    dut_port_0 : "0000:05:00.0"
    mac_address: "00:00:00:00:01:00"

Bind the port to dpdk igb_uio driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0

Test Case: match rule
=====================
1. Start the application with default settings::

    ./flow -l 1 -n 1

2. Send packets which matches the defined rule from tester::

    Pkt1 = Ether(dst="00:00:00:00:01:00")/IP(src="0.0.0.0", dst="192.168.1.1") \
    /Raw("x"*20)
    Pkt2 = Ether(dst="00:00:00:00:01:00")/IP(src="0.0.0.1", dst="192.168.1.1") \
    /Raw("x"*20)

3. Check the packets are received by queue 1::

    src=A4:BF:01:07:47:C8 - dst=00:00:00:00:01:00 - queue=0x1
    src=A4:BF:01:07:47:C8 - dst=00:00:00:00:01:00 - queue=0x1

Test Case: dismatch rule
========================
1. Start the application with default settings::

    ./flow -l 1 -n 1

2. Send packet which dismatches the defined rule from tester::

    Pkt1 = Ether(dst="00:00:00:00:01:00")/IP(src="0.0.0.0", dst="192.168.1.2") \
    /Raw("x"*20)

3. Check the packet is not received by queue 1::

    src=A4:BF:01:07:47:C8 - dst=00:00:00:00:01:00 - queue=0x0
