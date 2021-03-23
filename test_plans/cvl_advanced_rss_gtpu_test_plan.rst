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

==========================
CVL: Advanced RSS FOR GTPU
==========================

Description
===========
* Enable RSS for GTP-U Up/Down Link sperately.
* RSS based on 5 Tuple ( Src IP Address/Dst IP Address/Src Port/Dst Port/Protocol) using the DPDK RTE_FLOW rules for GTP-U packets).
* Support ipv4+ipv6 combination of GTP packet:
    ip4(outer) + ipv4(inner)
    ip4(outer) + ipv6(inner)
    ip6(outer) + ipv4(inner)
    ip6(outer) + ipv6(inner)
* Symmetric hash by rte_flow RSS action for GTP-U packets.
* simple-xor RSS support GTP-U.
* Need DDP Comms Package.

Pattern and input set
---------------------
.. table::

    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | Hash function: toeplitz                                                                                                                      |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    | Packet Type                   | Pattern                   | All the Input Set options in combination                                         |
    +===============================+===========================+==================================================================================+
    | GTP-U data packet types       | MAC_IPV4_GTPU_IPV4        | gtpu, ipv4, l3-src-only, l3-dst-only                                             |
    | IPv4/IPv6 transport           |                           |                                                                                  |
    | IPv4/IPv6 payload             |                           |                                                                                  |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV4_UDP    | gtpu, ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv4         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV4_TCP    | gtpu, ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv4         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV6        | gtpu, ipv6, l3-src-only, l3-dst-only                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV6_UDP    | gtpu, ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv6         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_IPV6_TCP    | gtpu, ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv6         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV4        | gtpu, ipv4, l3-src-only, l3-dst-only                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV4_UDP    | gtpu, ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv4         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV4_TCP    | gtpu, ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv4         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV6        | gtpu, ipv6, l3-src-only, l3-dst-only                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV6_UDP    | gtpu, ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv6         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_IPV6_TCP    | gtpu, ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv6         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4     | gtpu, ipv4, l3-src-only, l3-dst-only                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4_UDP | gtpu, ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv4         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4_TCP | gtpu, ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv4         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6     | gtpu, ipv6, l3-src-only, l3-dst-only                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6_UDP | gtpu, ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv6         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6_TCP | gtpu, ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv6         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4     | gtpu, ipv4, l3-src-only, l3-dst-only                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4_UDP | gtpu, ipv4-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv4         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4_TCP | gtpu, ipv4-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv4         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6     | gtpu, ipv6, l3-src-only, l3-dst-only                                             |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6_UDP | gtpu, ipv6-udp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv6         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6_TCP | gtpu, ipv6-tcp, l3-src-only, l3-dst-only, l4-src-only, l4-dst-only, ipv6         |
    +-------------------------------+---------------------------+----------------------------------------------------------------------------------+

.. table::

    +-------------------------------+---------------------------+-------------------+
    | Hash function: Symmetric_toeplitz                                             |
    +-------------------------------+---------------------------+-------------------+
    | Packet Type                   | Pattern                   | Input Set         |
    +===============================+===========================+===================+
    | GTP-U data packet types       | MAC_IPV4_GTPU_IPV4        | ipv4              |
    | IPv4/IPv6 transport           |                           |                   |
    | IPv4/IPv6 payload             |                           |                   |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_IPV4_UDP    | ipv4-udp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_IPV4_TCP    | ipv4-tcp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_IPV6        | ipv6              |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_IPV6_UDP    | ipv6-udp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_IPV6_TCP    | ipv6-tcp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_IPV4        | ipv4              |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_IPV4_UDP    | ipv4-udp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_IPV4_TCP    | ipv4-tcp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_IPV6        | ipv6              |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_IPV6_UDP    | ipv6-udp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_IPV6_TCP    | ipv6-tcp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4     | ipv4              |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4_UDP | ipv4-udp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV4_TCP | ipv4-tcp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6     | ipv6              |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6_UDP | ipv6-udp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV4_GTPU_EH_IPV6_TCP | ipv6-tcp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4     | ipv4              |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4_UDP | ipv4-udp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV4_TCP | ipv4-tcp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6     | ipv6              |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6_UDP | ipv6-udp          |
    +-------------------------------+---------------------------+-------------------+
    |                               | MAC_IPV6_GTPU_EH_IPV6_TCP | ipv6-tcp          |
    +-------------------------------+---------------------------+-------------------+


Prerequisites
=============

1. Hardware:

   - Intel E810 series ethernet cards: columbiaville_25g/columbiaville_100g/

2. Software:

   - dpdk: http://dpdk.org/git/dpdk
   - scapy: http://www.secdev.org/projects/scapy/

.. note::

   This rss feature designed for CVL NIC 25G and 100g, so below the case only support CVL nic.

3. bind the CVL port to dpdk driver in DUT::

    modprobe vfio-pci
    usertools/dpdk-devbind.py --force --bind=vfio-pci 0000:3b:00.0

.. note::

   The kernel must be >= 3.6+ and VT-d must be enabled in bios.

