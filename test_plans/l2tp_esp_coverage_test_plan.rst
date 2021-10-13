.. Copyright (c) <2020>, Intel Corporation
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

================================
test coverage for L2TPv3 and ESP 
================================

Description
===========
For each protocol, below is a list of standard features supported by the Columbiaville hardware and the impact on the feature for each protocol.  
Some features are supported in a limited manner as stated below.
 
IPSec(ESP):
L2 Tag offloads 
----L2 Tag Stripping - Yes
----L2 Tag insertion - Yes
Checksum offloads - Yes 
----Only outer layer 3 checksum for IP+ESP and IP+AH packets
----Outer layer 3 and 4 checksum for ESP over UDP packets
Manageability - No 
----Packets must be excluded
RDMA - No 
----Packets must be excluded
DCB 
----Priority Flow Control - No
 
L2TPv3:
L2 Tag offloads 
----L2 Tag Stripping - Yes
----L2 Tag insertion - Yes
Checksum offloads - Yes 
----Only outer layer 3
Manageability - No 
----Packets must be excluded
RDMA - No 
----Packets must be excluded
DCB 
----Priority Flow Control - No

this test plan is designed to check above offloads in L2TPv3 and ESP.
and CVL can't support tx checksum in vector path now, so only test the rx checksum offload.


Prerequisites
=============

1. create a vf from a pf::

    echo 1 > /sys/bus/pci/devices/0000\:af\:00.0/sriov_numvfs
    ip link set enp175s0f0 vf 0 mac 00:11:22:33:44:55

2. bind vf to vfio-pci::

    ./usertools/dpdk-devbind.py -b vfio-pci af:01.0


Test Case 1: test MAC_IPV4_L2TPv3 HW checksum offload
=====================================================

1. DUT enable rx checksum with "--enable-rx-cksum" when start testpmd::

    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -a af:01.0 -- -i --enable-rx-cksum

2. DUT setup csum forwarding mode::

    testpmd> port stop all
    testpmd> csum set ip hw 0
    testpmd> port start all
    testpmd> set fwd csum
    testpmd> set verbose 1
    testpmd> start

3. Tester send MAC_IPV4_L2TPv3 packets with correct checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3", proto=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")
    
4. DUT check the packets are correctly received with "PKT_RX_IP_CKSUM_GOOD" by DUT::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=518 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x22848a2680, pkt_len=518, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=115 l4_len=0 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 0              Bad-l4csum: 0             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   
5. Tester send MAC_IPV4_L2TPv3 packets with incorrect checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3", proto=115,chksum=0x123)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")
    
6. DUT check the packets are correctly received by DUT and report the checksum error::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=518 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2284780c40, pkt_len=518, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=115 l4_len=0 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 1              Bad-l4csum: 0             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


Test Case 2: test MAC_IPV4_ESP HW checksum offload
==================================================

1. DUT enable rx checksum with "--enable-rx-cksum" when start testpmd, setup csum forwarding mode::
 
    ./x86_64-native-linuxapp-gcc/app/testpmd -n 4 -a af:01.0 -- -i --enable-rx-cksum

2. DUT setup csum forwarding mode::

    testpmd> port stop all
    testpmd> csum set ip hw 0
    testpmd> port start all
    testpmd> set fwd csum
    testpmd> set verbose 1
    testpmd> start

3. Tester send MAC_IPV4_ESP packets with correct checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=50)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0")
    
4. DUT check the packets are correctly received with "PKT_RX_IP_CKSUM_GOOD" by DUT::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=522 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x22848a2fc0, pkt_len=522, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=50 l4_len=0 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 0              Bad-l4csum: 0             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   
5. Tester send MAC_IPV4_ESP packets with incorrect checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=50,chksum=0x123)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0")
    
6. DUT check the packets are correctly received by DUT and report the checksum error::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=522 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2284781580, pkt_len=522, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=50 l4_len=0 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 1              Bad-l4csum: 0             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


Test Case 3: test MAC_IPV4_AH HW checksum offload
=================================================

1. DUT enable rx checksum with "--enable-rx-cksum" when start testpmd, setup csum forwarding mode:

2. DUT setup csum forwarding mode::

    testpmd> port stop all
    testpmd> csum set ip hw 0
    testpmd> port start all
    testpmd> set fwd csum
    testpmd> set verbose 1
    testpmd> start

3. Tester send MAC_IPV4_AH packets with correct checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=51)/AH(spi=11)/Raw('x'*480)], iface="enp134s0f0")
    
4. DUT check the packets are correctly received with "PKT_RX_IP_CKSUM_GOOD" by DUT::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=526 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2284782800, pkt_len=526, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=51 l4_len=0 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 0              Bad-l4csum: 0             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

5. Tester send MAC_IPV4_AH packets with incorrect checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=51,chksum=0x123)/AH(spi=11)/Raw('x'*480)], iface="enp134s0f0")
    
6. DUT check the packets are correctly received by DUT and report the checksum error::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=526 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2284783140, pkt_len=526, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=51 l4_len=0 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 1              Bad-l4csum: 0             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


Test Case 4: test MAC_IPV4_NAT-T-ESP HW checksum offload
========================================================

1. DUT enable rx checksum with "--enable-rx-cksum" when start testpmd, setup csum forwarding mode:

2. DUT setup csum forwarding mode::

    testpmd> port stop all
    testpmd> csum set ip hw 0
    testpmd> csum set udp hw 0
    testpmd> port start all
    testpmd> set fwd csum
    testpmd> set verbose 1
    testpmd> start

3. Tester send MAC_IPV4_NAT-T-ESP pkt with correct IPv4 checksum and correct UDP checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=4500)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0")

