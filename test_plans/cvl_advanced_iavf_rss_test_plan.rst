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

==============================
CVL: IAVF Advanced RSS FOR CVL
==============================

Description
===========


IAVF Advanced RSS support columbiaville nic with ice , throught create rule include related pattern and input-set
to hash IP and ports domain, diversion the packets to the difference queues in VF.

* inner header hash for tunnel packets, including comms package.
* symmetric hash by rte_flow RSS action.
* input set change by rte_flow RSS action.
* For PFCP protocal, the destination port value of the outer UDP header is equal to 8805(0x2265).
  PFCP Node headers shall be identified when the Version field is equal to 001 and the S field is equal 0.
  PFCP Session headers shall be identified when the Version field is equal to 001 and the S field is equal 1.
  CVL only support RSS hash for PFCP Session SEID value.
* For L2TPv3 protocal, the IP proto id is equal to 115(0x73).
  CVL only support RSS hash for L2TPv3 Session id value.
* For ESP protocal, the IP proto id is equal to 50(0x32).
  CVL only support RSS hash for ESP SPI value.
* For AH protocal, the IP proto id is equal to 51(0x33).
  CVL only support RSS hash for AH SPI value.
* For NAT_T-ESP protocal, the destination port value of the outer UDP header is equal to 4500(0x1194).
  CVL only support RSS hash for NAT_T-ESP SPI value.

Pattern and input set
---------------------

.. table::

    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | Default hash function: Non Symmetric_toeplitz                                                                                                |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | Packet Type                   | Pattern                   | All the Input Set options in combination                                         |
    +===============================+===========================+==================================================================================+
    | IPv4/IPv6 + TCP/UDP/SCTP      | MAC_IPV4                  | eth, l2-src-only, l2-dst-only, ipv4, l3-src-only, l3-dst-only                    |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_UDP              | eth, l2-src-only, l2-dst-only, ipv4-udp, l3-src-only, l3-dst-only,               |
    |                               |                           | l4-src-only, l4-dst-only                                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_TCP              | eth, l2-src-only, l2-dst-only, ipv4-tcp, l3-src-only, l3-dst-only,               |
    |                               |                           | l4-src-only, l4-dst-only                                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_SCTP             | eth, l2-src-only, l2-dst-only, ipv4-sctp, l3-src-only, l3-dst-only,              |
    |                               |                           | l4-src-only, l4-dst-only                                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6                  | eth, l2-src-only, l2-dst-only, ipv6, l3-src-only, l3-dst-only                    |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_UDP              | eth, l2-src-only, l2-dst-only, ipv6-udp, l3-src-only, l3-dst-only,               |
    |                               |                           | l4-src-only, l4-dst-only                                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_TCP              | eth, l2-src-only, l2-dst-only, ipv6-tcp, l3-src-only, l3-dst-only,               |
    |                               |                           | l4-src-only, l4-dst-only                                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_SCTP             | eth, l2-src-only, l2-dst-only, ipv6-sctp, l3-src-only, l3-dst-only,              |
    |                               |                           | l4-src-only, l4-dst-only                                                         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | GTP-U data packet types       | MAC_IPV4_GTPU_IPV4        | gtpu, ipv4, l3-src-only, l3-dst-only                                             |
    | IPv4/IPv6 transport           |                           |                                                                                  |
    | IPv4/IPv6 payload             |                           |                                                                                  |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV4_UDP    | ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV4_TCP    | ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV6        | gtpu, ipv6, l3-src-only, l3-dst-only                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV6_UDP    | ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV6_TCP    | ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV4        | gtpu, ipv4, l3-src-only, l3-dst-only                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV4_UDP    | ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV4_TCP    | ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV6        | gtpu, ipv6, l3-src-only, l3-dst-only                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV6_UDP    | ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV6_TCP    | ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4     | ipv4, l3-src-only, l3-dst-only                                                   |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4_UDP | ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4_TCP | ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6     | ipv6, l3-src-only, l3-dst-only                                                   |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6_UDP | ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6_TCP | ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4     | ipv4, l3-src-only, l3-dst-only                                                   |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4_UDP | ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4_TCP | ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6     | ipv6, l3-src-only, l3-dst-only                                                   |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6_UDP | ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6_TCP | ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only                     |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | VLAN                          | MAC_VLAN_IPV4             | c-vlan                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV4_UDP_PAY     | c-vlan                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV4_TCP_PAY     | c-vlan                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV4_SCTP_PAY    | c-vlan                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV6             | c-vlan                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV6_UDP_PAY     | c-vlan                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV6_TCP_PAY     | c-vlan                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_VLAN_IPV6_SCTP_PAY    | c-vlan                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | ESP                           | MAC_IPV4_ESP              | esp                                                                              |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_UDP_ESP          | esp                                                                              |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_ESP              | esp                                                                              |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_UDP_ESP          | esp                                                                              |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | AH                            | MAC_IPV4_AH               | ah                                                                               |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_AH               | ah                                                                               |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | L2TP                          | MAC_IPV4_L2TP             | l2tpv3                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_L2TP             | l2tpv3                                                                           |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | PFCP                          | MAC_IPV4_PFCP             | pfcp                                                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_PFCP             | pfcp                                                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+

