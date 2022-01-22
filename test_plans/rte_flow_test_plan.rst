.. # BSD LICENSE
    #
    # Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
    # Copyright © 2018[, 2020] The University of New Hampshire. All rights reserved.
    # All rights reserved.
    #
    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions
    # are met:
    #
    #   * Redistributions of source code must retain the above copyright
    #     notice, this list of conditions and the following disclaimer.
    #   * Redistributions in binary form must reproduce the above copyright
    #     notice, this list of conditions and the following disclaimer in
    #     the documentation and/or other materials provided with the
    #     distribution.
    #   * Neither the name of Intel Corporation nor the names of its
    #     contributors may be used to endorse or promote products derived
    #     from this software without specific prior written permission.
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    # A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    # OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    # SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    # LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    # DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    # THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

rte_flow Tests
========================================
This document contains the test plan for the rte_flow API.

Prerequisites
=============
The DUT must have one 10G Ethernet ports connected to one port on
Tester that are controlled by packet generator::

    dut_port_0 <---> tester_port_0

Assume the DUT 10G Ethernet ports' pci device id is as the following::

    dut_port_0 : "0000:05:00.0"
    mac_address: "00:00:00:00:01:00"

Bind the port to dpdk igb_uio driver::

    ./usertools/dpdk-devbind.py -b igb_uio 05:00.0

You will also need to have Python 3.6 installed along with scapy to create test packets.

Pattern Item and Property Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
We create a flow rule for each property in each pattern item. We then send one packet that is expected to pass,
and about four packets that are expected to fail.

We only test one pattern item and one property at a time.

Flow rules are created using **testpmd** and packets are created/sent using **scapy**.

NOTE: Some pattern items and properties could not be tested
due to the fact that testpmd does not support them. See **dpdk-dts/test_plans/unsupported.rst**
for a listing of these items and properties.

Item: ETH
~~~~~~~~~


Test Case: dst (destination MAC) rule
-------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

.. 

2. Set the test flow rule (If the Ethernet destination MAC is equal to 90:61:ae:fd:41:43, send the packet to queue 1):

::

    flow create 0 ingress pattern eth dst is 90:61:ae:fd:41:43 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether(dst="90:61:ae:fd:41:43") / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

           Pkt1 = Ether(dst=\"90:61:ae:fd:41:44") / ('\\x00' * 64)
           Pkt2 = Ether(dst=\"90:61:ae:fd:41:45") / ('\\x00' * 64)
           Pkt3 = Ether(dst=\"90:61:ae:fd:41:46") / ('\\x00' * 64)
           Pkt4 = Ether(dst=\"91:61:ae:fd:41:43") / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Test Case: src (source MAC) rule
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the Ethernet source MAC is equal to 90:61:ae:fd:41:43, send the packet to queue 1)

::

    flow create 0 ingress pattern eth src is 90:61:ae:fd:41:43 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether(dst="90:61:ae:fd:41:43") / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

            Pkt1 = Ether(dst=\"90:61:ae:fd:41:44") / ('\\x00' * 64)
            Pkt2 = Ether(dst=\"90:61:ae:fd:41:45") / ('\\x00' * 64)
            Pkt3 = Ether(dst=\"90:61:ae:fd:41:46") / ('\\x00' * 64)
            Pkt4 = Ether(dst=\"91:61:ae:fd:41:43") / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: type (EtherType or TPID) rule
-----------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the Ethernet type is 0x0800, send the packet to queue 1):

::

    flow create 0 ingress pattern eth type is 0x0800 / end actions queue index 1 / end

..

3. Send a packet that matches the rule: 

::

            Pkt0 = Ether(type=0x0800) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

            Pkt1 = Ether(type=0x0842) / ('\\x00' * 64)
            Pkt2 = Ether(type=0x8100) / ('\\x00' * 64)
            Pkt3 = Ether(type=0x9100) / ('\\x00' * 64)
            Pkt4 = Ether(type=0x8863) / ('\\x00' * 64)
            Pkt5 = Ether(type=0x9000) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Item: GRE
~~~~~~~~~

Test Case: protocol (protocol type) rule
-----------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the GRE protocol is equal to 0x0800,send the packet to queue 1) :

::


    flow create 0 ingress pattern gre protocol is 0x0800 / end actions queue index 1 / end

..

3. Send a packet that matches the rule: 

::

            Pkt0 = Ether() / GRE(proto=0x0800) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

            Pkt1 = Ether() / GRE(proto=0x0842) / ('\\x00' * 64)
            Pkt2 = Ether() / GRE(proto=0x8100) / ('\\x00' * 64)
            Pkt3 = Ether() / GRE(proto=0x0806) / ('\\x00' * 64)
            Pkt4 = Ether() / GRE(proto=0x809B) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Item: ICMP
~~~~~~~~~~

Test Case: icmp_type (ICMP message type) rule
----------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the ICMP type is 3, send the packet to queue 1) :

::


    flow create 0 ingress pattern icmp type is 3 / end actions queue index 1 / end

..

3. Send a packet that matches the rule: 

::

            Pkt0 = Ether() / ICMP(type=3) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

            Pkt1 = Ether() / ICMP(type=3) / ('\\x00' * 64)
            Pkt2 = Ether() / ICMP(type=13) / ('\\x00' * 64)
            Pkt3 = Ether() / ICMP(type=11) / ('\\x00' * 64)
            Pkt4 = Ether() / ICMP(type=12) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: icmp_code (ICMP message code) rule
