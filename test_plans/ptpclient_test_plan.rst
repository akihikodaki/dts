.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2017 Intel Corporation

==================================
Sample Application Tests: IEEE1588
==================================

The PTP (Precision Time Protocol) client sample application is a simple 
example of using the DPDK IEEE1588 API to communicate with a PTP master 
clock to synchronize the time on the NIC and, optionally, on the Linux 
system.

Prerequisites
=============
Assume one port is connected to the tester and "linuxptp.x86_64"
has been installed on the tester.

Case Config::

    Meson: For support IEEE1588, build DPDK with '-Dc_args=-DRTE_LIBRTE_IEEE1588'

The sample should be validated on Intel® Ethernet 700 Series, 82599 and i350 Nics.

Test case: ptp client
======================
Start ptp server on tester with IEEE 802.3 network transport::

    ptp4l -i p785p1 -2 -m

Start ptp client on DUT and wait few seconds::

    ./<build_target>/examples/dpdk-ptpclient -c f -n 3 -- -T 0 -p 0x1

Check that output message contained T1,T2,T3,T4 clock and time difference
between master and slave time is about 10us in 82599, 20us in Intel® Ethernet 700 Series,
8us in i350.
   
Test case: update system
========================
Reset DUT clock to initial time and make sure system time has been changed::

    date -s "1970-01-01 00:00:00"    

Strip DUT and tester board system time::

    date +"%s.%N"

Start ptp server on tester with IEEE 802.3 network transport::

    ptp4l -i p785p1 -2 -m -S

Start ptp client on DUT and wait few seconds::

    ./<build_target>/examples/dpdk-ptpclient -c f -n 3 -- -T 1 -p 0x1

Make sure DUT system time has been changed to same as tester.
Check that output message contained T1,T2,T3,T4 clock and time difference
between master and slave time is about 10us in 82599, 20us in Intel® Ethernet 700 Series,
8us in i350.
