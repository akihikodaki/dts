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
The DUT must have four 10G Ethernet ports connected to two ports on
Tester that are controlled by packet generator::

    dut_port_0 <---> tester_port_0
    dut_port_1 <---> tester_port_1

Assume two DUT 10G Ethernet ports' pci device id is as the following::

    dut_port_0 : "0000:05:00.0"
    dut_port_1 : "0000:05:00.1"

1. Compile DPDK and sample with defining::

    CONFIG_RTE_SCHED_COLLECT_STATS=y

2. Bind four ports to dpdk igb_uio driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0 05:00.1

Test Case: 1 pipe, 8 TCs
========================
1. This example uses a single packet flow configuration
   which creates one RX thread on lcore 5 reading from port 0
   and a worker thread on lcore 7 writing to port 1::

    ./qos_sched -l 1,5,7 -n 4 -- -i --pfc "0,1,5,7" --cfg ../profile.cfg

2. The traffic manage setting is configured in profile.cfg.
   Set flows with QinQ inner vlan ID=0, which represents pipe 0.
   Set IP dst address from 10.0.0.0~10.0.0.7, which enter queue0~queue7,
   mapping TC0~TC7.
   Frame size=70bytes.
   Send rate is 100% linerate.
   The pipe’s rate is limited to 1/4096 linerate.
   So priority guarantees tc0 rate, while tc1 has few packet forwarded.
   All of the packets of tc2~tc7 are dropped::

    qos_sched> stats port 1 subport 0 pipe 0

    +----+-------+-------------+-------------+-------------+-------------+-------------+
    | TC | Queue |   Pkts OK   |Pkts Dropped |  Bytes OK   |Bytes Dropped|    Length   |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  0 |   0   |        6934 |     2388410 |      457644 |   157635060 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  1 |   0   |          34 |     2395345 |        2244 |   158092770 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  2 |   0   |           0 |     2396210 |           0 |   158149860 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  3 |   0   |           0 |     3613033 |           0 |   238460178 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  4 |   0   |           0 |     2381392 |           0 |   157171872 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  5 |   0   |           0 |     2381377 |           0 |   157170882 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  6 |   0   |           0 |     2381925 |           0 |   157207050 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  7 |   0   |           0 |     2382177 |           0 |   157223682 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+

3. The traffic manage setting is configured in profile.cfg.
   Change pipe profile 0, set tb rate and tc rate to 3051750=1/409.6=0.244% port rate
   Set IP dst address from 10.0.0.0~10.0.0.7, which enter queue0~queue7,
   mapping TC0~TC7.
   Send rate is 1% linerate.
   Each TC send rate has 0.125% linerate.
   So TC0 packets can be all forwarded, no drop.
   TC1 packets can be forwarded, while there is about 4.5% packets dropped.
   Other TCs’ packets are dropped::

    qos_sched> stats port 1 subport 0 pipe 0

    +----+-------+-------------+-------------+-------------+-------------+-------------+
    | TC | Queue |   Pkts OK   |Pkts Dropped |  Bytes OK   |Bytes Dropped|    Length   |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  0 |   0   |      150824 |           0 |     9954384 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  1 |   0   |      144700 |        6124 |     9550200 |      404184 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  2 |   0   |           0 |      150824 |           0 |     9954384 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  3 |   0   |           0 |      150824 |           0 |     9954384 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  4 |   0   |           0 |      150824 |           0 |     9954384 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  5 |   0   |           0 |      150824 |           0 |     9954384 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  6 |   0   |           0 |      150824 |           0 |     9954384 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  7 |   0   |           0 |      150824 |           0 |     9954384 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+

Test Case: 4 pipe, 4 TCs
========================
1. This example uses a single transmission configuration
   which creates one RX thread on lcore 5 reading from port 0
   and a worker thread on lcore 7 writing to port 1::

    ./qos_sched -l 1,5,7 -n 4 -- -i --pfc "0,1,5,7" --cfg ../profile.cfg