.. table::

    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    | Hash function: Symmetric_toeplitz                                                                                                          |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    | Packet Type                   | Pattern                   | Input Set                                                                      |
    +===============================+===========================+================================================================================+
    | IPv4/IPv6 + TCP/UDP/SCTP      | MAC_IPV4                  | ipv4                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_UDP              | ipv4-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_TCP              | ipv4-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_SCTP             | ipv4-sctp                                                                      |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6                  | ipv6                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_UDP              | ipv6-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_TCP              | ipv6-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_SCTP             | ipv6-sctp                                                                      |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    | GTP-U data packet types       | MAC_IPV4_GTPU_IPV4        | ipv4                                                                           |
    | IPv4/IPv6 transport           |                           |                                                                                |
    | IPv4/IPv6 payload             |                           |                                                                                |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV4_UDP    | ipv4-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV4_TCP    | ipv4-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV6        | ipv6                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV6_UDP    | ipv6-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV6_TCP    | ipv6-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV4        | ipv4                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV4_UDP    | ipv4-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV4_TCP    | ipv4-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV6        | ipv6                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV6_UDP    | ipv6-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV6_TCP    | ipv6-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4     | ipv4                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4_UDP | ipv4-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4_TCP | ipv4-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6     | ipv6                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6_UDP | ipv6-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6_TCP | ipv6-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4     | ipv4                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4_UDP | ipv4-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4_TCP | ipv4-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6     | ipv6                                                                           |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6_UDP | ipv6-udp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6_TCP | ipv6-tcp                                                                       |
    +-------------------------------+---------------------------+--------------------------------------------------------------------------------+

.. note::

    This test plan only cover the packet type IPv4/IPv6 + TCP/UDP/SCTP,
    including toeplitz, symmetric.
    simple xor is not support in IAVF.
    Other packet types will be coverd in other test plans.
    Rules with src/dst mac addresses as hash input set can not be applied
    to tunnel packets. So in the test cases with input set src/dst mac addresses,
    matched packets do not include tunnel packets.

Prerequisites
=============

1. Hardware:

   - Intel E810 series ethernet cards: columbiaville_25g/columbiaville_100g/

2. Software:

   - dpdk: http://dpdk.org/git/dpdk
   - scapy: http://www.secdev.org/projects/scapy/

.. note::

   This rss feature designed for CVL NIC 25G and 100g, so below the case only support CVL nic.

3. create a VF from a PF in DUT, set mac address for thi VF::

    echo 1 > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
    ip link set enp24s0f0 vf 0 mac 00:11:22:33:44:55

4. bind the VF to dpdk driver in DUT::

    modprobe vfio-pci
    usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:18:01.0

.. note::

   The kernel must be >= 3.6+ and VT-d must be enabled in bios.

5. Launch the testpmd to configuration queue of rx and tx number 16 in DUT::

    ./x86_64-native-linuxapp-gcc/app/dpdk-testpmd  -c 0xff -n 4 -w 0000:18:01.0 -- -i --rxq=16 --txq=16
    testpmd>set fwd rxonly
    testpmd>set verbose 1

6. start scapy and configuration NVGRE and GTP profile in tester
   scapy::

   >>> import sys
   >>> sys.path.append('~/dts/dep')
   >>> from nvgre import NVGRE
   >>> from scapy.contrib.gtp import *

