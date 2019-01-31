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

=======
QoS API
=======

Description
===========
The generic API for the Quality of Service (QoS) Traffic Management of Ethernet
devices, which includes the following main features: hierarchical scheduling,
traffic shaping, congestion management, packet marking.
The TM setting commands are as following:
1. Add the port traffic management private shaper profile::

    testpmd> add port tm node shaper profile (port_id) (shaper_profile_id) \
    (cmit_tb_rate) (cmit_tb_size) (peak_tb_rate) (peak_tb_size) \
    (packet_length_adjust)

2. Add nonleaf node to port traffic management hiearchy::

    testpmd> add port tm nonleaf node (port_id) (node_id) (parent_node_id) \
    (priority) (weight) (level_id) (shaper_profile_id) \
    (n_sp_priorities) (stats_mask) (n_shared_shapers) \
    [(shared_shaper_0) (shared_shaper_1) ...] \

3. Add leaf node to port traffic management hiearchy::

    testpmd> add port tm leaf node (port_id) (node_id) (parent_node_id) \
    (priority) (weight) (level_id) (shaper_profile_id) \
    (cman_mode) (wred_profile_id) (stats_mask) (n_shared_shapers) \
    [(shared_shaper_id) (shared_shaper_id) ...] \

4. Commit the traffic management hierarchy on the port::

    testpmd> port tm hierarchy commit (port_id) (clean_on_fail)

Prerequisites
=============
For i40e, need enable rss
For ixgbe, need disable rss.
The DUT must have two 10G Ethernet ports connected to two ports on tester::

    dut_port_0 <---> tester_port_0
    dut_port_1 <---> tester_port_1

Assume two DUT 10G Ethernet ports' pci device id is as the following::

    dut_port_0 : "0000:05:00.0"
    dut_port_1 : "0000:05:00.1"

Bind two ports to dpdk driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0 05:00.1

Test Cases for I40e：
====================

Test Case: dcb 4 tc queue mapping
=================================
1. Start testpmd and set DCB::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-27 -n 4 --master-lcore=23 -- -i --nb-cores=4 --rxq=4 --txq=4 --rss-ip
    testpmd> port stop all
    testpmd> port config 0 dcb vt off 4 pfc off
    testpmd> port config 1 dcb vt off 4 pfc off
    testpmd> port start all
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Send packets with set vlan user priority 0, 1, 2, 3, verify::

    pkt1 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=0)/IP()/Raw('x'*20)
    pkt2 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=1)/IP()/Raw('x'*20)
    pkt3 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=2)/IP()/Raw('x'*20)
    pkt4 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=3)/IP()/Raw('x'*20)

   packet with vlan user priority 0 should be received by queue 0
   packet with vlan user priority 1 should be received by queue 1
   packet with vlan user priority 2 should be received by queue 2
   packet with vlan user priority 3 should be received by queue 3

Test Case: dcb 8 tc queue mapping
=================================
1. Start testpmd and set DCB::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-31 -n 4 --master-lcore=23 -- -i --nb-cores=8 --rxq=8 --txq=8 --rss-ip
    testpmd> port stop all
    testpmd> port config 0 dcb vt off 8 pfc off
    testpmd> port config 1 dcb vt off 8 pfc off
    testpmd> port start all
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Send packet with set vlan user priority 0, 1, 2, 3, 4, 5, 6, 7, verify::

    pkt1 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=0)/IP()/Raw('x'*20)
    pkt2 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=1)/IP()/Raw('x'*20)
    pkt3 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=2)/IP()/Raw('x'*20)
    pkt4 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=3)/IP()/Raw('x'*20)
    pkt5 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=4)/IP()/Raw('x'*20)
    pkt6 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=5)/IP()/Raw('x'*20)
    pkt7 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=6)/IP()/Raw('x'*20)
    pkt8 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=7)/IP()/Raw('x'*20)

   packet with vlan user priority 0 should be received by queue 0
   packet with vlan user priority 1 should be received by queue 1
   packet with vlan user priority 2 should be received by queue 2
   packet with vlan user priority 3 should be received by queue 3
   packet with vlan user priority 4 should be received by queue 4
   packet with vlan user priority 5 should be received by queue 5
   packet with vlan user priority 6 should be received by queue 6
   packet with vlan user priority 7 should be received by queue 7

Test Case: shaping 1 port 4 tc
==============================
1. Start testpmd and set DCB::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-27 -n 4 --master-lcore=23 -- -i --nb-cores=4 --rxq=4 --txq=4 --rss-ip
    testpmd> port stop all
    testpmd> port config 0 dcb vt off 4 pfc off
    testpmd> port config 1 dcb vt off 4 pfc off

2. Add root non leaf node::

    testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0

3. Add private shaper 1, 2, 3, 4 for tc node 0-4::

    testpmd> add port tm node shaper profile 1 1 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 2 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 3 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 4 0 0 25000000 0 0

