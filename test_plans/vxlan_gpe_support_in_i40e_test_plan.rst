.. Copyright (c) <2019> Intel Corporation
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

============================
I40E VXLAN-GPE Support Tests
============================

Prerequisites
=============

1. The DUT has at least 2 DPDK supported I40E NIC ports::

    Tester      DUT
    eth1  <---> PORT 0
    eth2  <---> PORT 1

2. Support igb_uio driver::

    modprobe uio
    insmod  ./x86_64-native-linuxapp-gcc/kmod/igb_uio.ko
    ./usertools/dpdk-devbind.py --bind=igb_uio 04:00.0 04:00.1

Test Case 1: VXLAN-GPE ipv4 packet detect
=========================================
1. Start testpmd::

    # testpmd -c 0xf -n 4 -- -i

2. Add VXLAN-GPE packet type support in test pmd and enable verbose log::

    testpmd> set fwd io
    testpmd> set verbose 1
    testpmd> port config 0 udp_tunnel_port add vxlan-gpe 4790

3. Send VXLAN-GPE packets to testpmd and check received packets::

    scapy> pkt=Ether(dst="3C:FD:FE:A8:C8:20")/IP(src="18.0.0.1")/UDP(dport=4790,sport=43)/VXLAN(flags=12)/IP(src="10.0.0.1")
    scapy> sendp(pkt1, iface="ens802f1", count=1)

4. Expected output from testpmd::

    src=00:00:00:00:00:00 - dst=3C:FD:FE:A8:C8:20 - type=0x0800 - length=70 - nb_segs=1 - RSS hash=0x51ed6fc5 - RSS
    queue=0x2 - hw ptype: L2_ETHER L3_IPV4_EXT_UNKNOWN TUNNEL_GRENAT INNER_L3_IPV4_EXT_UNKNOWN
    INNER_L4_NONFRAG  - sw ptype: L2_ETHER L3_IPV4 L4_UDP  - l2_len=14 - l3_len=20 - l4_len=8
    - VXLAN packet: packet type =24721, Destination UDP port =4790, VNI = 0 - Receive queue=0x2

Test Case 2: VXLAN-GPE tunnel remove test
=========================================
1. After Test Case 1, delete the VXLAN-GPE packet type::

    testpmd> port config 0 udp_tunnel_port rm vxlan-gpe 4790

2. Send VXLAN-GPE packets to testpmd and check the received packets

3. Expected result::

    testpmd should treat the packet as a normal UDP packet

Test Case 3: Tunnel filter VXLAN-GPE support
============================================
1. Start testpmd with tunneling packet type to vxlan and disable receive side
   scale for hardware limitation::

    # testpmd -c ffff -n 4 -- -i --disable-rss --rxq=4 --txq=4 --nb-cores=8 --nb-ports=2 --tx-offloads=0x8fff

2. Set rxonly packet forwarding mode and enable verbose log::

    testpmd> set fwd rxonly
    testpmd> set verbose 1

3. Add one new Cloud filter as table listed first::

    testpmd> tunnel_filter add 0 11:22:33:44:55:66 00:00:20:00:00:01 192.168.2.2 1 vxlan-gpe imac-ivlan 1 3

4. Then send one packet and check packet was forwarded into right queue.

+------------+------------+------------+----------+----------+--------+-------+
| Outer Mac  | Inner Mac  | Inner Vlan | Outer Ip | Inner Ip | Vni ID | Queue |
+------------+------------+------------+----------+----------+--------+-------+
| No         | Yes        | Yes        | No       | No       | No     | 1     |
+------------+------------+------------+----------+----------+--------+-------+
| No         | Yes        | Yes        | No       | No       | Yes    | 1     |
+------------+------------+------------+----------+----------+--------+-------+
| No         | Yes        | No         | No       | No       | Yes    | 1     |
+------------+------------+------------+----------+----------+--------+-------+
| No         | Yes        | No         | No       | No       | No     | 1     |
+------------+------------+------------+----------+----------+--------+-------+
| Yes        | Yes        | No         | No       | Yes      | Yes    | 1     |
+------------+------------+------------+----------+----------+--------+-------+
| No         | No         | No         | No       | Yes      | No     | 1     |
+------------+------------+------------+----------+----------+--------+-------+
