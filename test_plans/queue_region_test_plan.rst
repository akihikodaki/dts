.. Copyright (c) <2017>, Intel Corporation
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

===========================================
Fortville Configure RSS Queue Regions Tests
===========================================
Description
===========

FVL/FPK and future CVL/CPK NICs support queue regions configuration for
RSS in PF/VF, so different traffic classes or different packet
classification types can be separated to different queue regions which
includes several queues, but traffic classes and packet classification
cannot co-existing with the support of queue region functionality.
Different PCtype packets take rss algorithm in different queue regions.

Examples:

• all TCP packets with SYN flags set can be sent to queue A, when TCP
  packets with out SYN flags will be distributed to queues B-F.

• IPv4 and IPv6 packets distributed to different queue regions

• UDP and TCP packets distributed to different queue regions

• Different tunnels distributed to different queue regions (requires
  tunnels PCTYPEs creation using personalization profiles)

• different traffic classes defined in VLAN PCP bits distributed to
  different queue regions

For FVL see chapter 7.1.7 of the latest datasheet.
For FPK/CPK see corresponding EAS sections.

Prerequisites
=============

1. Hardware:
   Fortville

2. software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. bind the port to dpdk driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0

   the mac address of 05:00.0 is 00:00:00:00:01:00

4. start the testpmd::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 1ffff -n 4 -- -i --rxq=16 --txq=16
    testpmd> port config all rss all
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

Test case 1: different pctype packet can enter the expected queue region
========================================================================

1. Set queue region on a port::

    testpmd> set port 0 queue-region region_id 0 queue_start_index 1 queue_num 1
    testpmd> set port 0 queue-region region_id 1 queue_start_index 3 queue_num 2
    testpmd> set port 0 queue-region region_id 2 queue_start_index 6 queue_num 2
    testpmd> set port 0 queue-region region_id 3 queue_start_index 8 queue_num 2
    testpmd> set port 0 queue-region region_id 4 queue_start_index 11 queue_num 4
    testpmd> set port 0 queue-region region_id 5 queue_start_index 15 queue_num 1

2. Set the mapping of flowtype to region index on a port::

    testpmd> set port 0 queue-region region_id 0 flowtype 31
    testpmd> set port 0 queue-region region_id 1 flowtype 32
    testpmd> set port 0 queue-region region_id 2 flowtype 33
    testpmd> set port 0 queue-region region_id 3 flowtype 34
    testpmd> set port 0 queue-region region_id 4 flowtype 35
    testpmd> set port 0 queue-region region_id 5 flowtype 45
    testpmd> set port 0 queue-region region_id 2 flowtype 41
    testpmd> set port 0 queue-region flush on
 
3. send packet::

    pkt1 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=23,dport=24)/Raw('x'*20) 
    pkt2 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=33,dport=34,flags="S")/Raw('x'*20)
    pkt3 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=33,dport=34,flags="PA")/Raw('x' * 20)
    pkt4 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)
    pkt5 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x'*20)
    pkt6 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/IPv6(src="2001::1", dst="2001::2")/Raw('x' * 20)
    pkt7 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/IPv6(src="2001::1", dst="2001::2")/UDP(sport=24,dport=25)/Raw('x'*20)
    pkt8 = Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=1)/IP(src="192.168.0.1", dst="192.168.0.2")/Raw('x'*20)

   verify the pkt1 to queue 1, pkt2 to queue 3 or queue 4,
   pkt3 to queue 6 or queue 7, pkt4 to queue 8 or queue 9,
   pkt5 to queue 11 or 12 or 13 or 14,
   pkt6 to queue 15, pkt7 to queue 6 or queue 7,
   pkt8 enter the same queue with pkt5.

4. verified the rules can be listed and flushed::
 
    testpmd> show port 0 queue-region
    testpmd> set port 0 queue-region flush off

Notes: fortville can't parse the TCP SYN type packet, fortpark can parse it.
So if fortville, pkt2 to queue 6 or queue 7.

Test case 2: different user priority packet can enter the expected queue region
===============================================================================

1. Set queue region on a port::

    testpmd> set port 0 queue-region region_id 0 queue_start_index 0 queue_num 1
    testpmd> set port 0 queue-region region_id 7 queue_start_index 1 queue_num 8
    testpmd> set port 0 queue-region region_id 2 queue_start_index 10 queue_num 4