4. DUT check the packets are correctly received with "PKT_RX_L4_CKSUM_GOOD" and "PKT_RX_IP_CKSUM_GOOD" by DUT::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=530 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV4 L4_UDP  - l2_len=14 - l3_len=20 - l4_len=8 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x22847843c0, pkt_len=530, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=8
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 0              Bad-l4csum: 0             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

5. Tester send MAC_IPV4_NAT-T-ESP pkt with correct IPv4 checksum and incorrect UDP checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=4500,chksum=0x123)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0")

6. DUT check the packets are correctly received with "PKT_RX_IP_CKSUM_GOOD" and report UDP checksum error by DUT::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=530 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV4 L4_UDP  - l2_len=14 - l3_len=20 - l4_len=8 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2284784d00, pkt_len=530, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=8
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 0              Bad-l4csum: 1             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

7. Tester send MAC_IPV4_NAT-T-ESP pkt with incorrect IPv4 checksum and correct UDP checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(chksum=0x123)/UDP(dport=4500)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0")

8. DUT check the packets are correctly received with "PKT_RX_L4_CKSUM_GOOD" and report IP checksum error by DUT::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=530 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV4 L4_UDP  - l2_len=14 - l3_len=20 - l4_len=8 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x22848a1400, pkt_len=530, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=8
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 1              Bad-l4csum: 0             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

9. Tester send MAC_IPV4_NAT-T-ESP pkt with incorrect IPv4 checksum and incorrect UDP checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(chksum=0x123)/UDP(dport=4500,chksum=0x123)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0")

10. DUT check the packets are correctly received by DUT and report the checksum error::

     testpmd> port 0/queue 0: received 1 packets
     src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x0800 - length=530 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV4 L4_UDP  - l2_len=14 - l3_len=20 - l4_len=8 - Receive queue=0x0
     ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
     -----------------
     port=0, mbuf=0x22848a0ac0, pkt_len=530, nb_segs=1:
     rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
     tx: m->l2_len=14 m->l3_len=20 m->l4_len=8
     tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
     stop
     Telling cores to stop...
     Waiting for lcores to finish...

     ---------------------- Forward statistics for port 0  ----------------------
     RX-packets: 1              RX-dropped: 0             RX-total: 1
     Bad-ipcsum: 1              Bad-l4csum: 1             Bad-outer-l4csum: 0
     TX-packets: 1              TX-dropped: 0             TX-total: 1
     ----------------------------------------------------------------------------

     +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
     RX-packets: 1              RX-dropped: 0             RX-total: 1
     TX-packets: 1              TX-dropped: 0             TX-total: 1
     ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


Test Case 5: test MAC_IPV6_NAT-T-ESP HW checksum offload
========================================================

1. DUT enable rx checksum with "--enable-rx-cksum" when start testpmd, setup csum forwarding mode:

2. DUT setup csum forwarding mode::

    testpmd> port stop all
    testpmd> csum set udp hw 0
    testpmd> port start all
    testpmd> set fwd csum
    testpmd> set verbose 1
    testpmd> start

3. Tester send MAC_IPV6_NAT-T-ESP packets with correct checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=4500)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0")
    
4. DUT check the packets are correctly received with "PKT_RX_L4_CKSUM_GOOD" by DUT::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x86dd - length=550 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV6 L4_UDP  - l2_len=14 - l3_len=40 - l4_len=8 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x228489e5c0, pkt_len=550, nb_segs=1:
    rx: l2_len=14 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=40 m->l4_len=8
    tx: flags=PKT_TX_L4_NO_CKSUM PKT_TX_IPV6
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 0              Bad-l4csum: 0             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
     
5. Tester send MAC_IPV6_NAT-T-ESP packets with incorrect checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=4500,chksum=0x123)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0")
    
6. DUT check the packets are correctly received by DUT and report the checksum error::

    testpmd> port 0/queue 0: received 1 packets
    src=00:00:00:00:00:00 - dst=00:11:22:33:44:55 - type=0x86dd - length=550 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER L3_IPV6 L4_UDP  - l2_len=14 - l3_len=40 - l4_len=8 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x228489dc80, pkt_len=550, nb_segs=1:
    rx: l2_len=14 ethertype=86dd l3_len=40 l4_proto=17 l4_len=8 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_BAD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=40 m->l4_len=8
    tx: flags=PKT_TX_L4_NO_CKSUM PKT_TX_IPV6
    stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    Bad-ipcsum: 0              Bad-l4csum: 1             Bad-outer-l4csum: 0
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 1              RX-dropped: 0             RX-total: 1
    TX-packets: 1              TX-dropped: 0             TX-total: 1
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


Test Case 6: test MAC_IPV4_L2TPv3 l2 tag
========================================

subcase 1: vlan stripping
-------------------------
1. DUT set vlan filter on and enable the vlan receipt::

    testpmd > vlan set filter on 0
    testpmd > set fwd mac
    testpmd > set verbose 1
    testpmd > rx_vlan add 1 0

2. DUT enable the vlan header stripping with vlan tag identifier 1::
    
    testpmd > vlan set strip off 0
    testpmd > start

3. Tester send MAC_IPV4_L2TPv3 pkt with vlan tag identifier 1(ether/vlan/ip/l2tp):: 

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")

4. DUT check the pkt is recieved and fwd with vlan tag 1::

    testpmd> port 0/queue 0: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    tcpdump -i enp134s0f0 -Q in -e -n -v -x
    15:19:26.315127 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto unknown (115), length 504)
    127.0.0.1 > 127.0.0.1:  ip-proto-115 484

