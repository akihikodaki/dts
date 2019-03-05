.. Copyright (c) <2018>, Intel Corporation
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

===========================
DDP PPPoE/L2TPv2/PPPoL2TPv2
===========================

Fortville supports PPPoE/L2TPv2/PPPoL2TPv2 new protocols after loading profile.
For DDP introduction, please refer to ddp gtp or ddp mpls test plan.

Requirements as below::

    - RSS for PPPoE packets: without IP payload, using session id and source
      MAC as hash input set. With IP payload, using IP addresses and L4 ports
      as hash input set.

    - Classification for non-multicast IP encapsulated to PPPoL2TP: using
      inner 5-tuple as hash input set for RSS.

    - Classification for multicast IP encapsulated to PPPoL2TP: assign
      packets to specific queue according to inner dst IP address.

Dynamic flow type mapping eliminates usage of number of hard-coded flow
types in bulky if-else statements. For instance, when configure hash enable
flags for RSS in i40e_config_hena() function and will make partitioning FVL
in i40e PMD more scalable.

I40e PCTYPEs are statically mapped to RTE_ETH_FLOW_* types in DPDK, defined in
rte_eth_ctrl.h, flow types used to define ETH_RSS_* offload types in
rte_ethdev.h. RTE_ETH_FLOW_MAX is defined now as 22, leaves 42 flow type
unassigned.

Ppp-oe-ol2tpv2.pkgo defines and supports below pctype packets, also could
check the information using command "ddp get info <profile>" after loading
the profile, left numbers are pctype values, right are supported packets::

    14: L2TPv2CTRL
    15: PPPoE IPV4
    16: PPPoE IPV6
    17: PPPoE
    18: PPPoL2TPv2 IPV4
    19: PPPoL2TPv2 IPV6
    20: PPPoL2TPv2
    21: L2TPv2PAY

There are so many kinds of packets that we can't cover all pctype test
scenarios, below test plan focuses on above requirements to illustrate usage,
also could do similar test for other packets. Select flow types value between
23 and 63, design pctype, flow type and default input set mapping as below::

    +----------------------+------------+------------+----------------------------------+----------------------------------+
    | Packet Type          |   PcTypes  | Flow Types |           Hash Input Set         |           FD Input Set           |
    +----------------------+------------+------------+----------------------------------+----------------------------------+
    | L2TPv2CTL            |     14     |    27      |        MAC SA, Session ID        |        MAC SA, Session ID        |
    +----------------------+------------+------------+----------------------------------+----------------------------------+
    | PPPoE IPV4           |     15     |    28      | IPv4 SA, IPv4 DA, S-Port, D-Port | IPv4 SA, IPv4 DA, S-Port, D-Port |
    +----------------------+------------+------------+----------------------------------+----------------------------------+
    | PPPoE IPV6           |     16     |    29      | IPv6 SA, IPv6 DA, S-Port, D-Port | IPv6 SA, IPv6 DA, S-Port, D-Port |
    +----------------------+------------+------------+----------------------------------+----------------------------------+
    | PPPoE                |     17     |    30      |        MAC SA, Session ID        |        MAC SA, Session ID        |
    +----------------------+------------+------------+----------------------------------+----------------------------------+
    | PPPoL2TPv2 IPV4      |     18     |    23      | IPv4 SA, IPv4 DA, S-Port, D-Port | IPv4 SA, IPv4 DA, S-Port, D-Port |
    +----------------------+------------+------------+----------------------------------+----------------------------------+
    | PPPoL2TPv2 IPV6      |     19     |    24      | IPv6 SA, IPv6 DA, S-Port, D-Port | IPv6 SA, IPv6 DA, S-Port, D-Port |
    +----------------------+------------+------------+----------------------------------+----------------------------------+
    | PPPoL2TPv2           |     20     |    25      |        MAC SA, Session ID        |        MAC SA, Session ID        |
    +----------------------+------------+------------+----------------------------------+----------------------------------+
    | L2TPv2PAY            |     21     |    26      |        MAC SA, Session ID        |        MAC SA, Session ID        |
    +----------------------+------------+------------+----------------------------------+----------------------------------+

Prerequisites
=============

1. Host PF in DPDK driver::

    ./tools/dpdk-devbind.py -b igb_uio 81:00.0