2. The traffic manage setting is configured in profile.cfg.
   Set three flows with QinQ inner vlan ID=0/1/2/3, which represents pipe 0/1/2/3.
   Set IP dst address 10.0.0.0 of pipe 0.
   Set IP dst address 10.0.0.1 of pipe 1.
   Set IP dst address 10.0.0.2 of pipe 2.
   Set IP dst address 10.0.0.3 of pipe 3.
   Frame size=70bytes.
   Send rate is 100% linerate.
   The RX rate of port 1 is limited to 4/4096 linerate.
   You can see each pipe is limited to 1/4096 linerate.
   only one TC has packets forwarded in each pipe::

    qos_sched> stats port 1 subport 0 pipe 0
    qos_sched> stats port 1 subport 0 pipe 1
    qos_sched> stats port 1 subport 0 pipe 2
    qos_sched> stats port 1 subport 0 pipe 3

Test Case: 1 pipe, 12 TCs
=========================
1. This example uses a single transmission configuration
   which creates one RX thread on lcore 5 reading from port 0
   and a worker thread on lcore 7 writing to port 1::

    ./qos_sched -l 1,5,7 -n 4 -- -i --pfc "0,1,5,7" --cfg ../profile.cfg

2. The traffic manage setting is configured in profile.cfg.
   change pipe profile 0, set tb rate and tc rate to 1/40.96 port rate::

    tb rate = 30517500
    tc 0 rate = 30517500
    ......
    tc 12 rate = 30517500

   Set one flow with QinQ inner vlan ID=0, which represents pipe 0.
   Set IP dst address 10.0.0.0~10.0.0.15, which enter queue0~queue15,
   mapping TC0~TC12.
   Frame size=70bytes.
   Send rate is 1% linerate.
   Each TC send rate has 0.0625% linerate.
   The pipe rate and each tc rate in configuration file is limited to 1/40.96 =2.44%linerate.
   So all the packets of different TCs can be forwarded without drop.
   You can check the pipe stats::

    qos_sched> stats port 1 subport 0 pipe 0

    +----+-------+-------------+-------------+-------------+-------------+-------------+
    | TC | Queue |   Pkts OK   |Pkts Dropped |  Bytes OK   |Bytes Dropped|    Length   |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  0 |   0   |       14995 |           0 |      989670 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  1 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  2 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  3 |   0   |       14995 |           0 |      989670 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  4 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  5 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  6 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  7 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  8 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  9 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  10 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  11 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   0   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   1   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   2   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   3   |       14996 |           0 |      989736 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+

Test Case: 1 pipe, set a TC rate to 0
=====================================
1. This example uses a single transmission configuration
   which creates one RX thread on lcore 5 reading from port 0
   and a worker thread on lcore 7 writing to port 1::

    ./qos_sched -l 1,5,7 -n 4 -- -i --pfc "0,1,5,7" --cfg ../profile.cfg

2. The traffic manage setting is configured in profile.cfg.
   change pipe profile 0, set tb rate and tc rate to 1/40.96 port rate::

    tb rate = 30517500
    tc 0 rate = 30517500
    ......
    tc 12 rate = 30517500

   And set TC0 rate to 0 of subport and pipe configuration::

    queue sizes = 64 0 64 64 64 64 64 64 64 64 64 64 64
    tc 1 rate = 0

   Set one flow with QinQ inner vlan ID=0, which represents pipe 0.
   Set IP dst address 10.0.0.0~10.0.0.3, which should enter queue0~queue3,
   mapping TC0~TC3.
   Frame size=70bytes.
   Send rate is 1% linerate.
   Each TC send rate has 0.25% linerate.
   The pipe rate and each tc rate in configuration file is limited to 1/40.96 =2.44%linerate.
   So all the packets of different TCs can be forwarded without drop.
   You can check the pipe stats, there is no packets received by TC1::

    qos_sched> stats port 1 subport 0 pipe 0

    +----+-------+-------------+-------------+-------------+-------------+-------------+
    | TC | Queue |   Pkts OK   |Pkts Dropped |  Bytes OK   |Bytes Dropped|    Length   |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  0 |   0   |       30572 |           0 |     2017752 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  1 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  2 |   0   |       30572 |           0 |     2017752 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  3 |   0   |       30571 |           0 |     2017686 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  4 |   0   |       30572 |           0 |     2017752 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  5 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  6 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+

