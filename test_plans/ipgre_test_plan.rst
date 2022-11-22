.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2010-2017 Intel Corporation

=========================================
Generic Routing Encapsulation (GRE) Tests
=========================================

Generic Routing Encapsulation (GRE) is a tunneling protocol developed by
Cisco Systems that can encapsulate a wide variety of network layer
protocols inside virtual point-to-point links over an Internet Protocol
network. Intel® Ethernet 700 Series support GRE packet detecting, checksum
computing and filtering.

Prerequisites
=============

Intel® Ethernet 700 Series/
Intel® Ethernet Network Adapter X710-T4L/
Intel® Ethernet Network Adapter X710-T2L/
Intel® Ethernet 800 Series nic should be on the DUT.

Test Case 1: GRE ipv4 packet detect
===================================

Start testpmd and enable rxonly forwarding mode::

    ./<build_target>/app/dpdk-testpmd -c ffff -n 4 -- -i
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

    ./<build_target>/app/dpdk-testpmd -c ffff -n 4 -- -i --enable-hw-vlan
    testpmd> set fwd rxonly
    testpmd> set verbose 1
    testpmd> start

    Due to the kernel enables Qinq and cannot be closed, the DPDK only add `extend on` to make the VLAN filter
    work normally. Therefore, if the i40e firmware version >= 8.4 the DPDK can only add `extend on` to make the VLAN filter work normally:
    testpmd> vlan set extend on 0

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

    ./<build_target>/app/dpdk-testpmd -c ff -n 3 -- -i --enable-rx-cksum  --port-topology=loop
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