2. Start testpmd on host, set chained port topology mode, add txq/rxq to
   enable multi-queues. If test PF flow director, need to add
   --pkt-filter-mode=perfect on testpmd to enable flow director. In general,
   PF's max queue is 64::

    ./testpmd -c f -n 4 -- -i --port-topology=chained --txq=64 --rxq=64
    --pkt-filter-mode=perfect

Load/delete dynamic device personalization
==========================================

1. Stop testpmd port before loading profile::

    testpmd > port stop all

2. Load ppp-oe-ol2tpv2.pkgo file to the memory buffer, save original
   configuration and return in the same buffer to the ppp-oe-ol2tpv2.bak
   file::

    testpmd > ddp add (port_id) /tmp/ppp-oe-ol2tpv2.pkgo,
    /tmp/ppp-oe-ol2tpv2.bak

3. Remove profile from the network adapter and restore original
   configuration::

    testpmd > ddp del (port_id) /tmp/ppp-oe-ol2tpv2.bak

4. Start testpmd port::

    testpmd > port start all

Note
====

Ppp-oe-ol2tpv2.pkgo profile has been released publicly. You could download
below version to do our regression relative test. Loading DDP profile is
the prerequisite for below RSS and flow director cases::

    https://downloadcenter.intel.com/download/28040

Test Case: RSS for PPPoE with default input set
===============================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoE PAY flow type id 30 to pcytpe id 17 mapping item::

    testpmd> port config 0 pctype mapping update 17 30

3. Check flow type to pctype mapping adds 17 this mapping

4. Enable flow type id 30's RSS::

    testpmd> port config all rss 30

5. Start testpmd, set fwd rxonly, enable output print

6. Default hash input set are MAC SA, session ID. Send sessionid
   PPPoE PAY packet, check RSS could work, print PKT_RX_RSS_HASH::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x7)

7. Send different sessionid PPPoE PAY packet, check to receive packet from
   different queue::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x8)

8. Send different source address PPPoE PAY packet, check to receive packet
   from different queue::

    p=Ether(src="3C:FD:FE:A3:A0:02", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x7)

9. Send different destination address PPPoE PAY packet, check to receive
   packet from same queue::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:02")/
    PPPoE(sessionid=0x7)


Test Case: RSS for PPPoE Ipv4 with default input set
====================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoE Ipv4 flow type id 28 to pcytpe id 15 mapping item::

    testpmd> port config 0 pctype mapping update 15 28

3. Check flow type to pctype mapping adds 15 this mapping

4. Enable flow type id 28's RSS::

    testpmd> port config all rss 28

5. Start testpmd, set fwd rxonly, enable output print

6. Default hash input set are IPv4 SA, IPv4 DA, sport, dport. Send PPPoE
   IPv4 packet, check RSS could work, print PKT_RX_RSS_HASH::

    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.2")/UDP(sport=4000,dport=8000)/Raw('x' * 20)

7. Send different inner source, destination address, sport, dport PPPoE
   IPv4 packets, check to receive packet from different queues::

    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.2",
    dst="2.2.2.2")/UDP(sport=4000,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.3")/UDP(sport=4000,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.2")/UDP(sport=4001,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.2")/UDP(sport=4000,dport=8001)/Raw('x' * 20)

8. Send different sessionid PPPoE IPv4 packet, check to receive packet
   from same queue::

    p=Ether()/PPPoE(sessionid=0x8)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.2")/UDP(sport=4000,dport=8000)/Raw('x' * 20)

Test Case: RSS for PPPoE IPv6 with default input set
====================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoE IPv6 flow type id 29 to pcytpe id 16 mapping item::

    testpmd> port config 0 pctype mapping update 16 29

3. Check flow type to pctype mapping adds 16 this mapping

4. Enable flow type id 29's RSS::

    testpmd> port config all rss 29

5. Start testpmd, set fwd rxonly, enable output print

6. Default hash input set are IPv6 SA, IPv6 DA, sport, dport. Send PPPoE
   IPv6 packet, check RSS could work, print PKT_RX_RSS_HASH::

    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000,dport=8000)/Raw('x' * 20)

7. Send different inner source, destination address, sport, dport PPPoE
   IPv6 packets, check to receive packet from different queues::

    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0002",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0002")/
    UDP(sport=4000,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4001,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000,dport=8001)/Raw('x' * 20)