Test Case: best effort TC12
===========================
1. This example uses a single transmission configuration
   which creates one RX thread on lcore 5 reading from port 0
   and a worker thread on lcore 7 writing to port 1::

    ./qos_sched -l 1,5,7 -n 4 -- -i --pfc "0,1,5,7" --cfg ../profile.cfg

2. The traffic manage setting is configured in profile.cfg.
   Set flows with QinQ inner vlan ID=0, which represents pipe 0.
   Set IP dst address from 10.0.0.12~10.0.0.14, which enter queue12~queue14,
   mapping TC12.
   Frame size=70bytes.
   Send rate is 100% linerate.
   The pipe’s rate is limited to 1/4096 linerate.
   You can check the pipe stats::

    qos_sched> stats port 1 subport 0 pipe 0

    +----+-------+-------------+-------------+-------------+-------------+-------------+
    | TC | Queue |   Pkts OK   |Pkts Dropped |  Bytes OK   |Bytes Dropped|    Length   |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  0 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  1 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  2 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  3 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  4 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  5 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  6 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  7 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  8 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  9 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  10 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  11 |   0   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   0   |        2475 |     9709255 |      163350 |   640810830 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   1   |        2475 |     9708965 |      163350 |   640791690 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   2   |        2475 |     9709249 |      163350 |   640810434 |          64 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   3   |           0 |           0 |           0 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+

   Each queue received same quantity of packets.
   It is different from other TCs.
   Because four queues of TC12 have the same priority, and the wrr weights = 1 1 1 1.

Test Case: 4096 pipes, 12 TCs
=============================
1. This example uses a single transmission configuration
   which creates one RX thread on lcore 5 reading from port 0
   and a worker thread on lcore 7 writing to port 1::

    ./qos_sched -l 1,5,7 -n 4 -- -i --pfc "0,1,5,7" --cfg ../profile.cfg

2. The traffic manage setting is configured in profile.cfg.
   Set flows with QinQ inner vlan ID=random, which represents pipe 0-4095.
   Set IP dst address from 10.0.0.0~10.0.0.15, which enter queue0~queue15,
   mapping TC0~TC12.
   Frame size=70bytes.
   Send rate is 100% linerate, which is 13.89Mpps.
   Each pipe’s rate is limited to 1/4096 linerate.
   Received rate from port 1 is 11.67Mpps.
   TC0~11 rate are priority guaranteed.
   TC12 has packets dropped.
   You can check the pipe0~pipe4095 stats::

    qos_sched> stats port 1 subport 0 pipe 0

    +----+-------+-------------+-------------+-------------+-------------+-------------+
    | TC | Queue |   Pkts OK   |Pkts Dropped |  Bytes OK   |Bytes Dropped|    Length   |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  0 |   0   |        1510 |           8 |       99660 |         528 |          19 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  1 |   0   |        1429 |           0 |       94314 |           0 |          22 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  2 |   0   |        1518 |           5 |      100188 |         330 |          36 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  3 |   0   |        1525 |           0 |      100650 |           0 |          23 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  4 |   0   |        1512 |           0 |       99792 |           0 |          31 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  5 |   0   |        1480 |           0 |       97680 |           0 |          21 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  6 |   0   |        1505 |           6 |       99330 |         396 |          22 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  7 |   0   |        1574 |          10 |      103884 |         660 |          24 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  8 |   0   |        1477 |           0 |       97482 |           0 |          25 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  9 |   0   |        1421 |           0 |       93786 |           0 |          24 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  10 |   0   |        1486 |           8 |       98076 |         528 |          22 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  11 |   0   |        1466 |           0 |       96756 |           0 |          27 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   0   |        1008 |         504 |       66528 |       33264 |          59 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   1   |        1006 |         454 |       66396 |       29964 |          57 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   2   |        1002 |         458 |       66132 |       30228 |          54 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   3   |        1005 |         413 |       66330 |       27258 |          57 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+

    qos_sched> stats port 1 subport 0 pipe 1
    ......
    qos_sched> stats port 1 subport 0 pipe 4095

   There is a few packets dropped in TC0~TC11.
   This is the limitation of the implementation due to approximation we apply
   at some places in the code for performance reasons.
   The strict priority of the traffic classes has some 1-5% inaccuracy.