5. Tester send MAC_IPV4_L2TPv3 pkt with vlan tag identifier 2::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2)/IP(proto=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")

6. DUT check the pkt is not recieved::

    testpmd> stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 0              RX-dropped: 0             RX-total: 0
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 0              RX-dropped: 0             RX-total: 0
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

7. DUT disable the vlan header stripping with vlan tag identifier 1::

    testpmd > vlan set strip on 0
    testpmd > start

8. Tester send MAC_IPV4_L2TPv3 pkt with vlan tag identifier 1::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")

9. DUT check the pkt is recieved and fwd without vlan tag identifier 1::

    testpmd> port 0/queue 0: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x0800 - length=518 - nb_segs=1 - RSS hash=0x0 - RSS queue=0x0 - VLAN tci=0x1 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x0
    ol_flags: PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_GOOD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN

    15:20:43.803087 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 518: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto unknown (115), length 504)
    127.0.0.1 > 127.0.0.1:  ip-proto-115 484

subcase 2: vlan insertion
-------------------------

1. Add tx vlan offload on port 0, take care the first param is port::

    testpmd> vlan set strip off 0
    testpmd> port stop all
    testpmd> tx_vlan set 0 1
    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> port start all
    testpmd> start

2. Tester send MAC_IPV4_L2TPv3 packets without vlan to port 0::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")

3. Tester check recieved the pkt with vlan tag identifier 1::

    16:08:17.119129 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 526: vlan 1, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto unknown (115), length 504)
    127.0.0.1 > 127.0.0.1:  ip-proto-115 484


Test Case 7: test MAC_IPV6_L2TPv3 l2 tag
========================================

subcase 1: vlan stripping
-------------------------
1. DUT set vlan filter on and enable the vlan receipt::

    testpmd > vlan set filter on 0
    testpmd > set fwd mac
    testpmd > set verbose 1
    testpmd > rx_vlan add 1 0

2. DUT enable the vlan header stripping with vlan tag identifier 1::
    
    testpmd > vlan set strip off 0
    testpmd > start

3. Tester send MAC_IPV6_L2TPv3 pkt with vlan tag identifier 1(ether/vlan/ip/l2tp):: 

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(nh=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")

4. DUT check the pkt is fwd with vlan tag 1::

    16:10:25.899116 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 542: vlan 1, p 0, ethertype IPv6, (hlim 64, next-header unknown (115) payload length: 484) ::1 > ::1: ip-proto-115 484

5. Tester send MAC_IPV6_L2TPv3 pkt with vlan tag identifier 2::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2)/IPv6(nh=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")

6. DUT check the pkt is not recieved::

    testpmd> stop
    Telling cores to stop...
    Waiting for lcores to finish...

    ---------------------- Forward statistics for port 0  ----------------------
    RX-packets: 0              RX-dropped: 0             RX-total: 0
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ----------------------------------------------------------------------------

    +++++++++++++++ Accumulated forward statistics for all ports+++++++++++++++
    RX-packets: 0              RX-dropped: 0             RX-total: 0
    TX-packets: 0              TX-dropped: 0             TX-total: 0
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

7. DUT disable the vlan header stripping with vlan tag identifier 1::

    testpmd > vlan set strip on 0
    testpmd > start

8. Tester send MAC_IPV6_L2TPv3 pkt with vlan tag identifier 1::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(nh=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")

9. DUT check the pkt is fwd without vlan tag identifier 1::

    16:13:20.231049 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv6 (0x86dd), length 538: (hlim 64, next-header unknown (115) payload length: 484) ::1 > ::1: ip-proto-115 484

subcase 2: vlan insertion
-------------------------

1. Add tx vlan offload on port 0, take care the first param is port::

    testpmd> vlan set strip off 0
    testpmd> port stop all
    testpmd> tx_vlan set 0 1
    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> port start all
    testpmd> start

2. Tester send MAC_IPV6_L2TPv3 packets without vlan to port 0::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=115)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")

3. Tester check recieved the pkt with vlan tag identifier 1::

    16:15:35.311109 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 546: vlan 1, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv6, (hlim 64, next-header unknown (115) payload length: 484) ::1 > ::1: ip-proto-115 484


Test Case 8: test MAC_IPV4_ESP l2 tag
=====================================

subcase 1: vlan stripping
-------------------------
1. DUT set vlan filter on and enable the vlan receipt::

    testpmd > vlan set filter on 0
    testpmd > set fwd mac
    testpmd > set verbose 1
    testpmd > rx_vlan add 1 0

2. DUT enable the vlan header stripping with vlan tag identifier 1::
    
    testpmd > vlan set strip off 0
    testpmd > start

3. Tester send MAC_IPV4_ESP pkt with vlan tag identifier 1(ether/vlan/ip/esp):: 

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=50)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

4. DUT check the pkt is fwd with vlan tag 1::

    16:19:22.039132 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 526: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto ESP (50), length 508)
    127.0.0.1 > 127.0.0.1: ESP(spi=0x00000001,seq=0x0), length 488

5. Tester send MAC_IPV4_ESP pkt with vlan tag identifier 2::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2)/IP(proto=50)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

6. DUT check the pkt is not recieved:

7. DUT disable the vlan header stripping with vlan tag identifier 1::

    testpmd > vlan set strip on 0
    testpmd > start

8. Tester send MAC_IPV4_ESP pkt with vlan tag identifier 1::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=50)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

9. DUT check the pkt is fwd without vlan tag identifier 1::

    16:20:49.995057 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 522: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto ESP (50), length 508)
    127.0.0.1 > 127.0.0.1: ESP(spi=0x00000001,seq=0x0), length 488

subcase 2: vlan insertion
-------------------------

1. Add tx vlan offload on port 0, take care the first param is port::

    testpmd> vlan set strip off 0
    testpmd> port stop all
    testpmd> tx_vlan set 0 1
    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> port start all
    testpmd> start

2. Tester send MAC_IPV4_ESP packets without vlan to port 0::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=50)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

3. Tester check recieved the pkt with vlan tag identifier 1::

    16:23:08.631125 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 530: vlan 1, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto ESP (50), length 508)
    127.0.0.1 > 127.0.0.1: ESP(spi=0x00000001,seq=0x0), length 488


Test Case 9: test MAC_IPV6_ESP l2 tag
=====================================

