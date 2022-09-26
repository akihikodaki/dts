.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

==================
TestPMD PCAP Tests
==================

This document provides tests for the userland Intel(R) 82599
Gigabit Ethernet Controller Poll Mode Driver (PMD) when using
pcap files as input and output.

The core configurations description is:

- 2C/1T: 2 Physical Cores, 1 Logical Core per physical core
- 4C/1T: 4 Physical Cores, 1 Logical Core per physical core

Prerequisites
=============

The suit support NIC: Intel® Ethernet 700 Series, Intel® Ethernet 800 Series, 82599 and igc driver NIC.

This test does not requires connections between DUT and tester as it is focused
in PCAP devices created by Test PMD.

It is Test PMD application itself which send and receives traffic from and to
PCAP files, no traffic generator is involved.

Pcap PMD has a dependency to `libpcap` and `libpcap-devel` package needs to be
installed to be able to use pcap PMD.
When `libpcap-devel` is installed, meson automatically enables building pcap PMD.

Test Case: test_send_packets_with_one_device
============================================

It is necessary to generate the input pcap file for one interface test. The
pcap file can be created using scapy. Create a file with 1000 frames with the
following structure::

  Ether(src='00:00:00:00:00:<last Eth>', dst='00:00:00:00:00:00')/IP(src='192.168.1.1', dst='192.168.1.2')/("X"*26))

<last Eth> goes from 0 to 255 and repeats.

The linuxapp is started with the following parameters:

::

  -c 0xffffff -n 3 --vdev 'eth_pcap0;rx_pcap=in.pcap;tx_pcap=out.pcap' --
  -i --port-topology=chained


Start the application and the forwarding, by typing `start` in the command line
of the application. After a few seconds `stop` the forwarding and `quit` the
application.

Check that the frames of in.pcap and out.pcap files are the same using scapy.

Test Case: test_send_packets_with_two_devices
=============================================

Create 2 pcap files with 1000 and 500 frames as explained in
`test_send_packets_with_one_device` test case.

The linuxapp is started with the following parameters:

::

  -c 0xffffff -n 3 --vdev 'eth_pcap0;rx_pcap=in1.pcap;tx_pcap=out1.pcap,"eth_pcap1;rx_pcap=in2.pcap;tx_pcap=out2.pcap'
  -- -i


Start the application and the forwarding, by typing `start` in the command line
of the application. After a few seconds `stop` the forwarding and `quit` the
application.

Check that the frames of the in1.pcap and out2.pcap, and in2.pcap and out1.pcap
file are the same using scapy.
