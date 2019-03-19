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

====================
Move RSS to rte_flow
====================
Description
===========

Generic flow API (rte_flow) has been actually defined to include RSS, but
till now, RSS is out of rte_flow. It was suggested to move existing RSS to
rte_flow. This can be better for users, and may save effort for CPK
development. RSS enabling: now, rte_flow API enabling RSS is support on
igb/ixgbe/i40e. RSS input set changing: now, rte flow API RSS input set is
support on i40e.

Notes: non-default RSS hash functions are not supported -- Operation not
supported.

Prerequisites
=============

1. Hardware:
   Fortville/82599/I350

2. Software:
   dpdk: http://dpdk.org/git/dpdk
   scapy: http://www.secdev.org/projects/scapy/

3. Bind the pf port to dpdk driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0 05:00.1

4. Configure eight packets ready sent to port 0::

    pkt1 = Ether(dst="00:00:00:00:01:00")/IP(src="10.0.0.1",dst="192.168.0.2")/SCTP(dport=80, sport=80)/("X"*48)
    pkt2 = Ether(dst="00:00:00:00:01:00")/IP(src="10.0.0.1",dst="192.168.0.2")/UDP(dport=50, sport=50)/("X"*48)
    pkt3 = Ether(dst="00:00:00:00:01:00")/IP(src="10.0.0.1",dst="192.168.0.3")/TCP(dport=50, sport=50)/("X"*48)
    pkt4 = Ether(dst="00:00:00:00:01:00")/IP(src="10.0.0.1",dst="192.168.0.2")/("X"*48)
    pkt5 = Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1",dst="2001::2",nh=132)/SCTP(dport=80, sport=80)/("X"*48)
    pkt6 = Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1",dst="2001::2")/UDP(dport=50, sport=50)/("X"*48)
    pkt7 = Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1",dst="2001::2")/TCP(dport=50, sport=50)/("X"*48)
    pkt8 = Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::1",dst="2001::2")/("X"*48)

Test case: disable and enable rss
=================================

1. Start the testpmd::

    ./testpmd -c 1ffff -n 4 -- -i --nb-cores=8 --rxq=4 --txq=4 --port-topology=chained
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Show port default RSS fuctions::

    testpmd> show port 0 rss-hash
    RSS functions:
     ipv4-frag ipv4-other ipv6-frag ipv6-other ip

   Send the ipv4-other packets with different src/dst ip address.
   All the packets are distributed to all the four queues.

3. disable all RSS fuctions::

    testpmd> flow create 0 ingress pattern end actions rss types none end / end
    Flow rule #0 created
    testpmd> show port 0 rss-hash
    RSS disabled

   Send the ipv4-udp packets with different src/dst ip address.
   All the packets are distributed to queue 0.
   Notes: only i40e support the command,
   others don't support the command created.

4. enable RSS fuction with all RSS hash type::

    testpmd> flow create 0 ingress pattern end actions rss types all end / end
    Flow rule #1 created
    testpmd> show port 0 rss-hash
    RSS functions:
     all ipv4-frag ipv4-tcp ipv4-udp ipv4-sctp ipv4-other ipv6-frag ipv6-tcp ipv6-udp ipv6-sctp ipv6-other l2-payload ip udp tcp sctp

   Send the ipv4-udp packets with different src/dst ip address.
   All the packets are distributed to all the four queues.

Notes: the default RSS functions are different among several NICs.
Here shows the printing of NIC with i40e driver.

Test case: enable ipv4-udp rss
==============================

1. Start the testpmd::

    ./testpmd -c 1ffff -n 4 -- -i --nb-cores=8 --rxq=4 --txq=4 --port-topology=chained
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Show port default RSS fuctions::

    testpmd> show port 0 rss-hash
    RSS functions:
     ipv4-frag ipv4-other ipv6-frag ipv6-other ip

   Send the ipv4-other packets with different src/dst ip address.
   All the packets are distributed to all the four queues.
   Send the ipv4-udp packets with different src/dst ip and sport/dport.
   All the packets are distributed to queue 0.
   Notes: different NICs has different default RSS type function.
   the result is for i40e.

3. Enable ipv4-udp, and set all the queues into RSS queue rule::

    testpmd> flow create 0 ingress pattern end actions rss types ipv4-udp end / end
    Flow rule #0 created
    testpmd> show port 0 rss-hash
    RSS functions:
     ipv4-udp udp

   Send the ipv4-other packets with different src/dst ip address.
   All the packets are distributed to queue 0.
   Send the ipv4-udp packets with different src/dst ip and sport/dport.
   All the packets are distributed to all the four queues.