subcase 1: vlan stripping
-------------------------
1. DUT set vlan filter on and enable the vlan receipt::

    testpmd > vlan set filter on 0
    testpmd > set fwd mac
    testpmd > set verbose 1
    testpmd > rx_vlan add 1 0

2. DUT enable the vlan header stripping with vlan tag identifier 1::
    
    testpmd > vlan set strip off 0
    testpmd > start

3. Tester send MAC_IPV6_ESP pkt with vlan tag identifier 1(ether/vlan/ip/esp):: 

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(nh=50)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

4. DUT check the pkt is fwd with vlan tag 1::

    16:25:49.075114 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 546: vlan 1, p 0, ethertype IPv6, (hlim 64, next-header ESP (50) payload length: 488) ::1 > ::1: ESP(spi=0x00000001,seq=0x0), length 488

5. Tester send MAC_IPV6_ESP pkt with vlan tag identifier 2::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2)/IPv6(nh=50)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

6. DUT check the pkt is not recieved:

7. DUT disable the vlan header stripping with vlan tag identifier 1::

    testpmd > vlan set strip on 0
    testpmd > start

8. Tester send MAC_IPV6_ESP pkt with vlan tag identifier 1::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(nh=50)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

9. DUT check the pkt is fwd without vlan tag identifier 1::

    16:26:40.279043 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv6 (0x86dd), length 542: (hlim 64, next-header ESP (50) payload length: 488) ::1 > ::1: ESP(spi=0x00000001,seq=0x0), length 488

subcase 2: vlan insertion
-------------------------

1. Add tx vlan offload on port 0, take care the first param is port::

    testpmd> vlan set strip off 0
    testpmd> port stop all
    testpmd> tx_vlan set 0 1
    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> port start all
    testpmd> start

2. Tester send MAC_IPV6_ESP packets without vlan to port 0::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=50)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

3. Tester check recieved the pkt with vlan tag identifier 1::

    16:28:30.323047 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 550: vlan 1, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv6, (hlim 64, next-header ESP (50) payload length: 488) ::1 > ::1: ESP(spi=0x00000001,seq=0x0), length 488


Test Case 10: test MAC_IPV4_AH l2 tag
=====================================

subcase 1: vlan stripping
-------------------------
1. DUT set vlan filter on and enable the vlan receipt::

    testpmd > vlan set filter on 0
    testpmd > set fwd mac
    testpmd > set verbose 1
    testpmd > rx_vlan add 1 0

2. DUT enable the vlan header stripping with vlan tag identifier 1::
    
    testpmd > vlan set strip off 0
    testpmd > start

3. Tester send MAC_IPV4_AH pkt with vlan tag identifier 1(ether/vlan/ip/ahA):: 

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=51)/AH(spi=1)/Raw('x'*480)], iface="enp134s0f0")

4. DUT check the pkt is fwd with vlan tag 1::

    16:30:56.899138 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 530: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto AH (51), length 512)
    127.0.0.1 > 127.0.0.1: AH(spi=0x00000001,sumlen=0,seq=0x0):  ip-proto-0 484

5. Tester send MAC_IPV4_AH pkt with vlan tag identifier 2::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2)/IP(proto=51)/AH(spi=1)/Raw('x'*480)], iface="enp134s0f0")

6. DUT check the pkt is not recieved:

7. DUT disable the vlan header stripping with vlan tag identifier 1::

    testpmd > vlan set strip on 0
    testpmd > start

8. Tester send MAC_IPV4_AH pkt with vlan tag identifier 1::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=51)/AH(spi=1)/Raw('x'*480)], iface="enp134s0f0")

9. DUT check the pkt is fwd without vlan tag identifier 1::

    16:34:32.599097 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 526: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto AH (51), length 512)
    127.0.0.1 > 127.0.0.1: AH(spi=0x00000001,sumlen=0,seq=0x0):  ip-proto-0 484


subcase 2: vlan insertion
-------------------------

1. Add tx vlan offload on port 0, take care the first param is port::

    testpmd> vlan set strip off 0
    testpmd> port stop all
    testpmd> tx_vlan set 0 1
    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> port start all
    testpmd> start

2. Tester send MAC_IPV4_AH packets without vlan to port 0::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=51)/AH(spi=1)/Raw('x'*480)], iface="enp134s0f0")

3. Tester check recieved the pkt with vlan tag identifier 1::

    16:37:21.783066 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 534: vlan 1, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto AH (51), length 512)
    127.0.0.1 > 127.0.0.1: AH(spi=0x00000001,sumlen=0,seq=0x0):  ip-proto-0 484


Test Case 11: test MAC_IPV6_AH l2 tag
=====================================

subcase 1: vlan stripping
-------------------------
1. DUT set vlan filter on and enable the vlan receipt::

    testpmd > vlan set filter on 0
    testpmd > set fwd mac
    testpmd > set verbose 1
    testpmd > rx_vlan add 1 0

2. DUT enable the vlan header stripping with vlan tag identifier 1::
    
    testpmd > vlan set strip off 0
    testpmd > start

3. Tester send MAC_IPV6_AH pkt with vlan tag identifier 1(ether/vlan/ip/ah):: 

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(nh=51)/AH(spi=1)/Raw('x'*480)], iface="enp134s0f0")

4. DUT check the pkt is fwd with vlan tag 1::

    16:32:11.519239 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 550: vlan 1, p 0, ethertype IPv6, (hlim 64, next-header AH (51) payload length: 492) ::1 > ::1: AH(spi=0x00000001,sumlen=0,seq=0x0): HBH (pad1)(pad1)[trunc] [|HBH]

5. Tester send MAC_IPV6_AH pkt with vlan tag identifier 2::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2)/IPv6(nh=51)/AH(spi=1)/Raw('x'*480)], iface="enp134s0f0")

