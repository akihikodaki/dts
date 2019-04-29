.. Copyright (c) <2014>, Intel Corporation
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

======================================
Layer-3 Forwarding with Access Control
======================================

Description
===========

This document contains the test plan and results for testing
``l3fwd-acl`` using the ACL library for access control and L3
forwarding.

The ``l3fwd-acl`` application uses an IPv4 5-tuple syntax for packet
matching. The 5-tuple consist of source IP address, destination IP
address, source port, destination port and a protocol identifier.

The ``l3fwd-acl`` application supports two types of rules:

#. Route information which is used for L3 forwarding.
#. An access control list which defines the black list to block.

The ``l3fwd-acl`` application needs to load ACL and route rules before
running. Route rules are mandatory while ACL rules are optional. After
receiving packets from ports, ``l3fwd-acl`` will extract the necessary
info from the TCP/IP header of received packets and perform a lookup
in a rule database to figure out whether the packets should be dropped
(in the ACL range) or forwarded to desired ports.


Prerequisites
=============

1. The DUT has at least 2 DPDK supported IXGBE/I40E NIC ports::

    Tester      DUT
    eth1  <---> PORT 0
    eth2  <---> PORT 1

2. Support igb_uio driver::

    modprobe uio
    insmod  ./x86_64-native-linuxapp-gcc/kmod/igb_uio.ko
    ./usertools/dpdk-devbind.py --bind=igb_uio 04:00.0 04:00.1

Test Case: packet match ACL rule
================================

Ipv4 packet match source ip address 200.10.0.1 will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv4.db
    @200.10.0.1/32 0.0.0.0/0 0 : 65535 0 : 65535 0/0
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv6.db
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one ipv4 packet with source ip address 200.10.0.1 will be dropped.
    Send one ipv4 packet with source ip address 200.10.0.2 will be forwarded to PORT0

Ipv4 packet match destination ip address 100.10.0.1 will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv4.db
    @0.0.0.0/0 100.10.0.1/32 0 : 65535 0 : 65535 0/0
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv6.db
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one ipv4 packet with destination ip address 100.10.0.1 will be dropped.
    Send one ipv4 packet with destination ip address 100.10.0.2 will be forwarded to PORT0

Ipv4 packet match source port 11 will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv4.db
    @0.0.0.0/0 0.0.0.0/0 11 : 11 0 : 65535 0/0
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv6.db
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one ipv4 packet with source port 11 will be dropped.
    Send one ipv4 packet with source port 1 will be forwarded to PORT0

Ipv4 packet match destination port 101 will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv4.db
    @0.0.0.0/0 0.0.0.0/0 0 : 65535 101 : 101 0/0
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv6.db
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one ipv4 packet with destination port 101 will be dropped.
    Send one ipv4 packet with destination port 1 will be forwarded to PORT0

Ipv4 packet match protocol TCP will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv4.db
    @0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 6/0xff
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv6.db
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one TCP ipv4 packet will be dropped.
    Send one UDP ipv4 packet will be forwarded to PORT0

Ipv4 packet match 5-tuple will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv4.db
    @200.10.0.1/32 100.10.0.1/32 11 : 11 101 : 101 0x06/0xff
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv6.db
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one TCP ipv4 packet with source ip address 200.10.0.1,
    destination ip address 100.10.0.1, source port 11, destination
    port 101 will be dropped.

    Send one TCP ipv4 packet with source ip address 200.10.0.2,
    destination ip address 100.10.0.1, source port 11, destination
    port 101 will be forwarded to PORT0.

Ipv6 packet match source ipv6 address 2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128 will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv6.db
    @2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0/0
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv4.db
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one ipv6 packet with source ip address 2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128 will be dropped.
    Send one ipv6 packet with source ip address 2001:0db8:85a3:08d3:1319:8a2e:0370:7342/128 will be forwarded to PORT0

Ipv6 packet match destination ipv6 address 2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128  will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv6.db
    @0:0:0:0:0:0:0:0/0 2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128 0 : 65535 0 : 65535 0/0
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv4.db
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one ipv6 packet with destination ip address 2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128 will be dropped.
    Send one ipv6 packet with destination ip address 2002:0db8:85a3:08d3:1319:8a2e:0370:7343/128 will be forwarded to PORT0

Ipv6 packet match source port 11 will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv6.db
    @0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 11 : 11 0 : 65535 0/0
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv4.db
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one ipv6 packet with source port 11 will be dropped.
    Send one ipv6 packet with source port 1 will be forwarded to PORT0

Ipv6 packet match destination port 101 will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv6.db
    @0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 101 : 101 0/0
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv4.db
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one ipv6 packet with destination port 101 will be dropped.
    Send one ipv6 packet with destination port 1 will be forwarded to PORT0

Ipv6 packet match protocol TCP will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv6.db
    @0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 6/0xff
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv4.db
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one TCP ipv6 packet will be dropped.
    Send one UDP ipv6 packet will be forwarded to PORT0

Ipv6 packet match 5-tuple will be dropped::

    Add one ACL rule and default route rule in /root/rule_ipv6.db
    @2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128 2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128 11 : 11 101 : 101 0x06/0xff
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one default rule in rule file /root/rule_ipv4.db
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
     --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one TCP ipv6 packet with source ip address 2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128,
    destination ip address 2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128,source port 11,
    destination port 101 will be dropped.

    Send one TCP ipv6 packet with source ip address 2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128,
    destination ip address 2002:0db8:85a3:08d3:1319:8a2e:0370:7343/128, source port 11,
    destination port 101 will be forwarded to PORT0.