8. Send different sessionid PPPoE IPv6 packet, check to receive packet
   from same queue::

    p=Ether()/PPPoE(sessionid=0x8)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000,dport=8000)/Raw('x' * 20)

Test Case: RSS for L2TPv2 PAY with default input set
====================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update L2TP PAY flow type id 26 to pcytpe id 21 mapping item::

    testpmd> port config 0 pctype mapping update 21 26

3. Check flow type to pctype mapping adds 21 this mapping

4. Enable flow type id 26's RSS::

    testpmd> port config all rss 26

5. Start testpmd, set fwd rxonly, enable output print

6. Default hash input set are MAC SA, session ID. Send sessionid
   L2TP PAY packet, check RSS could work, print PKT_RX_RSS_HASH::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/IP()/
    UDP(dport=1701, sport=1701)/L2TP(sessionid=0x7)/Raw('x' * 20)

7. Send different sessionid L2TP PAY packet, check to receive packet from
   different queue::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/IP()/
    UDP(dport=1701, sport=1701)/L2TP(sessionid=0x8)/Raw('x' * 20)

8. Send different source address L2TP PAY packet, check to receive packet
   from different queue::

    p=Ether(src="3C:FD:FE:A3:A0:02", dst="4C:FD:FE:A3:A0:01")/IP()/
    UDP(dport=1701, sport=1701)/L2TP(sessionid=0x7)/Raw('x' * 20)

9. Send different destination address L2TP PAY packet, check to receive
   packet from same queue::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:02")/IP()/
    UDP(dport=1701, sport=1701)/L2TP(sessionid=0x7)/Raw('x' * 20)

Test Case: RSS for PPPoE according to sessionid
===============================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoE PAY flow type id 30 to pcytpe id 17 mapping item::

    testpmd> port config 0 pctype mapping update 17 30

3. Check flow type to pctype mapping adds 17 this mapping

4. Reset PPPoE hash input set configuration::

    testpmd> port config 0 pctype 17 hash_inset clear all

5. Sessionid word is 47, enable hash input set for sessionid::

    testpmd> port config 0 pctype 17 hash_inset set field 47

6. Enable flow type id 30's RSS::

    testpmd> port config all rss 30

7. Start testpmd, set fwd rxonly, enable output print

8. Send sessionid PPPoE PAY packet, check RSS could work, print
   PKT_RX_RSS_HASH::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x7)

9. Send different sessionid PPPoE PAY packet, check to receive packet from
   different queue::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x8)

Test Case: RSS for PPPoE according to source address
====================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoE PAY flow type id 30 to pcytpe id 17 mapping item::

    testpmd> port config 0 pctype mapping update 17 30

3. Check flow type to pctype mapping adds 17 this mapping

4. Reset PPPoE hash input set configuration::

    testpmd> port config 0 pctype 17 hash_inset clear all

5. Source mac words are 3~5, enable hash input set for source IPv4::

     testpmd> port config 0 pctype 17 hash_inset set field 3
     testpmd> port config 0 pctype 17 hash_inset set field 4
     testpmd> port config 0 pctype 17 hash_inset set field 5

6. Enable flow type id 30's RSS::

    testpmd> port config all rss 30

7. Start testpmd, set fwd rxonly, enable output print

8. Send source address PPPoE PAY packet, check RSS could work, print
   PKT_RX_RSS_HASH::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x7)

9. Send different source address PPPoE packet, check to receive packet from
   different queue::

    p=Ether(src="3C:FD:FE:A3:A0:02", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x7)

10. Send different destination address PPPoE packet, check to receive packet
    from same queue::

     p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:02")/
     PPPoE(sessionid=0x7)

Test Case: RSS for PPPoL2TP IPv4 according to inner source IPv4
===============================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoL2TP IPv4 flow type id 23 to pcytpe id 18 mapping item::

    testpmd> port config 0 pctype mapping update 18 23

3. Check flow type to pctype mapping adds 23 this mapping

4. Reset PPPoL2TP IPv4 hash input set configuration::

    testpmd> port config 0 pctype 18 hash_inset clear all

5. Inner source IPv4 words are 15~16 , enable hash input set for them::

    testpmd> port config 0 pctype 18 hash_inset set field 15
    testpmd> port config 0 pctype 18 hash_inset set field 16