4. Launch the testpmd to configuration queue of rx and tx number 64 in DUT::

    testpmd>./x86_64-native-linuxapp-gcc/app/testpmd  -c 0xff -n 4 -- -i --rxq=64 --txq=64 --disable-rss --port-topology=loop
    testpmd>set fwd rxonly
    testpmd>set verbose 1

5. start scapy and configuration NVGRE and GTP profile in tester
   scapy::

    >>> import sys
    >>> from scapy.contrib.gtp import *

.. note::

   There are some gaps between the expected result and actual result in multirule cases and combination cases.
   the gaps will be resolved in 20.11 release, so the related cases will not be automated before fix version.

toeplitz cases
==============
all the test cases in the pattern::

    outer ipv4 + inner ipv4
    outer ipv4 + inner ipv6
    outer ipv6 + inner ipv4
    outer ipv6 + inner ipv6

run the same test steps as below:

1. validate rule.
2. create rule and list rule.
3. send a basic hit pattern packet,record the hash value.
   check the packet distributed to queue by rss.
4. send hit pattern packets with changed input set in the rule.
   check the received packets have different hash value with basic packet.
   check all the packets are distributed to queues by rss.
5. send hit pattern packets with changed input set not in the rule.
   check the received packet have same hash value with the basic packet.
   check all the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.
6. send not hit pattern packets with input set in the rule.
   check the received packets have not hash value, and distributed to queue 0.
   note: if there is not this type packet in the case, omit this step.
7. distroy the rule and list rule.
8. send same packets with step 3.
   check the received packets have not hash value, and distributed to queue 0,

Pattern: outer ipv4 + inner ipv4
--------------------------------

Test case: MAC_IPV4_GTPU_EH_IPV4 with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

DL case

basic hit pattern packets are the same in this test case:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp216s0f0")

ipv4-udp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp216s0f0")

all the DL cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_L3DST
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/TCP()/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_L3SRC
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-udp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP()/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-udp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_GTPU
::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/ICMP()/("X"*480)],iface="enp216s0f0")


UL case

basic hit pattern packets are the same in this test case:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-tcp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP()/("X"*480)],iface="enp216s0f0")

ipv4-udp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp216s0f0")

all the UL cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_L3DST
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_L3DST.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_L3SRC
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_L3SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_GTPU
::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types gtpu end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_UL_IPV4_GTPU.


Test case: MAC_IPV4_GTPU_EH_IPV4_UDP with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

DL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

all the DL cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_IPV4
::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_UDP_GTPU
::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

UL case

basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

all the UL cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L3DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L3SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4DST.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3DST_L4SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4DST.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L3SRC_L4SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4DST.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_L4SRC.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_IPV4
::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_IPV4.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP.

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_UDP_GTPU
::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss types gtpu end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase MAC_IPV4_GTPU_EH_DL_IPV4_UDP_GTPU.


Test case: MAC_IPV4_GTPU_EH_IPV4_TCP with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
the rules and packets in this test case is similar to "Test case: MAC_IPV4_GTPU_EH_IPV4_UDP with UL/DL"
just change some parts of rules and packets:

    rule:
        change inner udp to tcp, change ipv4-udp to ipv4-tcp
    packets:
        if the packet's inner L4 layer is UDP, change it to TCP;
        if the packet's inner L4 layer is TCP, change it to UDP;

DL case

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3DST
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3SRT
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L4DST
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP
:::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_DL_IPV4_TCP_GTPU
::::::::::::::::::::::::::::::::::::::::::

UL case

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3DST
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3SRT
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L4DST
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_L4SRC
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP
:::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_UL_IPV4_TCP_GTPU
::::::::::::::::::::::::::::::::::::::::::


Test case: MAC_IPV4_GTPU_EH_IPV4 without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-udp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp216s0f0")

all the cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_L3DST
::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set::
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-udp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-udp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP()/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_L3SRC
::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4
::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_GTPU
:::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

Test case: MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

all the cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L3DST_L4DST
::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L4DST
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_L4SRC
::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_IPV4
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP
::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_EH_IPV4_UDP_GTPU
:::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32, dport=33)/("X"*480)],iface="enp216s0f0")

Test case: MAC_IPV4_GTPU_EH_IPV4_TCP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
the rules and packets in this test case is similar to "Test case: MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL"
just change some parts of rules and packets:

    rule:
        change inner udp to tcp, change ipv4-udp to ipv4-tcp
    packets:
        if the packet's inner L4 layer is UDP, change it to TCP;
        if the packet's inner L4 layer is TCP, change it to UDP;

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST
::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRT
::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST_L4DST
::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3DST_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC_L4DST
::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L3SRC_L4SRC
::::::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L4DST
::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_L4SRC
::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP
::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_EH_IPV4_TCP_GTPU
:::::::::::::::::::::::::::::::::::::::


Test case: MAC_IPV4_GTPU_IPV4
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-udp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp216s0f0")

all the cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_L3DST
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set:
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-udp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::
ipv4-nonfrag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

ipv4-frag packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2",frag=6)/("X"*480)],iface="enp216s0f0")

ipv4-icmp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2")/ICMP()/("X"*480)],iface="enp216s0f0")

ipv4-udp packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP()/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_L3SRC
:::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4
:::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_GTPU
::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

Test case: MAC_IPV4_GTPU_IPV4_UDP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
basic hit pattern packets are the same in this test case::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