Test Case: packet match Exact route rule
========================================
Add two exact rule as below in rule_ipv4.db::

	R200.10.0.1/32 100.10.0.1/32 11 : 11 101 : 101 0x06/0xff 0
	R200.20.0.1/32 100.20.0.1/32 12 : 12 102 : 102 0x06/0xff 1

Add two exact rule as below in rule_ipv6.db::

	R2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128 2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128 11 : 11 101 : 101 0x06/0xff 0
	R2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128 2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128 12 : 12 102 : 102 0x06/0xff 1

Start l3fwd-acl and send packet::

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    Send one TCP ipv4 packet with source ip address 200.10.0.1, destination
    ip address 100.10.0.1,source port 11, destination port 101 will be forward to PORT0.

    Send one TCP ipv4 packet with source ip address 200.20.0.1, destination
    ip address 100.20.0.1,source port 12, destination port 102 will be forward to PORT1.

    Send one TCP ipv6 packet with source ip address 2001:0db8:85a3:08d3:1319:8a2e:0370:7344,
    destination ip address 2002:0db8:85a3:08d3:1319:8a2e:0370:7344, source port 11,
    destination port 101 will be forward to PORT0.

    Send one TCP ipv6 packet with source ip address 2001:0db8:85a3:08d3:1319:8a2e:0370:7344,
    destination ip address 2002:0db8:85a3:08d3:1319:8a2e:0370:7344,source port 12,
    destination port 102 will be forward to PORT1.

Test Case: packet match LPM route rule
============================================
Add two LPM rule as below in rule_ipv4.db::

	R0.0.0.0/0 1.1.1.0/24 0 : 65535 0 : 65535 0x00/0x00 0
	R0.0.0.0/0 2.1.1.0/24 0 : 65535 0 : 65535 0x00/0x00 1

Add two LPM rule as below in rule_ipv6.db::

	R0:0:0:0:0:0:0:0/0 1:1:1:1:1:1:0:0/96 0 : 65535 0 : 65535 0x00/0x00 0
	R0:0:0:0:0:0:0:0/0 2:1:1:1:1:1:0:0/96 0 : 65535 0 : 65535 0x00/0x00 1

Start l3fwd-acl and send packet::

	./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
	--rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

	Send one TCP ipv4 packet with destination ip address 1.1.1.1 will be forward to PORT0.
	Send one TCP ipv4 packet with source ip address 2.1.1.1 will be forward to PORT1.

	Send one TCP ipv6 packet with destination ip address 1:1:1:1:1:1:0:0 will be forward to PORT0.
	Send one TCP ipv6 packet with source ip address 2:1:1:1:1:1:0:0 will be forward to PORT1.

Test Case: packet match by scalar function
============================================
Packet match 5-tuple will be dropped::

    Add one ACL rule and default route rule in rule_ipv4.db
    @200.10.0.1/32 100.10.0.1/32 11 : 11 101 : 101 0x06/0xff
    R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 0

    Add one ACL rule and default route rule in rule_ipv6.db
    @2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128 2002:0db8:85a3:08d3:1319:8a2e:0370:7344/101 11 : 11 101 : 101 0x06/0xff
    R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 0

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db" --scalar

    Send one TCP ipv4 packet with source ip address 200.10.0.1, destination ip address 100.10.0.1,
    source port 11, destination port 101 will be dropped.
    Send one TCP ipv4 packet with source ip address 200.10.0.2, destination ip address 100.10.0.1,
    source port 11, destination port 101 will be forwarded to PORT0.

    Send one TCP ipv6 packet with source ip address 2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128,
    destination ip address 2002:0db8:85a3:08d3:1319:8a2e:0370:7344/101, source port 11,
    destination port 101 will be dropped.

    Send one TCP ipv6 packet with source ip address 2001:0db8:85a3:08d3:1319:8a2e:0370:7343,
    destination ip address 2002:0db8:85a3:08d3:1319:8a2e:0370:7344, source port 11,
    destination port 101 will be forwarded to PORT0.

Test Case: Invalid ACL rule
============================================
Add two ACL rule as below in rule_ipv4.db::

	R0.0.0.0/0 1.1.1.0/24 12 : 11 : 65535 0x00/0x00 0
	R0.0.0.0/0 2.1.1.0/24 0 : 65535 0 : 65535 0x00/0x00 1

Add two ACL rule as below in rule_ipv6.db::

	R0:0:0:0:0:0:0:0/0 1:1:1:1:1:1:0:0/96 0 : 65535 0 : 65535 0
	R0:0:0:0:0:0:0:0/0 2:1:1:1:1:1:0:0/96 0 : 65535 0 : 65535 0x00/0x00 1

Start l3fwd-acl::

    ./examples/l3fwd-acl/build/l3fwd-acl -c ff -n 3 -- -p 0x3 --config="(0,0,2),(1,0,3)"
    --rule_ipv4="/root/rule_ipv4.db" --rule_ipv6="/root/rule_ipv6.db"

    The l3fwdacl will not set up because of ivalid ACL rule.
