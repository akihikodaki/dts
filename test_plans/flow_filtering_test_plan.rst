.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2011-2019 Intel Corporation

====================
Flow Filtering Tests
====================

The Basic RTE flow filtering sample application is a simple example
of a creating a RTE flow rule. It is intended as a demonstration
of the basic components RTE flow rules.
The Flow Filtering results are produced using ''flow'' application::

    ./dpdk-flow_filtering -l 1 -n 1

There is a flow rule defined in the sample code.
You can check the detailed information of the flow rule from
http://doc.dpdk.org/guides/sample_app_ug/flow_filtering.html

The matching item is dst IP address: "192.168.1.1".
The match action is entering the queue 1.
IGB not support flow example.
ICE support flow example.

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

    ./dpdk-flow_filtering -l 1 -n 1

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

    ./dpdk-flow_filtering -l 1 -n 1

2. Send packet which dismatches the defined rule from tester::

    Pkt1 = Ether(dst="00:00:00:00:01:00")/IP(src="0.0.0.0", dst="192.168.1.2") \
    /Raw("x"*20)

3. Check the packet is not received by queue 1::

    src=A4:BF:01:07:47:C8 - dst=00:00:00:00:01:00 - queue=0x0