-----------------------------------------------

NOTE: ICMP code meaning is dependent on type.
We tested type 3, code 3.

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the ICMP type is 3 and the ICMP code is 3, send the packet to queue 1) :

::

    flow create 0 ingress pattern icmp type is 3 code is 3 / end actions queue index 1 / end

..

3. Send a packet that matches the rule: 

::

 Pkt0 = Ether() / ICMP(type=3, code=3) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / ICMP(type=3, code=3) / ('\\x00' * 64)
    Pkt2 = Ether() / ICMP(type=3, code=0) / ('\\x00' * 64)
    Pkt3 = Ether() / ICMP(type=11, code=1) / ('\\x00' * 64)
    Pkt4 = Ether() / ICMP(type=12, code=2) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Item: IPv4
~~~~~~~~~~~

Test Case: tos (Type of Service) rule
----------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 type of service is 0, send the packet to queue 1) :

::


    flow create 0 ingress pattern ipv4 tos is 0 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(tos=0) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(tos=2) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(tos=4) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(tos=8) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(tos=16) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: ttl (time to live) rule
-------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 packet's time to live is 64, send the packet to queue 1) :

::


   flow create 0 ingress pattern ipv4 ttl is 64 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(ttl=64) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

   Pkt1 = Ether() / IP(ttl=128) / ('\\x00' * 64)
   Pkt2 = Ether() / IP(ttl=255) / ('\\x00' * 64)
   Pkt3 = Ether() / IP(ttl=32) / ('\\x00' * 64)
   Pkt4 = Ether() / IP(ttl=100) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Test Case: proto (IPv4 protocol) rule
----------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 protocol is 0x06, send the packet to queue 1) :

::

 flow create 0 ingress pattern ipv4 proto is 0x06 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(proto=0x06) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

   Pkt1 = Ether() / IP(proto=0x01) / ('\\x00' * 64)
   Pkt2 = Ether() / IP(proto=0x11) / ('\\x00' * 64)
   Pkt3 = Ether() / IP(proto=0x12) / ('\\x00' * 64)
   Pkt4 = Ether() / IP(proto=0x58) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: src (IPv4 source) rule
------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.5, send the packet to queue 1) :

::

   flow create 0 ingress pattern ipv4 src is 192.168.0.5 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=192.168.0.5) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=10.10.10.10) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=132.177.127.6) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=192.168.0.4) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=192.168.0.250) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Test Case: dst (IPv4 destination) rule
------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 destination is 192.168.0.5, send the packet to queue 1) :

::

    flow create 0 ingress pattern ipv4 dst is 192.168.0.5 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=192.168.0.5) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(dst=10.10.10.10) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(dst=132.177.127.6) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(dst=192.168.0.4) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(dst=192.168.0.250) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Item: IPv6
~~~~~~~~~~~

Test Case: tc (Traffic Class) rule
------------------------------------
1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv6 traffic class is 0, send the packet to queue 1) :

::

    flow create 0 ingress pattern ipv6 tc is 0 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IPv6(tc=0) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IPv6(tc=1) / ('\\x00' * 64)
    Pkt2 = Ether() / IPv6(tc=2) / ('\\x00' * 64)
    Pkt3 = Ether() / IPv6(tc=4) / ('\\x00' * 64)
    Pkt4 = Ether() / IPv6(tc=6) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: flow (Flow Code) rule
--------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv6 flow code is 0xABCD, send the packet to queue 1) :

::

    flow create 0 ingress pattern ipv6 flow is 0xABCD / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IPv6(fl=0xABCD) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

   Pkt1 = Ether() / IPv6(fl=0xABCE) / ('\\x00' * 64)
   Pkt2 = Ether() / IPv6(fl=0x0001) / ('\\x00' * 64)
   Pkt3 = Ether() / IPv6(fl=0xFFFF) / ('\\x00' * 64)
   Pkt4 = Ether() / IPv6(fl=0x1234) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: proto (IPv6 protocol/next header protocol) rule
--------------------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv6 protocol is 0x06, send the packet to queue 1) :

::

    flow create 0 ingress pattern ipv6 proto is 0x06 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IPv6(nh=6) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

   Pkt1 = Ether() / IPv6(nh=17) / ('\\x00' * 64)
   Pkt2 = Ether() / IPv6(nh=41) / ('\\x00' * 64)
   Pkt3 = Ether() / IPv6(nh=0) / ('\\x00' * 64)
   Pkt4 = Ether() / IPv6(nh=60) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: hop (Hop Limit) rule
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv6 hop limit is 64, send the packet to queue 1) :
::

    flow create 0 ingress pattern ipv6 hop is 64 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IPv6(hlim=64) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

   Pkt1 = Ether() / IPv6(hlim=128) / ('\\x00' * 64)
   Pkt2 = Ether() / IPv6(hlim=32) / ('\\x00' * 64)
   Pkt3 = Ether() / IPv6(hlim=255) / ('\\x00' * 64)
   Pkt4 = Ether() / IPv6(hlim=100) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Test Case: dst (IPv6 destination) rule
---------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv6 destination is 2001:...:b1c2, send the packet to queue 1) :