Test case: set valid and invalid queue
======================================

1. Start the testpmd::

    ./testpmd -c 1ffff -n 4 -- -i --nb-cores=8 --rxq=16 --txq=16 --port-topology=chained
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Set queue 0, 8 and 15 into RSS queue rule::

    testpmd> flow create 0 ingress pattern end actions rss queues 0 8 15 end / end

   Send the ipv4-other packets with different src/dst ip address.
   All the packets are distributed to queue 0/8/15.
   Send the ipv4-udp packets with different src/dst ip and sport/dport.
   All the packets are distributed to queue 0.

3. Set a second RSS queue rule::

    testpmd> flow create 0 ingress pattern end actions rss queues 3 end / end
    testpmd> flow create 0 ingress pattern end actions rss types ipv4-udp end queues 3 end / end

   The two rules failed to be created.
   There can't be more than one RSS queue rule.

4. Reset the RSS queue rule::

    testpmd> flow flush 0
    testpmd> flow create 0 ingress pattern end actions rss types ipv4-udp end queues 3 end / end

   The rule is set successfully.
   Send the ipv4-other packets with different src/dst ip address.
   All the packets are distributed to queue 0.
   Send the ipv4-udp packets with different src/dst ip and sport/dport.
   All the packets are distributed to queue 0/8/15.

5. Set a wrong parameter: queue ID is 16 ::

    testpmd> flow create 0 ingress pattern end actions rss queues 16 end / end

   The rule failed to be created.

6. Set all the queues to the rule::

    testpmd> flow create 0 ingress pattern end actions rss queues 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 end / end

   Send the ipv4-other packets with different src/dst ip address.
   The packets may be distributed to any of the queue 0-15.

Notes: The max queue number may be different in different NIC types.
We can set different queue number in command line with different NIC types.

Test case: Different packet types
=================================

1. Start the testpmd::

    ./testpmd -c 1ffff -n 4 -- -i --nb-cores=8 --rxq=16 --txq=16 --port-topology=chained
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Set queue 1, 8 and 15 into RSS queue rule::

    testpmd> flow create 0 ingress pattern end actions rss types udp ipv4-tcp ipv6-sctp ipv4-other end queues 1 8 15 end / end

3. Send the eight packets to port 0.
   pkt2/pkt3/pkt4/pkt5/pkt6 are distributed to queue 1/8/15.
   Other packets are distributed to queue 0.

4. Set a different packet type RSS queue rule::

    testpmd> flow create 0 ingress pattern end actions rss types ipv6-other end queues 3 end / end

   The rule failed to be created.
   There can't be more than one RSS queue rule.

Test case: disable rss in command-line
======================================

1. Start the testpmd::

    ./testpmd -c 0x3 -n 4 -- -i --rxq=8 --txq=8 --disable-rss --port-topology=chained
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Send the eight packets to port 0.
   All the packets are distributed to queue 0.

3. enable all RSS function type::

    testpmd> flow create 0 ingress pattern end actions rss types all end / end

   Send the eight packets to port 0.
   All the packets are distributed to any of queue 0-7

   or set the RSS queue rule::

    testpmd> flow create 0 ingress pattern end actions rss types ipv6-tcp ipv4-udp sctp ipv6-other end queues 5 6 7 end / end

   Send the eight packets to port 0.
   pkt1/pkt2/pkt5/pkt7/pkt8 are distributed to queue 5/6/7.
   Other packets are distributed to queue 0.

4. Clean the rule::

    testpmd> flow flush 0

   Send the eight packets to port 0.
   All the packets are distributed to queue 0.

Test case: set key and key_len
==============================

Only i40e support key and key_len setting.

