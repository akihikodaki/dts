.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2017 Intel Corporation

===============
DDP GTP Qregion 
===============

DDP profile 0x80000008 adds support for GTP with IPv4 or IPv6 payload. 
The test case plan focus on more DDP GTP requirements as below. For DDP 
GTP introduction, please refer to DDP GTP test plan. 

Requirements
============
1. GTP-C distributed to control plane queues region using outer IP 
   destination address as hash input set (there is no inner IP headers 
   for GTP-C packets)
2. GTP-U distributed to data plane queues region using inner IP source
   address as hash input set.
3. GTP-C distributed to control plane queues region using TEID as hash
   input set. 
4. GTP-U distributed to data plane queues region using TEID and inner 
   packet 5-tuple as hash input set.
5. Requirements 1 and 2 should be possible for IPv6 addresses to use 64,
   48 or 32-bit prefixes instead of full address.

Intel® Ethernet 700 Series supports queue regions configuration for RSS,
so different traffic classes or different packet classification types
can be separated to different queue regions which includes several queues.
Support to set hash input set info for RSS flexible payload, then enable
new protocols' RSS.
Dynamic flow type feature introduces GTP pctype and flow type, design 
and add queue region/queue range mapping as below table. For more detailed 
and relative information, please refer to dynamic flow type and queue 
region test plan::

    +-------------+------------+------------+--------------+-------------+
    | Packet Type |   PCTypes  | Flow Types | Queue region | Queue range |  
    +-------------+------------+------------+--------------+-------------+
    | GTP-U IPv4  |     22     |    26      |      0       |     1~8     |   
    +-------------+------------+------------+--------------+-------------+
    | GTP-U IPv6  |     23     |    23      |      1       |     10~25   |
    +-------------+------------+------------+--------------+-------------+
    | GTP-U PAY4  |     24     |    24      |      2       |     30~37   |   
    +-------------+------------+------------+--------------+-------------+
    | GTP-C PAY4  |     25     |    25      |      3       |     40~55   |   
    +-------------+------------+------------+--------------+-------------+
	
Prerequisites
=============

1. Host PF in DPDK driver::

    ./tools/dpdk-devbind.py -b igb_uio 81:00.0

2. Start testpmd on host, set chained port topology mode, add txq/rxq to 
   enable multi-queues. In general, PF's max queue is 64::

    ./<build>/app/dpdk-testpmd -c f -n 4 -- -i --port-topology=chained --txq=64 --rxq=64


Load/delete dynamic device personalization 
==========================================

1. Stop testpmd port before loading profile::

    testpmd > port stop all

2. Load gtp.pkgo file to the memory buffer, save original configuration 
   and return in the same buffer to the gtp.bak file::

    testpmd > ddp add (port_id) /tmp/gtp.pkgo,/tmp/gtp.bak

3. Remove profile from the network adapter and restore original
   configuration::

    testpmd > ddp del (port_id) /tmp/gtp.bak
	
4. Start testpmd port::

    testpmd > port start all

Note:

1. Gtp.pkgo profile has been released publicly. You could download below
   version to do relative test.
   https://downloadcenter.intel.com/download/27587

2. Loading DDP is the prerequisite for below GTP relative cases. Load
   profile again once restarting testpmd to let software detect this
   event, although has “profile has already existed” reminder.


Flow type and queue region mapping setting
==========================================
1. As above mapping table, set queue region on a port::

    testpmd> set port 0 queue-region region_id 0 queue_start_index 1 queue_num 8
    testpmd> set port 0 queue-region region_id 1 queue_start_index 10 queue_num 16
    testpmd> set port 0 queue-region region_id 2 queue_start_index 30 queue_num 8
    testpmd> set port 0 queue-region region_id 3 queue_start_index 40 queue_num 16
	
2. Set the mapping of flow type to region index on a port::

    testpmd> set port 0 queue-region region_id 0 flowtype 26
    testpmd> set port 0 queue-region region_id 1 flowtype 23
    testpmd> set port 0 queue-region region_id 2 flowtype 24
    testpmd> set port 0 queue-region region_id 3 flowtype 25
    testpmd> set port 0 queue-region flush on

