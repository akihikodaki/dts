.. Copyright (c) <2021>, Intel Corporation
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
CVL IAVF: Advanced RSS For PPPoL2TPv2oUDP
=========================================

Description
===========

Support IAVF PPPoL2TPv2oUDP RSS Hash.
Required to distribute packets based on inner IP src+dest address and TCP/UDP src+dest port

Prerequisites
=============

1. Hardware:

  - Intel E810 series ethernet cards: columbiaville_25g/columbiaville_100g/

2. Software:

  - dpdk: http://dpdk.org/git/dpdk
  - scapy: http://www.secdev.org/projects/scapy/

.. note::

    This rss feature designed for CVL NIC 25G and 100G, so below cases only support CVL NIC.

3. load PPPoL2TPv2oUDP package

4. create a VF from a PF in DUT, set mac address for thi VF::

    echo 1 > /sys/bus/pci/devices/0000\:3b\:00.0/sriov_numvfs
    ip link set enp59s0f0 vf 0 mac 00:11:22:33:44:55

5. bind VF to vfio-pci::

    modprobe vfio-pci
    ./usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:3b:01.0

.. note::

    The kernel must be >= 3.6+ and VT-d must be enabled in bios.

6. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0xff -n 4 -a 0000:3b:01.0 -- -i --disable-rss --rxq=16 --txq=16 --rxd=384 --txd=384
    testpmd>set fwd rxonly
    testpmd>set verbose 1


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_PAY
=========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_FRAG
==========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200', frag=6)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201', frag=6)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=============================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_PAY
=====================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_ipv4_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_PAY
=====================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=====================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.201')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.201')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=============================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=============================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=============================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_udp_ipv4_udp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_UDP_PAY
=============================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=============================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=============================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=============================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=============================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.201')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=============================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.201')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=========================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=========================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=========================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv4_tcp_ipv4_tcp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV4_TCP
=========================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_FRAG
==========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_PAY
=========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=============================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_FRAG
======================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_ipv6_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_FRAG
======================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=====================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=============================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=============================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=============================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_udp_ipv6_udp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_UDP_PAY
=============================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=============================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=============================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=============================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=============================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=============================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_src_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=========================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_src_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=========================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_dst_only_l4_src_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=========================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv6_udp_l2tpv2_ppp_ipv6_tcp_ipv6_tcp_l3_dst_only_l4_dst_only_MAC_IPV6_PPPoL2TPV2_IPV6_TCP
=========================================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-dst-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=99)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IPv6(src='2001::3', dst='2001::4')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2925', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=24)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_PAY
=========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_FRAG
==========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200', frag=6)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201', frag=6)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200', frag=6)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY
=============================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv4_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_TCP
=========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv4_udp_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_UDP_PAY
=================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv4_tcp_ipv4_MAC_IPV4_PPPoL2TPV2_IPV4_TCP
=============================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv4 / tcp / end actions rss types ipv4 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.101', dst='192.168.1.200')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.201')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x21')/IP(src='192.168.1.100', dst='192.168.1.200')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_FRAG
==========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/IPv6ExtHdrFragment()/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_PAY
=========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY
=============================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv6_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_TCP
=========================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IPv6(src='2001::1', dst='2001::2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv6_udp_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_UDP_PAY
=================================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / udp / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.


Test case: eth_ipv4_udp_l2tpv2_ppp_ipv6_tcp_ipv6_MAC_IPV4_PPPoL2TPV2_IPV6_TCP
=============================================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / ipv6 / tcp / end actions rss types ipv6 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2923', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=23, dport=24)/Raw('x' * 80)

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2025')/TCP(sport=23, dport=24)/Raw('x' * 80)

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    Ether(src='00:11:22:33:44:66', dst='00:11:22:33:44:55')/IP(src='100.0.1.1', dst='100.0.1.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/TCP(sport=25, dport=99)/Raw('x' * 80)

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    Ether(src='00:11:22:33:44:77', dst='00:11:22:33:44:55')/IP(src='100.0.0.1', dst='100.0.0.2')/UDP(dport=1701, sport=1702)/L2TP(session_id=0x7)/HDLC(address=0xff, control=0x03)/Raw(b'\\x00\\x57')/IPv6(src='ABAB:910B:6666:3457:8295:3333:1800:2929', dst='CDCD:910A:2222:5498:8475:1111:3900:2020')/UDP(sport=23, dport=24)/Raw('x' * 80)

   check the packet rss hash value is 0.

7. distroy the rule and and check there is no rule listed.

#l2tpv2 control + data
Test case 1: l2tpv2_session_id_MAC_IPV4_L2TPV2_CONTROL
======================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type control / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)],iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)],iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 2: eth_l2_src_only_MAC_IPV4_L2TPV2_CONTROL
====================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type control / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77)/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)],iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)],iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 3: l2tpv2_session_id_MAC_IPV6_L2TPV2_CONTROL
======================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type control / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)],iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)],iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 4: eth_l2_src_only_MAC_IPV6_L2TPV2_CONTROL
====================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type control / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x2222)],iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0xc80,len=12,session_id=0x1111)],iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 5: l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA
===================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 6: eth_l2_src_only_MAC_IPV4_L2TPV2_DATA
=================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 7: l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_L
=====================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 8: eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_L
===================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 9: l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_S
=====================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 10: eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_S
====================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully. 

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 11: l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_O
======================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 12: eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_O
====================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 13: l2tpv2_session_id_MAC_IPV4_L2TPV2_DATA_L_S
========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 14: eth_l2_src_only_MAC_IPV4_L2TPV2_DATA_L_S
======================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 15: l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA
====================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 16: eth_l2_src_only_MAC_IPV6_L2TPV2_DATA
==================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 17: l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_L
======================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 18: eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_L
====================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x2222)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=8,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 19: l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_S
======================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 20: eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_S
====================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 21: l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_O
======================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 22: eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_O
====================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 23: l2tpv2_session_id_MAC_IPV6_L2TPV2_DATA_L_S
========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 24: eth_l2_src_only_MAC_IPV6_L2TPV2_DATA_L_S
======================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x2222)], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=12,session_id=0x1111)], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 25: l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA
========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 26: eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA
======================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 27: l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_L
==========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 28: eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_L
========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 29: l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_S
==========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 30: eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_S
========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_s / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 31: l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_O
==========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 32: eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_O
========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_o / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 33: l2tpv2_session_id_MAC_IPV4_PPPoL2TPV2_DATA_L_S
============================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 34: eth_l2_src_only_MAC_IPV4_PPPoL2TPV2_DATA_L_S
==========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / l2tpv2 type data_l_s / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 35: l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA
========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 36: eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA
======================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x000,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 37: l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_L
==========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 38: eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_L
========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x400,len=12,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 39: l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_S
==========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 40: eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_S
========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_s / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x080,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 41: l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_O
==========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 42: eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_O
========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_o / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x2222,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x020,session_id=0x1111,offset=6)/Raw('\x00\x00\x00\x00')/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 43: l2tpv2_session_id_MAC_IPV6_PPPoL2TPV2_DATA_L_S
============================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / end actions rss types l2tpv2 end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='11:22:33:44:55:77')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

Test case 44: eth_l2_src_only_MAC_IPV6_PPPoL2TPV2_DATA_L_S
==========================================================
1. validate the rule, and check there is not rule listed.

2. create a rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / l2tpv2 type data_l_s / ppp / end actions rss types eth l2-src-only end key_len 0 queues end / end

   check there is a rss rule listed successfully.

3. send a basic hit pattern packet,record the hash value::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet distributed to queue by rss.

4. send hit pattern packets with changed input set in the rule::

    sendp([Ether(src='11:22:33:44:55:77')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.

5. send hit pattern packets with changed input set not in the rule::

    sendp([Ether(src='00:00:00:00:00:01')/IPv6()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x2222)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.

6. send not hit pattern packet::

    sendp([Ether(src='00:00:00:00:00:01')/IP()/UDP(dport=1701)/L2TP(hdr=0x480,len=16,session_id=0x1111)/HDLC()/Raw('\x00\x00')], iface="ens260f0")

   check the packet rss hash value is 0.

7. distroy the rule and check there is no rule listed.