all the cases have same pattern, so we send same
not hit pattern/not defined input set packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L4DST
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_L4SRC
:::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_IPV4
::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4 end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP
:::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=32,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: MAC_IPV4_GTPU_IPV4_UDP_GTPU
::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types gtpu end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

hit pattern/not defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1", src="192.168.1.2")/UDP(sport=32,dport=33)/("X"*480)],iface="enp216s0f0")


Test case: MAC_IPV4_GTPU_IPV4_TCP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
the rules and packets in this test case is similar to "Test case: MAC_IPV4_GTPU_IPV4_UDP"
just change some parts of rules and packets:

    rule:
        change inner udp to tcp, change ipv4-udp to ipv4-tcp
    packets:
        if the packet's inner L4 layer is UDP, change it to TCP;
        if the packet's inner L4 layer is TCP, change it to UDP;

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3DST
:::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3SRT
:::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3DST_L4DST
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3DST_L4SRC
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3SRC_L4DST
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L3SRC_L4SRC
:::::::::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L4DST
:::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_IPV4_TCP_L4SRC
:::::::::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_IPV4_TCP
:::::::::::::::::::::::::::::::

Subcase: MAC_IPV4_GTPU_IPV4_TCP_GTPU
::::::::::::::::::::::::::::::::::::

Pattern: outer ipv4 + inner ipv6
--------------------------------

reconfig all the cases of "Pattern: outer ipv4 + inner ipv4"

    rule:
        change inner ipv4 to ipv6, change ipv4-udp to ipv6-udp, change ipv4-tcp to ipv6-tcp.
    packets:
        change the packet's inner L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.

Pattern: outer ipv6 + inner ipv4
--------------------------------

reconfig all the cases of "Pattern: outer ipv4 + inner ipv4"

    rule:
        change outer ipv4 to ipv6.
    packets:
        change the packet's outer L3 layer from IP to IPv6;

Pattern: outer ipv6 + inner ipv6
--------------------------------

reconfig all the cases of "Pattern: outer ipv4 + inner ipv4"

    rule:
        change outer ipv4 to ipv6.
        change inner ipv4 to ipv6, change ipv4-udp to ipv6-udp, change ipv4-tcp to ipv6-tcp.
    packets:
        change the packet's outer L3 layer from IP to IPv6;
        change the packet's inner L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.

negative case
=============
Subcase: invalid input set 
--------------------------
1. create rules with invalid input set::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types tcp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss types ipv4-tcp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss types tcp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / tcp / end actions rss types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp ipv6 end key_len 0 queues end / end

   check all the rule failed to be created.

2. validate all the rules in step 1, check all the rule failed to be validated.

default pattern supported case
==============================
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. send packets with switched l3 address of each packet type in the list:

   IPv4_GTPU_EH_DL_IPv4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_UL_IPv4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_DL_IPv4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_UL_IPv4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_DL_IPv4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_UL_IPv4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_IPv4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_IPv4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_IPv4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_DL_IPv6::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_UL_IPv6::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_DL_IPv6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_UL_IPv6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_DL_IPv6_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_EH_UL_IPv6_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_IPv6::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_IPv6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv4_GTPU_IPv6_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_DL_IPv4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_UL_IPv4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_DL_IPv4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_UL_IPv4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_DL_IPv4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_UL_IPv4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_IPv4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2", src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_IPv4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_IPv4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_DL_IPv6::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_UL_IPv6::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_DL_IPv6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_UL_IPv6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_DL_IPv6_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_EH_UL_IPv6_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_IPv6::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_IPv6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

   IPv6_GTPU_IPv6_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

3. check all the packets with symmetric L3 address have different hash value and distributed to queues by RSS.

inner L4 protocal hash case
===========================

Subcase: MAC_IPV4_GTPU_IPV4_UDP/TCP
-----------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

4. check the two packets received with different hash values, and distributed to queue by RSS.

5. flush the rules, send the two packets again, check they are distributed to the same queue.

Subcase: MAC_IPV4_GTPU_EH_IPV6_UDP/TCP
--------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

4. check the two packets received with different hash values, and distributed to queue by RSS.

5. flush the rules, send the two packets again, check they are distributed to the same queue.

Subcase: MAC_IPV6_GTPU_IPV4_UDP/TCP
-----------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create rules::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

4. check the two packets received with different hash values, and distributed to queue by RSS.

5. flush the rules, send the two packets again, check they are distributed to the same queue.

Subcase: MAC_IPV6_GTPU_EH_IPV6_UDP/TCP
--------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create rules::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss types ipv6-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss types ipv6-tcp end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")

4. check the two packets received with different hash values, and distributed to queue by RSS.

5. flush the rules, send the two packets again, check they are distributed to the same queue.

multirules case
===============
Subcase: IPV4_GTPU_IPV4/IPV4_GTPU_EH_IPV4
-----------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create IPV4_GTPU_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check the three packets have different hash value.
   send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")

   check the three packets have different hash value.

4. create IPV4_GTPU_EH_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.
   send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

6. destroy IPV4_GTPU_IPV4 rule::

    flow destroy 0 rule 0