3. flush all queue regions::
 
    testpmd> set port 0 queue-region flush off


Test Case: Outer IPv6 dst controls GTP-C queue in queue region
==============================================================

1. Check flow ptype to pctype mapping::

    testpmd> show port 0 pctype mapping
	
2. Update GTP-C flow type id 25 to pctype id 25 mapping item::

    testpmd> port config 0 pctype mapping update 25 25
	
3. Check flow ptype to pctype mapping adds 25 this mapping 

4. Reset GTP-C hash configure::

    testpmd> port config 0 pctype 25 hash_inset clear all

5. Outer dst address words are 50~57, enable hash input set for outer dst::

    testpmd> port config 0 pctype 25 hash_inset set field 50
    testpmd> port config 0 pctype 25 hash_inset set field 51
    testpmd> port config 0 pctype 25 hash_inset set field 52
    testpmd> port config 0 pctype 25 hash_inset set field 53
    testpmd> port config 0 pctype 25 hash_inset set field 54
    testpmd> port config 0 pctype 25 hash_inset set field 55
    testpmd> port config 0 pctype 25 hash_inset set field 56
    testpmd> port config 0 pctype 25 hash_inset set field 57

6. Enable flow type id 25's RSS::

    testpmd> port config all rss 25

7. Start testpmd, set fwd rxonly, enable output print

8. Send outer dst GTP-C packet, check RSS could work, verify the queue is 
   between 40 and 55, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP(dport=2123)/
    GTP_U_Header()/Raw('x'*20)

9. Send different outer dst GTP-C packet, check pmd receives packet from 
   different queue but between 40 and 55::

    p=Ether()/IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0002")/UDP(dport=2123)/
    GTP_U_Header()/Raw('x'*20)
	
10. Send different outer src GTP-C packet, check pmd receives packet from 
    same queue::

     p=Ether()/IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0002",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
     UDP(dport=2123)/GTP_U_Header()/Raw('x'*20)

	 
Test Case: TEID controls GTP-C queue in queue region
====================================================

1. Check flow ptype to pctype mapping::

    testpmd> show port 0 pctype mapping
	
2. Update GTP-C flow type id 25 to pctype id 25 mapping item::

    testpmd> port config 0 pctype mapping update 25 25
	
3. Check flow ptype to pctype mapping adds 25 this mapping 

4. Reset GTP-C hash configure::

    testpmd> port config 0 pctype 25 hash_inset clear all

5. Teid words are 44 and 45, enable hash input set for teid::

    testpmd> port config 0 pctype 25 hash_inset set field 44
    testpmd> port config 0 pctype 25 hash_inset set field 45

6. Enable flow type id 25's RSS::

    testpmd> port config all rss 25

7. Start testpmd, set fwd rxonly, enable output print

8. Send teid GTP-C packet, check RSS could work, verify the queue is 
   between 40 and 55, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IPv6()/UDP(dport=2123)/GTP_U_Header(teid=0xfe)/Raw('x'*20) 

9. Send different teid GTP-C packet, check receive packet from different 
   queue but between 40 and 55::

    p=Ether()/IPv6()/UDP(dport=2123)/GTP_U_Header(teid=0xff)/Raw('x'*20)


Test Case: TEID controls GTP-U IPv4 queue in queue region
=========================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping
	
2. Update GTP-U IPv4 flow type id 26 to pctype id 22 mapping item::

    testpmd> port config 0 pctype mapping update 22 26
	
3. Check flow ptype to pctype mapping adds 26 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv4 hash configure::
    
    testpmd> port config 0 pctype 22 hash_inset clear all
	
5. Teid words are 44 and 45, enable hash input set for teid::
    
    testpmd> port config 0 pctype 22 hash_inset set field 44
    testpmd> port config 0 pctype 22 hash_inset set field 45
	
6. Enable flow type id 26's RSS::

    testpmd> port config all rss 26

7. Start testpmd, set fwd rxonly, enable output print

8. Send teid GTP-U IPv4 packet, check RSS could work, verify the queue is 
   between 1 and 8, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0xfe)/IP()/Raw('x'*20)
	