Default parameters
------------------

   MAC::

    [Src MAC]: 68:05:CA:BB:26:E0
    [Dest MAC]: 00:11:22:33:44:55

   IPv4::

    [Dest IP]: 192.168.0.1
    [Source IP]: 192.168.0.2

   IPv6::

    [Source IPv6]: ABAB:910B:6666:3457:8295:3333:1800:2929
    [Dest IPv6]: CDCD:910A:2222:5498:8475:1111:3900:2020

   UDP/TCP/SCTP::

    [Source Port]: 22
    [Dest Port]: 23

toeplitz Test steps
===================
all the test cases run the same test steps as below:

1. validate rule.
2. create rule and list rule.
3. send a basic hit pattern packet,record the hash value,
   check the packet is distributed to queues by RSS.
4. send hit pattern packet with changed input set in the rule.
   check the received packet have different hash value with basic packet.
   check the packet is distributed to queues by rss.
5. send hit pattern packet with changed input set not in the rule.
   check the received packet have same hash value with the basic packet.
   check the packet is distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.
6. destroy the rule and list rule.
7. send same packet with step 3.
   check the received packet have different hash value with basic packet.

Test case: MAC_IPV4
===================
basic hit pattern packets are the same in this test case:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.0.2')/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_L2SRC
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l2-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5",frag=7)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=19,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_L2DST
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l2-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5",frag=7)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=19,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_L2SRC_L2DST
-----------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types eth end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5",frag=7)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/TCP(sport=23,dport=25)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_L3SRC
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.1.2')/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.1.1", src='192.168.0.2')/UDP(sport=32,dport=33)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_L3DST
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.1.1", src='192.168.0.2')/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.1.2')/UDP(sport=32,dport=33)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_ALL
---------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.1.1", src='192.168.0.2')/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.1.2')/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")


Test case: MAC_IPV4_UDP
=======================

basic hit pattern packets are the same in this test case.
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L2SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L2DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L2SRC_L2DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types eth end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.3", src="192.168.0.5")/UDP(sport=25,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L3SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L3DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L3SRC_L4SRC
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L3SRC_L4DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L3DST_L4SRC
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L3DST_L4DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L4SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_L4DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)], iface="enp134s0f0")

Subcase: MAC_IPV4_UDP_ALL
-------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")


Test case: MAC_IPV4_TCP
=======================
the rules and packets in this test case is similar to "Test case: MAC_IPV4_UDP"
just change some parts of rules and packets:

    rule:
        change udp to tcp, change ipv4-udp to ipv4-tcp
    packets:
        if the packet's L4 layer is UDP, change it to TCP;
        if the packet's L4 layer is TCP, change it to UDP;
        if tunnel packet, change inner L4 layer from UDP to TCP;
        if tunnel packet, change inner L4 layer from TCP to UDP;

Subcase: MAC_IPV4_TCP_L2SRC
---------------------------

Subcase: MAC_IPV4_TCP_L2DST
---------------------------

Subcase: MAC_IPV4_TCP_L2SRC_L2DST
---------------------------------

Subcase: MAC_IPV4_TCP_L3SRC
---------------------------

Subcase: MAC_IPV4_TCP_L3DST
---------------------------

Subcase: MAC_IPV4_TCP_L3SRC_L4SRC
---------------------------------

Subcase: MAC_IPV4_TCP_L3SRC_L4DST
---------------------------------

Subcase: MAC_IPV4_TCP_L3DST_L4SRC
---------------------------------

Subcase: MAC_IPV4_TCP_L3DST_L4DST
---------------------------------

Subcase: MAC_IPV4_TCP_L4SRC
---------------------------

Subcase: MAC_IPV4_TCP_L4DST
---------------------------

Subcase: MAC_IPV4_TCP_ALL
-------------------------


Test case: MAC_IPV4_SCTP
========================
the rules and packets in this test case is similar to "Test case: MAC_IPV4_UDP"
just change some parts of rules and packets:

    rule:
        change udp to sctp, change ipv4-udp to ipv4-sctp
    packets:
        if the packet's L4 layer is UDP, change it to SCTP;
        if tunnel packet, change inner L4 layer from UDP to SCTP;
        others can be not changed.

Subcase: MAC_IPV4_SCTP_L2SRC
----------------------------

Subcase: MAC_IPV4_SCTP_L2DST
----------------------------

Subcase: MAC_IPV4_SCTP_L2SRC_L2DST
----------------------------------