6. DUT check the pkt is not recieved:

7. DUT disable the vlan header stripping with vlan tag identifier 1::

    testpmd > vlan set strip on 0
    testpmd > start

8. Tester send MAC_IPV6_AH pkt with vlan tag identifier 1::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6(nh=51)/AH(spi=1)/Raw('x'*480)], iface="enp134s0f0")

9. DUT check the pkt is fwd without vlan tag identifier 1::

    16:35:27.395058 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv6 (0x86dd), length 546: (hlim 64, next-header AH (51) payload length: 492) ::1 > ::1: AH(spi=0x00000001,sumlen=0,seq=0x0): HBH (pad1)(pad1)[trunc] [|HBH]


subcase 2: vlan insertion
-------------------------

1. Add tx vlan offload on port 0, take care the first param is port::

    testpmd> vlan set strip off 0
    testpmd> port stop all
    testpmd> tx_vlan set 0 1
    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> port start all
    testpmd> start

2. Tester send MAC_IPV6_AH packets without vlan to port 0::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6(nh=51)/AH(spi=1)/Raw('x'*480)], iface="enp134s0f0")

3. Tester check recieved the pkt with vlan tag identifier 1::

    16:38:02.311042 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 554: vlan 1, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv6, (hlim 64, next-header AH (51) payload length: 492) ::1 > ::1: AH(spi=0x00000001,sumlen=0,seq=0x0): HBH (pad1)(pad1)[trunc] [|HBH]


Test Case 12: test MAC_IPV4_NAT-T-ESP l2 tag
============================================

subcase 1: vlan stripping
-------------------------
1. DUT set vlan filter on and enable the vlan receipt::

    testpmd > vlan set filter on 0
    testpmd > set fwd mac
    testpmd > set verbose 1
    testpmd > rx_vlan add 1 0

2. DUT enable the vlan header stripping with vlan tag identifier 1::
    
    testpmd > vlan set strip off 0
    testpmd > start

3. Tester send MAC_IPV4_NAT-T-ESP pkt with vlan tag identifier 1(ether/vlan/ip/udp/esp):: 

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

4. DUT check the pkt is fwd with vlan tag 1::

    16:43:18.351118 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 534: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto UDP (17), length 516)
    127.0.0.1.4500 > 127.0.0.1.4500: UDP-encap: ESP(spi=0x00000001,seq=0x0), length 488

5. Tester send MAC_IPV4_NAT-T-ESP pkt with vlan tag identifier 2::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2)/IP()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

6. DUT check the pkt is not recieved:

7. DUT disable the vlan header stripping with vlan tag identifier 1::

    testpmd > vlan set strip on 0
    testpmd > start

8. Tester send MAC_IPV4_NAT-T-ESP pkt with vlan tag identifier 1::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

9. DUT check the pkt is recieved without vlan tag identifier 1::

    16:46:50.015123 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 530: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto UDP (17), length 516)
    127.0.0.1.4500 > 127.0.0.1.4500: UDP-encap: ESP(spi=0x00000001,seq=0x0), length 488

subcase 2: vlan insertion
-------------------------

1. Add tx vlan offload on port 0, take care the first param is port::

    testpmd> vlan set strip off 0
    testpmd> port stop all
    testpmd> tx_vlan set 0 1
    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> port start all
    testpmd> start

2. Tester send MAC_IPV4_NAT-T-ESP packets without vlan to port 0::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

3. Tester check recieved the pkt with vlan tag identifier 1::

    16:49:41.875196 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 538: vlan 1, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto UDP (17), length 516)
    127.0.0.1.4500 > 127.0.0.1.4500: UDP-encap: ESP(spi=0x00000001,seq=0x0), length 488


Test Case 13: test MAC_IPV6_NAT-T-ESP l2 tag
============================================

subcase 1: vlan stripping
-------------------------
1. DUT set vlan filter on and enable the vlan receipt::

    testpmd > vlan set filter on 0
    testpmd > set fwd mac
    testpmd > set verbose 1
    testpmd > rx_vlan add 1 0

2. DUT enable the vlan header stripping with vlan tag identifier 1::
    
    testpmd > vlan set strip off 0
    testpmd > start

3. Tester send MAC_IPV6_NAT-T-ESP pkt with vlan tag identifier 1(ether/vlan/ip/udp/esp):: 

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

4. DUT check the pkt is fwd with vlan tag 1::

    16:44:13.959467 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 554: vlan 1, p 0, ethertype IPv6, (hlim 64, next-header UDP (17) payload length: 496) ::1.4500 > ::1.4500: [udp sum ok] UDP-encap: ESP(spi=0x00000001,seq=0x0), length 488

5. Tester send MAC_IPV6_NAT-T-ESP pkt with vlan tag identifier 2::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=2)/IPv6()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

6. DUT check the pkt is not recieved:

7. DUT disable the vlan header stripping with vlan tag identifier 1::

    testpmd > vlan set strip on 0
    testpmd > start

8. Tester send MAC_IPV6_NAT-T-ESP pkt with vlan tag identifier 1::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IPv6()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

9. DUT check the pkt is recieved without vlan tag identifier 1::

    16:47:30.747658 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv6 (0x86dd), length 550: (hlim 64, next-header UDP (17) payload length: 496) ::1.4500 > ::1.4500: [udp sum ok] UDP-encap: ESP(spi=0x00000001,seq=0x0), length 488

subcase 2: vlan insertion
-------------------------

1. Add tx vlan offload on port 0, take care the first param is port::

    testpmd> vlan set strip off 0
    testpmd> port stop all
    testpmd> tx_vlan set 0 1
    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> port start all
    testpmd> start