2. Set the mapping of User Priority to Traffic Classes on a port::

    testpmd> set port 0 queue-region UP 3 region_id 0
    testpmd> set port 0 queue-region UP 1 region_id 7
    testpmd> set port 0 queue-region UP 2 region_id 2
    testpmd> set port 0 queue-region UP 7 region_id 2
    testpmd> set port 0 queue-region flush on

3. send packet::

    pkt1=Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=3)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt2=Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=1)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt3=Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=2)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=32, dport=33)/Raw('x'*20)
    pkt4=Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=7)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=32, dport=33)/Raw('x'*20)
    pkt5=Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/Dot1Q(prio=7)/IP(src="192.168.0.3", dst="192.168.0.4")/UDP(sport=22, dport=23)/Raw('x'*20)
    pkt6=Ether(dst="00:00:00:00:01:00", src="00:02:00:00:00:01")/IP(src="192.168.0.3", dst="192.168.0.4")/UDP(sport=22, dport=23)/Raw('x'*20)

   verify the pkt1 to queue 0,
   pkt2 to queue 1 or 2 or 3 or 4 or 5 or 6 or 7 or 8.
   pkt3 to queue 10 or 11 or 12 or 13.
   pkt4 enter the same queue with pkt3.
   pkt5 to queue 10 or 11 or 12 or 13.
   pkt6 enter different queue from pkt5.

4. verified the rules can be listed and flushed::

    testpmd> show port 0 queue-region
    testpmd> set port 0 queue-region flush off

Test case 3: boundary value testing
===================================

1. boundary value testing of "Set a queue region on a port"

   the following three rules are set successfully::

    testpmd> set port 0 queue-region region_id 0 queue_start_index 0 queue_num 16
    testpmd> set port 0 queue-region flush on
    testpmd> set port 0 queue-region flush off
    testpmd> set port 0 queue-region region_id 0 queue_start_index 15 queue_num 1
    testpmd> set port 0 queue-region flush on
    testpmd> set port 0 queue-region flush off
    testpmd> set port 0 queue-region region_id 7 queue_start_index 2 queue_num 8
    testpmd> set port 0 queue-region flush on

   all the three rules can be listed::

    testpmd> show port 0 queue-region
    testpmd> set port 0 queue-region flush off

   the following four rules can't be set successfully.::

    testpmd> set port 0 queue-region region_id 8 queue_start_index 2 queue_num 2
    testpmd> set port 0 queue-region region_id 1 queue_start_index 16 queue_num 1
    testpmd> set port 0 queue-region region_id 2 queue_start_index 15 queue_num 2
    testpmd> set port 0 queue-region region_id 3 queue_start_index 2 queue_num 3

   no rules can be listed::

    testpmd> show port 0 queue-region
    testpmd> set port 0 queue-region flush off

2. boundary value testing of "Set the mapping of flowtype to region index
   on a port"::

    testpmd> set port 0 queue-region region_id 0 queue_start_index 2 queue_num 2
    testpmd> set port 0 queue-region region_id 7 queue_start_index 4 queue_num 4

   the first two rules can be set successfully::

    testpmd> set port 0 queue-region region_id 0 flowtype 63
    testpmd> set port 0 queue-region region_id 7 flowtype 0

   the first two rules can be listed::

    testpmd> show port 0 queue-region

   the last two rule can't be set successfully::

    testpmd> set port 0 queue-region region_id 0 flowtype 64
    testpmd> set port 0 queue-region region_id 2 flowtype 34
    testpmd> set port 0 queue-region flush on

   the last two rules can't be listed::

    testpmd> show port 0 queue-region
    testpmd> set port 0 queue-region flush off

3. boundary value testing of "Set the mapping of UP to region index
   on a port"::

    testpmd> set port 0 queue-region region_id 0 queue_start_index 2 queue_num 2
    testpmd> set port 0 queue-region region_id 7 queue_start_index 4 queue_num 4

   the first two rules can be set successfully::

    testpmd> set port 0 queue-region UP 7 region_id 0
    testpmd> set port 0 queue-region UP 0 region_id 7

   the first two rules can be listed::

    testpmd> show port 0 queue-region

   the last two rule can't be set successfully::

    testpmd> set port 0 queue-region UP 8 region_id 0
    testpmd> set port 0 queue-region UP 1 region_id 2
    testpmd> set port 0 queue-region flush on

   the last two rules can't be listed::

    testpmd> show port 0 queue-region
    testpmd> set port 0 queue-region flush off