9. Send different teid GTP-U IPv4 packet, check receive packet from different
   queue but between 1 and 8::
   
    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=0xff)/IP()/Raw('x'*20)

	
Test Case: Sport controls GTP-U IPv4 queue in queue region
==========================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping
	
2. Update GTP-U IPv4 flow type id 26 to pctype id 22 mapping item::

    testpmd> port config 0 pctype mapping update 22 26
	
3. Check flow ptype to pctype mapping adds 26 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv4 hash configure::
    
    testpmd> port config 0 pctype 22 hash_inset clear all
	
5. Sport words are 29 and 30, enable hash input set for sport::
    
    testpmd> port config 0 pctype 22 hash_inset set field 29
    testpmd> port config 0 pctype 22 hash_inset set field 30
	
6. Enable flow type id 26's RSS::

    testpmd> port config all rss 26

7. Start testpmd, set fwd rxonly, enable output print

8. Send sport GTP-U IPv4 packet, check RSS could work, verify the queue is 
   between 1 and 8, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=30)/IP()/
    UDP(sport=100,dport=200)/Raw('x'*20)

9. Send different sport GTP-U IPv4 packet, check pmd receives packet from 
   different queue but between 1 and 8::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=30)/IP()/
    UDP(sport=101,dport=200)/Raw('x'*20)
	

Test Case: Dport controls GTP-U IPv4 queue in queue region
==========================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update GTP-U IPv4 flow type id 26 to pctype id 22 mapping item::

    testpmd> port config 0 pctype mapping update 22 26

3. Check flow ptype to pctype mapping adds 26 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv4 hash configure::
    
    testpmd> port config 0 pctype 22 hash_inset clear all

5. Dport words are 29 and 30, enable hash input set for dport::
    
    testpmd> port config 0 pctype 22 hash_inset set field 29
    testpmd> port config 0 pctype 22 hash_inset set field 30

6. Enable flow type id 26's RSS::

    testpmd> port config all rss 26

7. Start testpmd, set fwd rxonly, enable output print

8. Send dprot GTP-U IPv4 packet, check RSS could work, verify the queue is 
   between 1 and 8, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=30)/IP()/
    UDP(sport=100,dport=200)/Raw('x'*20)

9. Send different dport GTP-U IPv4 packet, check receive packet from different 
   queue but between 1 and 8::
    
    p=Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=30)/IP()/
    UDP(sport=100,dport=201)/Raw('x'*20)


Test Case: Inner IP src controls GTP-U IPv4 queue in queue region
=================================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping
	
2. Update GTP-U IPv4 flow type id 26 to pctype id 22 mapping item::

    testpmd> port config 0 pctype mapping update 22 26
	
3. Check flow ptype to pctype mapping adds 26 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv4 hash configure::
    
    testpmd> port config 0 pctype 22 hash_inset clear all
	
5. Inner source words are 15 and 16, enable hash input set for inner src::
    
    testpmd> port config 0 pctype 22 hash_inset set field 15
    testpmd> port config 0 pctype 22 hash_inset set field 16
	
6. Enable flow type id 26's RSS::

    testpmd> port config all rss 26

7. Start testpmd, set fwd rxonly, enable output print

8. Send inner src GTP-U IPv4 packet, check RSS could work, verify the queue is 
   between 1 and 8, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP()/Raw('x'*20)
	
9. Send different src GTP-U IPv4 packet, check pmd receives packet from different 
   queue but between 1 and 8::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IP(src="1.1.1.2",dst="2.2.2.2")/UDP()/Raw('x'*20)

10. Send different dst GTP-U IPv4 packet, check pmd receives packet from same
    queue::

     p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
     IP(src="1.1.1.1",dst="2.2.2.3")/UDP()/Raw('x'*20)
	 

Test Case: Inner IP dst controls GTP-U IPv4 queue in queue region
=================================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping
	
2. Update GTP-U IPv4 flow type id 26 to pctype id 22 mapping item::

    testpmd> port config 0 pctype mapping update 22 26
	