3. If TX core defined::

    ./qos_sched -l 1,2,6,7 -n 4 -- -i --pfc "0,1,2,6,7" --cfg ../profile.cfg

   The received rate can reach linerate, which is 13.89Mpps, no packets are dropped::

    qos_sched> stats port 1 subport 0 pipe 0

    +----+-------+-------------+-------------+-------------+-------------+-------------+
    | TC | Queue |   Pkts OK   |Pkts Dropped |  Bytes OK   |Bytes Dropped|    Length   |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  0 |   0   |        7065 |           0 |      466290 |           0 |           2 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  1 |   0   |        6946 |           0 |      458436 |           0 |           2 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  2 |   0   |        7028 |           0 |      463848 |           0 |           1 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  3 |   0   |        7158 |           0 |      472428 |           0 |           1 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  4 |   0   |        7071 |           0 |      466686 |           0 |           1 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  5 |   0   |        7051 |           0 |      465366 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  6 |   0   |        7236 |           0 |      477576 |           0 |           4 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  7 |   0   |        7109 |           0 |      469194 |           0 |           5 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  8 |   0   |        7055 |           0 |      465630 |           0 |           2 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  9 |   0   |        7145 |           0 |      471570 |           0 |           3 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  10 |   0   |        7008 |           0 |      462528 |           0 |           2 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  11 |   0   |        7218 |           0 |      476388 |           0 |           2 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   0   |        7064 |           0 |      466224 |           0 |           1 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   1   |        7113 |           0 |      469458 |           0 |           4 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   2   |        7100 |           0 |      468600 |           0 |           2 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   3   |        6992 |           0 |      461472 |           0 |           0 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+

Test Case: qos_sched of two ports
=================================
1. This example with two packet flows configuration using different ports
   but sharing the same core for QoS scheduler is given below::

    ./qos_sched -l 1,2,6,7 -n 4 -- --pfc "0,1,2,6,7" --pfc "1,0,2,6,7" --cfg ../profile.cfg