1. Start the testpmd::

    ./testpmd -c 1ffff -n 4 -- -i --nb-cores=8 --rxq=4 --txq=4 --port-topology=chained
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Set ipv4-udp RSS and show the default RSS key::

    testpmd> flow create 0 ingress pattern end actions rss types ipv4-udp end / end
    testpmd> show port 0 rss-hash key
    RSS functions:
     ipv4-udp udp
    RSS key:
    74657374706D6427732064656661756C74205253532068617368206B65792C206F7665727269646520697420666F722062657474

   Send the five packets to port 0::

    pkt1 = Ether(dst='00:00:00:00:01:00')/IP(src='0.0.0.0',dst='4.0.0.0')/UDP(sport=100,dport=200)/('X'*48)
    pkt2 = Ether(dst='00:00:00:00:01:00')/IP(src='0.0.0.0',dst='4.0.0.0')/UDP(sport=100,dport=201)/('X'*48)
    pkt3 = Ether(dst='00:00:00:00:01:00')/IP(src='0.0.0.0',dst='4.0.0.0')/UDP(sport=101,dport=201)/('X'*48)
    pkt4 = Ether(dst='00:00:00:00:01:00')/IP(src='0.0.0.0',dst='4.0.0.1')/UDP(sport=101,dport=201)/('X'*48)
    pkt5 = Ether(dst='00:00:00:00:01:00')/IP(src='0.0.0.1',dst='4.0.0.1')/UDP(sport=101,dport=201)/('X'*48)

   pkt1 is distributed to queue 1.
   pkt2 is distributed to queue 3.
   pkt3 is distributed to queue 3.
   pkt4 is distributed to queue 1.
   pkt5 is distributed to queue 2.

3. Set ipv4-udp key::

    testpmd> flow flush 0
    testpmd> flow create 0 ingress pattern end actions rss types ipv4-udp end key \
    1234567890123456789012345678901234567890FFFFFFFFFFFF1234567890123456789012345678901234567890FFFFFFFFFFFF / end
    testpmd> show port 0 rss-hash key
    RSS functions:
     ipv4-udp udp
    RSS key:
    1234567890123456789012345678901234567890FFFFFFFFFFFF1234567890123456789012345678901234567890FFFFFFFFFFFF

   Send the same five packets to port 0,
   pkt1 is distributed to queue 3.
   pkt2 is distributed to queue 2.
   pkt3 is distributed to queue 2.
   pkt4 is distributed to queue 0.
   pkt5 is distributed to queue 3.

4. Set ipv4-udp with truncating key_len::

    testpmd> flow flush 0
    testpmd> flow create 0 ingress pattern end actions rss types ipv4-udp end key \
    1234567890123456789012345678901234567890FFFFFFFFFFFF1234567890123456789012345678901234567890FFFFFFFFFFFF key_len 50 / end
    testpmd> show port 0 rss-hash key
    RSS functions:
     ipv4-udp udp
    RSS key:
    4439796BB54C5023B675EA5B124F9F30B8A2C03DDFDC4D02A08C9B334AF64A4C05C6FA343958D8557D99583AE138C92E81150366

   Send the same five packets to port 0,
   pkt1 is distributed to queue 3.
   pkt2 is distributed to queue 3.
   pkt3 is distributed to queue 0.
   pkt4 is distributed to queue 1.
   pkt5 is distributed to queue 0.

   The key length is 52 bytes, if setting it shorter than 52, the key value doesn't take effect.
   The showed key value is an invalid value, not the default value.
   The key length is different among different NIC types.

5. Set ipv4-udp with padding key_len::

    testpmd> flow flush 0
    testpmd> flow create 0 ingress pattern end actions rss types ipv4-udp end key \
    1234567890123456789012345678901234567890FFFFFFFFFFFF1234567890123456789012345678901234567890FFFFFF key_len 52 / end
    testpmd> show port 0 rss-hash key
    RSS functions:
     ipv4-udp udp
    RSS key:
    1234567890123456789012345678901234567890FFFFFFFFFFFF1234567890123456789012345678901234567890FFFFFF657474

   Send the same five packets to port 0,
   pkt1 is distributed to queue 3.
   pkt2 is distributed to queue 2.
   pkt3 is distributed to queue 2.
   pkt4 is distributed to queue 0.
   pkt5 is distributed to queue 3.

   The lengh of key is 49 bytes, but the key_len is 52,
   so the last three bytes of key is padded by default value.

Test case: Flow directory rule and RSS rule combination
=======================================================

1. Start the testpmd::

    ./testpmd -c 1ffff -n 4 -- -i --nb-cores=8 --rxq=16 --txq=16 --pkt-filter-mode=perfect
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Set a RSS queue rule::

    testpmd> flow create 0 ingress pattern end actions rss types ipv4-udp end queues 6 7 8 end / end

   Send pkt2 to port 0, pkt2 is distributed to queue 8.

3. Set a flow directory rule::

    testpmd> flow create 0 ingress pattern eth / ipv4 src is 10.0.0.1 dst is 192.168.0.2 / udp src is 50 dst is 50 / end actions queue index 1 / end

   Send pkt2 to port 0, pkt2 is distributed to queue 1.

4. Destroy the flow directory rule::

    testpmd> flow destroy 0 rule 1

   Send pkt2 to port 0, pkt2 is distributed to queue 8 again.
   So flow directory filter is priority to RSS hash filter.

