.. SPDX-License-Identifier: BSD-3-Clause
   Copyright(c) 2019 Intel Corporation

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

    # dpdk-testpmd -c 0xf -n 4 -- -i

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