2. The traffic manage setting is configured in profile.cfg.
   Set flows with QinQ inner vlan ID=random, which represents pipe 0-4095.
   Set IP dst address from 10.0.0.0~10.0.0.15, which enter queue0~queue15,
   mapping TC0~TC12.
   Frame size=70bytes.
   Send rate is 100% linerate, which is 13.89Mpps.
   Received rate from port 0 and port 1 are both 8.10Mpps.
   No packets are dropped on two ports.
   You can check the pipe0~pipe4095 of port0 and port1 stats::

    qos_sched> stats port 0 subport 0 pipe 4095

    +----+-------+-------------+-------------+-------------+-------------+-------------+
    | TC | Queue |   Pkts OK   |Pkts Dropped |  Bytes OK   |Bytes Dropped|    Length   |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  0 |   0   |        6582 |           0 |      434316 |           0 |           7 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  1 |   0   |        6634 |           0 |      437706 |           0 |           2 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  2 |   0   |        6587 |           0 |      434596 |           0 |           6 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  3 |   0   |        6581 |           0 |      434242 |           0 |           7 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  4 |   0   |        6479 |           0 |      427518 |           0 |           9 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  5 |   0   |        6669 |           0 |      440018 |           0 |           9 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  6 |   0   |        6533 |           0 |      431048 |           0 |          10 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  7 |   0   |        6531 |           0 |      430894 |           0 |           5 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  8 |   0   |        6455 |           0 |      425902 |           0 |           6 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  9 |   0   |        6636 |           0 |      437836 |           0 |           7 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  10 |   0   |        6720 |           0 |      443382 |           0 |           2 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  11 |   0   |        6674 |           0 |      440354 |           0 |           9 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   0   |        6658 |           0 |      439256 |           0 |           8 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   1   |        6585 |           0 |      434470 |           0 |           7 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   2   |        6489 |           0 |      428112 |           0 |           4 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   3   |        6562 |           0 |      432984 |           0 |           8 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+

    qos_sched> stats port 1 subport 0 pipe 4

    +----+-------+-------------+-------------+-------------+-------------+-------------+
    | TC | Queue |   Pkts OK   |Pkts Dropped |  Bytes OK   |Bytes Dropped|    Length   |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  0 |   0   |         282 |           0 |       18612 |           0 |          16 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  1 |   0   |         259 |           0 |       17094 |           0 |          15 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  2 |   0   |         282 |           0 |       18612 |           0 |          13 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  3 |   0   |         256 |           0 |       16896 |           0 |          11 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  4 |   0   |         258 |           0 |       17028 |           0 |          18 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  5 |   0   |         285 |           0 |       18810 |           0 |          18 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  6 |   0   |         257 |           0 |       16962 |           0 |          15 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  7 |   0   |         295 |           0 |       19470 |           0 |          17 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  8 |   0   |         263 |           0 |       17358 |           0 |           8 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  9 |   0   |         305 |           0 |       20130 |           0 |          18 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  10 |   0   |         274 |           0 |       18084 |           0 |          13 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  11 |   0   |         279 |           0 |       18414 |           0 |          15 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   0   |         243 |           0 |       16038 |           0 |          14 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   1   |         302 |           0 |       19932 |           0 |          19 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   2   |         252 |           0 |       16632 |           0 |          12 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+
    |  12 |   3   |         274 |           0 |       18084 |           0 |          15 |
    +----+-------+-------------+-------------+-------------+-------------+-------------+

    RX port 1: rx: 8101753 err: 0 no_mbuf: 59022464
    TX port 0: tx: 8101744 err: 0
    -------+------------+------------+
           |  received  |   dropped  |
    -------+------------+------------+
      RX   |    8101684 |          0 |
    QOS+TX |    8101696 |          5 |   pps: 8101691
    -------+------------+------------+

    RX port 0: rx: 8100867 err: 0 no_mbuf: 59005408
    TX port 1: tx: 8100870 err: 0
    -------+------------+------------+
           |  received  |   dropped  |
    -------+------------+------------+
      RX   |    8100755 |          0 |
    QOS+TX |    8100772 |         39 |   pps: 8100733
    -------+------------+------------+

   It might be the case that packets are dropped due to less space in mempool.
   In this experiment, we are stressing the system with more packets
   to see how much scheduler can process.

Note that independent cores for the packet flow configurations
for each of the RX, WT and TX thread are also supported,
providing flexibility to balance the work.
The EAL coremask/corelist is constrained to contain
the default mastercore 1 and the RX, WT and TX cores only.

Test Case: Two Subports, different pipe profiles, different number of pipes I
=============================================================================
*Note: the sample can't be set to two subports,
so the two supports case can't be verified.*

1. Configure the profile.cfg file with two subports, two different pipe
   profiles and different number of pipes::

    [subport 0]
    number of pipes per subport = 2048
    pipe 0-2047 = 0       ; These pipes are configured with pipe profile 0
    [subport 1]
    number of pipes per subport = 512
    pipe 0-511 = 1        ; These pipes are configured with pipe profile 1

    [pipe profile 0]
    tb rate = 305175               ; Bytes per second
    tb size = 1000000              ; Bytes
    tc 0 rate = 305175             ; Bytes per second
    tc 1 rate = 305175             ; Bytes per second
    ......

    [pipe profile 1]
    tb rate = 1220700              ; Bytes per second
    tb size = 1000000              ; Bytes

    tc 0 rate = 1220700            ; Bytes per second
    tc 1 rate = 1220700            ; Bytes per second
    ......