Subcase: MAC_IPV4_SCTP_L3SRC
----------------------------

Subcase: MAC_IPV4_SCTP_L3DST
----------------------------

Subcase: MAC_IPV4_SCTP_L3SRC_L4SRC
----------------------------------

Subcase: MAC_IPV4_SCTP_L3SRC_L4DST
----------------------------------

Subcase: MAC_IPV4_SCTP_L3DST_L4SRC
----------------------------------

Subcase: MAC_IPV4_SCTP_L3DST_L4DST
----------------------------------

Subcase: MAC_IPV4_SCTP_L4SRC
----------------------------

Subcase: MAC_IPV4_SCTP_L4DST
----------------------------

Subcase: MAC_IPV4_SCTP_ALL
--------------------------


Test case: MAC_IPV6
===================
basic hit pattern packets are the same in this test case:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_L2SRC
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types eth l2-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_L2DST
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types eth l2-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2027")/UDP(sport=25,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_L2SRC_L2DST
-----------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types eth end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_L3SRC
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_L3DST
-----------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_ALL
---------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/ICMP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")


Test case: MAC_IPV6_UDP
=======================
basic hit pattern packets are the same in this test case:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_UDP_L2SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types eth l2-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_UDP_L2DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types eth l2-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_UDP_L2SRC_L2DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types eth end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2923",dst="CDCD:910A:2222:5498:8475:1111:3900:2025")/UDP(sport=25,dport=99)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_UDP_L3SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")


Subcase: MAC_IPV6_UDP_L3DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=33)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_UDP_L3SRC_L4SRC
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")


Subcase: MAC_IPV6_UDP_L3SRC_L4DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")


Subcase: MAC_IPV6_UDP_L3DST_L4SRC
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")


Subcase: MAC_IPV6_UDP_L3DST_L4DST
---------------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

Subcase: MAC_IPV6_UDP_L4SRC
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")


Subcase: MAC_IPV6_UDP_L4DST
---------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")


Subcase: MAC_IPV6_UDP_ALL
-------------------------
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

ipv4_udp_vxlan_ipv6_udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=32,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=33)/("X"*480)],iface="enp134s0f0")

3. hit pattern/not defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E1")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

Test case: MAC_IPV6_TCP
=======================
the rules and packets in this test case is similar to "Test case: MAC_IPV6_UDP"
just change some parts of rules and packets:

    rule:
        change udp to tcp, change ipv6-udp to ipv6-tcp
    packets:
        if the packet's L4 layer is UDP, change it to TCP;
        if the packet's L4 layer is TCP, change it to UDP;
        if tunnel packet, change inner L4 layer from UDP to TCP;
        if tunnel packet, change inner L4 layer from TCP to UDP;

Subcase: MAC_IPV6_TCP_L2SRC
---------------------------

Subcase: MAC_IPV6_TCP_L2DST
---------------------------

Subcase: MAC_IPV6_TCP_L2SRC_L2DST
---------------------------------

Subcase: MAC_IPV6_TCP_L3SRC
---------------------------

Subcase: MAC_IPV6_TCP_L3DST
---------------------------

Subcase: MAC_IPV6_TCP_L3SRC_L4SRC
---------------------------------

Subcase: MAC_IPV6_TCP_L3SRC_L4DST
---------------------------------

Subcase: MAC_IPV6_TCP_L3DST_L4SRC
---------------------------------

Subcase: MAC_IPV6_TCP_L3DST_L4DST
---------------------------------

Subcase: MAC_IPV6_TCP_L4SRC
---------------------------

Subcase: MAC_IPV6_TCP_L4DST
---------------------------

Subcase: MAC_IPV6_TCP_ALL
-------------------------


Test case: MAC_IPV6_SCTP
========================
the rules and packets in this test case is similar to "Test case: MAC_IPV6_UDP"
just change some parts of rules and packets:

    rule:
        change udp to sctp, change ipv6-udp to ipv6-sctp
    packets:
        if the packet's L4 layer is UDP, change it to SCTP;
        if tunnel packet, change inner L4 layer from UDP to SCTP;
        others can be not changed.

Subcase: MAC_IPV6_SCTP_L2SRC
----------------------------

Subcase: MAC_IPV6_SCTP_L2DST
----------------------------

Subcase: MAC_IPV6_SCTP_L2SRC_L2DST
----------------------------------