6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send inner source IPv4 PPPoL2TP IPv4 packet, check RSS could work, print
   PKT_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

9. Send different inner source IPv4 PPPoL2TP IPv4 packet, check to receive
   packet from different queue::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.2",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

10. Send different inner destination IP PPPoL2TP IPv4 packet, check to receive
    packet from same queue::

     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
     IP(src="1.1.1.1",dst="2.2.2.3")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

Test Case: RSS for PPPoL2TP IPv4 according to inner destination IPv4
====================================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoL2TP IPv4 flow type id 23 to pcytpe id 18 mapping item::

    testpmd> port config 0 pctype mapping update 18 23

3. Check flow type to pctype mapping adds 23 this mapping

4. Reset PPPoL2TP IPv4 hash input set configuration::

    testpmd> port config 0 pctype 18 hash_inset clear all

5. Inner destination IPv4 words are 27~28 , enable hash input set for them::

     testpmd> port config 0 pctype 18 hash_inset set field 27
     testpmd> port config 0 pctype 18 hash_inset set field 28

6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send inner destination IPv4 PPPoL2TP IPv4 packet, check RSS could work, print
   PKT_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

9. Send different inner destination IPv4 PPPoL2TP IPv4 packet, check to receive
   packet from different queue::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.3")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

10. Send different inner source IPv4 PPPoL2TP IPv4 packet, check to receive packet
    from same queue::

     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
     IP(src="1.1.1.2",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

Test Case: RSS for PPPoL2TP IPv4 according to sport
===================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoL2TP IPv4 flow type id 23 to pcytpe id 18 mapping item::

    testpmd> port config 0 pctype mapping update 18 23

3. Check flow type to pctype mapping adds 23 this mapping

4. Reset PPPoL2TP IPv4 hash input set configuration::

    testpmd> port config 0 pctype 18 hash_inset clear all

5. Sport word is 29, enable hash input set for it::

     testpmd> port config 0 pctype 18 hash_inset set field 29

6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send sport PPPoL2TP IPv4 packet, check RSS could work, print
   PKT_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

9. Send different sport PPPoL2TP IPv4 packet, check to receive packet from
   different queue::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4001, dport=8000)/Raw('x' * 20)

10. Send different dport PPPoL2TP IPv4 packet, check to receive packet from
    same queue::

     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
     IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8001)/Raw('x' * 20)

Test Case: RSS for PPPoL2TP IPv4 according to dport
===================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoL2TP IPv4 flow type id 23 to pcytpe id 18 mapping item::

    testpmd> port config 0 pctype mapping update 18 23

3. Check flow type to pctype mapping adds 23 this mapping

4. Reset PPPoL2TP IPv4 hash input set configuration::

    testpmd> port config 0 pctype 10 hash_inset clear all

5. Dport word is 30, enable hash input set for it::

    testpmd> port config 0 pctype 10 hash_inset set field 30

6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send dport PPPoL2TP IPv4 packet, check RSS could work, print
   PKT_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

9. Send different dport PPPoL2TP IPv4 packet, check to receive packet from
   different queue::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8001)/Raw('x' * 20)

10. Send different sport PPPoL2TP IPv4 packet, check to receive packet from
    same queue::

     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
     IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4001, dport=8000)/Raw('x' * 20)

Test Case: Flow director for PPPoE with default input set
=========================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoE PAY flow type id 30 to pcytpe id 17 mapping item::

    testpmd> port config 0 pctype mapping update 17 30

3. Start testpmd, set fwd rxonly, enable output print

4. Send PPPoE packets, check to receive packet from queue 0::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x7)

5. Use scapy to generate PPPoE raw packet test_pppoe.raw,
   source/destination address should be swapped in the template
   and traffic packets::

    a=Ether(dst="3C:FD:FE:A3:A0:01", src="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x7)

6. Setup raw flow type filter for flow director, configured queue is random
   queue between 0~63, such as 36::

    testpmd> flow_director_filter 0 mode raw add flow 30 fwd queue 36 fd_id 1
    packet test_pppoe.raw

7. Send matched swapped traffic packet, check to receive packet from
   configured queue 36::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x7)

8. Default flow director input set are MAC SA and session ID, send non-matched
   SA, sessionid, check to receive packet from queue 0::

    p=Ether(src="3C:FD:FE:A3:A0:02", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x7)
    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/
    PPPoE(sessionid=0x8)