::

   flow create 0 ingress pattern ipv6 dst is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2\") / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3\") / ('\\x00' * 64)
    Pkt2 = Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c4\") / ('\\x00' * 64)
    Pkt3 = Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c5\") / ('\\x00' * 64)
    Pkt4 = Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c6\") / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Test Case: src (IPv6 source) rule
-----------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv6 destination is 2001:...b1c2, send the packet to queue 1) :

::

    flow create 0 ingress pattern ipv6 src is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2\") / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3\") / ('\\x00' * 64)
    Pkt2 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c4\") / ('\\x00' * 64)
    Pkt3 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c5\") / ('\\x00' * 64)
    Pkt4 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c6\") / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Item: SCTP
~~~~~~~~~~~

Test Case: src (source port) rule
-------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the SCTP source port is 3838, send the packet to queue 1) :

::

    flow create 0 ingress pattern sctp src is 3838 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP() / SCTP(sport=3838) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP() / SCTP(sport=3939) / ('\\x00' * 64)
    Pkt2 = Ether() / IP() / SCTP(sport=5000) / ('\\x00' * 64)
    Pkt3 = Ether() / IP() / SCTP(sport=1998) / ('\\x00' * 64)
    Pkt4 = Ether() / IP() / SCTP(sport=1028) / ('\\x00' * 64)

..

Test Case: dst (destination port) rule
-----------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the SCTP destination port is 3838, send the packet to queue 1) :

::

    flow create 0 ingress pattern sctp dst is 3838 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP() / SCTP(dport=3838) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP() / SCTP(dport=3939) / ('\\x00' * 64)
    Pkt2 = Ether() / IP() / SCTP(dport=5000) / ('\\x00' * 64)
    Pkt3 = Ether() / IP() / SCTP(dport=1998) / ('\\x00' * 64)
    Pkt4 = Ether() / IP() / SCTP(dport=1028) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Test Case: tag (SCTP header tag) rule
--------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the SCTP tag is equal to 12345, send the packet to queue 1) :

::

    flow create 0 ingress pattern sctp tag is 12345 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP() / SCTP(tag=12345) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

   Pkt1 = Ether() / IP() / SCTP(tag=12346) / ('\\x00' * 64)
   Pkt2 = Ether() / IP() / SCTP(tag=12) / ('\\x00' * 64)
   Pkt3 = Ether() / IP() / SCTP(tag=9999) / ('\\x00' * 64)
   Pkt4 = Ether() / IP() / SCTP(tag=42) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: cksum (SCTP header checksum) rule
-----------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the SCTP checksum is equal to 0x1535b67, send the packet to queue 1) :

::

    flow create 0 ingress pattern sctp cksum is 0x01535b67 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP() / SCTP(chksum=0x01535b67)

..

4. Send packets that do not match the rule:

::

   Pkt1 = Ether() / IP() / SCTP(chksum=0x01535b68)
   Pkt2 = Ether() / IP() / SCTP(chksum=0xdeadbeef)
   Pkt3 = Ether() / IP() / SCTP(chksum=0x12345678)
   Pkt4 = Ether() / IP() / SCTP(chksum=0x385030fe)

..

5. Check to make sure that only the pass packet was received by queue 1.

Item: TCP
~~~~~~~~~~~

Test Case: src (source port) rule
--------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the TCP source port is equal to 3838, send the packet to queue 1) :

::

    flow create 0 ingress pattern tcp src is 3838 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP() / TCP(sport=3838) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP() / TCP(sport=3939) / ('\\x00' * 64)
    Pkt2 = Ether() / IP() / TCP(sport=5000) / ('\\x00' * 64)
    Pkt3 = Ether() / IP() / TCP(sport=1998) / ('\\x00' * 64)
    Pkt4 = Ether() / IP() / TCP(sport=1028) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: dst (destination port) rule
-----------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the TCP destination port is equal to 3838, send the packet to queue 1) :

::

    flow create 0 ingress pattern tcp dst is 3838 / end actions queue index 1 / end

..


3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP() / TCP(dport=3838) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP() / TCP(dport=3939) / ('\\x00' * 64)
    Pkt2 = Ether() / IP() / TCP(dport=5000) / ('\\x00' * 64)
    Pkt3 = Ether() / IP() / TCP(dport=1998) / ('\\x00' * 64)
    Pkt4 = Ether() / IP() / TCP(dport=1028) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Test Case: flags (TCP flags) rule
-----------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the TCP flags are equal to 0x02, send the packet to queue 1) :

::

    flow create 0 ingress pattern tcp flags is 0x02 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP() / TCP(flags=0x02) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP() / TCP(flags=0x01) / ('\\x00' * 64)
    Pkt2 = Ether() / IP() / TCP(flags=0x04) / ('\\x00' * 64)
    Pkt3 = Ether() / IP() / TCP(flags=0x08) / ('\\x00' * 64)
    Pkt4 = Ether() / IP() / TCP(flags=0x10) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Item: UDP
~~~~~~~~~~~

Test Case: src (source port) rule
-------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the UDP source port is equal to 3838, send the packet to queue 1) :