7. send same packets with step 5,
   packet 1-3 have not hash value, and distributed to queue 0.
   packet 4-9 get same result with step 5.

8. re-create IPV4_GTPU_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss types gtpu end key_len 0 queues end / end

9. send same packets with step 5,
   packet 1-9 get same result with step 5.

10. destroy IPV4_GTPU_EH_IPV4 rule::

     flow destroy 0 rule 1

11. send same packets with step 5,
    packet 1-3 get same result with step 5.
    packet 4-9 have not hash value, and distributed to queue 0.

Subcase: IPV4_GTPU_EH_IPV4 with/without UL/DL
---------------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create IPV4_GTPU_DL_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check the three packets have different hash value.

4. create IPV4_GTPU_EH_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

5. send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.
   send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

6. destroy IPV4_GTPU_EH_IPV4 rule::

    flow destroy 0 rule 1

7. send same packets with step 5,
   packet 1-6 have not hash value.


Subcase: IPV4_GTPU_EH_IPV4 without/with UL/DL
---------------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create IPV4_GTPU_EH_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

3. send packets::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   check packet 5 has same hash value with packet 4, packet 6 has different hash value with packet 4.

4. create IPV4_GTPU_UL_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

5. send same packets with step 3,
   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   check packet 5 has different hash value with packet 4, packet 6 has same hash value with packet 4.

6. destroy IPV4_GTPU_EH_IPV4 rule::

    flow destroy 0 rule 0

7. send same packets with step 3,
   packet 1-3 have not hash value, and distributed to queue 0,
   check packet 5 has different hash value with packet 4, packet 6 has same hash value with packet 4.

8. re-create IPV4_GTPU_EH_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

9. send same packets with step 3,
   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   check packet 5 has same hash value with packet 4, packet 6 has different hash value with packet 4.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

10. destroy IPV4_GTPU_EH_IPV4 rule again::

     flow destroy 0 rule 2

11. send same packets with step 3,
    packet 1-6 have not hash value, and distributed to queue 0.


Subcase: IPV4_GTPU_EH_IPV4 and IPV4_GTPU_EH_IPV4_UDP/TCP
--------------------------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. send packets with different inner UDP/TCP port::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   check packet 5 has same hash value with packet 4, packet 6 has different hash value with packet 4.
   check packet 8 has different hash value to packet 7, packet 9 have different hash value to packet 7 and 8.
   check packet 11 has different hash value to packet 10, packet 12 have different hash value to packet 10 and 11.

3. create IPV4_GTPU_DL_IPV4_UDP rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

4. send same packets with step 2,
   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   check packet 5 has different hash value with packet 4, packet 6 has same hash value with packet 4.
   check packet 8 has different hash value to packet 7, packet 9 have different hash value to packet 7 and 8.
   check packet 11 has different hash value to packet 10, packet 12 have different hash value to packet 10 and 11.

5. create IPV4_GTPU_UL_IPV4::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss types ipv4 l3-src-only end key_len 0 queues end / end

6. send same packets with step 2,
   check packet 2 has same hash value with packet 1, packet 3 has same hash value with packet 1.
   check packet 5 has different hash value with packet 4, packet 6 has same hash value with packet 4.
   check packet 8 has different hash value to packet 7, packet 9 have different hash value to packet 7 and 8.
   check packet 11 has different hash value to packet 10, packet 12 have same hash value to packet 10.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

7. destroy IPV4_GTPU_DL_IPV4_UDP rule::

    testpmd> flow destroy 0 rule 0

8. send same packets with step 2,
   check packet 2 has same hash value with packet 1, packet 3 has same hash value with packet 1.
   check packet 5 has same hash value with packet 4, packet 6 has different hash value with packet 4.
   check packet 8 has different hash value to packet 7, packet 9 have different hash value to packet 7 and 8.
   check packet 11 has different hash value to packet 10, packet 12 have same hash value to packet 10.

9. destroy IPV4_GTPU_UL_IPV4 rule::

    testpmd> flow destroy 0 rule 1

10. send same packets with step 2,
    check packet 1-3 have not hash value.
    check packet 5 has same hash value with packet 4, packet 6 has different hash value with packet 4.
    check packet 8 has different hash value to packet 7, packet 9 have different hash value to packet 7 and 8.
    check packet 10-12 have not hash value.


Subcase: IPV6_GTPU_EH_IPV6 and IPV6_GTPU_EH_IPV6_UDP/TCP
--------------------------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. send packets with different inner UDP/TCP port::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="enp216s0f0")

   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   check packet 5 has same hash value with packet 4, packet 6 has different hash value with packet 4.
   check packet 8 has different hash value to packet 7, packet 9 have different hash value to packet 7 and 8.
   check packet 11 has different hash value to packet 10, packet 12 have different hash value to packet 10 and 11.

3. create rule 0::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end

4. send same packets with step 2,
   check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.
   check packet 5 has same hash value with packet 4, packet 6 has different hash value with packet 4.
   check packet 8 has different hash value to packet 7, packet 9 have different hash value to packet 7 and 8.
   check packet 11 has different hash value to packet 10, packet 12 have different hash value to packet 10 and 11.

5. create rule 1::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 0 / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end