9. Send non-matched MAC DA, check to receive packet from queue 36::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:02")/
    PPPoE(sessionid=0x7)

Test Case: Flow director for PPPoE IPv4 with default input set
==============================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoE IPv4 flow type id 28 to pcytpe id 15 mapping item::

    testpmd> port config 0 pctype mapping update 15 28

3. Start testpmd, set fwd rxonly, enable output print

4. Send PPPoE IPv4 packets, check to receive packet from queue 0::

    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.2")/UDP(sport=4000,dport=8000)/Raw('x' * 20)

5. Use scapy to generate PPPoE IPv4 raw packet test_pppoe.raw,
   source/destination address and port should be swapped in the template
   and traffic packets::

    a=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(dst="1.1.1.1",
    src="2.2.2.2")/UDP(dport=4000,sport=8000)/Raw('x' * 20)

6. Setup raw flow type filter for flow director, configured queue is random
   queue between 0~63, such as 36::

    testpmd> flow_director_filter 0 mode raw add flow 28 fwd queue 36 fd_id
    1 packet test_pppoe.raw

7. Send matched swapped traffic packet, check to receive packet from
   configured queue 36::

    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.2")/UDP(sport=4000,dport=8000)/Raw('x' * 20)

8. Send non-matched inner src IP, inner dst IP, sport, dport packets, check to
   receive packet from queue 0::

    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.2",
    dst="2.2.2.2")/UDP(sport=4000,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.3")/UDP(sport=4000,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.2")/UDP(sport=4001,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.2")/UDP(sport=4000,dport=8001)/Raw('x' * 20)

9. Send non-matched sessionid packets, check to receive packet from queue 36::

    p=Ether()/PPPoE(sessionid=0x8)/PPP(proto=0x21)/IP(src="1.1.1.1",
    dst="2.2.2.2")/UDP(sport=4000,dport=8000)/Raw('x' * 20)

Test Case: Flow director for PPPoE IPv6 with default input set
==============================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoE IPv6 flow type id 29 to pcytpe id 16 mapping item::

    testpmd> port config 0 pctype mapping update 16 29

3. Start testpmd, set fwd rxonly, enable output print

4. Send PPPoE IPv6 packets, check to receive packet from queue 0::

    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000,dport=8000)/Raw('x' * 20)

5. Use scapy to generate PPPoE IPv4 raw packet test_pppoe.raw,
   source/destination address and port should be swapped in the template
   and traffic packets::

    a=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(dst="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    src="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(dport=4000,sport=8000)/Raw('x' * 20)

6. Setup raw flow type filter for flow director, configured queue is random
   queue between 0~63, such as 36::

    testpmd> flow_director_filter 0 mode raw add flow 29 fwd queue 36 fd_id 1
    packet test_pppoe.raw

7. Send matched swapped traffic packet, check to receive packet from
   configured queue 36::

    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000,dport=8000)/Raw('x' * 20)

8. Send non-matched inner src IPv6, inner dst IPv6, sport, dport packets,
   check to receive packet from queue 0::

    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0002",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0002")/
    UDP(sport=4000,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4001,dport=8000)/Raw('x' * 20)
    p=Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000,dport=8001)/Raw('x' * 20)

9. Send non-matched sessionid packets, check to receive packet from queue 36::

    p=Ether()/PPPoE(sessionid=0x8)/PPP(proto=0x57)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000,dport=8000)/Raw('x' * 20)

Test Case: Flow director for L2TPv2 PAY with default input set
==============================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update L2TP PAY flow type id 26 to pcytpe id 21 mapping item::

    testpmd> port config 0 pctype mapping update 21 26

3. Start testpmd, set fwd rxonly, enable output print

4. Send L2TP PAY packets, check to receive packet from queue 0::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/IP()/
    UDP(dport=1701, sport=1701)/L2TP(sessionid=0x7)/Raw('x' * 20)

5. Use scapy to generate L2TP PAY raw packet test_l2tp.raw,
   source/destination address should be swapped in the template
   and traffic packets::

    a=Ether(dst="3C:FD:FE:A3:A0:01", src="4C:FD:FE:A3:A0:01")/IP()/
    UDP(dport=1701, sport=1701)/L2TP(sessionid=0x7)/Raw('x' * 20)