2. Tester send MAC_IPV4_NAT-T-ESP packets without vlan to port 0::

    sendp([Ether(dst="00:11:22:33:44:55")/IPv6()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

3. Tester check recieved the pkt with vlan tag identifier 1::

    16:50:29.791349 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype 802.1Q (0x8100), length 558: vlan 1, p 0, ethertype 802.1Q, vlan 1, p 0, ethertype IPv6, (hlim 64, next-header UDP (17) payload length: 496) ::1.4500 > ::1.4500: [udp sum ok] UDP-encap: ESP(spi=0x00000001,seq=0x0), length 488


Test Case 14: MAC_IPV4_L2TPv3 vlan strip on + HW checksum offload check
=======================================================================

The pre-steps are as l2tp_esp_iavf_test_plan.

1. ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -a af:01.0 -- -i --rxq=16 --txq=16 --portmask=0x1 --nb-cores=2 --enable-rx-cksum

2. DUT create fdir rules for MAC_IPV4_L2TPv3 with queue index and mark::

    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 1 / end actions queue index 1 / mark id 4 / end
    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 2 / end actions queue index 2 / mark id 3 / end
    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 3 / end actions queue index 3 / mark id 2 / end
    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 4 / end actions queue index 4 / mark id 1 / end

3. Enable vlan filter and receipt of VLAN packets with VLAN Tag Identifier 1 on port 0, Enable vlan strip on VF0::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> vlan set strip on 0
    testpmd> set verbose 1
     
4. enable hw checksum::
   
    testpmd> set fwd csum
    Set csum packet forwarding mode
    testpmd> port stop all
    testpmd> csum set ip hw 0
    testpmd> csum set udp hw 0
    testpmd> port start all
    testpmd> start

5. Tester send matched packets with VLAN tag "1" and incorrect checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=115,chksum=0x123)/L2TP('\x00\x00\x00\x01')/Raw('x'*480)], iface="enp134s0f0")
    
6. DUT check the packets are distributed to expected queue with mark id and fwd without VLAN tag "1", and report the checksum error::

    testpmd> port 0/queue 1: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x0800 - length=518 - nb_segs=1 - RSS hash=0x828dafbf - RSS queue=0x1 - VLAN tci=0x1 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x1
    ol_flags: PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2268c09840, pkt_len=518, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=115 l4_len=0 flags=PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4

    15:20:43.803087 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 518: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto unknown (115), length 504)
    127.0.0.1 > 127.0.0.1:  ip-proto-115 484

7. Tester send mismatched packets with VLAN tag "1" and incorrect checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=115,chksum=0x123)/L2TP('\x00\x00\x00\x11')/Raw('x'*480)], iface="enp134s0f0")

8. DUT check the packets are not distributed to expected queue without mark id and fwd without VLAN tag "1", and report the checksum error::
   
    port 0/queue 15: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x0800 - length=518 - nb_segs=1 - RSS hash=0x828dafbf - RSS queue=0xf - VLAN tci=0x1 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0xf
    ol_flags: PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2269cba700, pkt_len=518, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=115 l4_len=0 flags=PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4

    15:20:43.803087 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 518: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto unknown (115), length 504)
    127.0.0.1 > 127.0.0.1:  ip-proto-115 484

9. DUT verify rule can be listed and destroyed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 L2TPV3OIP => QUEUE MARK
    1       0       0       i--     ETH IPV4 L2TPV3OIP => QUEUE MARK
    2       0       0       i--     ETH IPV4 L2TPV3OIP => QUEUE MARK
    3       0       0       i--     ETH IPV4 L2TPV3OIP => QUEUE MARK
    testpmd> flow destroy 0 rule 0

10. Tester send matched packets with VLAN tag "1" and incorrect checksum::

     sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=115,chksum=0x123)/L2TP('\x00\x00\x00\x01')/Raw('x'*480)], iface="enp134s0f0")

11.DUT check the packets are not distributed to expected queue without mark id and and without VLAN tag "1", and report the checksum error::

    testpmd> port 0/queue 15: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x0800 - length=518 - nb_segs=1 - RSS hash=0x828dafbf - RSS queue=0xf - VLAN tci=0x1 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0xf
    ol_flags: PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2269cb9dc0, pkt_len=518, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=115 l4_len=0 flags=PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4

    15:20:43.803087 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 518: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto unknown (115), length 504)
    127.0.0.1 > 127.0.0.1:  ip-proto-115 484


Test Case 15: MAC_IPV4_L2TPv3 vlan insert on + SW checksum offload check
========================================================================

1. ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -a af:01.0 -- -i --rxq=16 --txq=16 --portmask=0x1 --nb-cores=2 --enable-rx-cksum

2. DUT create fdir rules for MAC_IPV4_L2TPv3 with queue index and mark::

    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 1 / end actions queue index 1 / mark id 4 / end
    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 2 / end actions queue index 2 / mark id 3 / end
    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 3 / end actions queue index 3 / mark id 2 / end
    flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 4 / end actions queue index 4 / mark id 1 / end

3. Enable vlan filter and add tx vlan offload on port 0::

    testpmd> port stop all
    testpmd> rx_vlan add 1 0
    testpmd> vlan set filter on 0
    testpmd> tx_vlan set 0 1
    testpmd> port start all
    testpmd> set fwd mac
    testpmd> set verbose 1

4. Tester send matched packets without vlan::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=115)/L2TP('\x00\x00\x00\x02')/Raw('x'*480)], iface="enp134s0f0")
    
5. DUT check the packets are distributed to expected queue with mark id and fwd with VLAN tag "1" to tester::

    testpmd> port 0/queue 2: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0xf20d0ef3 - RSS queue=0x2 - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x2
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2268d26880, pkt_len=522, nb_segs=1:
    rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=115 l4_len=0 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: flags=PKT_TX_L4_NO_CKSUM PKT_TX_IPV4
    
    17:25:40.615279 a4:bf:01:6a:62:58 > 00:11:22:33:44:55, ethertype 802.1Q (0x8100), length 522: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto unknown (115), length 504, bad cksum 123 (->7a90)!)
    127.0.0.1 > 127.0.0.1:  ip-proto-115 484