6. send same packets with step 2,
   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   check packet 5 has same hash value with packet 4, packet 6 has different hash value with packet 4.
   check packet 8 has same hash value to packet 7, packet 9 have different hash value to packet 7.
   check packet 11 has different hash value to packet 10, packet 12 have different hash value to packet 10 and 11.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

7. destroy the rule 1::

    testpmd> flow destroy 0 rule 1

8. send same packets with step 2,
   check packet 1-3 have not hash value, and distributed to queue 0.
   check packet 5 has same hash value with packet 4, packet 6 has different hash value with packet 4.
   check packet 7-9 have not hash value, and distributed to queue 0.
   check packet 11 has different hash value to packet 10, packet 12 have different hash value to packet 10 and 11.

9. create rule 1 again, send destroy the rule 0, send same packets with step 2,
   check packet 2 has same hash value with packet 1, packet 3 has different hash value with packet 1.
   check packet 5 has same hash value with packet 4, packet 6 has different hash value with packet 4.
   check packet 8 has same hash value to packet 7, packet 9 have different hash value to packet 7.
   check packet 11 has different hash value to packet 10, packet 12 have different hash value to packet 10 and 11.


Subcase: IPV4_GTPU_EH_IPV6 and IPV4_GTPU_EH_IPV6_UDP/TCP without UL/DL
----------------------------------------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. send packets with different inner UDP/TCP port::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/TCP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2928",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2021")/("X"*480)],iface="enp216s0f0")

   check packet 2 has same hash value to packet 1.
   check packet 3 and packet 4 have different hash value to packet 1.
   check packet 5 and packet 6 and packet 7 have different hash value.

3. create rule 0::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end key_len 0 queues end / end

4. send same packets with step 2,
   check packet 2 has different hash value to packet 1.
   check packet 3 and packet 4 have same hash value to packet 1.
   check packet 5 and packet 6 and packet 7 have different hash value.

5. create rule 1::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv6 / end actions rss types ipv6 l3-dst-only end key_len 0 queues end / end

6. send same packets with step 2,
   check packet 2 has same hash value to packet 1.
   check packet 3 has same hash value to packet 1.
   check packet 4 has different hash value to packet 1.
   check packet 6 has same hash value to packet 5.
   check packet 7 has differnt hash value to packet 5.


Subcase: IPV6_GTPU_IPV4 and IPV6_GTPU_IPV4_UDP/TCP
--------------------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. send packets with different inner UDP/TCP port::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22,dport=33)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1",src="192.168.0.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.1.2")/UDP(sport=22,dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.1.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.1.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")

   check packet 2 has same hash value to packet 1.
   check packet 3 and packet 4 have different hash value to packet 1.
   check packet 5 and packet 6 and packet 7 have different hash value.

3. create rule 0::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end key_len 0 queues end / end

4. send same packets with step 2,
   check packet 2 has different hash value to packet 1.
   check packet 3 and packet 4 have same hash value to packet 1.
   check packet 5 and packet 6 and packet 7 have different hash value.

5. create rule 1::

    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

6. send same packets with step 2,
   check packet 2 has same hash value to packet 1.
   check packet 3 has different hash value to packet 1.
   check packet 4 has same hash value to packet 1.
   check packet 6 has same hash value to packet 5.
   check packet 7 has differnt hash value to packet 5.


toeplitz and symmetric rules combination
========================================
Subcase: toeplitz/symmetric with same pattern
---------------------------------------------
1. create a toeplitz rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")

   check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

3. create a symmetric rule:: 

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

4. send packets with switched inner ipv4 address::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp216s0f0")

   check the two packets have same hash value.

5. DUT verify rule can be listed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS
    1       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS

6. repeat step 2, check the toeplitz rule can't work now, but have hash value.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

7. destroy the rule 1::

    testpmd> flow destroy 0 rule 1

8. repeat step 4, check the symmetric can't work now, the packets have not hash value.

9. repeat step 2, check the toeplitz also can't work now, the packets have not hash value.

Subcase: toeplitz/symmetric with same pattern (switched rule order)
-------------------------------------------------------------------
1. create a symmetric rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

2. send packets with switched inner ipv4 address::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp216s0f0")

   check the two packets have same hash value.

3. create a toeplitz rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

4. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.10.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.10.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")

   check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

5. DUT verify rule can be listed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS
    1       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS

6. repeat step 2, check the symmetric rule can't work now, but have hash value.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

7. destroy the rule 1::

    testpmd> flow destroy 0 rule 1

8. repeat step 4, check the symmetric can't work now, the packets have not hash value.

9. repeat step 2, check the toeplitz also can't work now, the packets have not hash value.

Subcase: toeplitz/symmetric with different pattern (different UL/DL)
--------------------------------------------------------------------
1. create a toeplitz rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")

   check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.

3. create a symmetric rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

4. send packets with switched inner ipv4 address::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp216s0f0")

   check the two packets have same hash value.

5. DUT verify rule can be listed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS
    1       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS

6. repeat step 2, check the toeplitz rule also can work now.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

7. destroy the rule 1::

    testpmd> flow destroy 0 rule 1

8. repeat step 4, check the symmetric can't work now, the packets have not hash value.

9. repeat step 2, check the toeplitz also can work now.