6. Setup raw flow type filter for flow director, configured queue is random
   queue between 0~63, such as 36::

    testpmd> flow_director_filter 0 mode raw add flow 26 fwd queue 36 fd_id 1
    packet test_l2tp.raw

7. Send matched swapped traffic packet, check to receive packet from
   configured queue 36::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/IP()/
    UDP(dport=1701, sport=1701)/L2TP(sessionid=0x7)/Raw('x' * 20)

8. Default flow director input set are MAC SA and session ID, send non-matched
   SA, sessionid, check to receive packet from queue 0::

    p=Ether(src="3C:FD:FE:A3:A0:02", dst="4C:FD:FE:A3:A0:01")/IP()/
    UDP(dport=1701, sport=1701)/L2TP(sessionid=0x7)/Raw('x' * 20)
    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:01")/IP()/
    UDP(dport=1701, sport=1701)/L2TP(sessionid=0x8)/Raw('x' * 20)

9. Send non-matched MAC DA, check to receive packet from queue 36::

    p=Ether(src="3C:FD:FE:A3:A0:01", dst="4C:FD:FE:A3:A0:02")/IP()/
    UDP(dport=1701, sport=1701)/L2TP(sessionid=0x7)/Raw('x' * 20)

Test Case: Flow director for PPPoL2TP IPv4 with default input set
=================================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoL2TP IPv4 flow type id 23 to pcytpe id 18 mapping item::

    testpmd> port config 0 pctype mapping update 18 23

3. Start testpmd, set fwd rxonly, enable output print

4. Send PPPoL2TP IPv4 packets, check to receive packet from queue 0::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

5. Use scapy to generate PPPoL2TP IPv4 raw packet test_pppol2tp.raw,
   source/destination address and port should be swapped in the template
   and traffic packets::

    a=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(dst="1.1.1.1",src="2.2.2.2")/UDP(dport=4000, sport=8000)/Raw('x' * 20)

6. Setup raw flow type filter for flow director, configured queue is random
   queue between 0~63, such as 36::

    testpmd> flow_director_filter 0 mode raw add flow 23 fwd queue 36 fd_id 1
    packet test_pppol2tp.raw

7. Send matched swapped traffic packet, check to receive packet from
   configured queue 36::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

8. Send non-matched inner src IP, inner dst IP, sport, dport packets, check to
   receive packet from queue 0::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.2",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)
    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.3")/UDP(sport=4000, dport=8000)/Raw('x' * 20)
    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4001, dport=8000)/Raw('x' * 20)
    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8001)/Raw('x' * 20)

Test Case: Flow director for PPPoL2TP IPv6 with default input set
=================================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoL2TP IPv6 flow type id 24 to pcytpe id 19 mapping item::

    testpmd> port config 0 pctype mapping update 19 24

3. Start testpmd, set fwd rxonly, enable output print

4. Send PPPoL2TP IPv6 packets, check to receive packet from queue 0::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000, dport=8000)/Raw('x' * 20)

5. Use scapy to generate PPPoL2TP IPv6 raw packet test_pppol2tp.raw,
   source/destination address and port should be swapped in the template
   and traffic packets::

    a=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
    IPv6(dst="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    src="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(dport=4000, sport=8000)/Raw('x' * 20)

6. Setup raw flow type filter for flow director, configured queue is random
   queue between 0~63, such as 36::

    testpmd> flow_director_filter 0 mode raw add flow 24 fwd queue 36
    fd_id 1 packet test_pppol2tp.raw

7. Send matched swapped traffic packet, check to receive packet from
   configured queue 36::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000, dport=8000)/Raw('x' * 20)

8. Send non-matched inner src IPv6, inner dst IPv6, sport, dport packets,
   check to receive packet from queue 0::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0002",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000, dport=8000)/Raw('x' * 20)
    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0002")/
    UDP(sport=4000, dport=8000)/Raw('x' * 20)
    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4001, dport=8000)/Raw('x' * 20)
    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000, dport=8001)/Raw('x' * 20)

Test Case: Flow director for PPPoL2TP IPv4 according to inner destination IPv4
==============================================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoL2TP IPv4 flow type id 23 to pcytpe id 18 mapping item::

    testpmd> port config 0 pctype mapping update 18 23