::

    flow create 0 ingress pattern udp src is 3838 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::
    Pkt0 = Ether() / IP() / UDP(sport=3838) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP() / UDP(sport=3939) / ('\\x00' * 64)
    Pkt2 = Ether() / IP() / UDP(sport=5000) / ('\\x00' * 64)
    Pkt3 = Ether() / IP() / UDP(sport=1998) / ('\\x00' * 64)
    Pkt4 = Ether() / IP() / UDP(sport=1028) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: dst (destination port) rule
-----------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the UDP destination port is equal to 3838, send the packet to queue 1) :

::

    flow create 0 ingress pattern udp dst is 3838 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP() / UDP(dport=3838) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP() / UDP(dport=3939) / ('\\x00' * 64)
    Pkt2 = Ether() / IP() / UDP(dport=5000) / ('\\x00' * 64)
    Pkt3 = Ether() / IP() / UDP(dport=1998) / ('\\x00' * 64)
    Pkt4 = Ether() / IP() / UDP(dport=1028) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Item: VLAN
~~~~~~~~~~~

Test Case: tci (Tag Control Information) rule
-----------------------------------------------

NOTE: The VLAN tci is the combination of the fields pcp, dei, and vid.
We test them altogether as the tci and we test each field individually.

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the vlan tag control information value is 0xaaaa, send the packet to queue 1) :

::


    flow create 0 ingress pattern vlan tci is 0xaaaa / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / Dot1Q(prio = 0x0, id = 0x0, vlan = 0xbbb) / ('\\x00' * 64)
    Pkt2 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xccc) / ('\\x00' * 64)
    Pkt3 = Ether() / Dot1Q(prio = 0x5, id = 0x1, vlan = 0xaaa) / ('\\x00' * 64)
    Pkt4 = Ether() / Dot1Q(prio = 0x4, id = 0x0, vlan = 0xaaa) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: pcp (Priority Code Point) rule
--------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the VLAN priority code point is equal to 0x0, send the packet to queue 1) :

::

    flow create 0 ingress pattern vlan pcp is 0x0 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / Dot1Q(prio=0x0) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / Dot1Q(prio=0x1) / ('\\x00' * 64)
    Pkt2 = Ether() / Dot1Q(prio=0x2) / ('\\x00' * 64)
    Pkt3 = Ether() / Dot1Q(prio=0x3) / ('\\x00' * 64)
    Pkt4 = Ether() / Dot1Q(prio=0x7) / ('\\x00' * 64)

..

Test Case: dei (Drop Eligible Indicator) rule
-----------------------------------------------
NOTE: The only two possible values for dei are 0 and 1.

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the VLAN drop eligible indicator is equal to 0, send the packet to queue 1) :

::

    flow create 0 ingress pattern vlan dei is 0 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / Dot1Q(id=0)) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / Dot1Q(id=1) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Test Case: vid (VLAN identifier) rule
-----------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the VLAN identifier is equal to 0xabc, send the packet to queue 1) :

::

    flow create 0 ingress pattern vlan vid is 0xabc / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / Dot1Q(vlan=0xabc) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / Dot1Q(vlan=0xaaa) / ('\\x00' * 64)
    Pkt2 = Ether() / Dot1Q(vlan=0x123) / ('\\x00' * 64)
    Pkt3 = Ether() / Dot1Q(vlan=0x1f5) / ('\\x00' * 64)
    Pkt4 = Ether() / Dot1Q(vlan=0x999) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Test Case: tpid (Tag Protocol Identifier) rule
--------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the VLAN tag protocol identifier is equal to 0x8100, send the packet to queue 1) :

::

    flow create 0 ingress pattern vlan tpid is 0x8100 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / Dot1Q(type=0x8100) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / Dot1Q(type=0x0800) / ('\\x00' * 64)
    Pkt2 = Ether() / Dot1Q(type=0x0842) / ('\\x00' * 64)
    Pkt3 = Ether() / Dot1Q(type=0x809b) / ('\\x00' * 64)
    Pkt4 = Ether() / Dot1Q(type=0x86dd) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.


Item: VXLAN
~~~~~~~~~~~

Test Case: vni (VXLAN network identifier) rule
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the VXLAN network identifier is equal to 0x112233, send the packet to queue 1) :

::

    flow create 0 ingress pattern vxlan vni is 0x112233 / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP() / VXLAN(vni=0x112233) / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP() / VXLAN(vni=0x112234) / ('\\x00' * 64)
    Pkt2 = Ether() / IP() / VXLAN(vni=0x123456) / ('\\x00' * 64)
    Pkt3 = Ether() / IP() / VXLAN(vni=0xaabbcc) / ('\\x00' * 64)
    Pkt4 = Ether() / IP() / VXLAN(vni=0x999999) / ('\\x00' * 64)

..

5. Check to make sure that only the pass packet was received by queue 1.

Action Item Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
We create a simple flow rule that filters packets by matching IPv4 address (more rules are sometimes applied
depending on the action being tested). We then send one packet that is expected to pass,
and about four packets that are expected to fail. We check if the packet that is expected to pass
has the action we are testing applied to it.

We only test one action and one of the action's properties at a time, unless one property requires the context
of another.

Flow rules are created using **testpmd** and packets are created/sent using **scapy**.

NOTE: NVGRE_ENCAP and NVGRE_DECAP could not be tested at this time because Scapy does not support NVGRE.

We did not create an RSS test suite because one has already been created.