10. DUT re-create the symmetric rule::

     flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

11. destroy the rule 0::

     testpmd> flow destroy 0 rule 0

12. repeat step 4, check the symmetric also can work now.

13. repeat step 2, check the toeplitz can't work now, the packets have not hash value.

Subcase: toeplitz/symmetric with different pattern (with/without UL/DL)
-----------------------------------------------------------------------
1. create a toeplitz rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")

   check packet 2 has different hash value with packet 1, packet 3 has same hash value with packet 1.
   check packet 5 has different hash value with packet 4, packet 6 has same hash value with packet 4.

3. create a symmetric rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

4. send packets with switched inner ipv4 address::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1",dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.2",dst="192.168.0.1")/("X"*480)], iface="enp216s0f0")

   check the two packets have same hash value.

5. DUT verify rule can be listed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS
    1       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS

6. repeat step 2, check the toeplitz rule can work for UL packets, not work for DL packets.
   the DL and UL packets both have hash value.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

7. destroy the rule 1::

    testpmd> flow destroy 0 rule 1

8. repeat step 4, check the symmetric can't work now.

9. repeat step 2, check the toeplitz can work for both UL and DL packets.

10. DUT re-create the symmetric rule::

     flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

11. repeat step 4, check the symmetric can work now.

12. destroy the rule 0::

     testpmd> flow destroy 0 rule 0

13. repeat step 4, check the symmetric also can work now.

14. repeat step 2, check the toeplitz can't work now, the UL packets have not hash value.

Subcase: toeplitz/symmetric with different pattern
--------------------------------------------------
1. create a toeplitz rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end key_len 0 queues end / end

2. send packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.1", dst="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=32, dport=23)/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.1.2")/UDP(sport=22, dport=33)/("X"*480)], iface="enp216s0f0")

   check packet 2 and packet 3 have different hash value with packet 1, packet 4 has same hash value with packet 1.

3. create a symmetric rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end

4. send packets with switched inner ipv6 address::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888",dst="2222:3333:4444:5555:6666:7777:8888:9999")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="2222:3333:4444:5555:6666:7777:8888:9999",dst="1111:2222:3333:4444:5555:6666:7777:8888")/("X"*480)], iface="enp216s0f0")

   check the two packets have same hash value.

5. DUT verify rule can be listed::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 UDP => RSS
    1       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV6 => RSS

6. repeat step 2, check the toeplitz rule also can work now.

Note: the action after deleting rule is not guaranteed so far.
so the following step don't need to be run.

7. destroy the rule 1::

    testpmd> flow destroy 0 rule 1

8. repeat step 4, check the symmetric can't work now.

9. repeat step 2, check the toeplitz also can work now.

10. DUT re-create a symmetric rule::

     flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / end actions rss func symmetric_toeplitz types ipv6 end key_len 0 queues end / end

11. repeat step 4, check the symmetric can work now.

12. destroy the rule 0::

     testpmd> flow destroy 0 rule 0

13. repeat step 4, check the symmetric also can work now.

14. repeat step 2, check the toeplitz can't work now, the packets have hash value.


stress cases
============
Subcase: add/delete IPV4_GTPU_UL_IPV4_TCP rules
-----------------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create/delete IPV4_GTPU_UL_IPV4_TCP rule 100 times::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end key_len 0 queues end / end
    flow destroy 0 rule 0

3. create the rule again, and list the rule::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 TCP => RSS

4. send IPV4_GTPU_UL_IPV4_TCP packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.1.1", dst="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=32, dport=23)/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.1.2")/TCP(sport=22, dport=33)/("X"*480)], iface="enp216s0f0")

   check packet 2 and packet 3 have different hash value with packet 1, packet 4 has same hash value with packet 1.

Subcase: add/delete IPV4_GTPU_DL_IPV4 rules
-------------------------------------------
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

2. create/delete IPV4_GTPU_DL_IPV4 rule 100 times::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss types ipv4 l3-dst-only end key_len 0 queues end / end
    flow destroy 0 rule 0

3. create the rule again, and list the rule::

    testpmd> flow list 0
    ID      Group   Prio    Attr    Rule
    0       0       0       i--     ETH IPV4 UDP GTPU GTP_PSC IPV4 => RSS

4. send IPV4_GTPU_DL_IPV4 packets::

    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.0.1", dst="192.168.1.2")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="00:11:22:33:44:55")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x12345)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(src="192.168.1.1", dst="192.168.0.2")/("X"*480)], iface="enp216s0f0")

   check packet 2 have different hash value with packet 1, packet 3 has same hash value with packet 1.

symmetric cases
===============

start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --port-topology=loop

all the test cases run the same test steps as below:

1. validate rule.
2. if the rule inner protocol is IPV4_UDP/TCP or IPV6_UDP/TCP,
   set "port config all rss all".
3. send a basic hit pattern packet,record the hash value.
   then send a hit pattern packet with switched value of input set in the rule.
   check the two received packets have different hash value.
   check both the packets are distributed to queues by rss.
4. create rule and list rule.
5. send same packets with step 2.
   check the received packets have same hash value.
   check both the packets are distributed to queues by rss.