3. Reset PPPoL2TP IPv4 flow director input set configuration::

    testpmd> port config 0 pctype 18 fdir_inset clear all

4. Inner dst IP words are 27 and 28, enable flow director input set
   for them::

    testpmd> port config 0 pctype 18 fdir_inset set field 27
    testpmd> port config 0 pctype 18 fdir_inset set field 28

5. Start testpmd, set fwd rxonly, enable output print

6. Send PPPoL2TP IPv4 packets, check to receive packet from queue 0::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

7. Use scapy to generate PPPoL2TP IPv4 raw packet test_pppol2tp.raw,
   source/destination address and port should be swapped in the template
   and traffic packets::

    a=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(dst="1.1.1.1",src="2.2.2.2")/UDP(dport=4000, sport=8000)/Raw('x' * 20)

8. Setup raw flow type filter for flow director, configured queue is random
   queue between 0~63, such as 36::

    testpmd> flow_director_filter 0 mode raw add flow 23 fwd queue 36
    fd_id 1 packet test_pppol2tp.raw

9. Send matched swapped traffic packet, check to receive packet from
   configured queue 36::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

10. Send matched inner dst IP, but non-matched inner src IP, sport,
    dport packets, check to receive packet from queue 36::

     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
     IP(src="1.1.1.2",dst="2.2.2.2")/UDP(sport=4000, dport=8000)/Raw('x' * 20)
     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
     IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4001, dport=8000)/Raw('x' * 20)
     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
     IP(src="1.1.1.1",dst="2.2.2.2")/UDP(sport=4000, dport=8001)/Raw('x' * 20)

11. Send non-matched inner dst IP packets, check to receive packet from
    queue 0::

     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021)/
     IP(src="1.1.1.1",dst="2.2.2.3")/UDP(sport=4000, dport=8000)/Raw('x' * 20)

Test Case: Flow director for PPPoL2TP IPv6 according to inner destination IPv6
==============================================================================

1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update PPPoL2TP IPv6 flow type id 24 to pcytpe id 19 mapping item::

    testpmd> port config 0 pctype mapping update 19 24

3. Reset PPPoL2TP IPv6 flow director input set configuration::

    testpmd> port config 0 pctype 19 fdir_inset clear all

4. Inner dst IPv6 words are 21~28, enable flow director input set
   for them::

    testpmd> port config 0 pctype 19 fdir_inset set field 21
    testpmd> port config 0 pctype 19 fdir_inset set field 22
    testpmd> port config 0 pctype 19 fdir_inset set field 23
    testpmd> port config 0 pctype 19 fdir_inset set field 24
    testpmd> port config 0 pctype 19 fdir_inset set field 25
    testpmd> port config 0 pctype 19 fdir_inset set field 26
    testpmd> port config 0 pctype 19 fdir_inset set field 27
    testpmd> port config 0 pctype 19 fdir_inset set field 28

5. Start testpmd, set fwd rxonly, enable output print

6. Send PPPoL2TP IPv6 packets, check to receive packet from queue 0::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000, dport=8000)/Raw('x' * 20)

7. Use scapy to generate PPPoL2TP IPv6 raw packet test_pppol2tp.raw,
   source/destination address and port should be swapped in the template
   and traffic packets::

    a=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
    IPv6(dst="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    src="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(dport=4000, sport=8000)/Raw('x' * 20)

8. Setup raw flow type filter for flow director, configured queue is random
   queue between 0~63, such as 36::

    testpmd> flow_director_filter 0 mode raw add flow 24 fwd queue 36
    fd_id 1 packet test_pppol2tp.raw

9. Send matched swapped traffic packet, check receive packet from
   configured queue 36::

    p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
    UDP(sport=4000, dport=8000)/Raw('x' * 20)

10. Send matched inner dst IPv6, but non-matched inner src IPv6,
    sport, dport packets, check to receive packet from queue 36::

     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
     IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0002",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
     UDP(sport=4000, dport=8000)/Raw('x' * 20)
     p=(Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
     IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
     UDP(sport=4001, dport=8000)/Raw('x' * 20)
     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
     IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
     UDP(sport=4000, dport=8001)/Raw('x' * 20)

11. Send non-matched inner dst IPv6 packets, check to receive packet
    from queue 0::

     p=Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057)/
     IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0002")/
     UDP(sport=4000, dport=8000)/Raw('x' * 20)