Action: PASSTHRU
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: passthru test
------------------------------------------------
1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, let the packet pass through) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions passthru / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet was allowed to pass through.

Action: FLAG
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: flag test
------------------------------------------------
1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, flag the packet) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions flag / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet was flagged.

Action: DROP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: drop test
------------------------------------------------
1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, drop the packet) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions drop / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet was dropped.

Action: COUNT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: test_shared
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, add unshared counter action with id of 1) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions count shared 0 id 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has a counter action added to it.

Test Case: test_id
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, add counter action with id of 1) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions count id 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has a counter action added to it.

Action: MAC_SWAP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: mac_swap test
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, swap dst and src MAC addresses) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions mac_swap / end

..

3. Send a packet that matches the rule, with defined src and dst MAC addresses:

::

    Pkt0 = Ether(src=\"90:61:ae:fd:41:43\", dst = \"ab:cd:ef:12:34:56\") / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with defined src and dst MAC addresses:

::

    Pkt1 = Ether(src=\"90:61:ae:fd:41:43\", dst = \"ab:cd:ef:12:34:56\") / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether(src=\"90:61:ae:fd:41:43\", dst = \"ab:cd:ef:12:34:56\") / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether(src=\"90:61:ae:fd:41:43\", dst = \"ab:cd:ef:12:34:56\") / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether(src=\"90:61:ae:fd:41:43\", dst = \"ab:cd:ef:12:34:56\") / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its source and destination MAC addresses swapped.

Action: DEC_TTL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: dec_ttl test
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, decrease its TTL) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions dec_ttl / end

..

3. Send a packet that matches the rule, with a defined ttl:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\", ttl = 128) / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with a defined ttl:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\", ttl = 128) / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its ttl reduced.

Action: JUMP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: jump test
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, redirect the packet to group 1) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions jump group 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been added to group 1 on the destination device.


Action: MARK
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: mark test
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, mark the packet with an id of 0xABCDEF) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions mark id 0xABCDEF / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been marked with the correct id.

Action: QUEUE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: queue test
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, send the packet to queue 1) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions queue index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been added to queue 1.

Action: PF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: pf test
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, direct the packet to the physical function of the device) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions pf / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been directed to the physical function of the device.

Action: VF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: test_original
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, direct the packet to the original virtual function of the device) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions vf original / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been directed to the original virtual function of the device.

Test Case: test_id
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, direct the packet to the virtual function of id 1) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions vf id 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been directed to the virtual function with the id of 1.


Action: PHY_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: test_original
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, direct the packet to the original physical port of the device) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions phy_port original / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been directed to the original physical port of the device.

Test Case: test_index
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, direct the packet to the physical port of index 1) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions phy_port index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been directed to the physical port of index 1.


Action: PORT_ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: test_original
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, direct the packet to the original DPDK port ID) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions port_id original / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been directed to the original DPDK port ID of the device.

Test Case: test_id
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, direct the packet to the DPDK port of id 1) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions port_id id 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been directed to the DPDK port of id 1.


Action: METER
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: meter test
------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, apply a MTR object with id 1) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions meter mtr_id 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had MTR object with id 1 applied to it.

Action: SECURITY
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: security test
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, apply security session of id 1) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions security security_session 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had security session 1 applied to it.


Action: OF_SET_MPLS_TTL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_set_mpls_ttl test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, implement MPLS TTL with a value of 64) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_set_mpls_ttl mpls_ttl 64 / end

..

3. Send a packet that matches the rule, with an MPLS layer with assigned ttl:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with MPLS layers with assigned ttl:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its MPLS ttl defined as 64.

Action: OF_DEC_MPLS_TTL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_dec_mpls_ttl test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, decrement the MPLS ttl value) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_dec_mpls_ttl / end

..

3. Send a packet that matches the rule, with an MPLS layer with assigned ttl:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with MPLS layers with assigned ttl:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its MPLS ttl decremented.


Action: OF_SET_NW_TTL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_set_nw_ttl test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, implement IP TTL with a value of 64) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_set_nw_ttl nw_ttl 64 / end

..

3. Send a packet that matches the rule, with a defined TTL in the IP layer:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\", ttl=128)  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with a defined TTL in the IP layer:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\", ttl = 128) /  UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\", ttl = 128) / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its IP TTL defined as 64.


Action: OF_DEC_NW_TTL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_dec_nw_ttl test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, decrease the IP TTL) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_dec_nw_ttl / end

..

3. Send a packet that matches the rule, with a defined TTL in the IP layer:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\", ttl=128 )  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with a defined TTL in the IP layer:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\", ttl = 128) /  UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\", ttl = 128) / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its IP TTL decremented.

Action: OF_COPY_TTL_OUT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_copy_ttl_out test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, copy the TTL outwards) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_copy_ttl_out / end

..

3. Send a packet that matches the rule, with a defined TTL in the IP layer:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with a defined TTL in the IP layer:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\", ttl = 128) /  UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\", ttl = 128) / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its TTL copied outwards.

Action: OF_COPY_TTL_IN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_copy_ttl_in test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, copy the TTL inwards) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_copy_ttl_in / end

..

3. Send a packet that matches the rule, with a defined TTL in the IP layer:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with a defined TTL in the IP layer:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\", ttl = 128) /  UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\", ttl = 128) / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its TTL copied inwards.