Subcase: MAC_IPV6_SCTP_L3SRC
----------------------------

Subcase: MAC_IPV6_SCTP_L3DST
----------------------------

Subcase: MAC_IPV6_SCTP_L3SRC_L4SRC
----------------------------------

Subcase: MAC_IPV6_SCTP_L3SRC_L4DST
----------------------------------

Subcase: MAC_IPV6_SCTP_L3DST_L4SRC
----------------------------------

Subcase: MAC_IPV6_SCTP_L3DST_L4DST
----------------------------------

Subcase: MAC_IPV6_SCTP_L4SRC
----------------------------

Subcase: MAC_IPV6_SCTP_L4DST
----------------------------

Subcase: MAC_IPV6_SCTP_ALL
--------------------------


symmetric-toeplitz Test steps
=============================
all the test cases run the same test steps as below:

1. validate rule.
2. send hit pattern packets with switched value of input set in the rule.
   check the received packets have different hash value.
   check all the packets are distributed to queues by rss.
3. create rule and list rule.
4. send same packets with step 2.
   check the received packets have the same hash value.
   check all the packets are distributed to queues by rss.
5. send not hit pattern packets with switched value of input set in the rule.
   check the received packets have different hash value.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.
6. destroy the rule and list rule.
7. send same packets with step 2.
   check the received packets have different hash value, or have no hash value.

Test case: symmetric MAC_IPV4
=============================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="enp134s0f0")

ipv4-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)],iface="enp134s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.0.2')/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.2", src='192.168.0.1')/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")

3. not hit pattern with switched value of input set in the rule:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2928",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")


Test case: symmetric MAC_IPV4_UDP
=================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")

3. not hit pattern/not defined input set packets::
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")


Test case: symmetric MAC_IPV4_TCP
=================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=23,dport=22)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=23,dport=22)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan-eth-ipv4-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.0.2')/TCP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.2", src='192.168.0.1')/TCP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.0.2')/TCP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.2", src='192.168.0.1')/TCP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")

3. not hit pattern/not defined input set packets::
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan-eth-ipv4-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.0.2')/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.2", src='192.168.0.1')/UDP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")


Test case: symmetric MAC_IPV4_SCTP
==================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss func symmetric_toeplitz types ipv4-sctp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv4-sctp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/SCTP(sport=23,dport=22)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/SCTP(sport=23,dport=22)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan-eth-ipv4-sctp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.0.2')/SCTP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.2", src='192.168.0.1')/SCTP(sport=22,dport=23)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.1", src='192.168.0.2')/SCTP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IP(dst="192.168.0.2", src='192.168.0.1')/SCTP(sport=23,dport=22)/("X"*480)], iface="enp134s0f0")

3. not hit pattern/not defined input set packets::
ipv4-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")


Test case: symmetric MAC_IPV6
=============================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp134s0f0")

ipv6-frag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/IPv6ExtHdrFragment()/("X"*480)],iface="enp134s0f0")

ipv6-icmp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/ICMP()/("X"*480)],iface="enp134s0f0")

ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

ipv4-udp-vxlan-eth-ipv6 packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)], iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/UDP()/VXLAN()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)], iface="enp134s0f0")

3. not hit pattern with switched value of input set in the rule:
ipv4-nonfrag packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="enp134s0f0")

Test case: symmetric MAC_IPV6_UDP
=================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre-eth-ipv6-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. not hit pattern/not defined input set packets::
ipv6-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre-eth-ipv6-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

Test case: symmetric MAC_IPV6_TCP
=================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-tcp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre-eth-ipv6-tcp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. not hit pattern/not defined input set packets::
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre-eth-ipv6-udp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

Test case: symmetric MAC_IPV6_SCTP
==================================
1. create rss rule::

    flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss func symmetric_toeplitz types ipv6-sctp end key_len 0 queues end / end

2. hit pattern/defined input set:
ipv6-sctp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

nvgre-eth-ipv6-sctp packet::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IP()/NVGRE()/Ether()/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/SCTP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")