3. Check flow ptype to pctype mapping adds 26 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv4 hash configure::
    
    testpmd> port config 0 pctype 22 hash_inset clear all
	
5. Inner dst words are 27 and 28, enable hash input set for inner dst::
    
    testpmd> port config 0 pctype 22 hash_inset set field 27
    testpmd> port config 0 pctype 22 hash_inset set field 28
	
6. Enable flow type id 26's RSS::

    testpmd> port config all rss 26

7. Start testpmd, set fwd rxonly, enable output print

8. Send inner dst GTP-U IPv4 packet, check RSS could work, verify the queue is 
   between 1 and 8, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IP(src="1.1.1.1",dst="2.2.2.2")/UDP()/Raw('x'*20)
	
9. Send different dst address GTP-U IPv4 packet, check pmd receives packet 
   from different queue but between 1 and 8::
    
    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IP(src="1.1.1.1",dst="2.2.2.3")/UDP()/Raw('x'*20)

10. Send different src address, check pmd receives packet from same queue::

     p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
     IP(src="1.1.1.2",dst="2.2.2.2")/UDP()/Raw('x'*20)
	 

Test Case: TEID controls GTP-U IPv6 queue in queue region
=========================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update GTP-U IPv6 flow type id 23 to pctype id 23 mapping item::

    testpmd> port config 0 pctype mapping update 23 23

3. Check flow ptype to pctype mapping adds 23 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv6 hash configure::
    
    testpmd> port config 0 pctype 23 hash_inset clear all

5. Teid words are 44 and 45, enable hash input set for teid::
    
    testpmd> port config 0 pctype 23 hash_inset set field 44
    testpmd> port config 0 pctype 23 hash_inset set field 45

6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send teid GTP-U IPv6 packet, check RSS could work, verify the queue is 
   between 10 and 25, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0xfe)/IPv6()/
    UDP(sport=100,dport=200)/Raw('x'*20)

9. Send different teid GTP-U IPv4 packet, check pmd receives packet from 
   different queue but between 10 and 25::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=0xff)/IPv6()/
    UDP(sport=100,dport=200)/Raw('x'*20)

	
Test Case: Sport controls GTP-U IPv6 queue in queue region
==========================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping
	
2. Update GTP-U IPv6 flow type id 23 to pctype id 23 mapping item::

    testpmd> port config 0 pctype mapping update 23 23
	
3. Check flow ptype to pctype mapping adds 23 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv6 hash configure::
    
    testpmd> port config 0 pctype 23 hash_inset clear all
	
5. Sport words are 29 and 30, enable hash input set for sport::
    
    testpmd> port config 0 pctype 23 hash_inset set field 29
    testpmd> port config 0 pctype 23 hash_inset set field 30
	
6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send sport GTP-U IPv6 packet, check RSS could work, verify the queue is 
   between 10 and 25, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/IPv6()/
    UDP(sport=100,dport=200)/Raw('x'*20)

9. Send different sport GTP-U IPv6 packet, check pmd receives packet from 
   different queue but between 10 and 25::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/IPv6()/
    UDP(sport=101,dport=200)/Raw('x'*20)


Test Case: Dport controls GTP-U IPv6 queue in queue region
==========================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update GTP-U IPv6 flow type id 23 to pctype id 23 mapping item::

    testpmd> port config 0 pctype mapping update 23 23

3. Check flow ptype to pctype mapping adds 23 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv6 hash configure::
    
    testpmd> port config 0 pctype 23 hash_inset clear all

5. Dport words are 29 and 30, enable hash input set for dport::
    
    testpmd> port config 0 pctype 23 hash_inset set field 29
    testpmd> port config 0 pctype 23 hash_inset set field 30

6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send dport GTP-U IPv6 packet, check RSS could work, verify the queue 
   is between 10 and 25, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/IPv6()/
    UDP(sport=100,dport=200)/Raw('x'*20)

9. Send different dport GTP-U IPv6 packet, check pmd receives packet from 
   different queue but between 10 and 25::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/IPv6()/
    UDP(sport=100,dport=201)/Raw('x'*20)