Action: OF_POP_VLAN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_pop_vlan test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, pop the outer VLAN tag) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_pop_vlan / end

..

3. Send a packet that matches the rule, with a defined VLAN layer/tag:

::

    Pkt0 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with defined VLAN layers/tags:

::

    Pkt1 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"8.8.8.8\") /  UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its outer (only) VLAN tag popped.

Action: OF_PUSH_VLAN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_push_vlan test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, push a new VLAN tag with EtherType 0x8100) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_push_vlan ethertype 0x8100 / end

..

3. Send a packet that matches the rule, with a defined VLAN layer/tag:

::

    Pkt0 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with defined VLAN layers/tags:

::

    Pkt1 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"8.8.8.8\") /  UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had a VLAN tag with EtherType 0x8100 pushed onto it.

Action: OF_SET_VLAN_VID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Test Case: of_set_vlan_vid test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the VLAN vid to 0xbbb):

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_set_vlan_vid 0xbbb / end

..

3. Send a packet that matches the rule, with a defined VLAN layer/tag:

::

    Pkt0 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with defined VLAN layers/tags:

::

    Pkt1 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"8.8.8.8\") /  UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its VLAN vid set to 0xbbb.

Action: OF_SET_VLAN_PCP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_set_vlan_pcp test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the VLAN pcp to 0x7):

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_set_vlan_pcp 0x7 / end

..

3. Send a packet that matches the rule, with a defined VLAN layer/tag:

::

    Pkt0 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with defined VLAN layers/tags:

::

    Pkt1 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"8.8.8.8\") /  UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its VLAN pcp set to 0x7.

Action: OF_POP_MPLS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_pop_mpls test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, pop the outer MPLS tag) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_pop_mpls / end

..

3. Send a packet that matches the rule, with a defined MPLS layer/tag:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with defined MPLS layers/tags:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") /  MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") /  MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") /  MPLS(label = 0xab, ttl=128) /  UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its outer (only) MPLS tag popped.

Action: OF_PUSH_MPLS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: of_push_mpls test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, push a new MPLS tag with EtherType 0x0806) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_push_mpls ethertype 0x0806 / end

..

3. Send a packet that matches the rule, with a defined MPLS layer/tag:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with defined MPLS layers/tags:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") /  MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") /  MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / MPLS(label = 0xab, ttl=128) / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") /  MPLS(label = 0xab, ttl=128) /  UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had an MPLS tag with EtherType 0x0806 pushed onto it.


Action: VXLAN_ENCAP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test Case: vxlan_encap
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, encapsulate with a VXLAN tag with overlay definition (vni) 0x112233) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions vxlan_encap definition 0x112233 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") /  UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") /  UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") /  UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been encapsulated with a VXLAN tag with vni 0x112233.

Action: VXLAN_DECAP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: vxlan_decap
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, strip all VXLAN headers :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions vxlan_decap / end

..

3. Send a packet that matches the rule, with a VXLAN header:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\")  / UDP() / VXLAN() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with VXLAN headers:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") /  UDP() / VXLAN() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") /  UDP() / VXLAN() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / VXLAN() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / VXLAN()/  ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its VXLAN header stripped.

Action: RAW_ENCAP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: test_data
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, encapsulate with a VLAN tag with the header value 0x8100aaaa:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions raw_encap data 0x8100aaaa / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been encapsulated with a VLAN tag with the header value 0x8100aaaa.

Test Case: test_preserve
---------------------------------


1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1,
encapsulate with a VLAN tag with the header value of 0x8100aaaa and a preserve bitmask of 0xffffffff:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions raw_encap data 0x8100aaaa preserve 0xffffffff / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") /  UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been encapsulated with a VLAN tag with the header value 0x8100aaaa
and has a preserve bitmask of 0xffffffff.

Test Case: test_size
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1,
encapsulate with a VLAN tag with the header value of 0x8100aaaa and a data (header) size of 32.

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions raw_encap data 0x8100aaaa size 32/ end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") /  UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been encapsulated with a VLAN tag with the header value 0x8100aaaa
and has a size of 32.

Action: RAW_DECAP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: test_data
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, decapsulate a VLAN tag with the header value 0x8100aaaa:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions raw_decap data 0x8100aaaa / end

..

3. Send a packet that matches the rule, with a matching VLAN header:

::

    Pkt0 = Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with matching VLAN headers:

::

    Pkt1 = Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src=\"10.0.30.99\") /  UDP() / ('\\x00' * 64)
    Pkt3 = Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src=\"132.177.0.99\") /  UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its VLAN tag decapsulated.


Test Case: test_size
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, decapsulate a VLAN tag with the header value 0x8100aaaa
and header size of 32:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions raw_decap data 0x8100aaaa size 32 / end

..

3. Send a packet that matches the rule, with a matching VLAN header:

::

    Pkt0 = Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src=\"192.168.0.1\")  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with matching VLAN headers:

::

    Pkt1 = Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src=\"10.0.30.99\") /  UDP() / ('\\x00' * 64)
    Pkt3 = Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src=\"132.177.0.99\") /  UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its VLAN tag of size 32 decapsulated.

Action: SET_IPV4_SRC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: set_ipv4_src test
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the ipv4 src to 172.16.0.10) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_ipv4_src ipv4_addr 172.16.0.10 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its IPv4 source address set to 172.16.0.10.