6. send two not hit pattern packets with switched value of input set in the rule.
   check the received packets have different hash value.
   check both the packets are distributed to queues by rss.
   note: if there is not this type packet in the case, omit this step.
7. distroy the rule and list rule.
8. send the same packets in step3, only switch ip address.
   check the received packets which switched ip address have different hash value.

Pattern: symmetric outer ipv4 + inner ipv4
------------------------------------------

Test case: symmetric MAC_IPV4_GTPU_EH_IPV4 with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Subcase: symmetric MAC_IPV4_GTPU_EH_DL_IPV4
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

hit pattern/defined input set:
MAC_IPV4_GTPU_EH_DL_IPV4 nonfrag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4 frag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_ICMP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/ICMP()/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP()/("X"*480)],iface="enp216s0f0")
    
not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_EH_UL_IPV4 nonfrag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_UL_IPV4 frag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_UL_IPV4_ICMP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/ICMP()/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_UL_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP()/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP()/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_DL_IPV6 nonfrag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4 nonfrag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

Subcase: symmetric MAC_IPV4_GTPU_EH_UL_IPV4
:::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase symmetric MAC_IPV4_GTPU_EH_DL_IPV4.

Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_UDP with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Subcase: symmetric MAC_IPV4_GTPU_EH_DL_IPV4_UDP
:::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_EH_UL_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_DL_IPV4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1", src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2", src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_DL_IPV6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2", src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Subcase: symmetric MAC_IPV4_GTPU_EH_UL_IPV4_UDP
:::::::::::::::::::::::::::::::::::::::::::::::
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

packets: change the pdu_type value(0->1/1->0) of packets of Subcase symmetric MAC_IPV4_GTPU_EH_DL_IPV4_UDP.


Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_TCP with UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
the rules and packets in this test case is similar to "Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_UDP with UL/DL"
just change some parts of rules and packets:

    rule:
        change inner udp to tcp, change ipv4-udp to ipv4-tcp
    packets:
        if the packet's inner L4 layer is UDP, change it to TCP;
        if the packet's inner L4 layer is TCP, change it to UDP;

Subcase: symmetric MAC_IPV4_GTPU_EH_DL_IPV4_TCP
:::::::::::::::::::::::::::::::::::::::::::::::

Subcase: symmetric MAC_IPV4_GTPU_EH_UL_IPV4_TCP
:::::::::::::::::::::::::::::::::::::::::::::::

Test case: symmetric MAC_IPV4_GTPU_EH_IPV4 without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

hit pattern/defined input set:
MAC_IPV4_GTPU_EH_IPV4 nonfrag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_IPV4 frag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.3",src="192.168.0.4",frag=6)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.4",src="192.168.0.3",frag=6)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_IPV4_ICMP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.6",src="192.168.0.5")/ICMP()/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.5",src="192.168.0.6")/ICMP()/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_EH_IPV6 nonfrag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4 nonfrag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set:
MAC_IPV4_GTPU_EH_DL_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_UL_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=1, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_EH_IPV4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_IPV6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_TCP without UL/DL
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
the rules and packets in this test case is similar to "Test case: symmetric MAC_IPV4_GTPU_EH_IPV4_UDP without UL/DL"
just change some parts of rules and packets:

    rule:
        change inner udp to tcp, change ipv4-udp to ipv4-tcp
    packets:
        if the packet's inner L4 layer is UDP, change it to TCP;
        if the packet's inner L4 layer is TCP, change it to UDP;


Test case: symmetric MAC_IPV4_GTPU_IPV4
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / end actions rss func symmetric_toeplitz types ipv4 end key_len 0 queues end / end

hit pattern/defined input set:
MAC_IPV4_GTPU_IPV4 nonfrag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4 frag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1", src="192.168.0.2",frag=6)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2", src="192.168.0.1",frag=6)/("X"*480)],iface="enp216s0f0")

MAC_IPV_GTPU_IPV4_ICMP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/ICMP()/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

MAC_IPV_GTPU_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP()/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP()/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_IPV6 nonfrag::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_EH_IPV4::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")

Test case: symmetric MAC_IPV4_GTPU_IPV4_UDP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end

hit pattern/defined input set:
MAC_IPV4_GTPU_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

not hit pattern with switched value of input set in the rule:
MAC_IPV4_GTPU_EH_IPV4_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV4_TCP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")

MAC_IPV4_GTPU_IPV6_UDP::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(dst="ABAB:910B:6666:3457:8295:3333:1800:2929",src="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")

Test case: symmetric MAC_IPV4_GTPU_IPV4_TCP
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
the rules and packets in this test case is similar to "Test case: symmetric MAC_IPV4_GTPU_IPV4_UDP"
just change some parts of rules and packets:

    rule:
        change inner udp to tcp, change ipv4-udp to ipv4-tcp
    packets:
        if the packet's inner L4 layer is UDP, change it to TCP;
        if the packet's inner L4 layer is TCP, change it to UDP;

Pattern: symmetric outer ipv4 + inner ipv6
------------------------------------------

reconfig all the cases of "Pattern: symmetric outer ipv4 + inner ipv4"

    rule:
        change inner ipv4 to ipv6, change ipv4-udp to ipv6-udp, change ipv4-tcp to ipv6-tcp.
    packets:
        change the packet's inner L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.