2. This example uses a single packet flow configuration
   which creates one RX thread on lcore 5 reading from port 0
   and a worker thread on lcore 7 writing to port 1::

    ./qos_sched -l 1,2,5,7 -n 4 -- -i --pfc "0,1,2,5,7" --cfg ../profile.cfg

3. The generator settings:
   Set IP dst address mode is random, and the mask is "255.255.255.0".
   Frame size=70bytes.
   Flow1: outer vlan id=0 inner vlan random mask 0XXXXXXXXXXX (2048 pipes)
   Flow2: outer vlan id=1 inner vlan random mask 000XXXXXXXXX (512 pipes)
   Each flow 50% max rate.

4. Check the result:
   Only send flow1, the received packets by ixia port 1: 6.967mpps.
   Only send flow2, the received packets by ixia port 1: 6.967mpps.
   Send two flows at the same time, the received packets by ixia port 1: 13.888 mpps.

Test Case: Two Subports, different pipe profiles, different number of pipes II
==============================================================================
*Note: the sample can't be set to two subports,
so the two supports case can't be verified.*

1. Configure the profile.cfg file the same with last case I.

2. This example uses a single packet flow configuration
   which creates one RX thread on lcore 5 reading from port 0
   and a worker thread on lcore 7 writing to port 1::

    ./qos_sched -l 1,2,5,7 -n 4 -- -i --pfc "0,1,2,5,7" --cfg ../profile.cfg

3. The generator settings:
   Set IP dst address mode is random, and the mask is "255.255.255.0".
   Frame size=70bytes.
   Flow1: outer vlan id=0 inner vlan random mask 0XXXXXXXXXXX (2048 pipes)
   Flow2: outer vlan id=1 inner vlan random mask 0000XXXXXXXX (256 pipes)
   Each flow 50% max rate.

4. Check the result:
   Only send flow1, the received packets by ixia port 1: 6.967mpps.
   Only send flow2, the received packets by ixia port 1: 3.838mpps.
   Send two flows at the same time, the received packets by ixia port 1: 10.805mpps.

Test Case: Redistribution of unused pipe BW to other pipes within the same subport
==================================================================================
1. Use default profile_ov.cfg, Set::

    CONFIG_RTE_SCHED_SUBPORT_TC_OV=y

2. This example uses a single packet flow configuration
   which creates one RX thread on lcore 5 reading from port 0
   and a worker thread on lcore 7 writing to port 1::

    ./qos_sched -l 1,2,5,7 -n 4 -- -i --pfc "0,1,2,5,7" --cfg ../profile_ov.cfg

3. The generator settings:
   Configure 4 flows:
   Frame size=70bytes.
   Outer vlan ID = 0
   Flow 1: Inner vlan ID = 0
   Flow 2: Inner vlan ID = 1
   Flow 3: Inner vlan ID = 2
   Flow 4: Inner vlan ID = 3
   IP dst address = 100.0.0.12
   Each flow’s Max rate = 25%
   Send four flows at the same time, the TX rate by ixia port0 is 13.888mpps,
   the received packets by ixia port1: 0.092mpps.

4. Disable the first flow, the TX rate by ixia port0 is 10.416mpps,
   the received packets by ixia port1 is still 0.092mpps.

5. Configure only one flow with max rate = 100%
   Set inner vlan ID count mode "increment", repeat count=32, step=1.
   Send the flow, the receive rate is 0.092mpps.
   Then set inner vlan ID count mode "increment", repeat count=16, step=1.
   Send the flow, the receive rate is still 0.092mpps.