Test Case: Inner IPv6 src controls GTP-U IPv6 queue in queue region
===================================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping
	
2. Update GTP-U IPv6 flow type id 23 to pctype id 23 mapping item::

    testpmd> port config 0 pctype mapping update 23 23
	
3. Check flow ptype to pctype mapping adds 23 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv6 hash configure::
    
    testpmd> port config 0 pctype 23 hash_inset clear all

5. Inner IPv6 src words are 13~20, enable hash input set for inner src::
    
    testpmd> port config 0 pctype 23 hash_inset set field 13
    testpmd> port config 0 pctype 23 hash_inset set field 14
    testpmd> port config 0 pctype 23 hash_inset set field 15
    testpmd> port config 0 pctype 23 hash_inset set field 16
    testpmd> port config 0 pctype 23 hash_inset set field 17
    testpmd> port config 0 pctype 23 hash_inset set field 18
    testpmd> port config 0 pctype 23 hash_inset set field 19
    testpmd> port config 0 pctype 23 hash_inset set field 20
	
6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send inner src address GTP-U IPv6 packets, check RSS could work, verify 
   the queue is between 10 and 25, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP()/Raw('x'*20)

9. Send different inner src GTP-U IPv6 packet, check pmd receives packet 
   from different queue but between 10 and 25::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0002",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP()/Raw('x'*20)
		
10. Send different inner dst GTP-U IPv6 packet, check pmd receives packet 
    from same queue::

     p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
     IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0002)/UDP()/Raw('x'*20)

Test Case: Inner IPv6 dst controls GTP-U IPv6 queue in queue region
===================================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping
	
2. Update GTP-U IPv6 flow type id 23 to pctype id 23 mapping item::

    testpmd> port config 0 pctype mapping update 23 23
	
3. Check flow ptype to pctype mapping adds 23 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv6 hash configure::
    
    testpmd> port config 0 pctype 23 hash_inset clear all
	
5. Inner IPv6 dst words are 21~28, enable hash input set for inner dst::
    
    testpmd> port config 0 pctype 23 hash_inset set field 21
    testpmd> port config 0 pctype 23 hash_inset set field 22
    testpmd> port config 0 pctype 23 hash_inset set field 23
    testpmd> port config 0 pctype 23 hash_inset set field 24
    testpmd> port config 0 pctype 23 hash_inset set field 25
    testpmd> port config 0 pctype 23 hash_inset set field 26
    testpmd> port config 0 pctype 23 hash_inset set field 27
    testpmd> port config 0 pctype 23 hash_inset set field 28
	 
6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send inner dst GTP-U IPv6 packets, check RSS could work, verify the 
   queue is between 10 and 25, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP()/Raw('x'*20)

9. Send different inner dst GTP-U IPv6 packets, check pmd receives packet 
   from different queue but between 10 and 25::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0002")/UDP()/Raw('x'*20)

10. Send different inner src GTP-U IPv6 packets, check pmd receives packet 
    from same queue::

     p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
     IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0002",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP()/Raw('x'*20)

Test Case: Outer 64 bit prefix dst controls GTP-C queue
=======================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update GTP-C flow type id 25 to pctype id 25 mapping item::

    testpmd> port config 0 pctype mapping update 25 25

3. Check flow type to pctype mapping adds 25 this mapping

4. Reset GTP-C hash configure::

    testpmd> port config 0 pctype 25 hash_inset clear all

5. Outer dst address words are 50~57, only setting 50~53 words means 64 bits
   prefixes, enable hash input set for outer dst::

    testpmd> port config 0 pctype 25 hash_inset set field 50
    testpmd> port config 0 pctype 25 hash_inset set field 51
    testpmd> port config 0 pctype 25 hash_inset set field 52
    testpmd> port config 0 pctype 25 hash_inset set field 53

6. Enable flow type id 25's RSS::

    testpmd> port config all rss 25

7. Start testpmd, set fwd rxonly, enable output print

8. Send outer dst GTP-C packet, check RSS could work, verify the queue is
   between 40 and 55, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP(dport=2123)/
    GTP_U_Header()/Raw('x'*20)