3. not hit pattern/not defined input set packets::
ipv6-udp packets::

    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")
    sendp([Ether(dst="00:11:22:33:44:55", src="68:05:CA:BB:26:E0")/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp134s0f0")


Test Case: negative case
========================
1. create rules with invalid input set::

    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types eth l3-src-only end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff3b61eb08, Invalid input set: Invalid argument
    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-udp end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff3b61eb08, Invalid input set: Invalid argument
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff3b61eb08, Invalid input set: Invalid argument
    testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff3b61eb08, Invalid input set: Invalid argument
    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv6 end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff3b61eb08, Invalid input set: Invalid argument
    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types ipv4 l3-src-only end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff3b61eb08, Invalid input set: Invalid argument
    testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss func symmetric_toeplitz types eth end key_len 0 queues end / end
    ice_flow_create(): Failed to create flow
    port_flow_complain(): Caught PMD error type 10 (item specification): cause: 0x7fff3b61eb08, Invalid input set: Invalid argument

   check all the rule failed to be created.


Test Case: multirules test
==========================

Subcase 1: two rules with same pattern but different hash input set, not hit default profile
--------------------------------------------------------------------------------------------

1. create a MAC_IPV4_UDP_L3_SRC_ONLY rule::

     flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_IPV4_UDP packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is different from the first packet.

3. create a rule with same pattern but different hash input set::

     flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_IPV4_UDP packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is the same as the first packet.
   change the field [Dest IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.7")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is different from the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   send a MAC_IPV4_UDP packet, you can find it hit default ipv4 profile::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")

   change the fields [Source IP] or [Dest IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.9")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.9")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")

   check the hash values of the last two packets are different from the first packet.
   destroy the rule 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   check the rule 0 not exists in the list.
   send a MAC_IPV4_UDP packet, you can find it hit default ipv4 profile::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")

   change the fields [Source IP] or [Dest IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.9")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")
     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.9")/UDP(dport=45)/Raw("x"*480)], iface="enp134s0f0")

   check the hash values of the last two packets are different from the first packet.

Subcase 2: two rules with same pattern but different hash input set, hit default profile
----------------------------------------------------------------------------------------

1. create a MAC_IPV4_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_IPV4_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*480)], iface="enp134s0f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is different from the first packet.
   change the field [Dest IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8")/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is the same as the first packet.

3. create a rule with same pattern but different hash input set::

     testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_IPV4_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*480)], iface="enp134s0f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is the same as the first packet.
   change the field [Dst IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.7")/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is different from the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   send the MAC_IPV4_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is not exist.

Subcase 3: two rules, scope smaller created first, and the larger one created later
-----------------------------------------------------------------------------------

1. create a MAC_IPV4_UDP_PAY_L4_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_IPV4_UDP_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="enp134s0f0")

   change the field [Source Port], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25, dport=45)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.8")/UDP(sport=23, dport=44)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is the same as the first packet.

3. create a MAC_IPV4_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_IPV4_UDP_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="enp134s0f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8")/UDP(sport=25, dport=99)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is the same as the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   repeat step 2, get the same result.
   destroy the rule 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   send a MAC_IPV4_UDP_PAY packet, check the hash values not exists.

Subcase 4: two rules, scope larger created first, and the smaller one created later
-----------------------------------------------------------------------------------

1. create a MAC_IPV4_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

2. send a MAC_IPV4_UDP_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="enp134s0f0")

   change the field [Source IP], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.8")/UDP(sport=25, dport=99)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is the same as the first packet.

3. create a MAC_IPV4_UDP_PAY_L3_SRC_ONLY rule::

     testpmd> flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end
     testpmd> flow list 0

   check the rule exists in the list.

4. send a MAC_IPV4_UDP_PAY packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=23, dport=45)/Raw("x"*480)], iface="enp134s0f0")

   change the field [Source Port], send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.3",dst="192.168.0.5")/UDP(sport=25, dport=45)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is different from the first packet.
   change other fields, send a packet::

     sendp([Ether(dst="00:11:22:33:44:55")/IP(src="192.168.0.7",dst="192.168.0.8")/UDP(sport=23, dport=44)/Raw("x"*480)], iface="enp134s0f0")

   check the hash value is the same as the first packet.

5. destroy the rule 1::

     testpmd> flow destroy 0 rule 1
     testpmd> flow list 0

   check the rule 1 not exists in the list.
   repeat step 2, hit ipv4 profile, get the same result.
   destroy the rule 0::

     testpmd> flow destroy 0 rule 0
     testpmd> flow list 0

   send a MAC_IPV4_UDP_PAY packet, check the hash values not exists.