Action: SET_IPV4_DST
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: set_ipv4_dst test
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 destination is 192.168.0.1, set the ipv4 dst to 172.16.0.10) :

::

    flow create 0 ingress pattern eth / ipv4 dst is 192.168.0.1 / udp / end actions set_ipv4_dst ipv4_addr 172.16.0.10 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(dst=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(dst=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(dst=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(dst=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(dst=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its IPv4 destination address set to 172.16.0.10.

Action: SET_IPV6_SRC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: set_ipv6_src test
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv6 source is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2,
set the ipv6 source to 2001:0000:9d38:6ab8:1c48:9999:aaaa:bbbb) :

::

    flow create 0 ingress pattern eth / ipv6 src is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2 / udp /
    end actions set_ipv6_src ipv6_addr 2001:0000:9d38:6ab8:1c48:9999:aaaa:bbbb / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c4\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c5\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c6\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its IPv6 source address set to 2001:0000:9d38:6ab8:1c48:9999:aaaa:bbbb.

Action: SET_IPV6_DST
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: set_ipv6_dst test
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv6 destination is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2,
set the ipv6 dst to 2001:0000:9d38:6ab8:1c48:9999:aaaa:bbbb) :

::

    flow create 0 ingress pattern eth / ipv6 src is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2 / udp /
    end actions set_ipv6_dst ipv6_addr 2001:0000:9d38:6ab8:1c48:9999:aaaa:bbbb / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c4\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c5\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c6\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its IPv6 destination address set to  2001:0000:9d38:6ab8:1c48:9999:aaaa:bbbb.

Action: SET_TP_SRC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: test_udp
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the tcp/udp source port to 1998:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_tp_src 1998/ end

..

3. Send a packet that matches the rule with a defined UDP source port:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP(sport=3838) / ('\\x00' * 64)

..

4. Send packets that do not match the rule with defined UDP source ports:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP(sport=3838) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP(sport=3838) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP(sport=3838) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP(sport=3838) / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its UDP source port set to 1998.

Test Case: test_tcp
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the tcp/udp source port to 1998:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions set_tp_src 1998 / end

..

3. Send a packet that matches the rule with a defined TCP source port:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / TCP(sport=3838) / ('\\x00' * 64)

..

4. Send packets that do not match the rule with defined TCP source ports:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / TCP(sport=3838) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / TCP(sport=3838) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / TCP(sport=3838) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / TCP(sport=3838) / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its TCP source port set to 1998.

Action: SET_TP_DST
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Test Case: test_udp
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 destination is 192.168.0.1, set the tcp/udp destination port to 1998:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_tp_dst 1998/ end

..

3. Send a packet that matches the rule with a defined UDP destination port:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP(dport=3838) / ('\\x00' * 64)

..

4. Send packets that do not match the rule with defined UDP destination ports:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP(dport=3838) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP(dport=3838) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP(dport=3838) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP(dport=3838) / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its UDP destination port set to 1998.

Test Case: test_tcp
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the tcp/udp destination port to 1998:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions set_tp_dst 1998 / end

..

3. Send a packet that matches the rule with a defined TCP destination port:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / TCP(dport=3838) / ('\\x00' * 64)

..

4. Send packets that do not match the rule with defined TCP destination ports:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / TCP(dport=3838) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / TCP(dport=3838) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / TCP(dport=3838) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / TCP(dport=3838) / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its TCP destination port set to 1998.
Action: SET_TTL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: set_ttl test
---------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set TTL to a value of 64) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_ttl ttl_value 64 / end

..

3. Send a packet that matches the rule, with a defined TTL in the IP layer:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\", ttl=128)  / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with a defined TTL in the IP layer:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\", ttl = 128) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\", ttl = 128) /  UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\", ttl = 128) / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its TTL defined as 64.

Action: SET_MAC_SRC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: set_mac_src test
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set MAC src to 10:20:30:40:50:60) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_mac_src mac_addr 10:20:30:40:50:60 / end

..

3. Send a packet that matches the rule, with a defined src MAC address:

::

    Pkt0 = Ether(src=\"90:61:ae:fd:41:43\") / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with defined src MAC addresses:

::

    Pkt1 = Ether(src=\"90:61:ae:fd:41:43\") / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether(src=\"90:61:ae:fd:41:43\" ) / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether(src=\"90:61:ae:fd:41:43\" ) / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether(src=\"90:61:ae:fd:41:43\" ) / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its source MAC address set to 10:20:30:40:50:60.

Action: SET_MAC_DST
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: set_mac_dst test
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set MAC dst to 10:20:30:40:50:60) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_mac_dst mac_addr 10:20:30:40:50:60 / end

..

3. Send a packet that matches the rule, with a defined dst MAC address:

::

    Pkt0 = Ether(src=\"90:61:ae:fd:41:43\") / IP(dst =\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with defined dst MAC addresses:

::

    Pkt1 = Ether(dst=\"90:61:ae:fd:41:43\") / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether(dst=\"90:61:ae:fd:41:43\" ) / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether(dst=\"90:61:ae:fd:41:43\" ) / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether(dst=\"90:61:ae:fd:41:43\" ) / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its destination MAC address set to 10:20:30:40:50:60.

Action: INC_TCP_SEQ
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: inc_tcp_seq test
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, increase the TCP seq value:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions inc_tcp_seq / end

..

3. Send a packet that matches the rule with a defined TCP seq value:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / TCP(seq=2) / ('\\x00' * 64)

..

4. Send packets that do not match the rule with defined TCP seq values:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / TCP(seq=2) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / TCP(seq=2) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / TCP(seq=2) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / TCP(seq=2) / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its TCP seq value increased.

Action: DEC_TCP_SEQ
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: dec_tcp_seq test
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, decrease the TCP seq value:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions dec_tcp_seq / end

..

3. Send a packet that matches the rule with a defined TCP seq value:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / TCP(seq=2) / ('\\x00' * 64)

..

4. Send packets that do not match the rule with defined TCP seq values:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / TCP(seq=2) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / TCP(seq=2) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / TCP(seq=2) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / TCP(seq=2) / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its TCP seq value decreased.

Action: INC_TCP_ACK
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: inc_tcp_ack test
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, increase the TCP ack value:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions inc_tcp_ack / end

..

3. Send a packet that matches the rule with a defined TCP ack value:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / TCP(ack=2) / ('\\x00' * 64)

..

4. Send packets that do not match the rule with defined TCP ack values:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / TCP(ack=2) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / TCP(ack=2) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / TCP(ack=2) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / TCP(ack=2) / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its TCP ack value increased.

Action: DEC_TCP_ACK
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: dec_tcp_ack test
----------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, decrease the TCP ack value:

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions dec_tcp_ack / end

..

3. Send a packet that matches the rule with a defined TCP ack value:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / TCP(ack=2) / ('\\x00' * 64)

..

4. Send packets that do not match the rule with defined TCP ack values:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / TCP(ack=2) / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / TCP(ack=2) / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / TCP(ack=2) / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / TCP(ack=2) / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its TCP ack value decreased.

Action: SET_TAG
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: test_data
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, tag the packet with the value 0xabc) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_tag data 0xabc / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been tagged with the correct data.

Test Case: test_mask
------------------------------------------------


1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, tag the packet with the value 0xabc and mask 0xcba) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_tag data 0xabc mask 0xcba / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been tagged with the correct data and mask.


Test Case: test_index
------------------------------------------------


1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the packet tag index 1 to the value 0xabc) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_tag data 0xabc index 1 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has been tagged with the correct data on the correct tag index.


Action: SET_META
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: test_data
------------------------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the packet's meta to the value 0xabc) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_meta data 0xabc / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had the correct metadata assigned to it.

Test Case: test_mask
------------------------------------------------


1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the packet's meta to the value 0xabc and mask 0xcba):

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_meta data 0xabc mask 0xcba / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had the correct metadata and mask assigned to it.

Action: SET_IPV4_DSCP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: set_ipv4_dscp test
-------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the IPv4 dscp (tos) to 2) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions set_ipv4_dscp 2 / end