Pattern: symmetric outer ipv6 + inner ipv4
------------------------------------------

reconfig all the cases of "Pattern: symmetric outer ipv4 + inner ipv4"

    rule:
        change outer ipv4 to ipv6.
    packets:
        change the packet's outer L3 layer from IP to IPv6;

Pattern: symmetric outer ipv6 + inner ipv6
------------------------------------------

reconfig all the cases of "Pattern: symmetric outer ipv4 + inner ipv4"

    rule:
        change outer ipv4 to ipv6.
        change inner ipv4 to ipv6, change ipv4-udp to ipv6-udp, change ipv4-tcp to ipv6-tcp.
    packets:
        change the packet's outer L3 layer from IP to IPv6;
        change the packet's inner L3 layer from IP to IPv6;
        change the ipv4 address to ipv6 address.

symmetric negative cases
========================
1. create rules with invalid input set::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types gtpu end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 l3-dst-only end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types tcp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp l3-src-only end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp l4-dst-only end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end

   check all the rules failed to be created.

2. validate all the rules in step 1::

    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types gtpu end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4 l3-dst-only end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-udp end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types tcp end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp l3-src-only end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp l4-dst-only end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp l3-dst-only l4-src-only end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / udp / end actions rss func symmetric_toeplitz types ipv4-udp ipv4 end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv6 / udp / gtpu / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv4 / tcp / end actions rss func symmetric_toeplitz types ipv4-tcp ipv4 end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / udp / end actions rss func symmetric_toeplitz types ipv6-udp ipv6 end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv6 / udp / gtpu / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end
    flow validate 0 ingress pattern eth / ipv6 / udp / gtpu / gtp_psc pdu_t is 1 / ipv6 / tcp / end actions rss func symmetric_toeplitz types ipv6-tcp ipv6 end key_len 0 queues end / end

   check all the rule failed to be validated.

global simple-xor
=================
1. create a simple-xor rule::

    flow create 0 ingress pattern end actions rss func simple_xor key_len 0 queues end / end

2. send packets with switched l3 address::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.1",src="192.168.0.2")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst="192.168.0.2",src="192.168.0.1")/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.2",src="192.168.0.1")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IPv6()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="1.1.4.1",dst="2.2.2.3")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IP(src="2.2.2.3",dst="1.1.4.1")/("X"*480)], iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/("X" * 80)], iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/("X" * 80)], iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=22, dport=23)/("X" * 80)], iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="ABAB:910B:6666:3457:8295:3333:1800:2929",dst="CDCD:910A:2222:5498:8475:1111:3900:2020")/UDP(sport=22, dport=23)/("X" * 80)], iface="enp216s0f0")

   check the pair of packets with switched l3 address have same hash value, and distributed to same queue.

3. create ipv4_gtpu_ipv4_udp and ipv6_udp rules::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / ipv4 / tcp / end actions rss types ipv4-tcp end key_len 0 queues end / end
    flow create 0 ingress pattern eth / ipv6 / udp  / end actions rss types ipv6-udp end key_len 0 queues end / end

4. send packets with switched l4 port or inner l4 port::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=22, dport=23)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/IP(dst="192.168.0.1",src="192.168.0.2")/TCP(sport=23, dport=22)/("X"*480)],iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=22, dport=23)/("X" * 80)], iface="enp216s0f0")
    sendp([Ether(dst="68:05:ca:a3:28:94")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:2020",dst="ABAB:910B:6666:3457:8295:3333:1800:2929")/UDP(sport=23, dport=22)/("X" * 80)], iface="enp216s0f0")

   check the packets with switched l4 port have different hash values.

5. distroy the simple-xor rule::

    flow destroy 0 rule 0

   send the packets in step2, check the pair of packets with switched l3 address have different hash value.
   send the packets in step4, check the pair of packets with switched l4 port have different hash value.

6. distroy the ipv4_gtpu_ipv4_udp and ipv6_udp rules::

    flow flush 0

   send the packets in step2, check the pair of packets with switched l3 address have different hash value.
   send the packets in step4, check the pair of packets with switched l4 port have same hash value, and distributed to same queue.


rss function when disable rss
=============================
1. start testpmd without disable rss::

    ./x86_64-native-linuxapp-gcc/app/testpmd -c 0xff -n 4 -- -i --rxq=64 --txq=64 --disable-rss --port-topology=loop

2. create a IPV4_GTPU_EH_IPV4 rule::

    flow create 0 ingress pattern eth / ipv4 / udp / gtpu / gtp_psc pdu_t is 0 / ipv4 / udp / end actions rss types ipv4-udp end key_len 0 queues end / end

3. send 1280 packets of IPV4_GTPU_EH_IPV4 packet type::

    sendp([Ether(dst="68:05:CA:BB:26:E0")/IP()/UDP(dport=2152)/GTP_U_Header(gtp_type=255, teid=0x123456)/GTPPDUSessionContainer(type=0, P=1, QFI=0x34)/IP(dst=RandIP(),src=RandIP())/UDP(sport=RandShort(),dport=RandShort())/("X"*480)],iface="enp216s0f0",count=1280)

4. check all the packets have hash value and distributed to all queues by RSS.
