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

======================
QoS Scheduler Tests
======================

The QoS Scheduler results are produced using ''qos_sched'' application.
The application has a number of command line options::

    ./qos_sched [EAL options] -- <APP PARAMS>

Mandatory application parameters include:
-pfc “RX PORT, TX PORT, RX LCORE, WT LCORE, TX CORE”: Packet flow configuration.
Multiple pfc entities can be configured in the command line,
having 4 or 5 items (if TX core defined or not).

The profile configuration file "profile.cfg" defines
all the port/subport/pipe/traffic class/queue parameters
needed for the QoS scheduler configuration.

The Port/Subport/Pipe/Traffic Class/Queue are the hierarchical entities
in a typical QoS application:

1. A subport represents a predefined group of users.

2. A pipe represents an individual user/subscriber.

3. A traffic class is the representation of a different traffic type
   with a specific loss rate, delay and jitter requirements;
   such as data voice, video or data transfers.

4. A queue hosts packets from one or multiple connections of the same type
   belonging to the same user.

The detailed description of the application items and mode can be found in
https://doc.dpdk.org/guides/sample_app_ug/qos_scheduler.html

Prerequisites
=============
The DUT must have four 10G Ethernet ports connected to four ports on
Tester that are controlled by the Scapy packet generator::

    dut_port_0 <---> tester_port_0
    dut_port_1 <---> tester_port_1
    dut_port_2 <---> tester_port_2
    dut_port_3 <---> tester_port_3

Or use IXIA as packet generator.

Assume four DUT 10G Ethernet ports' pci device id is as the following::

    dut_port_0 : "0000:05:00.0"
    dut_port_1 : "0000:05:00.1"
    dut_port_2 : "0000:05:00.2"
    dut_port_3 : "0000:05:00.3"

1. Compile DPDK and sample with defining::

    CONFIG_RTE_SCHED_COLLECT_STATS=y

2. Bind four ports to dpdk igb_uio driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0 05:00.1 05:00:2 05:00.3

Test Case: single packet flow
=============================
1. This example uses a single packet flow configuration
   which creates one RX thread on lcore 5 reading from port 3
   and a worker thread on lcore 7 writing to port 2::

    ./qos_sched -l 1,5,7 -n 4 -- --pfc "3,2,5,7" --cfg ../profile.cfg

2. Set flows with different vlan ID, which represent different pipes.
   Each Rx flow is shaping to 1/4096 of Tx flow.
   Set flows with different Destination IP address (0.0.X.0),
   such as 100.0.1.0-100.0.4.0, which represent different tc.
   Check the Rx/Tx Bps too.

Test Case: two packet flows
===========================
1. This example with two packet flow configurations using different ports
   but sharing the same core for QoS scheduler is given below::

    ./qos_sched -l 1,2,6,7 -n 4 -- --pfc "3,2,2,6,7" --pfc "1,0,2,6,7" --cfg ../profile.cfg

2. Set flows to port 3 and port 1 with different vlan ID.
   Each Rx flow is shaping to 1/4096 of Tx flow.
   Set flows with different Destination IP address (0.0.X.0),
   such as 100.0.1.0-100.0.4.0, which represent different tc.
   Check the Rx/Tx Bps too.

Note that independent cores for the packet flow configurations
for each of the RX, WT and TX thread are also supported,
providing flexibility to balance the work.
The EAL coremask/corelist is constrained to contain
the default mastercore 1 and the RX, WT and TX cores only.