..

3. Send a packet that matches the rule with a defined dscp (tos) value:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule with defined dscp (tos) values:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its IPv4 dscp (tos) value set to 2.


Action: SET_IPV6_DSCP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: set_ipv6_dscp test
-------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv6 src is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2, set its dscp (tc) value to 0x30):

::

    flow create 0 ingress pattern eth / ipv6 src is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2 / udp /
    end actions set_ipv6_dscp dscp 0x30 / end

..

3. Send a packet that matches the rule, with a defined dscp (tc) value:

::

    Pkt0 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3\", tc=0) / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule, with defined dscp (tc) values:

::

    Pkt1 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3\", tc=0) / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c4\", tc=0) / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c5\", tc=0) / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c6\", tc=0) / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its dscp (tc) value set to 0x30.

Action: AGE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Case: test_timeout
-------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the aging timeout value to 128) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions age timeout 128 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its aging timeout value set to 128.

Test Case: test_reserved
-------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the aging timeout value to 128 and reserved to 0) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions age timeout 128 reserved 0 / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its aging timeout value set to 128 and reserved bits set to 0.

Test Case: test_context
-------------------------------

1. Run testpmd in interactive mode with one port bound and available:

::

    ./<build_target>/app/dpdk-testpmd -c 3 -- -i

..

2. Set the test flow rule (If the IPv4 source is 192.168.0.1, set the aging timeout value to 128
   and flow context to the rte_flow pointer) :

::

    flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions age timeout 128 context NULL / end

..

3. Send a packet that matches the rule:

::

    Pkt0 = Ether() / IP(src=\"192.168.0.1\") / UDP() / ('\\x00' * 64)

..

4. Send packets that do not match the rule:

::

    Pkt1 = Ether() / IP(src=\"192.168.0.2\") / UDP() / ('\\x00' * 64)
    Pkt2 = Ether() / IP(src=\"10.0.30.99\") / UDP() / ('\\x00' * 64)
    Pkt3 = Ether() / IP(src=\"8.8.8.8\") / UDP() / ('\\x00' * 64)
    Pkt4 = Ether() / IP(src=\"132.177.0.99\") / UDP() / ('\\x00' * 64)

..

5. Check to make sure that the pass packet has had its aging timeout value set to 128 and its user flow context
set to the rte_flow pointer.