6. enable sw checksum::
    
    testpmd> set fwd csum
    Set csum packet forwarding mode
    testpmd> port stop all
    testpmd> csum set ip sw 0
    testpmd> csum set udp sw 0
    testpmd> port start all
    testpmd> start

7. Tester send mismatched packets with incorrect checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=115,chksum=0x123)/L2TP('\x00\x00\x00\x22')/Raw('x'*480)], iface="enp134s0f0")

8. DUT check the packets are not distributed to expected queue without mark id and report the checksum error::

    port 0/queue 3: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0xf20d0ef3 - RSS queue=0x3 - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x3
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2268e42f80, pkt_len=522, nb_segs=1:
    rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=115 l4_len=0 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: flags=PKT_TX_L4_NO_CKSUM PKT_TX_IPV4

9. DUT verify rule can be listed and destroyed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 L2TPV3OIP => QUEUE MARK
    1       0       0       i--     ETH IPV4 L2TPV3OIP => QUEUE MARK
    2       0       0       i--     ETH IPV4 L2TPV3OIP => QUEUE MARK
    3       0       0       i--     ETH IPV4 L2TPV3OIP => QUEUE MARK
    testpmd> flow destroy 0 rule 1

10. Tester send matched packets with incorrect checksum::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(proto=115,chksum=0x123)/L2TP('\x00\x00\x00\x02')/Raw('x'*480)], iface="enp134s0f0")

11.DUT check the packets are not distributed to expected queue without mark id and report the checksum error::

    testpmd> port 0/queue 3: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x8100 - length=522 - nb_segs=1 - RSS hash=0xf20d0ef3 - RSS queue=0x3 - sw ptype: L2_ETHER_VLAN L3_IPV4  - l2_len=18 - l3_len=20 - Receive queue=0x3
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2268e42640, pkt_len=522, nb_segs=1:
    rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=115 l4_len=0 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: flags=PKT_TX_L4_NO_CKSUM PKT_TX_IPV4


Test Case 16: MAC_IPV4_ESP vlan strip on + HW checksum offload check
====================================================================

The pre-steps are as l2tp_esp_iavf_test_plan.

1. ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -a af:01.0 -- -i --rxq=16 --txq=16 --portmask=0x1 --nb-cores=2 --enable-rx-cksum

2. DUT create fdir rules for MAC_IPV4_ESP with queue index and mark::

    flow create 0 ingress pattern eth / ipv4 / esp spi is 1 / end actions queue index 1 / mark id 4 / end
    flow create 0 ingress pattern eth / ipv4 / esp spi is 2 / end actions queue index 2 / mark id 3 / end
    flow create 0 ingress pattern eth / ipv4 / esp spi is 3 / end actions queue index 3 / mark id 2 / end
    flow create 0 ingress pattern eth / ipv4 / esp spi is 4 / end actions queue index 4 / mark id 1 / end

3. Enable vlan filter and receipt of VLAN packets with VLAN Tag Identifier 1 on port 0, Enable vlan strip on VF0::

    testpmd> vlan set filter on 0
    testpmd> rx_vlan add 1 0
    testpmd> vlan set strip on 0
     
4. enable hw checksum::
   
    testpmd> set fwd csum
    Set csum packet forwarding mode
    testpmd> set verbose 1
    testpmd> port stop all
    testpmd> csum set ip hw 0
    testpmd> csum set udp hw 0
    testpmd> port start all
    testpmd> start

5. Tester send matched packets with VLAN tag "1" and incorrect checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=50,chksum=0x123)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")
    
6. DUT check the packets are distributed to expected queue with mark id and fwd without VLAN tag "1", and report the checksum error::

    testpmd> port 0/queue 1: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x0800 - length=522 - nb_segs=1 - RSS hash=0xeb9be2c9 - RSS queue=0x1 - VLAN tci=0x1 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x1
    ol_flags: PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2268c0a180, pkt_len=522, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=50 l4_len=0 flags=PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4

    17:39:12.063112 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 522: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto ESP (50), length 508)
    127.0.0.1 > 127.0.0.1: ESP(spi=0x00000001,seq=0x0), length 488

7. Tester send mismatched packets with VLAN tag "1" and incorrect checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=50,chksum=0x123)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0")

8. DUT check the packets are not distributed to expected queue without mark id and fwd without VLAN tag "1", and report the checksum error::

    port 0/queue 9: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x0800 - length=522 - nb_segs=1 - RSS hash=0xeb9be2c9 - RSS queue=0x9 - VLAN tci=0x1 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x9
    ol_flags: PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x226960fd00, pkt_len=522, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=50 l4_len=0 flags=PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4

    17:40:33.967072 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 522: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto ESP (50), length 508)
    127.0.0.1 > 127.0.0.1: ESP(spi=0x0000000b,seq=0x0), length 488

9. DUT verify rule can be listed and destroyed::

    testpmd> flow list 0
    0       0       0       i--     ETH IPV4 ESP => QUEUE MARK
    1       0       0       i--     ETH IPV4 ESP => QUEUE MARK
    2       0       0       i--     ETH IPV4 ESP => QUEUE MARK
    3       0       0       i--     ETH IPV4 ESP => QUEUE MARK
    testpmd> flow destroy 0 rule 0