9. Send different outer dst 64 bit prefixes GTP-C packet, check pmd receives
   packet from different queue but between 40 and 55::

    p=Ether()/IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0001:0000:8a2e:0370:0001")/UDP(dport=2123)/
    GTP_U_Header()/Raw('x'*20)

10. Send different outer dst 64 bit suffixal GTP-C packet, check pmd receives
    packet from same queue::

     p=Ether()/IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0002")/UDP(dport=2123)/
     GTP_U_Header()/Raw('x'*20)

11. Send different outer src GTP-C packet, check pmd receives packet from
    same queue::

     p=Ether()/IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0002",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/
     UDP(dport=2123)/GTP_U_Header()/Raw('x'*20)


Test Case: Inner 48 bit prefix src controls GTP-U IPv6 queue
============================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update GTP-U IPv6 flow type id 23 to pctype id 23 mapping item::

    testpmd> port config 0 pctype mapping update 23 23

3. Check flow type to pctype mapping adds 23 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv6 hash configure::

    testpmd> port config 0 pctype 23 hash_inset clear all

5. Inner IPv6 src words are 13~20, only setting 13~15 words means 48 bit prefixes,
   enable hash input set for inner src::

    testpmd> port config 0 pctype 23 hash_inset set field 13
    testpmd> port config 0 pctype 23 hash_inset set field 14
    testpmd> port config 0 pctype 23 hash_inset set field 15

6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send inner src address GTP-U IPv6 packets, check RSS could work, verify
   the queue is between 10 and 25, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP()/Raw('x'*20)

9. Send different inner src 48 bit prefixes GTP-U IPv6 packet, check pmd
   receives packet from different queue but between 10 and 25::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IPv6(src="1001:0db8:85a4:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP()/Raw('x'*20)

10. Send different inner src 48 bit suffixal GTP-C packet, check pmd receives
    packet from same queue::

     p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
     IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0002",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP()/Raw('x'*20)

11. Send different inner dst GTP-U IPv6 packet, check pmd receives packet
    from same queue::

     p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
     IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0002")/UDP()/Raw('x'*20)


Test Case: Inner 32 bit prefix dst controls GTP-U IPv6 queue
============================================================
1. Check flow type to pctype mapping::

    testpmd> show port 0 pctype mapping

2. Update GTP-U IPv6 flow type id 23 to pctype id 23 mapping item::

    testpmd> port config 0 pctype mapping update 23 23

3. Check flow ptype to pctype mapping adds 23 this mapping::

    testpmd> show port 0 pctype mapping

4. Reset GTP-U IPv6 hash configure::

    testpmd> port config 0 pctype 23 hash_inset clear all

5. Inner IPv6 dst words are 21~28, only setting 21~22 words means 32 bit prefixes,
   enable hash input set for inner dst::

    testpmd> port config 0 pctype 23 hash_inset set field 21
    testpmd> port config 0 pctype 23 hash_inset set field 22

6. Enable flow type id 23's RSS::

    testpmd> port config all rss 23

7. Start testpmd, set fwd rxonly, enable output print

8. Send inner dst GTP-U IPv6 packets, check RSS could work, verify the
   queue is between 10 and 25, print RTE_MBUF_F_RX_RSS_HASH::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP()/Raw('x'*20)

9. Send different inner dst 32 bit prefixes GTP-U IPv6 packets, check pmd
   receives packet from different queue but between 10 and 25::

    p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
    IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
    dst="2001:0db9:85a3:0000:0000:8a2e:0370:0001")/UDP()/Raw('x'*20)

10. Send different inner dst 32 bit suffixal GTP-U packet, check pmd receives
    packet from same queue::

     p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
     IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0001",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0002")/UDP()/Raw('x'*20)

11. Send different inner src GTP-U IPv6 packets, check pmd receives packet
    from same queue::

     p=Ether()/IP()/UDP(dport=2152)/GTP_U_Header(teid=30)/
     IPv6(src="1001:0db8:85a3:0000:0000:8a2e:0370:0002",
     dst="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP()/Raw('x'*20)