4. Add tc node::

    testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 1 1 0 0
    testpmd> add port tm nonleaf node 1 900001 1000000 0 1 1 2 1 0 0
    testpmd> add port tm nonleaf node 1 900002 1000000 0 1 1 3 1 0 0
    testpmd> add port tm nonleaf node 1 900003 1000000 0 1 1 4 1 0 0

5. Add queue leaf node::

    testpmd> add port tm leaf node 1 0 900000 0 1 2 -1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 1 900001 0 1 2 -1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 2 900002 0 1 2 -1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 3 900003 0 1 2 -1 0 0xffffffff 0 0

6. Commit the traffic management hierarchy on the port::

    testpmd> port tm hierarchy commit 1 no
    testpmd> port start all
    testpmd> start

7. Send four flows with user priority 0, 1, 2, 3,
   verify shaping each flow to 200Mbps(25MBps).

Test Case:  shaping 1 port 8 tc
===============================
1. Start testpmd and set DCB::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-31 -n 4 --master-lcore=23 -- -i --nb-cores=8 --rxq=8 --txq=8 --rss-ip
    testpmd> port stop all
    testpmd> port config 0 dcb vt off 8 pfc off
    testpmd> port config 1 dcb vt off 8 pfc off

2. Add root non leaf node::

    testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0

3. Add private shaper 1, 2, 3, 4, 5, 6, 7, 8, for tc node 0-7::

    testpmd> add port tm node shaper profile 1 1 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 2 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 3 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 4 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 5 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 6 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 7 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 8 0 0 25000000 0 0

4. Add tc node::

    testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 1 1 0 0
    testpmd> add port tm nonleaf node 1 900001 1000000 0 1 1 2 1 0 0
    testpmd> add port tm nonleaf node 1 900002 1000000 0 1 1 3 1 0 0
    testpmd> add port tm nonleaf node 1 900003 1000000 0 1 1 4 1 0 0
    testpmd> add port tm nonleaf node 1 900004 1000000 0 1 1 5 1 0 0
    testpmd> add port tm nonleaf node 1 900005 1000000 0 1 1 6 1 0 0
    testpmd> add port tm nonleaf node 1 900006 1000000 0 1 1 7 1 0 0
    testpmd> add port tm nonleaf node 1 900007 1000000 0 1 1 8 1 0 0

5. Add queue leaf node::

    testpmd> add port tm leaf node 1 0 900000 0 1 2 -1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 1 900001 0 1 2 -1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 2 900002 0 1 2 -1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 3 900003 0 1 2 -1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 4 900004 0 1 2 -1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 5 900005 0 1 2 -1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 6 900006 0 1 2 -1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 7 900007 0 1 2 -1 0 0xffffffff 0 0

6. Commit the traffic management hierarchy on the port::

    testpmd> port tm hierarchy commit 1 no
    testpmd> port start all
    testpmd> start

7. Send four flows with user priority 0, 1, 2, 3, 4, 5, 6, 7,
   verify shaping each flow to 200Mbps(25MBps).

Test Case: shaping for port
===========================
1. Start testpmd::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 23-27 -n 4 --master-lcore=23 -- -i --nb-cores=4 --rxq=4 --txq=4 --rss-ip
    testpmd> port stop 1

1. Add private shaper 0::

    testpmd> add port tm node shaper profile 1 0 0 0 25000000 0 0

2. Add port (root nonleaf) node::

    testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 0 1 0 0

3. Commit the traffic management hierarchy on the port::

    testpmd> port tm hierarchy commit 1 no
    testpmd> port start 1
    testpmd> start

4. Start transmitting,
   verify shaping the traffic to 200Mbps(25MBps).

Test Cases for ixgbe:
====================

Test Case: dcb 4 tc queue mapping
=================================
1. Start testpmd and set DCB::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 3-7 -n 4 --master-lcore=3 -- -i --nb-cores=4 --rxq=4 --txq=4 --disable-rss
    testpmd> vlan set filter off 0
    testpmd> vlan set filter off 1
    testpmd> port stop all
    testpmd> port config 0 dcb vt off 4 pfc off
    testpmd> port config 1 dcb vt off 4 pfc off
    testpmd> port start all
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Send packets with set vlan user priority 0, 1, 2, 3, verify::

    pkt1 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=0)/IP()/Raw('x'*20)
    pkt2 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=1)/IP()/Raw('x'*20)
    pkt3 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=2)/IP()/Raw('x'*20)
    pkt4 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=3)/IP()/Raw('x'*20)

   packet with vlan user priority 0 should be received by queue 0
   packet with vlan user priority 1 should be received by queue 32
   packet with vlan user priority 2 should be received by queue 64
   packet with vlan user priority 3 should be received by queue 96

