.. Copyright(c) <2010-2017> Intel Corporation
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


=========================================
Generic Routing Encapsulation (GRE) Tests
=========================================

Generic Routing Encapsulation (GRE) is a tunneling protocol developed by Cisco Systems that can encapsulate a wide variety of network layer protocols inside virtual point-to-point links over an Internet Protocol network.
Fortville support GRE packet detecting, checksum computing and filtering.

Prerequisites
=============

Fortville/carlsville/columbiaville nic should be on the DUT.

Test Case 1: GRE ipv4 packet detect
===================================

Start testpmd and enable rxonly forwarding mode::

    testpmd -c ffff -n 4 -- -i
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

Send packet as table listed and packet type match each layer.

+------------+----------+-----------+----------+-----------+
| Outer Vlan | Outer IP | Tunnel    | Inner L3 | Inner L4  |
+------------+----------+-----------+----------+-----------+
| No         | Ipv4     | GRE       | Ipv4     | Udp       |
+------------+----------+-----------+----------+-----------+
| No         | Ipv4     | GRE       | Ipv4     | Tcp       |
+------------+----------+-----------+----------+-----------+
| No         | Ipv4     | GRE       | Ipv4     | Sctp      |
+------------+----------+-----------+----------+-----------+
| Yes        | Ipv4     | GRE       | Ipv4     | Udp       |
+------------+----------+-----------+----------+-----------+
| Yes        | Ipv4     | GRE       | Ipv4     | Tcp       |
+------------+----------+-----------+----------+-----------+
| Yes        | Ipv4     | GRE       | Ipv4     | Sctp      |
+------------+----------+-----------+----------+-----------+


Test Case 2: GRE ipv6 packet detect
===================================

Start testpmd and enable rxonly forwarding mode::

    testpmd -c ffff -n 4 -- -i --enable-hw-vlan
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

Send packet as table listed and packet type match each layer::

   Ether()/IPv6(nh=47)/GRE()/IP()/UDP()/Raw('x'*40)
   Ether()/IPv6(nh=47)/GRE(proto=0x86dd)/IPv6()/UDP()/Raw('x'*40)

+------------+----------+-----------+----------+-----------+
| Outer Vlan | Outer IP | Tunnel    | Inner L3 | Inner L4  |
+------------+----------+-----------+----------+-----------+
| No         | Ipv6     | GRE       | Ipv4     | Udp       |
+------------+----------+-----------+----------+-----------+
| No         | Ipv6     | GRE       | Ipv4     | Tcp       |
+------------+----------+-----------+----------+-----------+
| No         | Ipv6     | GRE       | Ipv4     | Sctp      |
+------------+----------+-----------+----------+-----------+
| Yes        | Ipv6     | GRE       | Ipv4     | Udp       |
+------------+----------+-----------+----------+-----------+
| Yes        | Ipv6     | GRE       | Ipv4     | Tcp       |
+------------+----------+-----------+----------+-----------+
| Yes        | Ipv6     | GRE       | Ipv4     | Sctp      |
+------------+----------+-----------+----------+-----------+

+------------+----------+-----------+----------+-----------+
| Outer Vlan | Outer IP | Tunnel    | Inner L3 | Inner L4  |
+------------+----------+-----------+----------+-----------+
| No         | Ipv6     | GRE       | Ipv6     | Udp       |
+------------+----------+-----------+----------+-----------+
| No         | Ipv6     | GRE       | Ipv6     | Tcp       |
+------------+----------+-----------+----------+-----------+
| No         | Ipv6     | GRE       | Ipv6     | Sctp      |
+------------+----------+-----------+----------+-----------+
| Yes        | Ipv6     | GRE       | Ipv6     | Udp       |
+------------+----------+-----------+----------+-----------+
| Yes        | Ipv6     | GRE       | Ipv6     | Tcp       |
+------------+----------+-----------+----------+-----------+
| Yes        | Ipv6     | GRE       | Ipv6     | Sctp      |
+------------+----------+-----------+----------+-----------+

Test Case 4: GRE packet chksum offload
======================================

Start testpmd with hardware checksum offload enabled::

    testpmd -c ff -n 3 -- -i --enable-rx-cksum  --port-topology=loop
    testpmd> set verbose 1
    testpmd> set fwd csum
    testpmd> csum set ip hw 0
    testpmd> csum set udp hw 0
    testpmd> csum set sctp hw 0
    testpmd> csum set outer-ip hw 0
    testpmd> csum set tcp hw 0
    testpmd> csum parse-tunnel on 0
    testpmd> start

Send packet with wrong outer IP checksum and check forwarded packet IP
checksum is correct::

    Ether()/IP(chksum=0x0)/GRE()/IP()/TCP()

Send packet with wrong inner IP checksum and check forwarded packet IP
checksum is correct::

    Ether()/IP()/GRE()/IP(chksum=0x0)/TCP()

Send packet with wrong inner TCP checksum and check forwarded packet TCP
checksum is correct::

    Ether()/IP()/GRE()/IP()/TCP(chksum=0x0)

Send packet with wrong inner UDP checksum and check forwarded packet UDP
checksum is correct::

    Ether()/IP()/GRE()/IP()/UDP(chksum=0xffff)

Send packet with wrong inner SCTP checksum and check forwarded packet SCTP
checksum is correct::

    Ether()/IP()/GRE()/IP()/SCTP(chksum=0x0)