10. Tester send matched packets with VLAN tag "1" and incorrect checksum::

     sendp([Ether(dst="00:11:22:33:44:55")/Dot1Q(vlan=1)/IP(proto=50,chksum=0x123)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")
    
11.DUT check the packets are not distributed to expected queue without mark id and and fwd without VLAN tag "1", and report the checksum error::

    testpmd> port 0/queue 9: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x0800 - length=522 - nb_segs=1 - RSS hash=0xeb9be2c9 - RSS queue=0x9 - VLAN tci=0x1 - sw ptype: L2_ETHER L3_IPV4  - l2_len=14 - l3_len=20 - Receive queue=0x9
    ol_flags: PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x226960f3c0, pkt_len=522, nb_segs=1:
    rx: l2_len=14 ethertype=800 l3_len=20 l4_proto=50 l4_len=0 flags=PKT_RX_VLAN PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_VLAN_STRIPPED PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: m->l2_len=14 m->l3_len=20 m->l4_len=0
    tx: flags=PKT_TX_IP_CKSUM PKT_TX_L4_NO_CKSUM PKT_TX_IPV4

    17:42:29.419400 00:11:22:33:44:55 > 02:00:00:00:00:00, ethertype IPv4 (0x0800), length 522: (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto ESP (50), length 508)
    127.0.0.1 > 127.0.0.1: ESP(spi=0x00000001,seq=0x0), length 488


Test Case 17: MAC_IPV6_NAT-T-ESP vlan insert on + SW checksum offload check
===========================================================================

1. ./x86_64-native-linuxapp-gcc/app/testpmd -l 6-9 -n 4 -a af:01.0 -- -i --rxq=16 --txq=16 --portmask=0x1 --nb-cores=2 --enable-rx-cksum

2. DUT create fdir rules for MAC_IPV6_NAT-T-ESP with queue index and mark::

    flow create 0 ingress pattern eth / ipv4 / udp / esp spi is 1 / end actions queue index 1 / mark id 4 / end
    flow create 0 ingress pattern eth / ipv4 / udp / esp spi is 2 / end actions queue index 2 / mark id 3 / end
    flow create 0 ingress pattern eth / ipv4 / udp / esp spi is 3 / end actions queue index 3 / mark id 2 / end
    flow create 0 ingress pattern eth / ipv4 / udp / esp spi is 4 / end actions queue index 4 / mark id 1 / end

3. Enable vlan filter and add tx vlan offload on port 0::

    testpmd> port stop all
    testpmd> rx_vlan add 1 0
    testpmd> vlan set filter on 0
    testpmd> tx_vlan set 0 1
    testpmd> port start all
    testpmd> set fwd mac
    testpmd> set verbose 1

4. Tester send matched packets without vlan::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(chksum=0x123)/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")
    
5. DUT check the packets are distributed to expected queue with mark id and fwd with VLAN tag "1" to tester::

    testpmd> port 0/queue 1: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x8100 - length=534 - nb_segs=1 - RSS hash=0x89b546af - RSS queue=0x1 - sw ptype: L2_ETHER_VLAN L3_IPV4 L4_UDP  - l2_len=18 - l3_len=20 - l4_len=8 - Receive queue=0x1
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2268c0a180, pkt_len=534, nb_segs=1:
    rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: flags=PKT_TX_L4_NO_CKSUM PKT_TX_IPV4

    17:49:14.935149 a4:bf:01:6a:62:58 > 00:11:22:33:44:55, ethertype 802.1Q (0x8100), length 534: vlan 1, p 0, ethertype IPv4, (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto UDP (17), length 516, bad cksum 123 (->7ae6)!)
    127.0.0.1.4500 > 127.0.0.1.4500: UDP-encap: ESP(spi=0x00000001,seq=0x0), length 488

6. enable sw checksum::
    
    testpmd> set fwd csum
    Set csum packet forwarding mode
    testpmd> port stop all
    testpmd> csum set ip sw 0
    testpmd> csum set udp sw 0
    testpmd> port start all
    testpmd> start

7. Tester send mismatched packets with incorrect checksum::

    sendp([Ether(dst="00:11:22:33:44:55")/IP(chksum=0x123)/UDP(dport=4500)/ESP(spi=11)/Raw('x'*480)], iface="enp134s0f0")

8. DUT check the packets are not distributed to expected queue without mark id and report the checksum error::

    port 0/queue 15: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x8100 - length=534 - nb_segs=1 - RSS hash=0x89b546af - RSS queue=0xf - sw ptype: L2_ETHER_VLAN L3_IPV4 L4_UDP  - l2_len=18 - l3_len=20 - l4_len=8 - Receive queue=0xf
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2269cba700, pkt_len=534, nb_segs=1:
    rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: flags=PKT_TX_L4_NO_CKSUM PKT_TX_IPV4

9. DUT verify rule can be listed and destroyed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP ESP => QUEUE MARK
    1       0       0       i--     ETH IPV4 UDP ESP => QUEUE MARK
    2       0       0       i--     ETH IPV4 UDP ESP => QUEUE MARK
    3       0       0       i--     ETH IPV4 UDP ESP => QUEUE MARK
    testpmd> flow destroy 0 rule 0

10. Tester send matched packets with incorrect checksum::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(chksum=0x123)/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)], iface="enp134s0f0")

11.DUT check the packets are not distributed to expected queue without mark id and report the checksum error::

    testpmd> port 0/queue 15: received 1 packets
    src=A4:BF:01:6A:62:58 - dst=00:11:22:33:44:55 - type=0x8100 - length=534 - nb_segs=1 - RSS hash=0x89b546af - RSS queue=0xf - sw ptype: L2_ETHER_VLAN L3_IPV4 L4_UDP  - l2_len=18 - l3_len=20 - l4_len=8 - Receive queue=0xf
    ol_flags: PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    -----------------
    port=0, mbuf=0x2269cb9dc0, pkt_len=534, nb_segs=1:
    rx: l2_len=18 ethertype=800 l3_len=20 l4_proto=17 l4_len=8 flags=PKT_RX_RSS_HASH PKT_RX_L4_CKSUM_GOOD PKT_RX_IP_CKSUM_BAD PKT_RX_OUTER_L4_CKSUM_UNKNOWN
    tx: flags=PKT_TX_L4_NO_CKSUM PKT_TX_IPV4