Test Case: dcb 8 tc queue mapping
=================================
1. Start testpmd and set DCB::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 3-11 -n 4 --master-lcore=3 -- -i --nb-cores=8 --rxq=8 --txq=8 --disable-rss
    testpmd> vlan set filter off 0
    testpmd> vlan set filter off 1
    testpmd> port stop all
    testpmd> port config 0 dcb vt off 8 pfc off
    testpmd> port config 1 dcb vt off 8 pfc off
    testpmd> port start all
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Send packet with set vlan user priority 0, 1, 2, 3, 4, 5, 6, 7, verify::

    pkt1 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=0)/IP()/Raw('x'*20)
    pkt2 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=1)/IP()/Raw('x'*20)
    pkt3 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=2)/IP()/Raw('x'*20)
    pkt4 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=3)/IP()/Raw('x'*20)
    pkt5 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=4)/IP()/Raw('x'*20)
    pkt6 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=5)/IP()/Raw('x'*20)
    pkt7 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=6)/IP()/Raw('x'*20)
    pkt8 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=7)/IP()/Raw('x'*20)

   packet with vlan user priority 0 should be received by queue 0
   packet with vlan user priority 1 should be received by queue 16
   packet with vlan user priority 2 should be received by queue 32
   packet with vlan user priority 3 should be received by queue 48
   packet with vlan user priority 4 should be received by queue 64
   packet with vlan user priority 5 should be received by queue 80
   packet with vlan user priority 6 should be received by queue 96
   packet with vlan user priority 7 should be received by queue 112

Test Case: shaping for queue with 4 tc
======================================
1. Start testpmd and set DCB::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 3-7 -n 4 --master-lcore=3 -- -i --nb-cores=4 --rxq=4 --txq=4 --disable-rss
    testpmd> vlan set filter off 0
    testpmd> vlan set filter off 1
    testpmd> port stop all
    testpmd> port config 0 dcb vt off 4 pfc off
    testpmd> port config 1 dcb vt off 4 pfc off
    testpmd> port start all

2. Add root non leaf node::

    testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0

3. Add tc node::

    testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900001 1000000 0 1 1 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900002 1000000 0 1 1 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900003 1000000 0 1 1 -1 1 0 0

4. Add private shaper 1, 2, 3, 4 for tc node 0-4::

    testpmd> add port tm node shaper profile 1 0 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 1 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 2 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 3 0 0 25000000 0 0

5. Add queue leaf node::

    testpmd> add port tm leaf node 1 0 900000 0 1 2 0 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 1 900001 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 2 900002 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 3 900003 0 1 2 3 0 0xffffffff 0 0

6. Commit the traffic management hierarchy on the port::

    testpmd> port tm hierarchy commit 1 no
    testpmd> port start all
    testpmd> start

7. Send four flows with user priority 0, 1, 2, 3,
   verify shaping each flow to 200Mbps(25MBps).

Test Case: shaping for queue with 8 tc
======================================
1. Start testpmd and set DCB::

    ./x86_64-native-linuxapp-gcc/app/testpmd -l 3-11 -n 4 --master-lcore=3 -- -i --nb-cores=8 --rxq=8 --txq=8 --disable-rss
    testpmd> vlan set filter off 0
    testpmd> vlan set filter off 1
    testpmd> port stop all
    testpmd> port config 0 dcb vt off 8 pfc off
    testpmd> port config 1 dcb vt off 8 pfc off
    testpmd> port start all

2. Add root non leaf node::

    testpmd> add port tm nonleaf node 1 1000000 -1 0 1 0 -1 1 0 0

3. Add tc node::

    testpmd> add port tm nonleaf node 1 900000 1000000 0 1 1 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900001 1000000 0 1 1 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900002 1000000 0 1 1 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900003 1000000 0 1 1 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900004 1000000 0 1 1 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900005 1000000 0 1 1 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900006 1000000 0 1 1 -1 1 0 0
    testpmd> add port tm nonleaf node 1 900007 1000000 0 1 1 -1 1 0 0

4. Add private shaper 1, 2, 3, 4, 5, 6, 7, 8, for tc node 0-7::

    testpmd> add port tm node shaper profile 1 0 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 1 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 2 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 3 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 4 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 5 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 6 0 0 25000000 0 0
    testpmd> add port tm node shaper profile 1 7 0 0 25000000 0 0

5. Add queue leaf node::

    testpmd> add port tm leaf node 1 0 900000 0 1 2 0 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 1 900001 0 1 2 1 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 2 900002 0 1 2 2 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 3 900003 0 1 2 3 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 4 900004 0 1 2 4 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 5 900005 0 1 2 5 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 6 900006 0 1 2 6 0 0xffffffff 0 0
    testpmd> add port tm leaf node 1 7 900007 0 1 2 7 0 0xffffffff 0 0

6. Commit the traffic management hierarchy on the port::

    testpmd> port tm hierarchy commit 1 no
    testpmd> port start all
    testpmd> start

7. Send four flows with user priority 0, 1, 2, 3, 4, 5, 6, 7, 8,
   verify shaping each flow to 200Mbps(25MBps).