Test case: Set queue-region generic flow api
==============================================
 
1. Start the testpmd::

    ./testpmd -c 1ffff -n 4 -- -i --nb-cores=16 --rxq=16 --txq=16 --port-topology=chained
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Set a RSS queue rule::

    testpmd> flow create 0 ingress pattern end actions rss types ipv4-tcp end queues 7 8 10 11 12 14 15 end / end

3. Send pkt to port 0::

    pkt1 = Ether(dst="00:00:00:00:01:00", src="52:00:00:00:00:00")/Dot1Q(prio=1) \
    /IP(src="10.0.0.1",dst="192.168.0.2")/TCP(dport=80, sport=80)/("X"*48)
    pkt2 = Ether(dst="00:00:00:00:01:00", src="52:00:00:00:00:00")/Dot1Q(prio=2) \
    /IP(src="10.0.0.1",dst="192.168.0.2")/TCP(dport=80, sport=80)/("X"*48)
    pkt3 = Ether(dst="00:00:00:00:01:00", src="52:00:00:00:00:00")/Dot1Q(prio=3) \
    /IP(src="10.0.0.1",dst="192.168.0.2")/TCP(dport=80, sport=80)/("X"*48)

   They are all distributed to queue 8.

4. Set three queue regions::

    testpmd> flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 7 8 end / end
    testpmd> flow create 0 ingress pattern vlan tci is 0x4000 / end actions rss queues 11 12 end / end
    testpmd> flow create 0 ingress pattern vlan tci is 0x6000 / end actions rss queues 15 end / end

   Send the 3 packets to port 0. They are distributed to queue 7/11/15.
   So the flow directory filter is priority to RSS hash filter.

5. Flush the L2-payload rule::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i-      => RSS
    1       0       0       i-      VLAN => RSS
    2       0       0       i-      VLAN => RSS
    3       0       0       i-      VLAN => RSS

    testpmd> flow destroy 0 rule 2
    Flow rule #2 destroyed
    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i-      => RSS
    1       0       0       i-      VLAN => RSS
    3       0       0       i-      VLAN => RSS

   Send the 3 packets to port 0. They are all distributed to queue 8.
   Queue region only can be deleted all or none.

Test case: Set queue region with invalid parameter
==================================================

1. Start the testpmd::

    ./testpmd -c 1ffff -n 4 -- -i --nb-cores=16 --rxq=16 --txq=16 --port-topology=chained
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Set a RSS queue rule::

    testpmd> flow create 0 ingress pattern end actions rss queues 8 10 11 12 15 end / end

3. Set invalid queue ID "9" to queue region::

    testpmd> flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 8 9 end / end
    Caught error type 11 (specific action): cause: 0x7ffda008efe8, no valid queues

   Queue of queue region must be included in rss function appointed queue.

4. Set discontinuous queue ID to queue region::

    testpmd> flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 8 10 end / end
    Caught error type 11 (specific action): cause: 0x7ffda008efe8, no valid queues

5. Set invalid queue number to queue region::

    testpmd> flow create 0 ingress pattern vlan tci is 0x4000 / end actions rss queues 10 11 12 end / end
    i40e_flow_parse_rss_action(): The region sizes should be any of the following values: 1, 2, 4, 8, 16, 32, 64 as long as the total number of queues do not exceed the VSI allocation
    Caught error type 2 (flow rule (handle)): Failed to create flow.

Test case: Queue region and RSS rule combination
=========================================================

Notes: Queue region is only supported by fortville, so this case only can
be implemented with fortville.

1. Start the testpmd::

    ./testpmd -c 1ffff -n 4 -- -i --nb-cores=8 --rxq=16 --txq=16 --port-topology=chained
    testpmd> port config all rss all
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

2. Set a queue region::

    testpmd> set port 0 queue-region region_id 0 queue_start_index 1 queue_num 1
    testpmd> set port 0 queue-region region_id 0 flowtype 31
    testpmd> set port 0 queue-region flush on

   Send pkt2 to port 0. It is distributed to queue 1.

3. Set a RSS queue rule::

    testpmd> flow create 0 ingress pattern end actions rss types ipv4-udp end queues 6 7 end / end

   Send pkt2 to port 0. It is still distributed to queue 1.

4. flush the queue region::

    testpmd> set port 0 queue-region flush off 

   Send pkt2 to port 0. It is distributed to queue 7.
   Queue region is priority to RSS queue rule.
